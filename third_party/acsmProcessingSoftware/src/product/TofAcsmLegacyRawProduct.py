# -*- coding: utf-8 -*-

"""
Description :
    ACSM raw data reader

Author(s) :
    AERIS/ICARE Nicolas PASCAL, nicolas-dot-pascal-at-univ-hyphen-lille-dot-fr

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
    v0.0.0 : 2017/03/15
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

from misc import TimeConverter

from product.Product import Product
from Variable import Variable
from iointerface.CsvReader import CsvReader

__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]


class TofAcsmRawProduct(Product):
    """
    Product Interface
    """
    # variables ID
    UTC_END_TIME_ID = "Time_end"
    OM_ID = "Org"
    NO3_ID = "NO3"
    SO4_ID = "SO4"
    NH4_ID = "NH4"
    CL_ID = "Chl"

    OM_F43_ID = "f43"
    OM_F44_ID = "f44"
    OM_F57_ID = "f57"
    OM_F60_ID = "f60"

    def __init__(self, fname=None, prod_id=None):
        """
        @param fname product filename(full path)
        @param prod_id a supported product ID. If not given, will be guest using the naming convention of fname

        """
        Product.__init__(
            self, fname, prod_id, CsvReader(fname, delimiter=",", has_colname=True, replace_chars=[(b'\r', b'\n')]))
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
        start_time = numpy.empty((sz), dtype=float)
        end_time = numpy.empty_like(start_time)

        v_year = self.reader.get_data(0, int)
        v_start_doy = self.reader.get_data(1, float)
        v_stop_doy = self.reader.get_data(2, float)

        for i in range(sz):
            year = v_year[i]
            start_doy = v_start_doy[i]
            end_doy = v_stop_doy[i]

            dt_start = TimeConverter.doy2dt(year, start_doy)
            dt_end = TimeConverter.doy2dt(year, end_doy)

            start_time[i] = calendar.timegm(dt_start.timetuple())
            end_time[i] = calendar.timegm(dt_end.timetuple())

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


#         for ds_name in self.reader.get_ds_names()[3:]:
        for ds_name in self.reader.get_ds_names()[1:]:
            self.add_var(Variable(ds_name,
                                  dims=dims,
                                  type_id=float))

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
#         iparam = self.vars_order.index(var_id) + 1
        iparam = self.vars_order.index(var_id) - 1

        # parse file to read it
        data = self.reader.get_data(iparam)
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
    prod_id = "PUY_ACSM_RAW"
    infile = "/data_push/ground_based/pull/COPDD/ACSM/station-rename/2020/COPDD_2020_07_07_ACSM_nativeData.txt"

    prod = TofAcsmRawProduct(infile, prod_id)
    print(prod)

    # check time decoding
    v_start_acq = prod.read_data(prod.START_ACQ_ID)
    v_end_acq = prod.read_data(prod.END_ACQ_ID)

    for start_acq, end_acq in zip(v_start_acq, v_end_acq):
        print((datetime.datetime.utcfromtimestamp(start_acq),
               "->", datetime.datetime.utcfromtimestamp(end_acq)))

    # read some datasets
    for var_id in prod.get_vars_id():
        print(("--- %s ---" % var_id))
        print((prod.read_data(var_id)))


if __name__ == "__main__":
    test()
