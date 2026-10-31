# -*- coding: utf-8 -*-
"""
Description :
    Interfaces that represents a product. The "real" products classes implement it.

    Contains the interfaces :
       Product : Base interfacce

Author(s) :
    AERIS/ICARE Nicolas PASCAL, nicolas-dot-pascal-at-univ-hyphen-lille-dot-fr

License :
  This file must be used under the terms of the CeCILL.
  This source file is licensed as described in the file COPYING, which
  you should have received as part of this distribution.  The terms
  are also available at
  http://www.cecill.info/licences/Licence_CeCILL_V2-en.txt

History :
--------
v0.0.0 : 2012/09/28
 - creation
"""

import os.path
import sys
from datetime import datetime

pkgdir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkgdir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

from misc.FileTools import check_file

from ProductIdentifier import ProductIdentifier


class Product (object):
    """
    Product Interface
    """
    # defalut version to use when none set in files
    default_version = "1-00"
    # used to identify wich instrument and platform correspond to the product
    product_identifier = ProductIdentifier()

    # spare product ID
    GENERIC_ID = "generic"

    # common variable IDs
    START_ACQ_ID = "start_acq"
    END_ACQ_ID = "end_acq"
    LAT_ID = "lat"
    LON_ID = "lon"

    def __init__(self, fname=None, prod_id=None, reader=None):
        """
        Constructor
        @param fname product filename ( full path )
        @param prod_id a supported product ID. If not given, will be guest using the naming convention of fnames
        @param reader the reading interface to use
        """
        self.fname = fname
        check_file(self.fname)

        # identify the ID of the product
        self.prod_id = prod_id
        if self.prod_id is None:
            self.prod_id = self.product_identifier.get_prod_id(self.fname)
        self.platform = None
        self.instrument = None
        if self.prod_id is not None and self.prod_id is not self.GENERIC_ID:
            self.platform = self.product_identifier.get_platform(self.prod_id)
            self.instrument = self.product_identifier.get_instrument(
                self.prod_id)

        # set the version
        self.version = None
        if self.prod_id is not self.GENERIC_ID:
            self.version = self.product_identifier.get_version(
                self.fname, self.prod_id)
        if self.version is None:
            self.version = self.default_version

        # the read interface to use
        self.reader = reader

        # dictionnary of variables eventually defined in self.var_cfg
        self.vars = {}
        # list of variable names in the order they were constructed
        self.vars_order = []

        # --- geolocation params
        # latitude position : scalar (fixed station) or vectors (moving)
        self.latitude = None
        # latitude limits (moving), same than self.latitude for fixed station
        self.start_lat, self.end_lat = None, None

        # longitude position : scalar (fixed station) or vectors (moving)
        self.longitude = None
        # longitude limits (moving), same than self.longitude for fixed station
        self.start_lon, self.end_lon = None, None

        # altitude : scalar (fixed station) or vectors (moving)
        self.altitude = None
        # longitude limits (moving), same than self.longitude for fixed station
        self.start_alt, self.end_alt = None, None

        if self.prod_id is not self.GENERIC_ID and self.platform.type == "ground_fixed":
            self.latitude = self.start_lat = self.end_lat = self.platform.latitude
            self.longitude = self.start_lon = self.end_lon = self.platform.longitude
            self.altitude = self.start_alt = self.end_alt = self.platform.altitude

        # geolocation vector indices
        self.igeo = None

        # --- time params
        # acquisition start and end time vectors
        self.start_acq, self.end_acq = None, None
        # acquisition time limits
        self.start_time, self.end_time = None, None

        # time vector indices
        self.itime = None

    def __del__(self):
        """
        @brief cleaner
        """
        if hasattr(self, "reader") and self.reader is not None:
            del self.reader
            self.reader = None

    def get_fname_re_match(self):
        """
        @brief return the filename regepxp match object
        """
        return self.product_identifier.get_match(self.fname, self.prod_id)

    def read_geolocation(self):
        """
        @brief return the platform lat, lon by default
        """
        return self.platform.latitude, self.platform.longitude

    def get_version(self):
        """
        @brief extract the versio form the filename. 1.0 by default
        """
        return self.version

    def create_vars(self):
        """
        @brief init the variables configuration file
        """
        raise NotImplementedError("Interface not implemented")

    def read_data(self, var_id):
        """
        read the variable dataset named as @a var_id and return it as a numpy array
        """
        raise NotImplementedError("Interface not implemented")

    def add_var(self, var):
        """
        @brief add a newly created variable
        """
        var_id = var.var_id
