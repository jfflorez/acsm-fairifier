"""
Description :
    Manages the scaling/packing of a data, depending of a scaling equation

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
    2010/04/12 : creation
"""


class DataScaler (object):
    """
    @class mainly a static class used for scaling data
    """
    # def _init_ ( self ) :
    # pass

    @staticmethod
    def get_equation_str(scale_id):
        """
        @brief return a string representing the scaling equation
        raise an exception if scale_id is set tyo an invalid value ( here None is considered as valid )
        """
        if scale_id is None:
            return "None"
        elif scale_id == 0:
            return "physical_value = scale_factor * (SDS_count - add_offset)"
        elif scale_id == 1:
            return "physical_value = scale_factor * (SDS_count + add_offset)"
        elif scale_id == 2:
            return "physical_value = (SDS_count - add_offset) / scale_factor"
        elif scale_id == 3:
            return "physical_value = (SDS_count + add_offset) / scale_factor"
        elif scale_id == 4:
            return "physical_value = SDS_count * scale_factor - add_offset"
        elif scale_id == 5:
            return "physical_value = SDS_count * scale_factor + add_offset"
        elif scale_id == 6:
            return "physical_value = SDS_count / scale_factor - add_offset"
        elif scale_id == 7:
            return "physical_value = SDS_count / scale_factor + add_offset"
        else:
            raise ValueError("Invalid scale ID %d" % (scale_id))
