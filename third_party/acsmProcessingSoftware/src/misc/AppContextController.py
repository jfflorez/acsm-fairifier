# -*- coding: utf-8 -*-

"""""

Description :
-------------
    Centralize and manages the applications return codes, exception and context

Limitations :
-------------
    use a decorator around the main function :

    import AppContextController
    ...
    @AppContextController.safe
    def main():
        ...

    if __name__ == "__main__":
        main()


Limitations :
-------------

Author(s) :
-----------
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


History:
--------
    v0.0.0: 2015/03/24
    - creation
"""

import sys

# --- APP RETURN CODES --- #
EXIT_MISSING_DATA = 6
EXIT_NO_DATA = 5
EXIT_UNSUPPORTED_INPUT = 4
EXIT_NO_INPUT = 3
EXIT_OUTPUT_EXISTS = 2
EXIT_FAILURE = 1
EXIT_SUCCESS = 0

FULL_VERBOSE = False

######################
#     Exceptions     #
######################


class GenericException(Exception):
    """
    @class GenericException base class of all custom exceptions
    """

    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class ExistingOutputException(GenericException):
    """
    @class UnsupportedProduct product not supported by checkers
    """

    def __init__(self, fpath="", msg="Output file already exists"):
        GenericException.__init__(self, "%s\n\t%s" % (fpath, msg))


class NoInputException(GenericException):
    """
    @class NoInput no required input files found
    """

    def __init__(self, msg="No input file found"):
        GenericException.__init__(self, msg)


class NoDataException(GenericException):
    """
    @class NoDataException no data found in file (but not necesseraly an empty file, for instance, a header but no data)
    """

    def __init__(self, fpath="", msg="No data found in file"):
        GenericException.__init__(self, msg + " " + fpath)


class MissingDataException(GenericException):
    """
    @class MissingDataException some missing data are found in file (but some are)
    """

    def __init__(self, fpath="", msg="Missing data found in file"):
        GenericException.__init__(self, msg + " " + fpath)


# decorator for controlling exception catch
def safe(fnct):
    """
    @brief decorator for exception catching
    @param function to be decorated
    """
    def safe_fnct():
        try:
            fnct()

        except ExistingOutputException as e:
            if FULL_VERBOSE:
                print(e)
            sys.exit(EXIT_OUTPUT_EXISTS)
        except MissingDataException as e:
            print(e)
            sys.exit(EXIT_MISSING_DATA)
        except NoDataException as e:
            print(e)
            sys.exit(EXIT_NO_DATA)
        except NoInputException as e:
            print(e)
            sys.exit(EXIT_NO_INPUT)
        except Exception as e:
            print(e)
            sys.exit(EXIT_FAILURE)
        except:
            sys.exit(EXIT_FAILURE)
        sys.exit(EXIT_SUCCESS)
    return safe_fnct
