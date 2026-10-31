"""
Description:
    Retrieve the numeric limits of a given numpy type. This is a patch class because the numpy.lib.getlimits manages this in latest numpy version

Author:
    CGTD/UDEV Nicolas PASCAL nicolas.pascal@icare.univ-lille1.fr

License:
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


History:
    2011/03/14: creation
"""

import numpy


class NumLimits(object):
    """
    @class mainly a static class used for testing datatypes validity and range
    """
    # list of float types
    float_dtypes = [numpy.float32, numpy.float64]
    # list of unsigned integer types
    uint_dtypes = [numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64]
    # list of signed integer types
    int_dtypes = [numpy.int8, numpy.int16, numpy.int32, numpy.int64]

    def __init(self):
        pass

    @staticmethod
    def is_unsigned_integer(typeid):
        """
        @brief check if the given numpy type ID represent an unsigned integer type
        @param typeid a numpy dtype
        """
        return typeid in NumLimits.uint_dtypes

    @staticmethod
    def is_signed_integer(typeid):
        """
        @brief check if the given numpy type ID represent an signed integer type
        @param typeid a numpy dtype
        """
        return typeid in NumLimits.int_dtypes

    @staticmethod
    def is_float(typeid):
        """
        @brief check if the given numpy type ID represent an floating point number type
        @param typeid a numpy dtype
        """
        return typeid in NumLimits.float_dtypes

    @staticmethod
    def is_integer(typeid):
        """
        @brief check if the given numpy type ID represent an integer type, signed or unsigned
        @param typeid a numpy dtype
        """
        return NumLimits.is_signed_integer(typeid) or NumLimits.is_unsigned_integer(typeid)

    @staticmethod
    def get_limits(typeid):
        """
        @brief return a tuple with the 2(min,max) valid values that can be used for the given type on the running machine
        @param typeid a numpy dtype
        """
        if NumLimits.is_float(typeid):
            limits = numpy.finfo(typeid)
        else:
            # should be all integers
            limits = numpy.iinfo(typeid)
        return(limits.min, limits.max)

##############  MAIN  ###############


def unit_test():
    """
    Unit test: check if the NumLimits.get_limits method acts like the numpy.lib.getlimits one
    """
    v_type_id = NumLimits.uint_dtypes + NumLimits.int_dtypes + NumLimits.float_dtypes
    for type_id in iter(v_type_id):
        print("%s: %s" % (type_id, str(NumLimits.get_limits(type_id))))


if __name__ == "__main__":
    unit_test()
