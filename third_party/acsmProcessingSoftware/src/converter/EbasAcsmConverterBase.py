# -*- coding: utf-8 -*-

"""
Description :
-------------
    ACSM converter Base class
    Abstract class, not intended to be used directly

Usage :
-------

Example :
---------


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
    v0.0.0 : 2023/03/23
    - creation
"""

import os.path
import sys
from optparse import OptionParser
import glob
import numpy
import collections
import re
pkgdir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkgdir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

from misc.FileTools import check_file, check_dir
from iointerface.AMESReader import AMESReader
from iointerface.AMESWriter import AMESWriter
from converter.Converter import Converter

__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]
__DEBUG__ = False
__THROW__ = True
__SHOW_BAD_INPUTS__ = False
__SHOW_OUTPUTS__ = True


class EbasAcsmConverterBase(object):
    """
    data converter
    """

    # - generic var IDs
    # START_ACQ_ID = "Days from the file reference point (start_time)"
    # END_ACQ_ID = "end_time of measurement, days from the file reference point"

    # fill values
    var_fills_conc = Converter.var_fills_conc  # 999999.9999
    var_fills_env = Converter.var_fills_env  # 9999.9999
    var_fills_qa = Converter.var_fills_qa  # 0.999
    var_fills_airbeam_ie = Converter.var_fill_airbeam_ie  # 9.9999E+99

    # output level
    olvl = None

    # arrays flags by categories
    MISSING_FLAGS = numpy.array([980, 999])
    INVALID_FLAGS = numpy.array(
        [456, 459, 460, 567, 568, 591, 593, 599, 635, 646, 659, 677, 899])
    VALID_FLAGS = numpy.array([0, 100, 110, 111, 120, 185, 410, 420, 457, 458,
                              476, 557, 558, 559, 645, 647, 651, 652, 660, 674, 676, 678, 780, 781])

    def __init__(self, fpath=None, inspected=False):
        """
        @brief constructor
        @param fpath input file path
        @param inspected manually inspected if True
        """
        object.__init__(self)
        check_file(fpath)
        self.fpath = fpath
        self.reader = AMESReader(self.fpath)
        # print(self.reader)
        self.inspected = inspected
        self.writer = None

    def get_invalid_mask(self, data_qa):
        """
        @brief return an invalidity mask, based on the input data_qa (suppose to have only 3 decimals)
        @param data_qa input QA flags array
        """
        mask = numpy.zeros(data_qa.shape, bool)
        int_data_qa = numpy.cast[int]((data_qa * 1000).round())
        for val in self.INVALID_FLAGS:
            mask |= (int_data_qa == val)
        return mask

    def get_valid_mask(self, data_qa):
        """
        @brief return an validity mask, based on the input data_qa (suppose to have only 3 decimals)
        @param data_qa input QA flags array
        """
        mask = numpy.zeros(data_qa.shape, bool)
        int_data_qa = numpy.cast[int]((data_qa * 1000).round())
        for val in self.VALID_FLAGS:
            mask |= (int_data_qa == val)
        return mask

    def process(self, outdir):
        """
        @brief write down next level data
        @param outdir output directory
        @return the path to the written file
        """
        if __DEBUG__:
            print("> processing {0:s} -> {1:s}".format(self.fpath, outdir))
        # - init: in/out copy
        self.writer = AMESWriter()
        self.writer.copy(self.reader)

        # - metadata tuning
        # update level
        self.writer.set_attr("Data level", self.olvl)
        # if 0b nrt, use a coarser time resolution to keep a consistant time serie (EBAS request)
        if self.olvl == "0b":
            s_dt_res = self.reader.get_attr("Orig. time res.")
            # if in seconds, coarser res in minutes is used
            m = re.match("^(?P<duration>[0-9]+)(?P<unit>s)$", s_dt_res.strip())
            if m is not None:
                dt_res = int(m.group("duration"))
                dt_res = int(numpy.ceil(dt_res / 60.))
                s_dt_res_out = str(dt_res) + "mn"
                self.writer.set_attr("Orig. time res.", s_dt_res_out)
                # print(s_dt_res + " -> " + s_dt_res_out)

        # - level conversion, done in children classes
        self.convert()
        # - final write
        outdir = os.path.abspath(outdir)
        check_dir(outdir)
        ofname = self.get_outfname()
        ofpath = os.path.join(outdir, ofname)
        self.writer.write(ofpath)
        return ofpath

    def convert(self):
        """
        @brief level conversion, implemented in children class
        """
        raise NotImplementedError()

    def get_invalid_acq(self, v_start_acq, v_end_acq, end_time_included=False,
                        start_time_included=False):
        """
        @brief build the mask and the values of acquisition errors as set in the error logger file
        @param v_start_acq vector of acquisition starts, using UNIX UTC EPOCH time
        @param v_end_acq vector of acquisition ends, using UNIX UTC EPOCH time
        @param end_time_included if True, end time is considered as invalid too
        @return mask of invalidated records
        """
        # if self.acq_err_logger is not None:
        #     return self.acq_err_logger.get_invalid_acq(v_start_acq, v_end_acq, end_time_included, start_time_included)
        # else:
        #     #  all considered as valid
        return numpy.zeros(v_start_acq.shape, dtype=bool), numpy.empty(v_start_acq.shape, dtype=float) + numpy.nan

    def get_outfname(self):
        """
        @brief construct the  standard actris filename for this granule and return it
        @param start_time start acquisition time in the format %Y%m%d%H%M%S"
        @param prod_time production time in the format %Y%m%d%H%M%S"
        @param lvl level of the product : 1 -> no time averaging ; 2 -> average all the year by day range
        """
        if self.olvl is None:
            raise ValueError("ERROR: destination level not set")
        lvl_tag = "lev{0:s}".format(str(self.olvl))

        # from inputs
        site = self.writer.get_attr("Station code")
        start_time = self.writer.get_attr("Startdate")
        prod_time = self.writer.prod_time.strftime("%Y%m%d%H%M%S")
        instrument = self.writer.get_attr("Instrument type")
        component = self.writer.get_attr("Component")
        matrix = self.writer.get_attr("Matrix")
        period = self.writer.get_attr("Period code")
        dt = self.writer.get_attr("Resolution code")
        method_ref = self.writer.get_attr("Method ref")
        instr_name = self.writer.get_attr("Instrument name")
        lvl_tag = "lev{0:s}".format(str(self.olvl))
        lab = self.writer.get_attr("Laboratory code")

        # fix eventual spaces
        instrument = instrument.replace(" ", "_")
        instr_name = instr_name.replace(" ", "_")
        method_ref = method_ref.replace(" ", "_")

        fname = "{site:s}.{start_time:s}.{prod_time:s}.{instrument:s}.{component:s}.{matrix:s}.{period:s}.{dt:s}.{lab:s}_{instr_name:s}.{method_ref:s}.{lvl_tag:s}.nas".format(
            site=site, start_time=start_time, prod_time=prod_time, instrument=instrument, component=component,
            matrix=matrix, period=period, dt=dt, method_ref=method_ref, instr_name=instr_name, lvl_tag=lvl_tag, lab=lab)
        return fname

    def get_invalid(self, indata):
        """
        @brief identify the invalid data values and return it in 2 dictionary buffers : one with invalid, one with NaNs
        @param indata input data buffer
        @return 3 buffers : one with mask of invalids, one with mask of NaNs, one with the manually invalidated values
        """
        raise NotImplementedError()

    def set_lev2_qa_flags(self, indata, outdata):
        """
        @brief build the level 2 aggregated informative flags
        @param indata input variables data buffer
        @param outdata input variables data buffer
        """
        # - output variables that have a flag
        out_var_ids = self.var_ids_env + self.var_ids_conc

        # --- hours iterator
        v_start_time = indata['start_time'][:].values
        v_end_time = indata['end_time'][:].values
        start_date, dt_start_date, dt_range, v_start_acq, v_end_acq = self.get_dt_range(v_start_time, v_end_time)

        # --- select records in hour time range
        for var_id in out_var_ids:
            var_id_qa = self.get_qa_var_id(var_id)
            if var_id_qa is None:
                continue

            # - invalidate and flag missing values
            fill = self.get_fill(var_id)
            is_nan = numpy.isnan(outdata[var_id])
            outdata[var_id][is_nan] = fill

            # outdata[var_id_qa] = numpy.empty(v_start_time.shape, dtype=float) + numpy.nan
            # print(var_id, var_id_qa)
            # outdata[var_id_qa][is_nan] = 0.999

            # - build input data validity mask
            indata_qa = indata[var_id_qa]
            is_valid = self.get_valid_mask(indata_qa)

            # - set hourly flag : most frequent flag in time range
            for idt, dt in enumerate(dt_range):
                t_min = dt.to_numpy()
                t_max = t_min + numpy.timedelta64(3600, "s")
                s = ((v_end_acq > t_min) & (v_start_acq < t_max))
                v_flags = indata_qa[s & is_valid]
                # if var_id == "Org":
                #     print(idt, dt, indata_qa[s])
                #     print(v_flags[:].values)
                #     print(numpy.bincount(v_flags))
                if v_flags.size == 0:
                    # all invalid, missing flag
                    outdata[var_id_qa][idt] = 0.999
                elif numpy.all(v_flags == 0):
                    # all valid, no infos
                    outdata[var_id_qa][idt] = 0.
                elif outdata[var_id][idt] != fill:
                    # add meaningful infos, hidden if fill
                    outdata[var_id_qa][idt] = collections.Counter(v_flags[v_flags != 0]).most_common()[0][0]
                # if var_id == "Org":
                #     print(">", outdata[var_id_qa][idt])

        return outdata


def get_parser(app):
    """
    Sets the available program options, and their default values
    """
    parser = OptionParser()

    parser.usage = "python3 " + app + \
        ".py [options]  <fname> <outdir>" + os.linesep
    parser.usage += os.linesep
    parser.usage += "with :" + os.linesep
    parser.usage += "\t<fname>  full path to the file to convert" + os.linesep
    parser.usage += "\t<outdir> output directory where will be wrote the ACTRIS files" + \
        os.linesep

    parser.add_option("-i", "--inspected", action="store_true", default=False, dest="inspected",
                      help="Generate manually inspected products (level 'a' tags)")

    # check the number of command line arguments
    if len(sys.argv) < 2:
        parser.print_help()
        raise ValueError("Missing command-line options")

    return parser


def get_args(app, check_infiles=True):
    """
    Check if the command line options are valid. If not, throws an exception describing the problem
    @param check_infiles is True, check file validity
    """
    parser = get_parser(app)
    (options, args) = parser.parse_args()

    infiles = args[:-1]
    _infiles = []
    for infile in infiles:
        _infiles += glob.glob(infile)
    _infiles.sort()
    infile = _infiles[0]

    check_file(infile)
    outdir = args[-1]
    check_dir(outdir)

    return infile, outdir, options
