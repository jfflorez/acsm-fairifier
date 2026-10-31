# -*- coding: utf-8 -*-

"""
Description :
    Generic data reader

Author(s) :
    CGTD/UDEV Nicolas PASCAL nicolas.pascal@icare.univ-lille1.fr

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
    2012/09/26 : creation
"""

import os

from misc.FileTools import check_file


class Reader(object):
    """
    Generic interface for data reading
    """

    def __init__(self, fname, prod_id=None):
        """
        @brief constructor
        @param fname input filename
        @param prod_id product id
        """
        object.__init__(self)

        check_file(fname)
        self.fname = fname

        self.prod_id = prod_id

        self.variables, self.vars_order = {}, []

    def add_ds(self, var):
        """
        @brief add a newly created variable
        @param var a Variable
        """
        var_id = var.var_id
        if var_id in self.variables:
            raise ValueError("Variable %s already exists" % var_id)
        self.variables[var_id] = var
        self.vars_order.append(var_id)

    def get_data(self, ds_id):
        """
        @brief read the given variable data and return it
        @param ds_id name or indice of the variable to read
        """
        return self.get_ds(ds_id).data

    def get_ds(self, ds_name):
        """
        @brief accessor to the variable by its name
        @param ds_name variable name or indice
        @return the variable
        """
#         var_id = TroposVariable.format_var_id(ds_name)
        if isinstance(ds_name, int):
            # var_id is an indice -> maps it to its variables string ID
            ds_name = self.vars_order[ds_name]
        return self.variables[ds_name]

    def has_ds(self, ds_name):
        """
        @brief check if the given column exists and return True if yes
        @param ds_name name of a dataset (ie a column)
        """
        return ds_name in self.get_ds_names()

    def get_ds_names(self):
        """
        @brief return the names of datasets
        """
        return self.vars_order

    def get_ds_dims(self, ds_name):
        """
        @brief return the dimensions of the given dataset
        """
        data = self.get_data(ds_name)
        return data.shape

    def get_ds_dtype(self, ds_name):
        """
        @brief return the data type of the given dataset
        """
        data = self.get_data(ds_name)
        return data.dtype

    def __str__(self):
        """
        @brief print out content
        """
        s = '#' * 5 + ' ' + self.__class__.__name__ + ' ' + '#' * 5 + os.linesep
        s += "fname        = %s%c" % (str(self.fname), os.linesep)
        s += "prod_id=" + str(self.prod_id) + os.linesep
        s += "nvars        = %s%c" % (str(len(self.vars_order)), os.linesep)
#         s += "nvals        = %s%c"%(str(self.nvals), os.linesep)
        s += os.linesep

        s += "[variables]%c" % (os.linesep)
        for k in iter(self.vars_order):
            s += "- %s - %c%s" % (str(k), os.linesep, str(self.variables[k]))
        return s
