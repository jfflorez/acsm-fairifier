# -*- coding: utf-8 -*-

"""
Description :
-------------
    ACTRIS ACSM converter updater tool

Limitations :
-------------
    -

Usage :
-------
    python3 updater.py
        

Copyright (©) 2023:
-------------------
    Université de Lille ;
    Commissariat à l'énergie atomique et aux énergies alternatives (CEA) ;
    Centre national de la recherche scientifique (CNRS)

Author(s) :
--------
    AERIS/ICARE Nicolas PASCAL, nicolas-dot-pascal-at-univ-hyphen-lille-dot-fr

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
    v0.0.0 : 2023/03/27
    - creation
"""
import os
import os.path
import urllib.request
import tempfile
import shutil
import zipfile
from optparse import OptionParser

app_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
app = os.path.splitext(os.path.basename(__file__))[0]


class Updater(object):
    """
    @brief pakage updater
    """
    # URL to the lastest software update
    app_name = "actris_acsm_converter"
    pkg_name = app_name + "-latest.zip"
    url_pkg = "https://www.icare.univ-lille.fr/depot/ACTRIS/ACMCC/software/" + pkg_name

    def __init__(self, verbose=False, dry_run=False, out_dir=app_dir):
        """
        @brief constructor
        """
        object.__init__(self)
        self.verbose = verbose
        self.dry_run = dry_run
        self.out_dir = os.path.abspath(os.path.normpath(out_dir))

        # init a temp working directory
        self.tmp_dir = self.init_tmp_dir()
        self.fpath_pkg_zip = self.download()
        self.extract()
        self.update()

    def __del__(self):
        """
        @brief housekeeping of temp files
        """
        if self.verbose:
            print("> cleaning temp directory " + self.tmp_dir)
        if not self.dry_run:
            if hasattr(self, "tmp_dir") and (self.tmp_dir is not None) and os.path.exists(self.tmp_dir):
                shutil.rmtree(self.tmp_dir)

    def init_tmp_dir(self):
        """
        @brief creat a working temporary directory
        @return the path to the temporary directory
        """
        if self.verbose:
            print("> creating temp directory", end=" ")
        tmp_dir = tempfile.mkdtemp(prefix="actris_acsm")
        if self.verbose:
            print(tmp_dir)
        return tmp_dir

    def download(self):
        """
        @brief download the latest software version package
        @return the path to the downloaded package
        """
        fdest = os.path.join(self.tmp_dir, self.pkg_name)
        if self.verbose:
            print("> downloading " + self.url_pkg + " -> " + fdest)
        if not self.dry_run:
            urllib.request.urlretrieve(self.url_pkg, fdest)
        return fdest

    def extract(self):
        """
        @brief extract software package
        """
        if self.verbose:
            print("> extracting " + self.fpath_pkg_zip)
        if not self.dry_run:
            with zipfile.ZipFile(self.fpath_pkg_zip, "r") as zip_ref:
                zip_ref.extractall(self.tmp_dir)

    def update(self):
        """
        @brief update software package, ignore cfg stuff
        """
        if self.verbose:
            print("> updating source code " + self.tmp_dir + " -> " + self.out_dir)

        # remove src/cfg stuff if already exists
        src_root = os.path.join(self.tmp_dir, self.app_name)
        src_cfg_dir = os.path.join(src_root, "src", "cfg")
        dst_cfg_dir = os.path.join(self.out_dir, "src", "cfg")
        if os.path.exists(dst_cfg_dir):
            if self.verbose:
                print("> cleaning " + src_cfg_dir)
            if not self.dry_run:
                shutil.rmtree(src_cfg_dir)

        # update source code
        if self.verbose:
            print("> updating " + src_root + " -> " + self.out_dir)
            if not self.dry_run:
                shutil.copytree(src_root, self.out_dir, dirs_exist_ok=True)


def get_parser(app):
    """
    Sets the available program options, and their default values
    """
    parser = OptionParser()

    parser.usage = "python3 " + app + ".py [options]" + os.linesep
    parser.usage += os.linesep

    parser.add_option("-o", "--out_dir",
                      action="store", default=app_dir, type="str", dest="out_dir",
                      help="Installation target directory (Default : " + app_dir + ")")
    parser.add_option("-v", "--verbose", action="store_true", default=False, dest="verbose", help="Verbose mode (Default : Disabled)")
    parser.add_option("-d", "--dry_run", action="store_true", default=False, dest="dry_run", help="Dry run mode (Default : Disabled)")

    return parser


def main():
    parser = get_parser(app)
    options = parser.parse_args()[0]
    Updater(verbose=options.verbose, dry_run=options.dry_run, out_dir=options.out_dir)


if __name__ == "__main__":
    main()
