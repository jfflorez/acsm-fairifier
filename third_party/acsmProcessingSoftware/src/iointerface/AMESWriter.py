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
import datetime
import io

from AMESBase import AMESBase
from AMESReader import AMESReader

__DEBUG__ = False


class AMESWriter(AMESBase):
    """
    manages the write of NASAS-AMES data
    """

    def __init__(self):
        AMESBase.__init__(self)
        self.prod_time = datetime.datetime.utcnow()

    def write(self, fpath):
        """
        @brief write data to ouput file
        """
        if __DEBUG__:
            print("> writing " + fpath)
        with io.open(fpath, "w") as fd:
            # --- header ---
            fd.write("{:d} {:d}".format(
                int(self.nlin_header), 1001) + os.linesep)
            fd.write("{:s}".format(self.originators) + os.linesep)
            fd.write("{:s}".format(self.organisation) + os.linesep)
            fd.write("{:s}".format(self.submitters) + os.linesep)
            fd.write("{:s}".format(self.projects) + os.linesep)
            fd.write("{:s}".format(self.vol_number) + os.linesep)
            fd.write("{:d} {:02d} {:02d}     {:d} {:02d} {:02d}".format(self.start_date.year, self.start_date.month,
                                                                        self.start_date.day, self.prod_time.year, self.prod_time.month, self.prod_time.day) + os.linesep)
            fd.write("{:s}".format(str(self.dt)) + os.linesep)
            fd.write("{:s}".format(self.x_var_name) + os.linesep)
            fd.write("{:d}".format(self.nvars) + os.linesep)
            s = ""
            for v in self.scaling_factors:
                if v is not None:
                    s += "{:.0f}. ".format(v)
            fd.write("{:s}".format(s.strip()) + os.linesep)
            s = ""
            for v in self.fill_values:
                if v is not None:
                    s += "{:s} ".format(str(v))
            fd.write("{:s}".format(s.strip()) + os.linesep)
            for var_name in self.var_names:
                if self.variables[var_name].is_dim:
                    # not a dependant variable
                    continue
                fd.write("{:s}".format(var_name) + os.linesep)
            fd.write("{:d}".format(0) + os.linesep)
            fd.write("{:d}".format(len(self.attributes) + len(self.submitter_contacts) +
                                   len(self.originator_contacts) + 1) + os.linesep)  # +1 for var_tags
            for k, v in self.attributes.items():
                if k == "Revision date":
                    fd.write("{:<32s}{:s}".format(
                        k + ":", self.prod_time.strftime("%Y%m%d%H%M%S")) + os.linesep)
                    continue
                if k == "File name":
                    fd.write("{:<32s}{:s}".format(
                        k + ":", os.path.basename(fpath)) + os.linesep)
                    continue
                fd.write("{:<32s}{:s}".format(k + ":", v) + os.linesep)
                if k == "Station WMO region":
                    # insert orignator+submitters here
                    for contact in self.originator_contacts + self.submitter_contacts:
                        fd.write("{:s}".format(contact) + os.linesep)

            fd.write("{:s}".format(self.get_colnames()) + os.linesep)
            # --- data ---
            v_fmt = ["{{:<{col_size:d}{fmt:s}}}".format(
                col_size=var.col_size, fmt=var.fmt) for var in self.variables.values()]
            # formatters = [ lambda x : fmt.format(x) for fmt in v_fmt]
            # s_data = self.data.to_string(header=False, index=False, formatters=formatters)
            data = self.data.to_numpy()
            nrows, ncols = data.shape
            s_data = ""
            for irow in range(nrows):
                for icol in range(ncols):
                    s_val = v_fmt[icol].format(data[irow, icol])
                    if icol == ncols - 1:
                        s_val = s_val.rstrip(" ")
                    s_data += s_val
                s_data += os.linesep
                # print (v)

            fd.write(s_data)
            # print (self.data.to_string(header=False, index=False, formatters=formatters))


def main():
    """
    Unit test
    """
    fname = os.path.expanduser("~") + "/depot/actris_acsm_converter/tests/SIRTA/ref/FR0020R.20210101000014.20210531065758.aerosol_mass_spectrometer.chemistry_ACSM.pm1_non_refractory.1420mn.30mn.FR01L_ACSM_Aerodyne_Quad_140-142.FR01L_Aerodyne_Quad_GIF.lev0b.nas"
    reader = AMESReader(fname)
    writer = AMESWriter()
    writer.copy(reader)
    # print(reader)
    # for ds_name in writer.get_ds_names():
    # data = writer.get_data(ds_name)
    # print(ds_name, data, data.shape, data.dtype)
    fpath = os.path.expanduser("~") + "/tmp/test.nas"
    writer.write(fpath)
    # os.system("kate " + fpath)


if __name__ == "__main__":
    main()
