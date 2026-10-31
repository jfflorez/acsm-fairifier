# -*- coding: utf-8 -*-
# encoding: utf-8
"""
Description :
-------------
    Defines the interface for decoding CSV (comma separated values) files, where first line sets the parametre names

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
    v0.0.0 : 2013/05/27
    - creation
"""

import os
import sys
import re
import csv
from Reader import Reader

try:
    from io import StringIO  # for python3 2
    # from __builtin__ import hasattr

except ImportError:
    from six import StringIO  # for python3 3


import codecs
# import cStringIO
# import io.BytesIO as BytesIO

import numpy
try:
    chr
except NameError:
    chr = chr


PY_V = 2
if sys.version_info[0] >= 3:
    PY_V = 3
    str = str


class CsvVariable(object):
    """
    represent a Csv file variable
    @todo subclass a standard variable for that and add just the ivar attribute to it
    """
    @staticmethod
    def format_var_id(var_id, encoding="utf-8"):
        """
        @brief format the given variable ID to manage non ascii characters, strip it, replace break returns by spaces
        @param var_id variable name
        @return the reformatted variable name
        """
        if isinstance(var_id, int):
            # var ID is an integer
            return str(var_id)

        # replace non unicode characters to "standard unicode replacement
        # character", then remove these unsupported characters
        uni_rpl_chr = chr(0xFFFD)

        if isinstance(var_id, str):
            if PY_V == 2:
                var_id = str(var_id, encoding, errors="replace")
            else:
                var_id = str(var_id)

        var_id = var_id.replace(uni_rpl_chr, "")

#         if PY_V == 2:
        res = str.encode(var_id.strip().replace("\n", " "), "utf-8").strip()
        res = str(res, "utf-8")

        return res

    def __init__(self, var_id, ivar, encoding="utf-8"):
        """
        @brief constructor
        @param var_id variable name : column title, stripped, with break return replaced by spaces
        @param ivar variable index in the file (ie colmun indice)
        @param encoding original encoding
        """
        object.__init__(self)
        self.var_id = self.format_var_id(var_id, encoding)
        self.ivar = ivar

    def __str__(self):
        """
        @brief print out content
        """
        s = "ID           = " + str(self.var_id) + os.linesep
        s += "ivar         = %s%c" % (str(self.ivar), os.linesep)
        return s


