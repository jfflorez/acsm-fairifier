# -*- coding: utf-8 -*-
"""
Description :
-------------
   Data read interface for the data of the ACSM operated by the LSCE/SIRTA at Gif Sur Yvette

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
    HYGEOS-AERIS/ICARE Nicolas PASCAL, nicolas-dot-pascal-at-univ-hyphen-lille-dot-fr

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
    v0.0.0 : 2016/03/14
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

from Product import Product
from Variable import Variable
from iointerface.CsvReader import CsvReader

__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]


class GifAcsmProduct(Product):
    """
    Product Interface
    """
    # variables ID
    LOCAL_TIME_ID = "acsm_local_time"
    UTC_TIME_ID = "acsm_utc_time"

    CONC_ORG_ID = "Org"
    CONC_SO4_ID = "SO4"
    CONC_NO3_ID = "NO3"
    CONC_NH4_ID = "NH4"
    CONC_CHL_ID = "Chl"

    def parse_utc_time_str(self, s_ts, day):
        """
        @brief decode an acquisition UTC time string, as set in the data files and return it as a datetime
        @param s_ts string to decode
        @param day start acfquisiton day : needed because format changed during lifetime of instrument
        """
        mdy, hms = s_ts.split()
        if day.year < 2017:
            m, d, y = mdy.split("/")
        else:
            d, m, y = mdy.split("/")

        hours, minutes, seconds = hms.split(":")
        return datetime.datetime(int(y), int(m), int(d), int(hours), int(minutes), int(seconds))

    def __init__(self, fname=None, prod_id=None):
        """
        @param fname product filename(full path)
        @param prod_id a supported product ID. If not given, will be guest using the naming convention of fname

        """
        Product.__init__(self, fname, prod_id, CsvReader(
            fname, delimiter=",", has_colname=True))

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
        # read day in filename : time format change during life of instrument
        # !!!
        re_m = self.get_fname_re_match()
        yy, mm, dd = int(re_m.group("year")), int(
            re_m.group("month")), int(re_m.group("day"))
        day = datetime.datetime(yy, mm, dd)

        # set acquisition time
        sz = self.reader.nvals
        start_time = numpy.empty((sz), dtype=float)
        for i, ts in enumerate(self.reader.get_data(self.UTC_TIME_ID)):
            d = self.parse_utc_time_str(ts, day)
            start_time[i] = calendar.timegm(d.timetuple())
        end_time = start_time
        return start_time, end_time

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
        for var_id, desc in [
            (self.CONC_ORG_ID, "Organic Concentration"),
            (self.CONC_SO4_ID, "SO4 Concentration"),
            (self.CONC_NO3_ID, "NO3 Concentration"),
            (self.CONC_NH4_ID, "NH4 Concentration"),
            (self.CONC_CHL_ID, "Chl Concentration"),
        ]:
            self.add_var(Variable(var_id, dims=dims, type_id=numpy.float,
                                  description=desc, unit="µg/m^3"))

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

        # find column position
#         iparam = self.vars_order.index(var_id) - 2
#         print var_id, "->", iparam

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
    prod_id = "GIF_ACSM_RAW"
#     infile = os.path.join(datadir, "GIF", "ACSM",
#                           "SIRTA_ACSM_ExportData_20151005_22_33_51.csv")
    infile = "/ground_based/pull/SIRTA/ACSM_RAW/2018/2018_01_13/SIRTA_ACSM_ExportData_20180113.csv"

    prod = GifAcsmProduct(infile, prod_id)
    print(prod)

    # read some datasets
    for var_id in prod.get_vars_id():
        print("--- %s ---" % var_id)
        print(prod.read_data(var_id))


if __name__ == "__main__":
    test()
