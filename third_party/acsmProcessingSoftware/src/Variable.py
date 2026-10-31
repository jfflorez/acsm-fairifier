# -*- coding: utf-8 -*-
"""
Description :
-------------
    A basic variable representation

Copyright (©) 2022:
-------------------
    Université de Lille ;

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
---------
    2010/04/12 : creation
"""

import os.path
from tempfile import NamedTemporaryFile
import numpy

from misc.DataScaler import DataScaler


class Variable (object):
    """
    @class represents a product variable
    """

    # object that manages the way the data are calibrated
    nattr = 20

    def __init__(self,
                 var_id,
                 name=None,
                 role=None,
                 interface=None,
                 dims=None,
                 type_id=None,
                 long_name=None,
                 std_name=None,
                 description=None,
                 unit=None,
                 val_min=None,
                 val_max=None,
                 fill=None,
                 missing=None,
                 scale_factor=1.,
                 scale_offset=0.,
                 scale_id=None,
                 in_fname=None,
                 dump_dir=None,
                 data=None
                 ):
        """
        @brief constructor
        code of the scaling equation to use for data uncalibration
        0 -> science value = ( binary value - scale_offset ) * scale_factor
        1 -> science value = ( binary value + scale_offset ) * scale_factor
        2 -> science value = ( binary value - scale_offset ) / scale_factor
        3 -> science value = ( binary value + scale_offset ) / scale_factor
        4 -> science value = ( binary value * scale_factor ) - scale_offset
        5 -> science value = ( binary value * scale_offset ) + scale_factor
        6 -> science value = ( binary value / scale_factor ) - scale_offset
        7 -> science value = ( binary value / scale_offset ) + scale_factor
        @param var_id internal usage : ID of the variable
        @param role I, T, or O for Input, Temporary and Output
        @param I/O interface to use : NCF for a netcdf dataset, SDS or VDATA for HDF4 dataset
        @param dims dimensions of the dataset. If equal to the var_id, the variable is considered as a dimension
        @param type_id identifier of the data. Uses HDF constants ( @see http://hdf.ncsa.uiuc.edu/old/RefMan41r3_html/DataTypeTable.fm.html for definitions )
        @param name name of the variable as read/wrote in the file ( ie name of the SDS for HDF files )
        @param long_name description of the variable ( ie long name for HDF )
        @param standard_name CF standard name of the variable
        @param unit unit of the variable
        @param val_min minimal valid value
        @param val_max maximal valid value
        @param fill fill value
        @param scale_factor scale multiplier
        @param scale_offset scale offset
        @param scale_id code of the scaling equation to use for data decalibration
        @param in_fname input filename, only for for input variables
        @param dump_dir if needed to store temporary the data to a binary file, this directory will be used
        """
        # name of the variable ( ie name of the SDS for HDF files )
        if var_id is None or len(var_id) == 0:
            raise ValueError("A variable must have an ID %s" % var_id)
        self.var_id = var_id
        # role of the variable : Input, Temporary and Output
        self.role = role
        # interface used to read the data : SDS, VDATA or NCF
        self.interface = interface

        # name of the dataset
        self.name = name
        # long description
        self.long_name = long_name
        # CF standard name
        self.std_name = std_name

        # description of the variable ( ie long name for HDF )
        self.description = description
        # unit of the variable
        self.unit = unit

        # Type of the data, using a string representation ( ex "float32",
        # "uint8", etc )
        self.type_id = type_id
        if self.type_id is not None:
            self.type_id = numpy.dtype(self.type_id)
        # Dimensions of the dataset
        self.dims = dims

        # fill value
        self.fill = fill
        if self.fill is not None:
            self.fill = numpy.array(self.fill, dtype=self.type_id).item() #numpy.cast[self.type_id](self.fill)
        # missing value
        self.missing = missing
        if self.missing is not None:
            self.missing = numpy.array(self.missing, dtype=self.type_id).item() #numpy.cast[self.type_id](self.missing)
        # minimal valid value
        self.val_min = val_min
        if self.val_min is not None:
            if self.val_min.find(".") != -1 or self.val_min.find("e") != -1:
                # seems to be a float
                self.val_min = numpy.float64(self.val_min)
            else:
                self.val_min = numpy.array(self.val_min, dtype=self.type_id).item() #numpy.cast[self.type_id](self.val_min)
        # maximal valid value
        self.val_max = val_max
        if self.val_max is not None:
            if self.val_max.find(".") != -1 or self.val_max.find("e") != -1:
                # seems to be a float
                self.val_max = numpy.float64(self.val_max)
            else:
                self.val_max = numpy.array(self.val_max, dtype=self.type_id).item() #numpy.cast[self.type_id](self.val_max)

        # code of the scaling equation to use for data uncalibration
        # 0 -> science value = ( binary value - scale_offset ) * scale_factor
        # 1 -> science value = ( binary value + scale_offset ) * scale_factor
        # 2 -> science value = ( binary value - scale_offset ) / scale_factor
        # 3 -> science value = ( binary value + scale_offset ) / scale_factor
        # 4 -> science value = ( binary value * scale_factor ) - scale_offset
        # 5 -> science value = ( binary value * scale_offset ) + scale_factor
        # 6 -> science value = ( binary value / scale_factor ) - scale_offset
        # 7 -> science value = ( binary value / scale_offset ) + scale_factor
        self.scale_id = scale_id
        if self.scale_id is None:
            self.scale_id = 5  # default netcdf scaling
        else:
            self.scale_id = int(self.scale_id)

        # scale multiplier */
        self.scale_factor = scale_factor
        if self.scale_factor is not None:
            self.scale_factor = numpy.float64(self.scale_factor)
        # scale offset */
        self.scale_offset = scale_offset
        if self.scale_offset is not None:
            self.scale_offset = numpy.float64(self.scale_offset)
        elif self.scale_factor is not None:
            # need an explicit offset of 0 if the scale factor is set
            self.scale_offset = 0.

        # manages the fonction to use depending of the scale ID */
        # static Data_Scaler data_scaler;

        # for input variables : input filename
        self.in_fname = in_fname
        # temporary dump directory
        self.dump_dir = dump_dir
        # descriptor (at OS level) of the temp binary file where the data can
        # eventually bu dumped to save memory
        self.fd = None

        # Data buffer
        self.data = data

    def get_fill_mask(self):
        """
        @brief return the mask of invalid pixels. If the fill_value is None, return None
        If the data are not loaded, raise an exception
        @return the mask of fill value pixels, None if no fill value has been set
        """
        return self.get_mask(self.fill)

    def get_mask(self, v):
        """
        @brief return the mask of pixels that have the value @a v. If @a v is None, return None
        If the data are not loaded, raise an exception
        @return the mask of pixels that are equal to v, even if v is set NaN. None v is None
        """
        if self.data is None:
            raise ValueError("data have not been loaded")

        if v is None:
            return None

        mask = None
        if numpy.isnan(v):
            mask = numpy.isnan(self.data)
        else:
            mask = (self.data == v)
        return mask

    def get_dims_id(self):
        """
        @brief return the variable dimensions as a list of string which are the dims name
        @warning if the variable is a dimension raise a ValueError exception
        """
        if self.is_dim():
            return [self.var_id, ]
        # split the dimensions string as a sequence
        s = self.dims.strip()[1:-1]  # strip and remove '(', ')' characters
        return [dim_id.strip() for dim_id in iter(s.split(','))]

    def is_dim(self):
        """
        return True if the variable is a dimension
        """
        return (self.dims is not None) and (self.dims == self.var_id)

    def load_data(self):
        """
        read the variable data from the input file. If the data have already been loaded, does nothing
        """
        if self.data is None:
            if self.fd is not None:
                # data previously read have been dumped to tmp -> restore it
                self.restore()