class CsvReader(Reader):
    """
    manages the read of XLS sheet data
    """

    def __init__(self, fname=None, delimiter=";", encoding="utf-8", has_colname=False, skip_rows=[], skip_last_delimiter=False,
                 ignore_tag=None, remove_chars=None, replace_chars=None, nvars=None, encoding_error="strict", skip_empty_vals=False, remove_duplicates=False):
        """
        @brief init the read interface
        @param fname input file name
        @param delimiter value delimiter
        @param encoding original encoding
        @param has_colname True if first line contain the variable names. If yes, variables Ids
            will be these strings. If not, it will be column number
        @param skip_rows don't read this first n rows if integer or row numbers if list, they contain unconsistent infos. Eventual column names are not count in it
        @param skip_last_delimiter sometimes, a dummy last delimiter is added. It breaks the classical csv format. If True, ignore it
        @param ignore_tag if a line starts with with tag(s), it will be ignored. Can be a single character or string or a list
        @param remove_chars list of characters to remove before parsing. Useful for ignoring dummy escape chars for instance
        @param replace_chars list of character repacement tuples. For instance if [('\r', '\n')] will replace all carriage return by a new line
        @param nvars force the number of variables. Useful when the first line does not have the good number of element
        @param skip_empty_vals if True, ignore 0-length values
        @param remove_duplicates remove duplicated lines
        """
        Reader.__init__(self, fname)
        self.buf = None

        self.delimiter = delimiter
        self.encoding = encoding
        self.encoding_error = encoding_error
        self.has_colname = has_colname
        self.skip_last_delimiter = skip_last_delimiter
        self.skip_rows = []
        if isinstance(skip_rows, int):
            # skip first rows
            self.skip_rows = list(range(skip_rows))
        elif isinstance(skip_rows, list):
            # skip list of rows
            self.skip_rows = skip_rows
        else:
            raise ValueError(
                "Invalid parametre skip_rows : must be an integer or a list")
        self.ignore_tag = ignore_tag
        self.remove_duplicates = remove_duplicates

        if self.ignore_tag is not None and not isinstance(self.ignore_tag, list):
            # make sure it is list
            self.ignore_tag = [self.ignore_tag]

        self.remove_chars = remove_chars
        if self.remove_chars is not None and not isinstance(self.remove_chars, list):
            # make sure it is list
            self.remove_chars = [self.remove_chars]
        self.replace_chars = replace_chars
        self.skip_empty_vals = skip_empty_vals

        # construct variables dictionnary
        self.variables = {}
        self.vars_order = []

        # file content buffer
        self.buf, self.nlines = self.get_buf(self.fname)
        self.nvals = self.nlines
        if self.has_colname is True:
            # line contains column names, not data
            self.nvals -= 1

        self._init_vars(nvars)
        self.nvars = len(list(self.variables.keys()))
        # wether a truncated line has been detected in file or not
        self.trunc_line_detected = False

    def __del__(self):
        """
        @brief destructor, close all opened files and/or buffers
        """
        if hasattr(self, "buf"):
            del self.buf
            self.buf = None

    def get_buf(self, fname):
        """
        @brief read the whole file and return the valid lines in a stringIO buffer
        So called valid lines are the ones that do not contain a NULL bytes character and are not empty
        @return the list of lines in the file and the number of lines
        """
        # - load whole file content in buffer
        with open(fname, "rb") as fd:

            _buf = fd.readlines()
        _buf = b"".join(_buf)

        # - eventually remove escape chars
        if self.remove_chars is not None:
            for chars in self.remove_chars:
                _buf = _buf.replace(chars, b"")
