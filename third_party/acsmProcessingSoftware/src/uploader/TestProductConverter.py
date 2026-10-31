# -*- coding: utf-8 -*-
"""
Description :
    Ground Based Data Converter base test class

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
import glob
import difflib

PKG_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "src"))
if PKG_ROOT not in sys.path:
    sys.path.append(os.path.join(PKG_ROOT))

from ConverterFactory import ConverterFactory

# print read data to standard output
TRACE = False
DATA_ROOT = os.path.abspath(os.path.dirname(__file__))


class TestProductConverter(unittest.TestCase):
    factory = ConverterFactory()

    # regexp of a successful diff between ref and generated file
    sre_diff_success = r"^-{3} \n" + \
                       r"\+{3} \n" + \
                       r"@@.*@@\n" + \
                       r"-Revision date:.*\n\n" + \
                       r"\+Revision date:.*\n\n" + \
                       r"@@.*@@\n" + \
                       r"-File name:.*\n\n" + \
                       r"\+File name:.*\n\n" + \
                       r"$"
    re_diff_success = re.compile(sre_diff_success, re.MULTILINE)

    def compare(self, fref, fout):
        """
        @brief compare the given nasa ames files
        """
        # --- load
        # diff = filecmp.cmp(fref, fout)
        sref = None
        sout = None
        with open(fref) as fd_in:
            sref = fd_in.readlines()
        with open(fout) as fd_in:
            sout = fd_in.readlines()
        # --- compare
        diff = difflib.unified_diff(sref, sout, n=0, lineterm="")
        s_diff = ""
        for line in diff:
            s_diff += line + "\n"

        m = self.re_diff_success.match(s_diff)
        return m is not None

    def _test_converter(self, site_dir, infiles, is_nrt=False, gen_ref=False, lvl=None):
        """
        @brief compare generated formatted file with a reference one
        @brief site_dir Site directory in tests/data tree
        @brief is_nrt is the product to generate a NRT one or not
        @brief gen_ref if True, regenrate the reference file
        """
        def update_fname_lines(s):
            """
            Change each line which contains the 'fname' meta-data
            The absolute path must be temporary changed

            @param s a string buffer will be parsed
            @return an updated string buffer
            """
            def substitute_fname_line(g):
                """
                Must be called by the function 're.sub()' as 2nd argument.
                Allows to replace a specific named pattern easily.
                """
                return g.group("start_line") + g.group("end_line")
            fname_line_pattern = re.compile(
                "(?P<start_line>^fname\s*=\s*)(?P<path>.*)(?P<end_line>/data/.*$)")
            new_s = ""  # temporary buffer
            for line in iter(s.splitlines()):
                match = fname_line_pattern.match(line)
                if match is not None:
                    line = re.sub(fname_line_pattern,
                                  substitute_fname_line, line)
                new_s += line + os.linesep
            return new_s

        # --- set working directories
        self.ref_dir = os.path.join(DATA_ROOT, site_dir, "ref")
        self.in_dir = os.path.join(DATA_ROOT, site_dir, "in")
        self.out_dir = os.path.join(DATA_ROOT, site_dir, "out")

        # --- clean up if needed
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)
        os.makedirs(self.out_dir)

        # --- generate converted product
        if lvl in [0, "0"]:
            # - raw -> lev0
            self.converter = self.factory.get_instance(infiles[0])
            self.converter.process(infiles, self.out_dir, nrt=is_nrt)
        elif lvl in ["0b", "1b", "2b"]:
            converter_class = self.factory.get_class_by_level(lvl)
            self.converter = converter_class(infiles[0])
            self.converter.process(self.out_dir)

        if gen_ref:
            # copy out to ref
            if os.path.exists(self.ref_dir):
                shutil.rmtree(self.ref_dir)
            shutil.copytree(self.out_dir, self.ref_dir)

        # --- compare generated product with reference
        fpattern = "*"
        if lvl is not None:
            # check one level only
            fpattern = "*.lev{0:s}.nas".format(str(lvl))
        search_ref = os.path.join(self.ref_dir, fpattern)
        search_out = os.path.join(self.out_dir, fpattern)

        # print (search_out)
        fref = glob.glob(search_ref)[0]
        fout = glob.glob(search_out)[0]
        return self.compare(fref, fout)