#             elif self.in_fname is not None :
#                 # read it from file
#                 self.data = HDFInputInterface.read_data ( self.in_fname, self.name ).squeeze()
            else:
                raise ValueError(
                    "Can't read the data of variable %s : no input file and no binary dump set" % self.name)

    def __del__(self):
        """
        Destructor. The dump files are closed properly and erased
        """
        # print "clean var " + str ( self.name )
        if self.fd is not None:
            dump_fname = self.fd.name
            self.fd.close()
            # make sure the file has really been erased. Should always be the
            # case, but...
            if os.path.exists(dump_fname):
                os.remove(dump_fname)

    def get_data_array(self):
        """
        build a numpy array from the data and return it. If the data has been stored, does not restore it (ie the self.data attribute will be None after it)
        """
        data = None
        if self.data is not None:
            data = self.data
        else:
            data = numpy.fromfile(self.fd.name, dtype=self.type_id)
            data.shape = tuple(self.dims)
        return data

    def restore(self):
        """
        load the data from a buffer file
        """
        if self.fd is not None:
            self.data = self.get_data_array()
            self.fd = None

    def dump(self):
        """
        write the data to a buffer file so it can be restored later
        """
        if self.fd is None:
            # Initializes a temporary file
            self.fd = NamedTemporaryFile(dir=self.dump_dir)
        if self.data is not None:
            # save data to buffer
            self.data.tofile(self.fd.name)
            self.dims = list(self.data.shape)
            self.data = None

    def _copy_attr(self, var):
        """
        copy the attributes of the variable @a var. name and role are the only attribute kept as it
        """
        if var is None:
            raise ValueError("Invalid source variable")

        self.long_name = var.long_name
        self.std_name = var.std_name
        self.in_fname = var.in_fname
        self.interface = var.interface
        self.description = var.description
        self.unit = var.unit
        self.type_id = var.type_id
        self.dims = var.dims
        self.scale_id = var.scale_id
        self.scale_factor = var.scale_factor
        self.scale_offset = var.scale_offset
        self.fill = var.fill
        self.missing = var.missing
        self.val_min = var.val_min
        self.val_max = var.val_max
        self.dump_dir = var.dump_dir

    def _copy_data(self, var):
        """
        copy the data of the variable @a var
        """
        if var is None:
            raise ValueError("Invalid source variable")
        var.load_data()
        self.data = var.data.copy()

    def copy(self, var):
        """
        copy the variable @a var
        """
        self._copy_attr(var)
        self._copy_data(var)

    def is_loaded(self):
        """
        check if the data have previously been set
        """
        return self.fd is not None or self.data is not None

    def is_dumped(self):
        """
        tell if the data has been flushed to a file
        """
        return self.fd is not None

    def __str__(self):
        """
        @brief print out content
        """
        s = '#' * 5 + ' ' + self.__class__.__name__ + \
            ' ' + '#' * 5 + os.linesep
        s += "ID               = %s%c" % (str(self.var_id), os.linesep)
        s += "Name             = %s%c" % (str(self.name), os.linesep)
        s += "Interface        = %s%c" % (str(self.interface), os.linesep)
        s += "Role             = %s%c" % (str(self.role), os.linesep)
        s += "Dimensions       = %s%c" % (str(self.dims), os.linesep)
        s += "Input filename   = %s%c" % (str(self.in_fname), os.linesep)
        s += "Long Name        = %s%c" % (str(self.long_name), os.linesep)
        s += "Standard Name    = %s%c" % (str(self.std_name), os.linesep)
        s += "Description      = %s%c" % (str(self.description), os.linesep)
        s += "Unit             = %s%c" % (str(self.unit), os.linesep)
        s += "Type             = %s%c" % (str(self.type_id), os.linesep)
        s += "Fill Value       = %s%c" % (str(self.fill), os.linesep)
        s += "Missing Value    = %s%c" % (str(self.missing), os.linesep)
        s += "Val_Min          = %s%c" % (str(self.val_min), os.linesep)
        s += "Val_Max          = %s%c" % (str(self.val_max), os.linesep)
        s += "Scale Factor     = %s%c" % (str(self.scale_factor), os.linesep)
        s += "Scale Offset     = %s%c" % (str(self.scale_offset), os.linesep)
        s += "Scaling Equation = %s%c" % (
            DataScaler.get_equation_str(self.scale_id), os.linesep)
        s += "Dump directory   = %s%c" % (str(self.dump_dir), os.linesep)
        dump_fname = None
        if self.fd is not None:
            dump_fname = self.fd.name
        s += "Dump File        = %s%c" % (str(dump_fname), os.linesep)
        s += "Data             = %s%c" % (str(self.data), os.linesep)

        return s


def main():
    """
    Unit test
    """
    v = Variable()
    print(v)

    v = Variable(name="Dummy_Name", interface="SDS",
                 description="My_desc", unit="Dummy_unit",
                 type_id="float32", dims=[10, 3],
                 val_min=-1., val_max=1., fill=-9999.,
                 scale_factor=1.5, scale_offset=0.7, scale_id=0)
    v.data = numpy.arange(30, dtype=v.type_id).reshape(v.dims)
    print(v)

    v.dump()
    print("--- after dump ---")
    print(v)

    v.restore()
    print("--- after restore ---")
    print(v)


if __name__ == "__main__":
    main()
