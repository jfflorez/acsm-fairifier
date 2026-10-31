# -*- coding: utf-8 -*-
"""
Description :
-------------
   Data read interface for the NRT data based on format defined in CAMS21a framework
   Base class for both Quad and ToF instruments

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
    v0.0.0 : 2023/03/17
        - creation
"""

import os.path
import sys
import datetime
import calendar
from collections import OrderedDict

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


class AcsmRawBaseProduct(Product):
    """
    Base Product Interface
    """
    # some variable IDs
    UTC_TIME_ID = "ACSM_time"  # time column name

    # UTC_TIME_FMT = "%d/%m/%Y %H:%M:%S"  # time column format
    UTC_TIME_FMT = "%Y/%m/%d %H:%M:%S"  # time column format

    # csv values separator
    SEP = "\t"

    DT_ACQ = 30 * 60  # default acquisition time resolution

    def __init__(self, fname=None, prod_id=None):
        """
        @param fname product filename(full path)
        @param prod_id a supported product ID. If not given, will be guest using the naming convention of fname

        """
        Product.__init__(self, fname, prod_id, CsvReader(
            fname, delimiter=self.SEP, has_colname=True, remove_duplicates=True))

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
            if var_id in [self.UTC_TIME_ID, "acsm_local_version", "ToF_QuadW", "LensW", "VaporizerW"]:
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


def test_quad():
    """
    Unit test
    """
    prod_id = "GIF_ACSM_140113_RAW_NRT"
    infile = os.path.dirname(__file__) + "/../../tests/SIRTA/in/SIRTA_ACSM-140113_2021.txt"
    print(infile)
    prod = AcsmRawBaseProduct(infile, prod_id)
    print(prod)

    # read some datasets
    for var_id in prod.get_vars_id():
        print("--- %s ---" % var_id)
        print(prod.read_data(var_id))


def test_tof():
    """
    Unit test
    """
    prod_id = "PUY_ACSM_0018_RAW_NRT"
    infile = os.path.dirname(__file__) + "/../../tests/COPDD/in/PuydeDome_ACSM-0018_2021.txt"

    prod = AcsmRawBaseProduct(infile, prod_id)
    print(prod)

    # read some datasets
    for var_id in prod.get_vars_id():
        print("--- %s ---" % var_id)
        print(prod.read_data(var_id))


if __name__ == "__main__":
    test_quad()
    test_tof()
