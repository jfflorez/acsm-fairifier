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
import numpy
import datetime
from collections import OrderedDict
import copy


class AMESVariable(object):
    """
    represent a AMES file variable
    @todo subclass a standard variable for that and add just the ivar attribute to it
    """

    RE_INT = re.compile(r"^[-+]?[0-9]+$")
    RE_FLOAT = re.compile(r"^(?P<int>[-+]?[0-9]*)\.(?P<dec>[0-9]+)$")
    RE_FLOAT_EXP = re.compile(r"^(?P<int>[-+]?[0-9]*)\.(?P<dec>[0-9]+)(E|e)(?P<exp>[-+]?[0-9]+)$")

    def __init__(self, var_id, ivar, var_tag, fill=None, is_dim=False, desc=None, unit=None, scale_factor=1.0, col_size=-1):
        """
        @brief constructor
        @param var_id variable full name
        @param ivar variable index in the file
        @param is_dim boolean that tells if the variable is an independant variable(ie a dimension)or not
        @param var_tag variable tag, eg column name
        @param unit variable unit
        @param desc description
        @param fill fill value
        @param scale_factor scaling factor
        @param
        """
        object.__init__(self)
        self.var_id = var_id
        self.ivar = ivar
        self.is_dim = is_dim
        self.var_tag = var_tag
        self.desc = desc
        self.unit = unit
        self.fill = fill
        self.scale_factor = scale_factor
        self.col_size = col_size
        self.fmt = self.detect_format()

    def detect_format(self):
        """
        @brief  based on fill value format, autodetect format string representation
        """
        if self.is_dim:
            return ".6f"
        if self.fill is None:
            return None

        s = str(self.fill)
        m_int = self.RE_INT.match(s)
        m_flt = self.RE_FLOAT.match(s)
        m_flt_exp = self.RE_FLOAT_EXP.match(s)
        if m_int is not None:
            return "d"
        elif m_flt is not None:
            sz_dec = len(m_flt.group("dec"))
            return ".{:d}f".format(sz_dec)
        elif m_flt_exp is not None:
            sz_dec = len(m_flt_exp.group("dec"))
            return ".{:d}E".format(sz_dec)
        else:
            return "s"

    def __str__(self):
        """
        @brief print out content
        """
        s = "ID           = %s%c" % (str(self.var_id), os.linesep)
        s += "tag         = %s%c" % (str(self.var_tag), os.linesep)
        s += "ivar         = %s%c" % (str(self.ivar), os.linesep)
        s += "is_dim       = %s%c" % (str(self.is_dim), os.linesep)
        s += "Description  = %s%c" % (str(self.desc), os.linesep)
        s += "Unit         = %s%c" % (str(self.unit), os.linesep)
        s += "Fill Value   = %s%c" % (str(self.fill), os.linesep)
        s += "Scale Factor = %s%c" % (str(self.scale_factor), os.linesep)
        s += "Column size  = %s%c" % (str(self.col_size), os.linesep)
        s += "Format       = %s%c" % (str(self.fmt), os.linesep)

        return s

    def set_col_size(self, col_size):
        """
        @brief col_size setter
        """
        self.col_size = col_size


