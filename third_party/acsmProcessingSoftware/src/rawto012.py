# -*- coding: utf-8 -*-

"""
Description :
-------------
    Raw to levels 0, 0a, 1 and 2, designed for yearly regular submissions

Usage :
-------
    Usage: python3 rawto012.py <infile> <infile_flag> <outdir>

Example :
---------

    python3 src/rawto012.py tests/SIRTA/in/SIRTA_ACSM-140113_2021.txt tests/SIRTA/in/SIRTA_ACSM-140113_FLAGS_2021.txt ~/test

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
    v0.0.0 : 2022/03/30
    - creation
"""
import os.path
import sys
import re
import shutil
import glob
import tempfile

#PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "src")) 
# Replace above line with the following. The above results in c:\Users\florez_j\Documents\GitLab\acsmnode\third_party\ebasAcsmSoftware\src\src.
# Therefore ConverterFactory is not reachable
PKG_ROOT = os.path.abspath(os.path.dirname(__file__))
if PKG_ROOT not in sys.path:
    sys.path.append(os.path.join(PKG_ROOT))


from ConverterFactory import ConverterFactory

# print read data to standard output
TRACE = False
DATA_ROOT = os.path.abspath(os.path.dirname(__file__))


class Application(object):
    factory = ConverterFactory()

    def __init__(self):
        object.__init__(self)

    def process(self, infiles, acq_err_log, outdir=os.path.join(os.path.expanduser("~"), "test")):
        """
        @brief generate all levels upon infiles in outdir
        """
        if isinstance(infiles, str):
            # make sure we have a list, even is a unique file
            infiles = [infiles]
        # make it windows compatible
        outdir = os.path.expanduser(outdir)
        # get model from first file
        model = self.factory.get_model_by_fname(infiles[0])

        # init temp dir
        with tempfile.TemporaryDirectory() as tmpdir:

            # --- raw -> lev0 --- #
            print("> processing " + str(infiles))
            converter = self.factory.get_instance(infiles[0], acq_err_log=acq_err_log)
            converter.process(infiles, tmpdir)

            if acq_err_log is not None:
                # ---------------------------------- #
                # ------ regular submissions ------- #
                # ---------------------------------- #
                # --- lev0 -> lev0a --- #
                infile = glob.glob(os.path.join(tmpdir, "*.lev0.nas"))[0]
                print("> processing " + str(infile))
                converter = self.factory.get_class_by_level("0a", model=model)(infile, inspected=True)
                converter.process(tmpdir)

                # --- lev0b -> lev1 --- #
                infile = glob.glob(os.path.join(tmpdir, "*.lev0a.nas"))[0]
                print("> processing " + str(infile))
                converter = self.factory.get_class_by_level("1", model=model)(infile, inspected=True)
                converter.process(tmpdir)

                # --- lev1b -> lev2 --- #
                infile = glob.glob(os.path.join(tmpdir, "*.lev1.nas"))[0]
                print("> processing " + str(infile))
                converter = self.factory.get_class_by_level("2", model=model)(infile, inspected=True)
                converter.process(tmpdir)
            else:
                # ------------------------------ #
                # ------ NRT submissions ------- #
                # ------------------------------ #
                # --- lev0 -> lev0b --- #
                infile = glob.glob(os.path.join(tmpdir, "*.lev0.nas"))[0]
                print("> processing " + str(infile))
                converter = self.factory.get_class_by_level("0b", model=model)(infile)
                converter.process(tmpdir)

                # --- lev0b -> lev1b --- #
                infile = glob.glob(os.path.join(tmpdir, "*.lev0b.nas"))[0]
                print("> processing " + str(infile))
                converter = self.factory.get_class_by_level("1b", model=model)(infile)
                converter.process(tmpdir)

                # --- lev1b -> lev2b --- #
                infile = glob.glob(os.path.join(tmpdir, "*.lev1b.nas"))[0]
                print("> processing " + str(infile))
                converter = self.factory.get_class_by_level("2b", model=model)(infile)
                converter.process(tmpdir)

            # --- move all files to output dir
            print("> move into " + outdir)
            for infile in glob.glob(os.path.join(tmpdir, "*.nas")):
                shutil.move(infile, outdir)


def main():
    """
    Unit test
    """
    infile = sys.argv[1]
    acq_err_log = sys.argv[2]
    outdir = sys.argv[3]

    app = Application()
    app.process(infile, acq_err_log, outdir=outdir)


def test():
    pkg_dir = os.path.dirname(__file__)
    indir = os.path.join(pkg_dir, "..", "tests", "SIRTA", "in")
    infile = os.path.join(indir, "SIRTA_ACSM-140113_2021.txt")
    acq_err_log = os.path.join(indir, "SIRTA_ACSM-140113_FLAGS_2021.txt")
    outdir = os.path.expanduser("~") + "/test"

    app = Application()
    app.process(infile, acq_err_log, outdir=outdir)


if __name__ == "__main__":
    main()
    # test()
