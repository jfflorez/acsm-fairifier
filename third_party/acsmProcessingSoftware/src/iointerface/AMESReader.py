# -*- coding: utf-8 -*-

"""
Description :
-------------
    Defines the interface for reading NASA-AMES files

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
    v0.0.0 : 2012/10/05
    - creation
"""

import os
import re
import pandas
import numpy
import datetime
import calendar
import io
from AMESBase import AMESBase, AMESVariable


class AMESReader(AMESBase):
    """
    manages the read of NASAS-AMES data
    """

    def __init__(self, fname=None):
        AMESBase.__init__(self)
        self.fname = fname

        self.get_content_desc()
        # construct variables dictionnary
        self._init_vars()

        self.is_data_loaded = False
        self.load_data()

    def get_data(self, ds_name):
        """
        @brief read the whole data of the given dataset, using the SD interface
        @warning this method can not be used for reading VD data
        @param ds_name name of the dataset to read
        """
        self.load_data()
        return AMESBase.get_data(self, ds_name)

    def get_ds_dims(self, ds_name):
        """
        @brief return the dimensions of the given dataset
        """
        self.load_data()
        return AMESBase.get_ds_dims(self, ds_name)

    def get_ds_dtype(self, ds_name):
        """
        @brief return the data type of the given dataset
        """
        self.load_data()
        return AMESBase.get_ds_dtype(self, ds_name)

    def get_content_desc(self):
        """
        @brief read the infos that describes the content : header_size, etc
        """
        with io.open(self.fname, newline='\n') as fd:
            ilin = -1
            for lin in fd:
                lin = lin.strip()
                # ignore empty lines
                if len(lin) == 0:
                    # dummy lines added under windows (\r\n). Shouldn't be the case anymore, because /n forced under windows now, but just in case...
                    continue
                ilin += 1
                # print (ilin, lin)
                if ilin == 0:
                    elts = lin.split()
                    self.nlin_header = int(elts[0])
                    continue
                if ilin == 1:
                    self.originators = lin
                if ilin == 2:
                    self.organisation = lin
                    continue
                if ilin == 3:
                    self.submitters = lin
                    continue
                if ilin == 4:
                    self.projects = lin
                    continue
                if ilin == 5:
                    self.vol_number = lin
                    continue
                if ilin == 6:
                    elts = lin[:10].split(" ")
                    self.start_date = datetime.date(
                        int(elts[0]), int(elts[1]), int(elts[2]))
                    continue
                if ilin == 7:
                    self.dt = lin
                    continue
                if ilin == 8:
                    # independent var
                    self.var_names.append(lin)
                    self.x_var_name = lin
                    continue
                if ilin == 9:
                    self.nvars = int(lin)
                    continue
                if ilin == 10:
                    elts = lin.split()
                    #  [None]  for axis var
                    self.scaling_factors = [None] + [float(v)
                                                     for v in elts if len(v) > 0]
                    continue
                if ilin == 11:
                    elts = lin.split()
                    #  [None]  for axis var
                    self.fill_values = [None] + [float(v)
                                                 for v in elts if len(v) > 0]
                    continue
                if ilin >= 12 and ilin < (12 + self.nvars):
                    # print (len(self.var_names), lin)
                    self.var_names.append(lin)
                    continue

                if lin.startswith("Originator"):
                    self.originator_contacts.append(lin)
                    continue
                if lin.startswith("Submitter"):
                    self.submitter_contacts.append(lin)
                    continue

                if ilin >= (12 + self.nvars + 2) and ilin < (self.nlin_header - 1):
                    # key: value attributes
                    elts = lin.split(":", 1)
                    if len(elts) != 2:
                        continue
                    self.attributes[elts[0].strip()] = elts[1].strip()
                    continue

                if ilin == (self.nlin_header - 1):
                    elts = lin.split()
                    self.var_tags = [v for v in elts if len(v) > 0]
                    self.str_var_tags = lin
                    break

    def _init_vars(self):
        """
        @brief constructs the variables dictionnary
        """
        # decode column size and update variable with it
        m_var_tags = re.findall(
            r"(([^\s]+)([\s]+)|(([^\s]+$)))", self.str_var_tags)
        n_independent_var = 1

        for ivar, var_name in enumerate(self.var_names):
            # print (ivar, var_name)
            col_size = len(m_var_tags[ivar][0])

            if ivar < n_independent_var:
                # --- dimension vars: only 1 assumed
                var_name = self.x_var_name
                self.variables[var_name] = AMESVariable(
                    var_name, ivar, self.var_tags[ivar], is_dim=True, col_size=col_size)
                continue

            # --- dependent vars
            unit = None
            if var_name.find(",") >= 0:
                unit = var_name.split(",")[1].strip()
            if var_name in self.variables.keys():
                print("WARNING: parameter already exists " + var_name)
            self.variables[var_name] = AMESVariable(
                var_name, ivar, self.var_tags[ivar], unit=unit, fill=self.fill_values[ivar], is_dim=False, scale_factor=self.scaling_factors[ivar], col_size=col_size)

    def load_data(self):
        """
        @brief load all the data if needed. Real decoding done only at first call
        """
        # data loaded in one block with pandas
        if not self.is_data_loaded:
            # init time axis
            self.data = pandas.read_csv(
                self.fname, parse_dates=[0], header=self.nlin_header - 1, index_col=0, delimiter=r'\s+', date_parser=lambda x: self.start_date + datetime.timedelta(days=float(x)))
            # load the data
            self.data = pandas.read_csv(
                self.fname, header=self.nlin_header - 1, delimiter=r'\s+')
            # create the index
            dt_start = datetime.datetime(
                self.start_date.year, self.start_date.month, self.start_date.day)
            start_time_idx = [
                dt_start + datetime.timedelta(days=float(x)) for x in self.data["start_time"]]
            start_time_idx = pandas.to_datetime(start_time_idx)
            self.data.index = start_time_idx

            # stores time range, as UNIX epoch time
            v_start_acq = [
                dt_start + datetime.timedelta(days=float(x)) for x in self.data["start_time"]]
            self.start_acq = numpy.array(
                [calendar.timegm(dt.timetuple()) for dt in v_start_acq])

            v_end_acq = [
                dt_start + datetime.timedelta(days=float(x)) for x in self.data["end_time"]]
            self.end_acq = numpy.array(
                [calendar.timegm(dt.timetuple()) for dt in v_end_acq])

            self.is_data_loaded = True


def main():
    """
    Unit test
    """
    fname = os.path.expanduser("~") + "/depot/actris_acsm_converter/tests/SIRTA/ref/FR0020R.20210101000014.20210614142430.aerosol_mass_spectrometer.chemistry_ACSM.pm1_non_refractory.1420mn.30mn.FR01L_ACSM_Aerodyne_Quad_140-142.FR01L_Aerodyne_Quad_GIF.lev0.nas"
    reader = AMESReader(fname)
    print(reader)

    for ds_name in reader.get_ds_names():
        data = reader.get_data(ds_name)
        print(ds_name, data, data.shape, data.dtype)


if __name__ == "__main__":
    main()
