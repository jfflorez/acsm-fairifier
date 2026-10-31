# -*- coding: utf-8 -*-

"""
Description :
-------------
    EBAS ACSM data uploader - generate hourly ACTRIS-NRT file for one product and submit them to EBAS

Usage :
-------


Example :
---------

    python3 hourly_uploader.py ACSM_140113_RAW_NRT 2021-09-01T11 -v -x

    python3 hourly_uploader.py MEL_ACSM_140143_RAW_NRT 2021-12-28T10 -v -x

Limitations :
-------------
    -

Copyright (©) 2022:
-------------------
    Université de Lille ;
    Commissariat à l'énergie atomique et aux énergies alternatives (CEA) ;
    Centre national de la recherche scientifique (CNRS)

Author(s) :
--------
    AERIS/ICARE/UDEV Nicolas PASCAL

License :
---------
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.


History :
--------
    v0.0.0 : 2021/06/15
    - creation
"""

import os
import os.path
import sys
import re
import tempfile
import datetime
import shutil
from optparse import OptionParser
import configparser
import pysftp_extension

pkg_dir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkg_dir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

from ConverterFactory import ConverterFactory
from misc.AppContextController import NoInputException
from misc.FileTools import unix_to_os_path

import DataSeeker as DataSeeker


# --- APPLICATION ---#
__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]

# --- APP RETURN CODES ---#
EXIT_FAILURE = 1
EXIT_SUCCESS = 0