#         print buf

        # - eventually replace some characters
        if self.replace_chars is not None:
            for search, replace in self.replace_chars:
                _buf = _buf.replace(search, replace)

        # - eventually strip BOM tag
        if self.encoding == 'utf-8' or self.encoding == "utf8":
            bom = codecs.BOM_UTF8
            if _buf.startswith(bom):
                _buf = _buf[len(bom):]
            bom = b"\xef\xbb\xbf"
            if _buf.startswith(bom):
                _buf = _buf[len(bom):]

        # - parse buffer as file like object
        _buf = _buf.decode(self.encoding, errors=self.encoding_error)
        _buf = _buf.encode("utf-8")

        fd = StringIO(str(_buf, "utf-8"))
        buf = ""
        nlines = 0
        # lines put in a dictionnary to check eventual duplicates
        v_lines = set()
        # check timestamp to see if a record with the same stamp already exists
        v_ts = []
        # QND Hack specific to ACSM
        UTC_TIME_FMT = "%Y/%m/%d %H:%M:%S"  # time column format
        r_ts = re.compile(r"^[0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")
        SEP = "\t"
        try:
            prev_s_ts = None
            for i, line in enumerate(fd):
                if i not in self.skip_rows:
                    line = line.strip()
                    if self.skip_last_delimiter and line.endswith(self.delimiter):
                        line = line[: -len(self.delimiter)]
                        line.strip()

                    # remove no data lines
                    if self.ignore_tag is not None:
                        if isinstance(self.ignore_tag, list):
                            skip_it = False
                            for tag in self.ignore_tag:
                                if line.startswith(tag):
                                    # ignore this line
                                    skip_it = True
                                    break
                            # eventually ignore the line
                            if skip_it:
                                continue
                        else:
                            raise ValueError(
                                "Can't interpret comment tag " + str(self.ignore_tag))

                    is_empty = len(line) == 0
                    has_null_byte = line.find('\0') != -1
                    is_line_duplicated = line in v_lines
                    # check if record with the same timestamp exists
                    s_ts = line[:line.find(SEP)]
                    is_record_duplicated = False
                    is_ascending = True
                    if r_ts.match(s_ts):
                        # is a record line
                        if s_ts in v_ts:
                            is_record_duplicated = True
                            prev_s_ts = s_ts
                        elif prev_s_ts is not None and s_ts < prev_s_ts:
                            is_ascending = False
                        else:
                            v_ts.append(s_ts)
                            prev_s_ts = s_ts
                            
                    if not is_empty and not has_null_byte and not is_line_duplicated and not is_record_duplicated and is_ascending:
                        buf += line + "\n"
                        v_lines.add(line)
                        nlines = nlines + 1
                    if has_null_byte:
                        print("WARNING: {:s} : NULL byte detected, line ignored".format(fname))
                    if is_line_duplicated:
                        print("WARNING: {:s} : line duplicated, ignored\n{:s}".format(fname, line))
                    if is_record_duplicated and not is_line_duplicated:
                        print("WARNING: {:s} : record duplicated, ignored\n{:s}".format(fname, line))
                    if not is_ascending:
                        print("WARNING: {:s} : record outdated (not in ascending order), ignored\n{:s}".format(fname, line))

        finally:
            fd.close()

        stream = StringIO(buf)
        return stream, nlines

    def add_skip_row(self, skip_row):
        """
        Append a unique row to skip and reinitialize the current buffer.

        @param skip_row the number of the line to skip
        """
        self.skip_rows.append(skip_row)
        self.buf, self.nlines = self.get_buf(self.fname)
        self.nvals = self.nlines
        if self.has_colname is True:
            # line contains column names, not data
            self.nvals -= 1

    def _init_vars(self, nvars):
        """
        @brief constructs the variables dictionary
        @param nvars force the number of variables. Useful when the first line does not have the good number of element
        """
        self.buf.seek(0)
        try:
            reader = csv.reader(
                self.buf, delimiter=self.delimiter, skipinitialspace=True)
            # set variables names :
            # - if 1st line contains column names, use it
            # - else use variable indice as title
#             varnames = reader.next()
            varnames = next(reader)
#             print(varnames)
#             print len(varnames)
#             aaa
            if nvars is None:
                # guess from file content
                nvars = len(varnames)


#             for ivar in xrange(nvars):
            for ivar in range(nvars):  # equivalent to python2 and 3
                var_id = varnames[ivar]
                if var_id != '':
                    if var_id in list(self.variables.keys()):
                        # already a coumn with this name. Make it unique, by
                        # suffiwing "-xx"
                        ndbl = len(
                            [v for v in list(self.variables.keys()) if re.match(var_id + "(\-[0-9]{2})?", v)])
                        var_id = var_id + "-%02d" % (ndbl + 1)

                    var = CsvVariable(var_id, ivar, encoding=self.encoding)
                    if var.var_id in self.variables:
                        new_var_id = "{var_id:s}_icol{icol:d}".format(
                            var_id=var.var_id, icol=ivar)
# print "WARNING: a column with this name already exists \"" + var.var_id
# + "\" ; rename it as \"" + new_var_id + "\""
                        var.var_id = new_var_id

                    self.variables[var.var_id] = var
                    self.vars_order.append(var.var_id)
        except StopIteration:
            # empty file, no variables
            self.variables = {}
            raise ValueError("Empty file %s" % self.fname)

    def get_data(self, col_id=None, dtype=None):
        """
        @brief read the data of the given column and return them (as a list of strings)
        @param col_id name or indice of the column to read
        """
        ivar = None
        if isinstance(col_id, str) or isinstance(col_id, str):
            ivar = self.get_ds(col_id).ivar
        else:
            # assume it is a column number
            ivar = int(col_id)

        # read data of column number ivar
