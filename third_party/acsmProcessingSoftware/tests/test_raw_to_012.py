# -*- coding: utf-8 -*-
"""
Description :
    from a raw file, genertaes all higher level

Usage:
    python3 raw_to_012.py <input-files>
    
Example:
    python3 test_raw_to_012.py SIRTA/in/SIRTA_ACSM-140113_*.txt
    python3 test_raw_to_012.py /data_push/ground_based/pull/ACMCC/sirta-acsm/2021/10/05/*
    
Author(s) :
    CGTD-ICARE/UDEV-HYGEOS Nicolas PASCAL

License :
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
    v0.0.0 : 2013/06/21
    - creation
"""

import os.path
import sys
import re
import unittest
import shutil
import filecmp
import glob
import difflib
import re
import tempfile

PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if PKG_ROOT not in sys.path:
    sys.path.append(os.path.join(PKG_ROOT))

from misc.FileTools import get_file_content, write_file_content

from ConverterFactory import ConverterFactory

# print read data to standard output
TRACE = False
DATA_ROOT = os.path.abspath(os.path.dirname(__file__))


class Application(object):
    factory = ConverterFactory()

    def __init__(self):
        object.__init__(self)

    def process(self, infiles, outdir=os.path.join(os.environ["HOME"], "test")):
        """
        @brief generate all levels upon infiles in outdir
        """
        # init temp dir
        with tempfile.TemporaryDirectory() as tmpdir:

            # --- raw -> lev0 --- #
            print("> processing " + str(infiles))
            converter = self.factory.get_instance(infiles[0])
            converter.process(infiles, tmpdir, nrt=True)

            # --- lev0 -> lev0b --- #
            infile = glob.glob(os.path.join(tmpdir, "*.lev0.nas"))[0]
            print("> processing " + str(infile))
            converter = self.factory.get_class_by_level("0b")(infile)
            converter.process(tmpdir)

            # --- lev0b -> lev1b --- #
            infile = glob.glob(os.path.join(tmpdir, "*.lev0b.nas"))[0]
            print("> processing " + str(infile))
            converter = self.factory.get_class_by_level("1b")(infile)
            converter.process(tmpdir)

            # --- lev1b -> lev2b --- #
            infile = glob.glob(os.path.join(tmpdir, "*.lev1b.nas"))[0]
            print("> processing " + str(infile))
            converter = self.factory.get_class_by_level("2b")(infile)
            converter.process(tmpdir)

            # --- move all files to output dir
            print("> move into " + outdir)
            for infile in glob.glob(os.path.join(tmpdir, "*.nas")):
                shutil.move(infile, outdir)


def main():
    """
    Unit test
    """
    infiles = sys.argv[1:]
    outdir = None

    app = Application()
    app.process(infiles)


if __name__ == "__main__":
    main()
