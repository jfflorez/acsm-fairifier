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

from product.Product import Product
from Variable import Variable
from iointerface.CsvReader import CsvReader

__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]


class QuadAcsmRawProduct(Product):
    """
    Product Interface
    """
    # some variable IDs
    UTC_TIME_ID = "ACSM_time"  # time column name

    OM_ID = "OM"
    NO3_ID = "NO3"
    SO4_ID = "SO4"
    NH4_ID = "NH4"
    CL_ID = "Cl"
    IE_NO3_ID = "IE_NO3"
    RIE_OM_ID = "RIE_OM"
    RIE_NO3_ID = "RIE_NO3"
    RIE_SO4_ID = "RIE_SO4"
    RIE_NH4_ID = "RIE_NH4"
    RIE_CL_ID = "RIE_Cl"
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
    SAMPLING_FLOWRATE_ID = "Sampling_Flowrate"
    RH_IN_ID = "RH_In"
    RH_OUT_ID = "RH_Out"
    T_IN_ID = "T_In"
    T_OUT_ID = "T_Out"
    OM_ERR_ID = "OM_err"
    NO3_ERR_ID = "NO3_err"
    SO4_ERR_ID = "SO4_err"
    NH4_ERR_ID = "NH4_err"
    CL_ERR_ID = "Cl_err"

    # UTC_TIME_FMT = "%d/%m/%Y %H:%M:%S"  # time column format
    UTC_TIME_FMT = "%Y/%m/%d %H:%M:%S"  # time column format

    DT_ACQ = 30 * 60  # default acquisition time resolution

    def __init__(self, fname=None, prod_id=None):
        """
        @param fname product filename(full path)
        @param prod_id a supported product ID. If not given, will be guest using the naming convention of fname

        """
        Product.__init__(self, fname, prod_id, CsvReader(
            fname, delimiter="\t", has_colname=True))

        # read the time vector
        self.start_acq, self.end_acq = self.read_time()

        # number of measurements
        self.sz = self.start_acq.size

        # init the variables
        self.create_vars()

        # set acquisition time range
        self.start_time = self.start_acq[0]
        self.end_time = self.end_acq[-1]

    def read_time(self):
        """
        @brief read the start and end time of measurements
        """
        # set acquisition time
        sz = self.reader.nvals
        start_acq = numpy.empty((sz), dtype=float)
        for i, ts in enumerate(self.reader.get_data(self.UTC_TIME_ID)):
            d = datetime.datetime.strptime(ts, self.UTC_TIME_FMT)
            start_acq[i] = calendar.timegm(d.timetuple())

        end_acq = start_acq + self.DT_ACQ
        return start_acq, end_acq

    def create_vars(self):
        """
        @brief init the variables
        """
        # time vars axis
        dims = numpy.array([self.sz], dtype=int)
        self.add_var(Variable(Product.START_ACQ_ID,
                              dims=dims,
                              type_id=self.start_acq.dtype,
                              data=self.start_acq))
        self.add_var(Variable(Product.END_ACQ_ID,
                              dims=dims,
                              type_id=self.end_acq.dtype,
                              data=self.end_acq))

        # float params (time)
        for var_id in self.reader.get_ds_names():
            # - set variable dtype
            dtype = float
            if var_id in [self.UTC_TIME_ID, "acsm_local_version", "ToF_QuadW"]:
                # only these variables are strings
                dtype = str
            # create it
            self.add_var(Variable(var_id,
                                  dims=dims,
                                  type_id=dtype))

    def read_data(self, var_id):
        """
        @brief read the variable dataset named as @a var_id and return it as a numpy array
        @param var_id a variable ID
        """
        self.check_var_id(var_id)

        if var_id == self.START_ACQ_ID:
            return self.start_acq
        elif var_id == self.END_ACQ_ID:
            return self.end_acq

        # parse file to read it
        data = self.reader.get_data(var_id)
        # empty values -> fill
        data = [v if v != "" else numpy.nan for v in iter(data)]
        type_id = self.vars[var_id].type_id
        if data == []:
            return numpy.array([], dtype=type_id)
        else:
            return numpy.cast[type_id](data)


def test():
    """
    Unit test
    """
    prod_id = "PUY_ACSM_0018_RAW_NRT"
    infile = os.path.dirname(
        __file__) + "/../../tests/COPDD/in/PuydeDome_ACSM-0018_2021.txt"

    prod = QuadAcsmRawProduct(infile, prod_id)
    print(prod)

    # read some datasets
    for var_id in prod.get_vars_id():
        print("--- %s ---" % var_id)
        print(prod.read_data(var_id))


if __name__ == "__main__":
    test()
