# -*- coding: utf-8 -*-

"""
Description :
-------------
    EBAS ACSM data uploader - High level process that must be enabled in windows task manager

Usage :
-------

    Usage: python3 uploader.py [options]

    Options:
    -h, --help            show this help message and exit
    -a, --all-days        Reprocess the whole time serie
    -p PROD_ID, --prod-id=PROD_ID
                            Process only this product is set. All by default
    -o OUTPUT_DIR, --output-directory=OUTPUT_DIR
                            output directory (default:/home/pascal/test)

    -v, --verbose         Print out processing informations
    -x, --overwrite       Overwrite existing files

Example :
---------

    # all instruments, from last successfull transfer. Default use

    python3 uploader.py

    # only one instrument, time serie, verbose and overwrite mode enabled
    python3 uploader.py -v -x -a ACSM_140113_RAW_NRT

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
import datetime
from optparse import OptionParser
import configparser

pkg_dir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkg_dir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

from hourly_uploader import HourlyUploader
import DataSeeker as DataSeeker
from misc.FileTools import unix_to_os_path


# --- APPLICATION ---#
__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]
__RUN_PROCESS__ = False

# --- APP RETURN CODES ---#
EXIT_FAILURE = 1
EXIT_SUCCESS = 0


class Uploader:
    # - string parsers
    re_hour_id = re.compile(
        r"^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})T(?P<hours>[0-9]{2})$")
    re_fname = re.compile(
        r"^.*_(?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})(?P<hours>[0-9]{2})(?P<minutes>[0-9]{2}).txt$")

    # - conversion processes factory

    # - input files seeker
    data_seeker = DataSeeker.DataSeeker()

    def __init__(self, all_days=False,
                 site_id=None,
                 prod_id=None,
                 verbose=False,
                 overwrite=False,
                 ):
        """
        Constructor
        @param all_days reprocess the whole time serie if set
        @param site_id process all enabled products from this site if set
        @parma prod_id if set, process only this product
        @param log_dir log directory, where will be stored the hour of the last successfull transfer for instance
        @param output_dir  pys5pbro output directory
        @param verbose  display processing informations
        @param overwrite  overwrite existing output files flag
        """
        # - init daily uploader
        self.hourly_uploader = HourlyUploader(
            verbose=verbose, overwrite=overwrite)
        self.all_days = all_days

        self.verbose = verbose
        self.overwrite = overwrite

        # - read log dir from upload.cfg file
        self.logdir = None
        self.config = self.load_upload_cfg()

        # - process all enabled product IDs set in data seeker
        if prod_id is None:
            prod_ids = [k for k in self.data_seeker.cfg.keys(
            ) if self.data_seeker.cfg[k].enable != "0"]
        else:
            prod_ids = [prod_id]
        for prod_id in prod_ids:
            self.process(prod_id)

    def load_upload_cfg(self):
        """
        @brief decode upload configuration infos
        """
        fpath_cfg = os.path.join(pkg_dir, "..", "cfg", "upload.cfg")
        parser = configparser.ConfigParser()
        parser.read(fpath_cfg)
        return parser

    def get_prod_acq_start(self, prod_id):
        """
        @brief for the given product, identify the start tile of serie
        """
        root_dir = self.data_seeker.get_root_dir(prod_id)
        if not os.path.exists(root_dir):
            raise ValueError("data root directory " + root_dir + " does not exist")
        dt_now = datetime.datetime.now()
        # print (root_dir, dt_now)

        # - find oldest year with data
        year = dt_now.year
        while os.path.exists(os.path.join(root_dir, "{:d}".format(year))):
            year -= 1
        year += 1

        # - find oldest day with data in year
        dpath = os.path.join(root_dir, "{:d}".format(year))
        dt_day = datetime.datetime(year, 1, 1, 0, 0, 0)
        while not os.path.exists(os.path.join(dpath, dt_day.strftime("%m"), dt_day.strftime("%d"))):
            dt_day += datetime.timedelta(days=1)

        # - oldest start of day with data
        dt_start = datetime.datetime(
            dt_day.year, dt_day.month, dt_day.day, 0, 0, 0)
        return dt_start

    def get_last_transfer_fpath(self, prod_id):
        """
        @brief returns path to the last hour of successful transfer log file
        """
        return os.path.join(self.log_dir, "last_{:s}_transfer.log".format(prod_id))

    def get_log_dir(self, prod_id):
        """
        @brief identify the log directory of the given product (eg where the last transfer log file is written)
        """
        site_id = self.data_seeker.get_site_id(prod_id)
        s_logdir = self.config[site_id]["log_dir"]
        log_dir = unix_to_os_path(s_logdir)
        return log_dir

    def process(self, prod_id):
        """
        @brief generate the ACTRIS file from input and upload it
        @param prod_id ID of the product to be process
        """
        # - identify oldest hour to be transfer
        dt_start = None
        # check if a last successful transfer file exists for this product
        self.log_dir = self.get_log_dir(prod_id)
        if not os.path.exists(self.log_dir):
            raise ValueError("transfer log directory " + self.log_dir + " does not exist")

        fpath_last_transfer = self.get_last_transfer_fpath(prod_id)
        print(fpath_last_transfer)
        if os.path.exists(fpath_last_transfer) and not self.all_days:
            with open(fpath_last_transfer) as fdin:
                lin = fdin.readlines()[0].strip()
                dt_start = datetime.datetime.strptime(
                    lin + ":00:00Z", "%Y-%m-%dT%H:%M:%SZ")
                dt_start += datetime.timedelta(hours=1)
        else:
            # - find oldest available hour for product
            dt_start = self.get_prod_acq_start(prod_id)
        # print (dt_start)

        # - most recent hour to transfer: now - 1h
        dt_end = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        # print(dt_end)
        if self.verbose:
            print("> {:s}: period to transfer {:s} -> {:s}".format(prod_id,
                                                                   str(dt_start), str(dt_end)))

        # - iterates over dates to transfer
        dt_delta = datetime.timedelta(hours=1)
        dt = dt_start
        while dt <= dt_end:
            # do stuff
            hour_id = dt.strftime("%Y-%m-%dT%H")
            if self.verbose:
                print("> processing hour " + hour_id)
            self.process_hour(prod_id, hour_id)
            dt += dt_delta

    def process_hour(self, prod_id, hour_id):
        """
        @brief run process on given product for given hour
        @param prod_id ID of the product to be process
        """
        try:
            self.hourly_uploader.process_product(prod_id, hour_id)
        except Exception as e:
            print(
                "ERROR: failed to process {:s} - {:s}\n{:s}".format(prod_id, hour_id, str(e)))
            return

        # - successful, store hour_id in trasnfer log file
        fpath_last_transfer = os.path.join(
            self.log_dir, "last_{:s}_transfer.log".format(prod_id))
        with open(fpath_last_transfer, "w") as fdout:
            fdout.write(hour_id)


"""
COMMAND LINE PARSING
"""


def get_options(parser):
    """
    Sets and process the available program options, and their default values
    """
    parser.usage = "python3 {:s}.py [options]".format(__APP__)

    parser.add_option("-a", "--all-days", action="store_true", dest="all_days",
                      help="Reprocess the whole time serie")
    parser.add_option("-p", "--prod-id",
                      action="store", default=None,
                      type="string", dest="prod_id", help="Process only this product. All by default")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      help="Print out processing informations")
    parser.add_option("-x", "--overwrite", action="store_true", dest="overwrite",
                      help="Overwrite existing files")

    return parser.parse_args()


"""
Main script
"""


def main():

    # try:

    # parse the command line arguments
    parser = OptionParser()
    options, args = get_options(parser)
    Uploader(all_days=options.all_days,
             prod_id=options.prod_id,
             verbose=options.verbose,
             overwrite=options.overwrite)

    # except Exception,msg:
    # print msg
    # sys.exit(EXIT_FAILURE)
    # except :
    # sys.exit(EXIT_FAILURE)

    # all works good
    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