class HourlyUploader:
    # - string parsers
    re_hour_id = re.compile(
        r"^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})T(?P<hours>[0-9]{2})$")
    re_fname = re.compile(
        r"^.*_(?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})(?P<hours>[0-9]{2})(?P<minutes>[0-9]{2}).txt$")

    # - conversion processes factory
    factory = ConverterFactory()
    # - input files seeker
    data_seeker = DataSeeker.DataSeeker()

    def __init__(self,
                 out_dir=None,
                 verbose=False,
                 overwrite=False,
                 ):
        """
        Constructor
        @param out_dir output directory if not default one
        @param verbose display processing informations
        @param overwrite overwrite existing output files flag
        """
        # - check and parse hour format
        self.re_m_hour_id = None

        self.out_dir = out_dir
        self.verbose = verbose
        self.overwrite = overwrite
        self.tmp_dpath = None

        # - load configuration infos
        self.host = None
        self.rdir = None
        self.user = None
        self.fpath_private_key = None
        self.config = self.load_upload_cfg()

    def load_upload_cfg(self):
        """
        @brief decode site upload configuration infos
        """
        fpath_cfg = os.path.join(pkg_dir, "..", "cfg", "upload.cfg")
        parser = configparser.ConfigParser()
        parser.read(fpath_cfg)
        return parser

    def get_conn_param(self, prod_id):
        """
        @brief returns the FTP connection infos, as set in upload.cfg file for the given product
        @return (remote ftp host, username; remote directory, private key path)
        """
        site_id = self.data_seeker.get_site_id(prod_id)
        host = self.config[site_id]["host"]
        user = self.config[site_id]["user"]
        rdir = self.config[site_id]["rdir"]
        # local pathes need to be platform dependent
        fpath_private_key = unix_to_os_path(
            self.config[site_id]["fpath_private_key"])
        return (host, user, rdir, fpath_private_key)

    def __del__(self):
        """
        @brief housekeeping
        """
        if hasattr(self, "tmp_dpath") and self.tmp_dpath is not None and os.path.exists(self.tmp_dpath):
            shutil.rmtree(self.tmp_dpath)

    def fname2dt(self, fpath):
        """
        @brief extract datetime info from filename and return it
        """
        re_m = self.re_fname.match(os.path.basename(fpath))
        if re_m is None:
            raise ValueError("Invalid filename " + str(fpath))
        return datetime.datetime(int(re_m.group("year")), int(re_m.group("month")), int(re_m.group("day")), int(re_m.group("hours")), int(re_m.group("minutes")), 0)

    def get_infiles(self, prod_id):
        """
        @brief list the input files: the one that starts during hour-id, and the last one from the hour before
        @param prod_id ID of the product to be process
        """
        if self.verbose:
            print("> seeking inputs for " + prod_id + ", " + self.hour_id)
        # handle change of day case
        cur_dt = datetime.datetime(int(self.re_m_hour_id.group("year")), int(self.re_m_hour_id.group(
            "month")), int(self.re_m_hour_id.group("day")), int(self.re_m_hour_id.group("hours")), 0, 0)
        prev_dt = cur_dt - datetime.timedelta(hours=1)
        infiles = []
        if prev_dt != cur_dt:
            infiles += self.data_seeker.get_infiles(
                prod_id, prev_dt.strftime("%Y-%m-%d"))
        infiles += self.data_seeker.get_infiles(
            prod_id, cur_dt.strftime("%Y-%m-%d"))
        # make sure they are unique
        infiles = list(set(infiles))
        infiles.sort()
        # print (infiles)

        # - index list of files
        v_dt = map(self.fname2dt, infiles)

        # - select last file of previous hour, and files that start during hour
        dt_prev_hour_min = cur_dt - datetime.timedelta(hours=1)
        dt_hour_min = cur_dt
        dt_hour_max = cur_dt + datetime.timedelta(hours=1)
        _infiles = []
        for fpath, dt in zip(infiles, v_dt):
            if (dt > dt_prev_hour_min) and (dt < dt_hour_min):
                # previous hour
                if len(_infiles) == 0:
                    _infiles.append(fpath)
                elif dt > self.fname2dt(_infiles[0]):
                    # more recent replace
                    _infiles[0] = fpath
            elif (dt >= dt_hour_min) and (dt < dt_hour_max):
                # current hour, add it
                _infiles.append(fpath)
        if self.verbose:
            print("> found: " + str(_infiles))
        return _infiles

    def get_out_dir(self, prod_id):
        """
        @brief the output local directory for generate files
        """
        if self.out_dir:
            # use a command line one
            return self.out_dir

        site_id = self.data_seeker.get_site_id(prod_id)
        # local pathes need to be platform dependent
        out_dir = unix_to_os_path(self.config[site_id]["out_dir"])
        return out_dir

    def is_upload_enable(self, prod_id):
        """
        @brief tell if upload is activated in upload.cfg file
        """
        site_id = self.data_seeker.get_site_id(prod_id)
        return int(self.config[site_id]["enable_upload"]) == 1

    def process_product(self, prod_id, hour_id):
        """
        @brief generate the ACTRIS file from input and upload it
        @param prod_id ID of the product to be process
        @param hour_id  Timestamp of the hour to process, as a string using syntax YYYY-MM-DDThh
        """
        # - check and parse hour format
        self.re_m_hour_id = self.re_hour_id.match(hour_id)
        if self.re_m_hour_id is None:
            raise ValueError("Invalid hour ID " + str(hour_id))
        self.hour_id = hour_id
        year = int(self.re_m_hour_id.group("year"))
        month = int(self.re_m_hour_id.group("month"))
        day = int(self.re_m_hour_id.group("day"))

        # select the input file
        self.infiles = self.get_infiles(prod_id)
        if self.infiles is None or self.infiles == []:
            print("ERROR: No input file found for product {:s} and hour {:s}".format(
                prod_id, self.hour_id))
            raise NoInputException()

        if self.verbose:
            print("> starting raw -> lev0 conversion, " + prod_id + ", " + self.hour_id)
        try:
            # - init a temp directory
            self.tmp_dpath = tempfile.mkdtemp(prefix="actris-acsm")

            # - run conversion, generate files in temp dir
            converter_class = self.factory.get_class_by_fname(self.infiles[0])
            converter = converter_class(prod_id)
            converter.process(self.infiles, self.tmp_dpath, nrt=True)

            # - final output directory
            out_dir = self.get_out_dir(prod_id)

            # - copy files from tmp to final directory
            infiles = os.listdir(self.tmp_dpath)
            outfiles = []
            for fname in infiles:
                fpath_src = os.path.join(self.tmp_dpath, fname)
                if not self.out_dir:
                    # use default arch
                    out_dir = os.path.join(out_dir, "{:d}".format(
                        year), "{:02d}".format(month), "{:02d}".format(day))
                if not os.path.exists(out_dir):
                    print("> creating " + out_dir)
                    os.makedirs(out_dir)
                shutil.move(fpath_src, out_dir)
                fpath_dst = os.path.join(out_dir, fname)
                outfiles.append(fpath_dst)
                if self.verbose:
                    print("> " + str(fpath_dst) + " written")

            if self.verbose:
                print("> done")
            # - upload
            if self.is_upload_enable(prod_id):
                self.upload(prod_id, outfiles)
        finally:
            if self.tmp_dpath is not None and os.path.exists(self.tmp_dpath):
                shutil.rmtree(self.tmp_dpath)
                self.tmp_dpath = None

    def _upload(self, sftp, files, rdir):
        """
        @brief upload files, with an initiated sftp connection
        @param sftp the pysftp instance
        @param files the files to be transfered
        @param rdir remote directory
        """
        if self.host == "sftpush.icare.univ-lille.fr":
            # local test hack
            sftp.chdir("test")
        # create and go into data directory
        if not sftp.exists(rdir):
            sftp.mkdir(rdir)
        sftp.chdir(rdir)
        # push files
        for f_src in files:
            fname = os.path.basename(f_src)
            if self.verbose:
                print("> transfering " + fname)
            sftp.put(f_src)    # upload file to allcode/pycode on remote
            if self.verbose:
                print("> done")

    def upload(self, prod_id, files):
        """
        @brief upload the generated files
        @param prod_id product ID
        @param files the files to be transfered
        """
        host, user, rdir, fpath_private_key = self.get_conn_param(prod_id)
        try:
            cnopts = pysftp_extension.CnOpts()
            cnopts.hostkeys = None

            # private key auth mode only
            with pysftp_extension.Connection(host, username=user, private_key=fpath_private_key, cnopts=cnopts, disabled_algorithms=dict(pubkeys=["rsa-sha2-512", "rsa-sha2-256"])) as sftp:
                self._upload(sftp, files, rdir)

            # # login auth mode
            # with pysftp.Connection(self.host, username=self.user, password=self.passwd, cnopts=cnopts) as sftp:
                # self._upload(sftp, files)

        except Exception as e:
            print("ERROR: data transfer failed : " + str(e))
            raise


