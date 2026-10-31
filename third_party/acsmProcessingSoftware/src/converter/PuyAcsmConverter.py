# -*- coding: utf-8 -*-

"""
Description :
-------------
    Puy de Dome ACSM data converter

Usage :
-------
    Usage: python3 PuyAcsmConverter.py [options]  <fname> <outdir>

    with :
        <fname>  full pathes to the files to convert
        <outdir> output directory where will be wrote the ACTRIS files

    Options:
      -h, --help            show this help message and exit
      -y YEAR, --year=YEAR  Year of the eventual Level 2 synthesis (Default :
                            Disabled)

Example :
---------


for y in {2015..2016}
do
    mkdir -p ~/test/GIF_ACSM_ACTRIS/${y}
    python3 ~/depot/ground_data_manager/src/converter/GifAcsmConverter.py ~/depot/ground_data_manager/data/PUY/ACSM/PUY_ACSM_RAW_${y}_V1-01.csv ~/test/PUY_ACSM_ACTRIS/${y} -y ${y}
done


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
    v0.0.0 : 2016/11/04
    - creation
"""


import os.path
import time
from datetime import datetime
import calendar

import numpy

import Converter
from TofAcsmConverter import TofAcsmConverter

from src.product.TofAcsmRawProduct import AcsmRawProduct
from product.Product import Product

import misc.Standardizer as Standardizer
from numpy import isfinite


__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]
__DEBUG__ = True
__THROW__ = True
__SHOW_BAD_INPUTS__ = False
__SHOW_OUTPUTS__ = False


class PuyAcsmConverter(TofAcsmConverter):
    """
    Puy ECOC data converter
    """
    # station infos
    station = "FR0030R"
    platform = "FR0030S"
    lab = "FR04L"

    wmo_land_use = "Forest"
    wmo_setting = "Mountain"
    gaw_type = "G"
    wmo_region = "6"

    gaw_id = "PUY"
    site = "Puy de Dome"
    station_name = "Puy de Dome"
    station_gaw_name = "Puy de Dome"
    wdca_id = "GAWAFR__PUY"

    latitude = 45.772223
    longitude = 2.964886
    altitude = 1465

    # instrument infos
    matrix = "pm1_non_refractory"
    sn = "13"

    # acquisition conditions
    acq_temp = 273.15  #  temperature in K
    acq_pres = 850.25  #  pressure in hPa

    # output file constants
    sz_header_base = 68

    def __init__(self, acq_err_log):
        """
        @brief constructor
        """
        TofAcsmConverter.__init__(
            self, "PUY_ACSM_RAW", AcsmRawProduct, acq_err_log=acq_err_log)

        self.method_ref = "FR01L_Ng_2011"
        self.instr_name = "{brand:s}_{model:s}_{gaw_id:s}".format(
            brand=self.brand, model=self.model, gaw_id=self.gaw_id)


def test():
    """
    Unit test
    """
    year = 2018

    acq_err_log = "/DATA/LIENS/GROUND-BASED/COPDD_Puy-De-Dome/ACSM/PUY_ACSM_ERR-LOG_V1-00.csv"

    infiles = ["/DATA/LIENS/GROUND-BASED/COPDD_Puy-De-Dome/ACSM/ACSM_RAW/" +
               str(year) + "/COPDD_" + str(year) + "_01_14_ACSM_nativeData.txt"]
    outdir = os.environ["HOME"] + "/test/PUY_ACSM_ACTRIS"

    prog = PuyAcsmConverter(acq_err_log)
    prog.process(infiles, outdir, year=year)


def main():

    acq_err_log = "/DATA/LIENS/GROUND-BASED/COPDD_Puy-De-Dome/ACSM/PUY_ACSM_ERR-LOG_V1-00.csv"
    prog = PuyAcsmConverter(acq_err_log)

    infiles, outdir, options = Converter.get_args(__APP__)
    prog.process(infiles, outdir, year=options.year)


if __name__ == "__main__":
    test()
#    main()
