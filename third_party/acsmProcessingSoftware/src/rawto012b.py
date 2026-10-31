# -*- coding: utf-8 -*-

"""
Description :
-------------
    Raw to levels 0, 0a, 1 and 2, designed for NRT submissions

Usage :
-------
    Usage: python3 rawto012.py <infile> <infile_flag> <outdir>

Example :
---------

    python3 src/rawto012.py tests/SIRTA/in/ ~/test

Limitations :
-------------
    -

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
    v0.0.0 : 2023/04/04
    - creation
"""
import os.path
import sys

PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if PKG_ROOT not in sys.path:
    sys.path.append(os.path.join(PKG_ROOT))

from rawto012 import Application


def main():
    """
    Unit test
    """
    infiles = sys.argv[1:-1]
    outdir = sys.argv[-1]

    app = Application()
    app.process(infiles, acq_err_log=None, outdir=outdir)


if __name__ == "__main__":
    main()