"""
COMMAND LINE PARSING
"""


def get_options(parser):
    """
    Sets and process the available program options, and their default values
    """
    parser.usage = "python3 {:s}.py [options] <prod-id> <hour-id>".format(
        __APP__)
    parser.usage += "\n\nArgs:"
    parser.usage += "\n  <prod-id> : ID of the product to process, see data_seeker.cfg file for supported ones"
    parser.usage += "\n  <hour-id> : hour to process, using the format YYYY-MM-DDThh"
    parser.add_option("-o", "--out_dir", dest="out_dir", default=None,
                      help="force a specific output directory")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      help="Print out processing informations")
    parser.add_option("-x", "--overwrite", action="store_true", dest="overwrite",
                      help="Overwrite existing files")

    # check the number of command line arguments
    if len(sys.argv) < 2:
        parser.print_help()
        raise ValueError("\nMissing command-line options")
    return parser.parse_args()


"""
Main script
"""


def main():

    # try:

    # parse the command line arguments
    parser = OptionParser()
    options, args = get_options(parser)
    prod_id = args[0]
    hour_id = args[1]

    prog = HourlyUploader(out_dir=options.out_dir,
                          verbose=options.verbose,
                          overwrite=options.overwrite)
    prog.process_product(prod_id, hour_id)
    # except Exception,msg:
    # print msg
    # sys.exit(EXIT_FAILURE)
    # except :
    # sys.exit(EXIT_FAILURE)

    # all works good
    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
