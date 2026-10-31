# -*- coding: utf-8 -*-
"""
Description :
    Reader for acquistion error logs

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
    v0.0.0 : 2012/09/28
     - creation
"""

import os

import numpy

from iointerface.CsvReader import CsvReader
from misc.TimeConverter import str_to_utc_epoch, utc_epoch_to_str


class AcquisitionErrorLogger(object):
    """
    Product Interface
    """
    # event variable IDs
    START_TIME = "Start Time"
    END_TIME = "End Time"
    DESCRIPTION = "Error Description"
    VALUE = "Error Value"

    def __init__(self, fname=None):
        """
        Constructor
        @param fname product filename ( full path )
        """
        object.__init__(self)
        self.fname = fname
#         self.reader = CsvReader(
# self.fname, delimiter=";", skip_rows=1, has_colname=True,
# ignore_tag="#")
        self.reader = CsvReader(
            self.fname, delimiter=";", skip_rows=1, has_colname=True, ignore_tag="#")
        # build events table
        self.parse_data()

    def parse_data(self):
        """
        decode the file
        """
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        v_start = self.reader.get_data(self.START_TIME)
        self.v_start_time = numpy.array(
            [str_to_utc_epoch(s_ts, fmt) for s_ts in v_start])
        self.v_end_time = numpy.array(
            [str_to_utc_epoch(s_ts, fmt) for s_ts in self.reader.get_data(self.END_TIME)])
        self.v_desc = numpy.array(self.reader.get_data(
            self.DESCRIPTION), dtype=numpy.str)
        vals = self.reader.get_data(self.VALUE)
        # for i, v in enumerate(vals):
        # print (v_start[i] + ": " + v)
        self.v_val = numpy.array(vals, dtype=float)

    def get_invalid_acq(self, v_start_acq, v_end_acq=None,
                        end_time_included=False, start_time_included=False
                        ):
        if v_end_acq is None:
            # "simulate" a time range
            v_end_acq = v_start_acq

        # ignore missing value flags. Not relevant if data is present
        # ignore also comments, with valid flags
        s_missing_data = (self.v_val == 0.999) | (
            self.v_val == 0.980) | (self.v_val == 0.000)
        v_start_time = self.v_start_time[~s_missing_data]
        v_end_time = self.v_end_time[~s_missing_data]
        v_val = self.v_val[~s_missing_data]
        # v_desc = self.v_desc[~s_missing_data]

        sz = len(v_start_acq)
        invalid_acq_mask = numpy.zeros(v_start_acq.shape, dtype=bool)
        invalid_acq_val = numpy.empty(
            v_start_acq.shape, dtype=numpy. float) + numpy.nan

        sz = v_start_acq.size
        for i, start_acq, end_acq in zip(list(range(sz)), v_start_acq, v_end_acq):
            if end_time_included is False:
                if start_time_included:
                    s = (end_acq >= v_start_time) & (
                        start_acq < v_end_time)
                else:
                    s = (end_acq > v_start_time) & (
                        start_acq < v_end_time)
            else:
                if start_time_included:
                    s = (end_acq >= v_start_time) & (
                        start_acq <= v_end_time)
                else:
                    s = (end_acq > v_start_time) & (
                        start_acq <= v_end_time)

            if s.any():
                i_err = numpy.where(s)[0][0]
                invalid_acq_mask[i] = True
                invalid_acq_val[i] = v_val[i_err]

        return invalid_acq_mask, invalid_acq_val

    def __str__(self):
        """
        return content as a string
        """
        s = '#' * 5 + ' ' + self.__class__.__name__ + \
            ' ' + '#' * 5 + os.linesep

        s += "fname     = " + self.fname + os.linesep
        s += "reader    = " + str(self.reader) + os.linesep

        fmt = "%Y-%m-%dT%H:%M:%SZ"
        for start, end, desc, val in zip(self.v_start_time, self.v_end_time, self.v_desc, self.v_val):
            s += "%s\t%s\t%s\t%g" % (utc_epoch_to_str(start, fmt),
                                     utc_epoch_to_str(end, fmt), desc, val) + os.linesep

        return s


def main():
    """
    Unit test
    """
    fname = os.path.expanduser("~") + \
        "/depot/ground_data_framework/data/VDA/VDA_SMPS_ERR-LOG_V1-00.csv"

    prod = AcquisitionErrorLogger(fname)

    print(prod)


if __name__ == "__main__":
    main()
