# -*- coding: utf-8 -*-

"""
Description :
-------------
    For GEODAIR purpose and Lille station, one need 15min interpolated data, based on ACSM lev0. This tool handle this process

Usage :
-------

    python3 l1b215min.py <input-file-lev0> -v -x
    
Example :
---------

    python3 l1b215min.py /work_dev/data/pascal/incoming/ACMCC/lille-acsm/lev0/2022/01/17/FR0027U.20220117144731.20220117152346.aerosol_mass_spectrometer.chemistry_ACSM.pm1_non_refractory.30mn.30mn.FR07L_Aerodyne_Q-ACSM_140-157.FR07L_Aerodyne_Q-ACSM_VDA.lev0.nas -v -x

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
    v0.0.0 : 2022/01/17
    - creation
"""

import os
import os.path
import sys
import glob
import re
import tempfile
import datetime
from time import time, strptime, strftime
import shutil
from optparse import OptionParser
import configparser
import ast

pkg_dir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkg_dir, "..", "src"))
if d not in sys.path:
    sys.path.append(os.path.join(d))

from misc.FileTools import unix_to_os_path
from misc.AppContextController import NoInputException, safe, ExistingOutputException
from EbasQuadAcsmConverter1bto15min import EbasQuadAcsmConverter1bto15min
from converter.EbasQuadAcsmConverter0bto1b import EbasQuadAcsmConverter0bto1b
from converter.EbasQuadAcsmConverter0to0b import EbasQuadAcsmConverter0to0b
from ConverterFactory import ConverterFactory

# --- APPLICATION ---#
__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]
__RUN_PROCESS__ = False

# --- APP RETURN CODES ---#
EXIT_FAILURE = 1
EXIT_SUCCESS = 0

# --- some default config stuff --- #
DEFAULT_OUTPUT_DIR = "/work_dev/data/pascal/incoming/ACMCC/lille-acsm/lev1b-15min"


class QuarterHourInterpolator:
    # - string parsers
    re_fname = re.compile(
        r"^(^(?P<station_id>[A-Z0-9]+))\.(?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})(?P<hours>[0-9]{2})(?P<minutes>[0-9]{2}).*\.lev0\.nas$")

    # - conversion processes factory
    factory = ConverterFactory()

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
        self.out_dir = out_dir
        self.verbose = verbose
        self.overwrite = overwrite
        self.tmp_dpath = None
        # output level id
        self.olvl = EbasQuadAcsmConverter1bto15min.olvl

    def process(self, infile):
        """
        @brief generate the ACTRIS file from input and upload it
        @param infile lev0 input file
        """
        # select the input file
        if infile is None or infile == "":
            print("ERROR: No input file set")
            raise NoInputException()

        # - check eventual output file existence
        fname = os.path.basename(infile)
        re_m = self.re_fname.match(fname)
        if re_m is None:
            msg = "ERROR: invalid input file  " + infile
            raise ValueError(msg)
        dt = datetime.datetime(int(re_m.group("year")), int(re_m.group("month")), int(
            re_m.group("day")), int(re_m.group("hours")), 0, 0) + datetime.timedelta(hours=1)

        # - final output directory
        odir = os.path.join(self.out_dir, "{:d}".format(
            dt.year), "{:02d}".format(dt.month), "{:02d}".format(dt.day))
        search = os.path.join(odir, "{station_id:s}.{year:d}{month:02d}{day:02d}{hours:02d}*{lvl:s}.nas".format(
            station_id=re_m.group("station_id"), year=dt.year, month=dt.month, day=dt.day, hours=dt.hour, lvl=self.olvl))
        ofpath = glob.glob(search)
        if not self.overwrite and len(ofpath) > 0:
            raise ExistingOutputException(str(ofpath))

        if self.verbose:
            print("> starting lev0 -> lev0b -> lev1b -> lev1b-15min conversions")
        try:
            # - init a temp directory
            self.tmp_dpath = tempfile.mkdtemp(prefix="actris-acsm")

            # --- run conversions, generate files in temp dir
            # - lev0 -> lev0b
            converter = EbasQuadAcsmConverter0to0b(infile)
            converter.process(self.tmp_dpath)
            # print (os.listdir(self.tmp_dpath))

            # - lev0b -> lev1b
            lvl = "0b"
            infile = glob.glob(os.path.join(
                self.tmp_dpath, "*.lev{lvl:s}.nas".format(lvl=lvl)))
            if len(infile) == 0:
                print("ERROR: can't find a lev{lvl:s} file in ".format(
                    lvl=lvl) + self.tmp_dpath)
                raise NoInputException()
            infile = infile[0]
            converter = EbasQuadAcsmConverter0bto1b(infile)
            converter.process(self.tmp_dpath)

            # - lev1b -> lev1b-15min
            lvl = "1b"
            infile = glob.glob(os.path.join(
                self.tmp_dpath, "*.lev{lvl:s}.nas".format(lvl=lvl)))
            if len(infile) == 0:
                print("ERROR: can't find a lev{lvl:s} file in ".format(
                    lvl=lvl) + self.tmp_dpath)
                raise NoInputException()
            infile = infile[0]
            converter = EbasQuadAcsmConverter1bto15min(infile)
            converter.process(self.tmp_dpath)
            # print (os.listdir(self.tmp_dpath))

            # - copy files from tmp to final directory
            lvl = self.olvl
            infile = glob.glob(os.path.join(
                self.tmp_dpath, "*.lev{lvl:s}.nas".format(lvl=lvl)))
            if len(infile) == 0:
                print("ERROR: can't find a lev{lvl:s} file in ".format(
                    lvl=lvl) + self.tmp_dpath)
            infile = infile[0]

            fpath_src = infile
            fname = os.path.basename(fpath_src)
            if not os.path.exists(odir):
                print("> creating " + odir)
                os.makedirs(odir)
            shutil.move(fpath_src, odir)
            # if self.verbose:
            print("> " + str(os.path.join(odir, fname)) + " written")

            if self.verbose:
                print("> done")

        finally:
            if self.tmp_dpath is not None and os.path.exists(self.tmp_dpath):
                shutil.rmtree(self.tmp_dpath)
                self.tmp_dpath = None

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


"""
COMMAND LINE PARSING
"""


def get_options(parser):
    """
    Sets and process the available program options, and their default values
    """
    parser.usage = "python3 {:s}.py [options] <input-file-lev0>".format(
        __APP__)
    parser.usage += "\n\nArgs:"
    parser.usage += "\n  <input-file-lev0> : level 0 to be processed"
    parser.add_option("-o", "--out_dir", dest="out_dir", default=DEFAULT_OUTPUT_DIR,
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


@safe
def main():

    # try:

    # parse the command line arguments
    parser = OptionParser()
    options, args = get_options(parser)
    infile = args[0]

    prog = QuarterHourInterpolator(out_dir=options.out_dir,
                                   verbose=options.verbose,
                                   overwrite=options.overwrite)
    prog.process(infile)
    # except Exception,msg:
    # print msg
    # sys.exit(EXIT_FAILURE)
    # except :
    # sys.exit(EXIT_FAILURE)

    # all works good
    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
