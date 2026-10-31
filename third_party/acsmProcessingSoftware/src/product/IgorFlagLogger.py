# -*- coding: utf-8 -*-
"""
Description :
    Reader for flag logs build inside IGOR application

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
    v0.0.0 : 2022/03/29
     - creation
"""

import os
import sys

import numpy

pkgdir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkgdir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

from product.Product import Product
from Variable import Variable
from iointerface.CsvReader import CsvReader
from misc.TimeConverter import str_to_utc_epoch, utc_epoch_to_str


class IgorFlagLogger(Product):
    """
    Product Interface
    """
    # --- variable IDs
    ACSM_TIME_ID = "ACSM_time"
    OM_QA_FLAG_ID = "numflag_OM"
    NO3_QA_FLAG_ID = "numflag_NO3"
    SO4_QA_FLAG_ID = "numflag_SO4"
    NH4_QA_FLAG_ID = "numflag_NH4"
    CL_QA_FLAG_ID = "numflag_Cl"

    def __init__(self, fname=None, prod_id=Product.GENERIC_ID):
        """
        @param fname product filename(full path)
        @param prod_id a supported product ID. If not given, will be guest using the naming convention of fname
        """
        Product.__init__(self, fname, prod_id, CsvReader(
            fname, delimiter="\t", has_colname=True, ignore_tag="#", remove_duplicates=True))

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
        # set start of acquisition times
        fmt = "%Y/%m/%d %H:%M:%S"
        start_acq = numpy.array(
            [str_to_utc_epoch(s_ts, fmt) for s_ts in self.reader.get_data(0)])
        end_acq = start_acq
        return start_acq, end_acq

    def create_vars(self):
        """
        @brief init the variables
        """
        # time vars axis
        dims = numpy.array([self.sz], dtype=numpy.int32)
        self.add_var(Variable(Product.START_ACQ_ID,
                              dims=dims,
                              type_id=self.start_acq.dtype,
                              data=self.start_acq))
        self.add_var(Variable(Product.END_ACQ_ID,
                              dims=dims,
                              type_id=self.end_acq.dtype,
                              data=self.end_acq))

        # flag params, int
        for var_id, desc in [
            (self.OM_QA_FLAG_ID, "Organic Matter Flag"),
            (self.NO3_QA_FLAG_ID, "SO4 Flag"),
            (self.SO4_QA_FLAG_ID, "NO3 Flag"),
            (self.NH4_QA_FLAG_ID, "NH4 Flag"),
            (self.CL_QA_FLAG_ID, "Chl Flag"),
        ]:
            self.add_var(Variable(var_id, dims=dims, type_id=numpy.int32,
                                  description=desc, unit="1"))

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


def main():
    """
    Unit test
    """
    indir = os.path.join(pkgdir, "..", "..", "tests", "SIRTA", "in")
    err_log = os.path.join(indir, "SIRTA_ACSM-140113_FLAGS_2021.txt")

    prod = IgorFlagLogger(err_log)
    print(prod)

    # read some datasets
    for var_id in prod.get_vars_id():
        print("--- %s ---" % var_id)
        print(prod.read_data(var_id))


if __name__ == "__main__":
    main()