class AMESBase(object):
    """
    manages the read of NASAS-AMES data
    """

    def __init__(self, fname=None):
        object.__init__(self)
        self.fname = fname

        # construct decoder infos
        self.nlin_header = -1
        self.start_date = None
        self.x_var_name = None
        self.x_var = None
        self.nvars = -1
        self.scaling_factors = None
        self.fill_values = None
        self.var_names = []
        self.var_tags = None
        # self.str_var_tags = None
        self.attributes = OrderedDict()
        self.organisation = None
        self.originators = ""
        self.originator_contacts = []
        self.submitters = ""
        self.submitter_contacts = []
        self.projects = None
        self.vol_number = None
        self.dt = None

        # construct variables dictionnary
        self.variables = OrderedDict()
        self.data = None

    def get_colnames(self):
        """
        @brief build the column names, even if vars have been removed dynamically
        """
        s = ""
        for var in self.variables.values():
            s += "{var_tag:<{col_size:d}s}".format(
                col_size=var.col_size, var_tag=var.var_tag)
        return s.strip()

    def del_var(self, ds_id):
        """
        @brief delete the given variable using its variable name or tag
        @param ds_id name or tag of the variable
        """
        ivar = self.get_ivar(ds_id)
        ds_name = list(self.variables.keys())[ivar]

        var = self.variables.pop(ds_name)
        self.var_names.pop(ivar)
        self.fill_values.pop(ivar)
        self.scaling_factors.pop(ivar)
        self.var_tags.pop(ivar)

        self.data = self.data.drop(var.var_tag, axis=1)
        self.nvars -= 1
        self.nlin_header -= 1

    def insert_var_after(self, var_tag_prev, var_tag, var_id, fill_value, col_size):
        """
        @brief insert the given variable after var_tag_prev
        @param var_tag_prev tag of the previous variable
        @param var_tag tag of variable to insert
        @param var_id ID of variable to insert
        @param fill_value, fill value
        @param data values variable data
        @param col_size table column width
        """
        # - update variable dictionary
        new_variables = OrderedDict()
        new_var_names = []
        ivar = 0
        for var in self.variables.values():
            # duplicate existing var
            new_variables[var.var_id] = var
            new_var_names.append(var.var_id)
            ivar += 1
            if var.var_tag == var_tag_prev:
                # insertion point, create new var
                # create variable
                new_var = AMESVariable(
                    var_id, ivar, var_tag, fill=fill_value, col_size=col_size)
                new_variables[new_var.var_id] = new_var
                new_var_names.append(new_var.var_id)
                # self.data.insert(ivar, data)

                self.fill_values.insert(ivar, fill_value)
                self.scaling_factors.insert(ivar, 1.)

                ivar += 1
        # print (data)

        self.variables = new_variables
        self.var_names = new_var_names

    def rename_var(self, var_id, new_var_id, unit=None):
        """
        @brief rename the given variable
        """
        # - need to build a new dictionary
        new_variables = OrderedDict()
        new_var_names = []
        for _var_id, var in self.variables.items():
            if _var_id == var_id:
                # update ds_name
                var.var_id = new_var_id
                if unit is not None:
                    var.unit = unit

            new_variables[var.var_id] = var
            new_var_names.append(var.var_id)
        self.variables = new_variables
        self.var_names = new_var_names

    def copy(self, ames_struct):
        """
        @brief copy the data of one AMES base instance to self
        @brief ames_struct an AMESBase instance
        """
        for k, v in ames_struct.__dict__.items():
            self.__setattr__(k, copy.deepcopy(v))

    def get_var_name(self, var_tag):
        """
        @brief get the variable name from its tag
        """
        ivar = self.get_ivar(var_tag)
        return self.var_names[ivar]

    def get_var(self, var_tag):
        """
        @brief get the variable from its tag
        """
        var_name = self.get_var_name(var_tag)
        return self.variables[var_name]

    def get_var_tags(self):
        """
        @brief get the list of variable tags (ie ccolumn names)
        """
        return [var.var_tag for var in self.variables.values()]

    def get_ivar(self, ds_name):
        """
        @brief return the column index of the given dataset. Full variable name or tag can be used
        """
        ivar = 0
        for k, v in self.variables.items():
            if k == ds_name or v.var_tag == ds_name:
                return ivar
            ivar += 1

        ds_names = "\n".join(list(self.variables.keys()))
        raise ValueError(
            "Variable %s does not exist. Available are \n:%s" % (ds_name, ds_names))

    def get_var_tag(self, ds_name):
        """
        @brief return the column index of the given dataset. Full variable name or tag can be used
        """
        ivar = self.get_ivar(ds_name)
        var_name = self.var_names[ivar]
        return self.variables[var_name].var_tag

    def exists_var(self, ds_name):
        """
        @brief test if the given variable exists. Return True if yes
        @param ds_name name of the variable
        @return True if the variable exists, False else
        """
        if ds_name in self.variables.keys():
            return True
        # try tags
        var_tags = self.get_var_tags()
        return ds_name in var_tags

    def get_data(self, ds_name):
        """
        @brief read the whole data of the given dataset, using the SD interface
        @warning this method can not be used for reading VD data
        @param ds_name name of the dataset to read
        """

        var_tag = self.get_var_tag(ds_name)
        return numpy.array(self.data[var_tag])

    def get_ds_fill(self, ds_name, attr_name="fill"):
        """
        read the fill value of the given dataset
        If attr_name is None, read the fill value by using standard methods. If given, returns the value read for this SDS attribute
        @param ds_name name of the dataset to read
        @param attr_name name of the SDS attribute that stores the fill value
        @return the fill value
        """
        return getattr(self.variables[ds_name], attr_name)

    def get_ds_attr(self, ds_name, attr_name):
        """
        returns the value of a sds attribute
        @param ds_name name of the dataset to read
        @param attr_name name of the SDS attribute that stores the fill value
        @return the attribute value
        """
        return getattr(self.variables[ds_name], attr_name)

    def get_attr_names(self):
        """
        @brief return the list of attributes ID. Contains all the AMES standard ones plus the ACTRIS specific ones
        """
        return list(self.attributes.keys())

    def get_attr(self, attr_name):
        """
        @brief return value of the attribute @a attr_name
        """
        if attr_name == "DATE":
            # retrocompatibilty with nappy
            return self.start_date.year, self.start_date.month, self.start_date.day
        return self.attributes[attr_name]

    def set_attr(self, attr_name, attr_val):
        """
        @brief attribute setter
        """
        if attr_name == "DATE":
            self.start_date = datetime.date(
                attr_val.year, attr_val.month, attr_val.day)
        else:
            self.attributes[attr_name] = attr_val

    def get_ds_names(self):
        """
        @brief return the names of datasets
        """
        return list(self.variables.keys())