#         if self.vars.has_key(var_id):
        if var_id in self.vars:
            raise ValueError("Variable %s already exists" % var_id)
        self.vars[var_id] = var
        self.vars_order.append(var_id)

    def print_vars(self):
        """
        print the created variables
        """
        for var in iter(self.get_vars()):
            print(var)

    def is_loaded_var(self, var_id):
        """
        check if the data of the given variable have already been loaded
        """
        return self.vars[var_id].is_loaded()

    def load_var(self, var_id):
        """
        load the given variable data
        """
        var = self.vars[var_id]
        if not var.is_loaded():
            var.load_data()

    def get_vars(self):
        """
        return the list of variables in the order they were constructed
        """
        return [self.vars[k] for k in iter(self.vars_order)]

    def get_vars_id(self):
        """
        return the list of variables names
        """
        _vars = self.get_vars()
        return [var.var_id for var in iter(_vars)]

    def exists_var_id(self, var_id):
        """
        @brief check if the given variable exists. Raise an
        """
        return var_id in self.get_vars_id()

    def check_var_id(self, var_id):
        """
        @brief check if the variable exists. If not raise an exception
        """
        if not self.exists_var_id(var_id):
            s = "Variable %s does not exist" % var_id + os.linesep
            s += "Availables are : %s" % str(self.get_vars_id())
            raise ValueError(s)

    def get_name(self):
        """
        return the product filename
        """
        return self.fname

    def get_var(self, var_id, load_data=False):
        """
        @brief Read an input HDF4 variable and return it
        @param var_name SDS name of the variable
        @param load_data if True, read and store the data as well as initiating the variable
        """
#         if not self.vars.has_key(var_id):
        if not var_id in self.vars:
            raise ValueError(
                "No variable named %s set for this product" % var_id)
        var = self.vars[var_id]
        if load_data is True:
            var.load_data()
        return var

    def get_var_fill(self, var_id):
        """
        @brief return the fill value of the given variable
        @return the fill value
        """
#         if not self.vars.has_key(var_id):
        if not var_id in self.vars:
            raise ValueError(
                "No variable named %s set for this product" % var_id)
        return self.vars[var_id].fill

    def get_var_dtype(self, var_id):
        """
        @brief return the fill value of the given variable
        @return the fill value
        """
#         if not self.vars.has_key(var_id):
        if not var_id in self.vars:
            raise ValueError(
                "No variable named %s set for this product" % var_id)
        return self.vars[var_id].type_id

    def get_xdata(self):
        """
        @brief return the X axis data. Time vector by default
        """
        return self.start_acq

    def get_ydata(self):
        """
        @brief return the Y axis data for 2D dataset. Product specific
        """
        raise NotImplementedError("Interface not implemented")

    def __str__(self):
        """
        return content as a string
        """
        s = '#' * 5 + ' ' + self.__class__.__name__ + \
            ' ' + '#' * 5 + os.linesep

        s += "fname     = " + self.fname + os.linesep
        s += "prod_id   = " + self.prod_id + os.linesep
        s += "version   = " + self.version + os.linesep
        s += "latitude  = " + str(self.latitude) + os.linesep
        s += "start_lat = " + str(self.start_lat) + os.linesep
        s += "end_lat   = " + str(self.end_lat) + os.linesep
        s += "longitude = " + str(self.longitude) + os.linesep
        s += "start_lon = " + str(self.start_lon) + os.linesep
        s += "end_lon   = " + str(self.end_lon) + os.linesep
        s += "altitude  = " + str(self.altitude) + os.linesep
        s += "start_alt = " + str(self.start_alt) + os.linesep
        s += "end_alt   = " + str(self.end_alt) + os.linesep

        # convert time in human readable format
        for ts, attr_name in [(self.start_time, "start_time"), (self.end_time, "end_time")]:
            if ts is not None:
                ts = datetime.utcfromtimestamp(ts)
            s += attr_name + "   = " + str(ts) + os.linesep

        s += "[platform] " + os.linesep + str(self.platform)
        s += "[instrument] " + os.linesep + str(self.instrument)
        s += "[reader]" + os.linesep + str(self.reader)
        s += "[variables]" + os.linesep
        for v in iter(self.get_vars()):
            s += str(v.var_id) + os.linesep

        return s
