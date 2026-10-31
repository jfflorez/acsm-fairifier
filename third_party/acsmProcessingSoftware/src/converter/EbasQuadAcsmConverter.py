# -*- coding: utf-8 -*-

"""
Description :
-------------
    Quad ACSM converter Base. Dedicated to NRT submissions
    Abstract class, not intended to be used directly

Usage :
-------

Example :
---------


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
    v0.0.0 : 2021/06/14
    - creation
"""

import os.path
import sys

pkgdir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkgdir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

from converter import EbasAcsmConverterBase


class EbasQuadAcsmConverter(EbasAcsmConverterBase.EbasAcsmConverterBase):
    """
    data converter
    """

    def __init__(self, fpath=None, inspected=False):
        """
        @brief constructor
        @param fpath input file path
        @param inspected manually inspected if True
        """
        EbasAcsmConverterBase.EbasAcsmConverterBase.__init__(
            self, fpath, inspected)


def get_parser(app):
    """
    Sets the available program options, and their default values
    """
    return EbasAcsmConverterBase.get_parser(app)


def get_args(app, check_infiles=True):
    """
    Check if the command line options are valid. If not, throws an exception describing the problem
    @param check_infiles is True, check file validity
    """
    return EbasAcsmConverterBase.get_args(app, check_infiles)