#     def get_ds_tags(self):
#         """
#         @brief return the names of datasets
#         """
#         return list(self.variables.keys())

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
        s = '# ' * 5 + ' ' + self.__class__.__name__ + ' ' + '# ' * 5 + os.linesep
        s += "fname        = %s%c" % (str(self.fname), os.linesep)
        s += os.linesep

        s += "[descriptor]%c" % (os.linesep)
        s += "nlin_header        = %s%c" % (str(self.nlin_header), os.linesep)
        s += "start_date        = %s%c" % (
            str(self.start_date), os.linesep)
        s += "x_var_name        = %s%c" % (str(self.x_var_name), os.linesep)
        s += "nvars        = %s%c" % (str(self.nvars), os.linesep)
        s += "scaling_factors        = %s%c" % (
            str(self.scaling_factors), os.linesep)
        s += "fill_values        = %s%c" % (str(self.fill_values), os.linesep)
        s += "var_names        = %s%c" % (str(self.var_names), os.linesep)
        s += "var_tags        = %s%c" % (str(self.var_tags), os.linesep)
        s += os.linesep

        s += "organisation        = %s%c" % (
            str(self.organisation), os.linesep)
        s += "originators        = %s%c" % (str(self.originators), os.linesep)
        for v in self.originator_contacts:
            s += "    %s%c" % (str(v), os.linesep)
        s += "submitters        = %s%c" % (str(self.submitters), os.linesep)
        for v in self.submitter_contacts:
            s += "    %s%c" % (str(v), os.linesep)
        s += "projects        = %s%c" % (str(self.projects), os.linesep)
        s += "vol_number        = %s%c" % (str(self.vol_number), os.linesep)
        s += "dt        = %s%c" % (str(self.dt), os.linesep)
        for k, v in self.attributes.items():
            s += "%s : %s%c" % (str(k), str(v), os.linesep)

        s += os.linesep

        self.organisation = None
        self.originators = ""
        self.originator_contacts = []
        self.submitters = ""
        self.submitter_contacts = []
        self.projects = None
        self.vol_number = None
        self.dt = None

        s += "[]%c" % (os.linesep)

        for k, v in self.attributes.items():
            s += "%s : %s%c" % (str(k), str(v), os.linesep)

        s += "[attributes]%c" % (os.linesep)
        for k, v in self.attributes.items():
            s += "%s : %s%c" % (str(k), str(v), os.linesep)
        s += os.linesep

        s += "[variables]%c" % (os.linesep)
        for k, v in self.variables.items():
            s += "- %s - %c%s" % (str(k), os.linesep, str(v))
        return s


def main():
    """
    Unit test
    """
    fname = os.path.expanduser("~") + "/depot/actris_acsm_converter/tests/SIRTA/ref/FR0020R.20210101000014.20210531065758.aerosol_mass_spectrometer.chemistry_ACSM.pm1_non_refractory.1420mn.30mn.FR01L_ACSM_Aerodyne_Quad_140-142.FR01L_Aerodyne_Quad_GIF.lev0b.nas"
    reader = AMESBase(fname)
    print(reader)

    for ds_name in reader.get_ds_names():
        data = reader.get_data(ds_name)
        print(ds_name, data, data.shape, data.dtype)


if __name__ == "__main__":
    main()
