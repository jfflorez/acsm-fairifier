# -*- coding: utf-8 -*-

"""
Description :
-------------
    Contains some basic units conversion functions

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
    v0.0.0 : 2013/09/20
    - creation
"""

ZERO_CELSIUS = 273.15
ATM2HPA = 1013.25


def celsius2kelvin(temp):
    """
    @brief convert a Temperature in Celsius degrees to Kelvin
    @param temp a temperature in Celsius degrees
    @return a temperature in Kelvin
    """
    return temp + ZERO_CELSIUS


def kelvin2celsius(temp):
    """
    @brief convert a Temperature in Kelvin to Celsius degrees
    @param temp a temperature in Kelvin
    @return a temperature in Celsius degrees
    """
    return temp - ZERO_CELSIUS


def atm2hpa(pres):
    """
    @brief convert a pressure given in atmosphere into hPa
    @param pres a pressure in atm
    @return a pressure in hPa
    """
    return pres * ATM2HPA


def torr2hpa(pres):
    """
    @brief convert a pressure given in Torr into hPa
    @param pres a pressure in Torr
    @return a pressure in hPa
    """
    return pres * 1.333224