#         print(self.buf[:10])
        self.buf.seek(0)
        v_data = []

        reader = csv.reader(
            self.buf, delimiter=self.delimiter, skipinitialspace=True)
        # if 1st line contains column names -> skip it
        line = None
        if self.has_colname is True:
            #             reader.next()
            next(reader)
        try:
            while True:
                #                 line = reader.next()
                line = next(reader)
                vals = [v.strip() for v in line]
                if self.skip_empty_vals:
                    vals = [v for v in vals if len(v) > 0]
                nvals = len(vals)
#                 line = "".join(vals)
#                 if len(line) > 0: # skip empty lines

                if nvals != self.nvars:
                    # missing values : fill them with empty characters
                    vals += [''] * (self.nvars - nvals)
                    if self.trunc_line_detected is False:
                        self.trunc_line_detected = True
                        print(("WARNING: %s, uncomplete line detected" %
                               self.fname))
                        print(line)

#                         _names = self.get_vars()
#                         _vals = vals
#                         print self.nvars
#                         print len(_names)
#                         for i in xrange(min(len(_names), len(_vals))):
#                             print i, _names[i], _vals[i]
#                         aaa
                v_data.append(vals[ivar])
        except StopIteration:
            pass
        # eventual cast
        if dtype is not None:
            v_data = numpy.cast[dtype](v_data)
        return v_data

    def get_ds(self, ds_name):
        """
        @brief accessor to the variable by its name
        @param ds_name variable name
        @return the variable
        """
        var_id = CsvVariable.format_var_id(ds_name)
        return self.variables[var_id]

    def get_vars(self):
        """
        @brief return all variables in the order they were created
        """
        return [self.variables[var_id] for var_id in self.get_ds_names()]

    def get_ds_fill(self, ds_name):
        """
        read the fill value of the given dataset
        @param ds_name name of the dataset to read
        @return the fill value. Most of the time an empty character
        """
        return self.get_ds(ds_name).fill

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
        return [var_id for var_id in self.vars_order]
#         return self.variables.keys()

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
        s = '#' * 5 + ' ' + self.__class__.__name__ + \
            ' ' + '#' * 5 + os.linesep
        s += "fname        = %s%c" % (str(self.fname), os.linesep)
        s += "nvars        = %s%c" % (str(self.nvars), os.linesep)
        s += "nvals        = %s%c" % (str(self.nvals), os.linesep)
        s += os.linesep

        s += "[variables]%c" % (os.linesep)
#         for k, v in self.variables.iteritems():
        for k, v in iter(list(self.variables.items())):
            s += "- %s - %c%s" % (str(k), os.linesep, str(v))
        return s


def main():
    """
    Unit test
    """
#     fname = "/home/pascal/depot/ground_data_framework/data/OPE/AETHA/aethalometer_20130207.csv"
#     fname = "/home/pascal/depot/sir_actris_converter/data/nephe_native/sirta20120101_000000.txt"
#     fname = "/home/pascal/depot/ground_data_framework/data/CHC/AETHA/CHC_AETHA_RAW_2012-01-13_V1-00.csv"

#     fname = "/home/pascal/depot/ground_data_framework/data/CHC/NEPHE/CHC_NEPHE_RAW_2013-05-07_V1-00.csv"
#     reader = CsvReader(fname, delimiter=",", skip_rows=1)

    fname = "/home/pascal/depot/ground_data_framework/data/OPE/AETHA/OPE_AETH_RAW-2014-01-21_V1-00.csv"
    reader = CsvReader(fname, delimiter=";")

#     fname = "/home/pascal/depot/ground_data_framework/data/VDA/LIDAR_RAW/LOA_CE370_L1B-PR2_2012-03-20T00-00-00_1440_V1-00.txt"
#     reader = CsvReader(fname, delimiter=" ")

    print(reader)
    for ds_name in reader.get_ds_names():
        print(("-" + reader.get_ds(ds_name).var_id + "-"))
        data = reader.get_data(ds_name)
        print((data, len(data)))


if __name__ == "__main__":
    main()
