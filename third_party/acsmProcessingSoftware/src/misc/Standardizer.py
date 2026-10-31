# -*- coding: utf-8 -*-

"""
Description :
-------------
    Functions that transfom data to standard like computing concentrations to standard P, T conditions 

Limitations :
-------------
    -

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
    v0.0.0 : 2014/01/24
    - creation
"""
import numpy

# standard temperature in Kelvin
T_STD = 273.15
# standard pressure in hPa
P_STD = 1013.25


def to_std(data, T_loc, P_loc, T_std=T_STD, P_std=P_STD, is_prop_vol=True, fill=None):
    """
    @brief transform the given concentration or attenuation data to standard P, T conditions
    @param data input data array. Inplace modified, not finite value set to NaN, eventual finite fill values kept
    @param T_loc acquisition temperature, K. Can be a constant or a vector
    @param P_loc acquisition pressure, hPa. Can be a constant or a vector
    @param T_std standard temperature, K
    @param P_std standard pressure conditions, hPa
    @param is_prop_vol tells if data is proportional to the volume.
    @param fill the finite fill value used. Data with with value are kept
    @return the standardized data array
    """
    # --- make sure we have vectors for acquisition conditions
    v_T_loc = T_loc
    if not isinstance(v_T_loc, numpy.ndarray):
        v_T_loc = numpy.repeat(v_T_loc, data.size)
    v_T_loc = v_T_loc.astype(float)

    v_P_loc = P_loc
    if not isinstance(v_P_loc, numpy.ndarray):
        v_P_loc = numpy.repeat(v_P_loc, data.size)
    v_P_loc = v_P_loc.astype(float)

    # --- correction factors ; data = constant * volume
#     cf = numpy.empty_like(v_T_loc)
    if is_prop_vol is True:
        # cf = (P_std * T_loc) / P_loc * T_std
        numerator = (P_std * T_loc)
        divider = P_loc * T_std

    else:
        # cf = (P_loc * T_std) / (P_std * T_loc)
        numerator = (P_loc * T_std)
        divider = (P_std * T_loc)

    # protect against zero division
#     is_zero_divider = (divider == 0)
    if isinstance(divider, numpy.ndarray):
        divider[divider == 0] = numpy.nan
    elif divider == 0:
        divider = numpy.nan
    # compute coef
    cf = numerator / divider

    # just treat "real" values
#     s_valid = numpy.isfinite(data)
#     s_invalid = (~s_valid)
    s_nan = ~numpy.isfinite(data)
    s_fill = numpy.zeros_like(s_nan)
    if fill is not None:
        s_fill = (data == fill)

    s_valid = ((~s_nan) & (~s_fill))
    s_invalid = ~s_valid

    if not isinstance(cf, numpy.ndarray):
        data[s_valid] *= cf
    else:
        data[s_valid] = data[s_valid] * cf[s_valid]

    # make sure to uses NaNs for bad data
    if numpy.any(s_invalid):
        data[s_nan] = numpy.nan
        if fill is not None:
            data[s_fill] = fill

    return data
