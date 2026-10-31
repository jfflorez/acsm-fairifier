# -*- coding: utf-8 -*-
"""
Description :
-------------
   Data read interface for the NRT data based on format defined in CAMS21a framework

Usage :
-------
    -

Example :
---------

Copyright (©) 2022:
-------------------
    Université de Lille ;
    Commissariat à l'énergie atomique et aux énergies alternatives (CEA) ;
    Centre national de la recherche scientifique (CNRS)

Author(s) :
--------
    AERIS/ICARE/UDEV Nicolas PASCAL

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
    v0.0.0 : 2020/11/03
        - creation
"""

import os.path
import sys
import datetime
import calendar

import numpy

pkgdir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkgdir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

from product.AcsmRawProduct import AcsmRawProduct

__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]


class QuadAcsmRawProduct(AcsmRawProduct):
    """
    Product Interface
    """
    RF_ID = "RF"
    CHAMBERT_ID = "ChamberT"
    AIRBEAM_ID = "Airbeam"
    NEWSTART_EVENTS_ID = "NewStart_Events"
    INLETPCLOSED_ID = "InletPClosed"
    INLETPOPEN_ID = "InletPOpen"
    INLETP_ID = "InletP"
    VAPT_ID = "VapT"
    EMCURRENT_ID = "EmCurrent"
    SEMVOL_ID = "SEMVol"
    HEATERBIAS_ID = "HeaterBias"
    VAPV_ID = "VapV"
    OM_F44_ID = "OM_f44"
    OM_F43_ID = "OM_f43"
    OM_F60_ID = "OM_f60"
    NO3_F30_ID = "NO3_f30"
    NO3_F46_ID = "NO3_f46"

    OM_F44_ERR_ID = "OM_f44_err"
    OM_F43_ERR_ID = "OM_f43_err"
    OM_F60_ERR_ID = "OM_f60_err"
    NO3_F30_ERR_ID = "NO3_f30_err"
    NO3_F46_ERR_ID = "NO3_f46_err"

    ACSM_LOCAL_VERSION_ID = "acsm_local_version"
    ACMCC_EXPORT_VER_ID = "ACMCC_export_ver"
    TP1_S_ID = "TP1_S"
    TP1_W_ID = "TP1_W"
    TP1_T_ID = "TP1_T"
    TP2_S_ID = "TP2_S"
    TP2_W_ID = "TP2_W"
    TP2_T_ID = "TP2_T"
    TP3_S_ID = "TP3_S"
    TP3_W_ID = "TP3_W"
    TP3_T_ID = "TP3_T"

    # UTC_TIME_FMT = "%d/%m/%Y %H:%M:%S"  # time column format
    UTC_TIME_FMT = "%Y/%m/%d %H:%M:%S"  # time column format

    DT_ACQ = 30 * 60  # default acquisition time resolution

    def __init__(self, fname=None, prod_id=None):
        """
        @param fname product filename(full path)
        @param prod_id a supported product ID. If not given, will be guest using the naming convention of fname

        """
        AcsmRawProduct.__init__(self, fname, prod_id)

def test():
    """
    Unit test
    """
    prod_id = "GIF_ACSM_140113_RAW_NRT"
    infile = os.path.dirname(
        __file__) + "/../../tests/SIRTA/in/SIRTA_ACSM-140113_2021.txt"

    prod = QuadAcsmRawProduct(infile, prod_id)
    print(prod)

    # read some datasets
    for var_id in prod.get_vars_id():
        print("--- %s ---" % var_id)
        print(prod.read_data(var_id))


if __name__ == "__main__":
    test()
