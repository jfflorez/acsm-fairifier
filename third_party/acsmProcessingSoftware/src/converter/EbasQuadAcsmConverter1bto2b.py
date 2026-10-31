# -*- coding: utf-8 -*-

"""
Description :
-------------
    EBAS Quad ACSM converter - level 1b to 2b
    Compute hourly means

Usage :
-------
    Usage: python3 QuadAcsmConverter.py [options]  <fname> <outdir>

    with :
        <fname>  full pathes to the files to convert
        <outdir> output directory where will be wrote the ACTRIS files

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
    v0.0.0 : 2021/06/14
    - creation
"""

import os
import os.path
import glob
import sys
import datetime
import numpy
import pandas

pkg_dir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkg_dir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

import converter.EbasQuadAcsmConverter as EbasQuadAcsmConverter
from misc.AppContextController import MissingDataException

__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]
__DEBUG__ = True
__THROW__ = True
__SHOW_BAD_INPUTS__ = False
__SHOW_OUTPUTS__ = True


class EbasQuadAcsmConverter1bto2b(EbasQuadAcsmConverter.EbasQuadAcsmConverter):
    """
    data converter
    """

    # --- used input vars (column names)
    # - time axis
    START_ACQ_ID = "start_time"
    END_ACQ_ID = "end_time"

    # - acq conditions
    INLETP_ID = "inletP"
    T_IN_ID = "T_in"
    RH_IN_ID = "RH_in"

    # - concentrations
    OM_ID = "Org"
    NO3_ID = "NO3"
    NO3_F30_ID = "NO3_30"
    NO3_F46_ID = "NO3_46"
    SO4_ID = "SO4"
    NH4_ID = "NH4"
    CL_ID = "Chl"
    OM_F44_ID = "Org_44"
    OM_F43_ID = "Org_43"
    OM_F60_ID = "Org_60"

    # - groups of param of same kind
    var_ids_env = [
        INLETP_ID,
        # T_IN_ID,
        # RH_IN_ID
    ]

    var_ids_conc = [
        OM_ID,
        NO3_ID,
        NO3_F30_ID,
        NO3_F46_ID,
        SO4_ID,
        NH4_ID,
        CL_ID,
        OM_F44_ID,
        OM_F43_ID,
        OM_F60_ID,
    ]

    var_ids_conc_err = ["err_" + var_id for var_id in var_ids_conc]

    # --- limits
    # all errors below this limit are considered as invalid
    LOWER_ERR_LIMIT = 5e-5

    #  output level
    # olvl = "2b"

    def __init__(self, fpath=None, inspected=False):
        """
        @brief constructor
        @param fpath input file path
        @param acq_err_log path the error logger (manual QC)
        """
        EbasQuadAcsmConverter.EbasQuadAcsmConverter.__init__(
            self, fpath, inspected)
        # output level
        if self.inspected:
            self.olvl = "2"
        else:
            self.olvl = "2b"

    def convert(self):
        """
        @brief level conversion, set concentrations to SCTP
        """
        self.average()

    @staticmethod
    def ames_time_to_numpy_dt(start_date, v_time):
        """
        @brief convert times in NASA AMES format (a start_date origin and decimal days) to a numpy datetime64 array
        """
        dt_start_date = numpy.datetime64(start_date)
        v_time *= 24 * 3600  # to seconds
        v_time = numpy.cast[int](numpy.round(v_time))
        v_time = numpy.array([numpy.timedelta64(dt, "s") for dt in v_time])
        return dt_start_date + v_time

    def get_dt_range(self, v_start_time, v_end_time):
        """
        @brief build the datetime range iterator over hours
        """
        start_date = self.reader.start_date
        # v_start_acq = self.ames_time_to_numpy_dt(
        #     start_date, data['start_time'][:].values)
        # v_end_acq = self.ames_time_to_numpy_dt(
        #     start_date, data['end_time'][:].values)
        v_start_acq = self.ames_time_to_numpy_dt(start_date, v_start_time)
        v_end_acq = self.ames_time_to_numpy_dt(start_date, v_end_time)

        # --- iterate over hours
        dt_start_date = datetime.datetime(
            start_date.year, start_date.month, start_date.day)
        # start is the first hour after first record
        dt_start = v_start_acq[0].astype(datetime.datetime)
        dt_start = datetime.datetime(
            dt_start.year, dt_start.month, dt_start.day, dt_start.hour, 0, 0)
        dt_start += datetime.timedelta(hours=1)
        # hour of last record
        dt_end = v_start_acq[-1].astype(datetime.datetime)
        dt_end = datetime.datetime(
            dt_end.year, dt_end.month, dt_end.day, dt_end.hour, 0, 0)
        dt_range = pandas.date_range(start=dt_start, end=dt_end, freq="H")
        return start_date, dt_start_date, dt_range, v_start_acq, v_end_acq

    def get_weighted_stats(self, data):
        """
        @brief compute the time weighted mean and stddev of all data
        """
        # --- start/end of acquisition vectors
        v_start_time = data['start_time'][:].values
        v_end_time = data['end_time'][:].values
        start_date, dt_start_date, dt_range, v_start_acq, v_end_acq = self.get_dt_range(v_start_time, v_end_time)

        # check if we have enough data for computing an hourly mean
        if len(dt_range) == 0:
            raise MissingDataException(msg="Not enough data to compute an hourly mean")

            # --- compte stats for each hourly window
        outdata = None
        for dt in dt_range:
            # print (dt)
            hourly_data = self.get_stats(
                data, dt, dt_start_date, v_start_acq, v_end_acq)
            if outdata is None:
                outdata = hourly_data
            else:
                # merge
                for key in outdata:
                    outdata[key] += hourly_data[key]

        # - buid a time serie with that
        for key in outdata:
            outdata[key] = numpy.array(outdata[key])
        v_start_acq_out = self.ames_time_to_numpy_dt(
            start_date, outdata['start_time'])
        outdata = pandas.DataFrame(
            data=outdata, columns=outdata.keys(), index=v_start_acq_out)

        return outdata

    def get_stats(self, indata, dt, dt_start_date, v_start_acq, v_end_acq):
        """
        @brief compte time range weighted mean and std for all paramaters in dataframe
        @param indata the full time resolution data frame
        @param dt hour to average
        @param dt_start_date time axis origin
        @param v_start_acq start of acquisition time vector (precomputed for speed)
        @param v_end_acq end of acquisition time vector (precomputed for speed)
        """
        # --- init storage struct
        # outdata = pandas.Series(index=[dt], dtype=object)
        outdata = {}
        # start/end time in decimal days from origin
        start_time = (dt - dt_start_date).total_seconds() / \
            86400.  # to seconds
        end_time = start_time + (1. / 24)
        outdata["start_time"] = [start_time]
        outdata["end_time"] = [end_time]
        # init empty columns
        for col in indata.columns:
            if col in ["start_time", "end_time"]:
                # already done
                continue
            outdata[col] = [numpy.nan]

        # --- select records in hour time range
        t_min = dt.to_numpy()
        t_max = t_min + numpy.timedelta64(3600, "s")
        s = ((v_end_acq > t_min) & (v_start_acq < t_max))
        if not s.any():
            # - no data in time range
            return outdata

        # --- compute time range weights
        # all acquisition time range in considered hour -> 1
        # else, fraction acquisition time range in considered hour (first and last element)
        n_elts = s.sum()
        weights = numpy.ones((n_elts), dtype=numpy.float64)
        # first element
        if v_start_acq[0] < t_min and v_end_acq[0] > t_min:
            weights[0] = (v_end_acq[0] - t_min) / \
                (v_end_acq[0] - v_start_acq[0])
        # last element
        if v_start_acq[-1] < t_max and v_end_acq[-1] > t_max:
            weights[-1] = (t_max - v_start_acq[-1]) / \
                (v_end_acq[-1] - v_start_acq[-1])
        # print (weights)
        for col in indata.columns:
            if col in ["start_time", "end_time"] or col.startswith("numflag_"): # or col.startswith("err_"):
                # not relevant datasets ; err recomputed here
                continue
            values = indata[col][s].values

            # - filter out flagged values
            is_valid = numpy.isfinite(values)
            _values = values[is_valid]
            _weights = weights[is_valid]

            # -> avg
            _mean = numpy.nan
            if numpy.any(is_valid):
                _mean = numpy.average(_values, weights=_weights)
            outdata[col] = [_mean]
            # print(col, values, "mean:", _mean)

            ## -> stddev, source, concentrations only
            #if col in self.var_ids_conc:
                #_std = numpy.nan
                #if numpy.any(is_valid):
                    #variance = numpy.average(
                        #(_values - _mean) ** 2, weights=_weights)
                    #_std = numpy.sqrt(variance)
                #outdata["err_" + col] = [_std]
        return outdata

    def get_qa_var_id(self, var_id):
        """
        @brief for the given variable, return the variable ID that represents its QA flag. None if no QA for the parameter
        """
        if var_id in self.var_ids_env:
            None
        elif var_id in self.var_ids_conc_err:
            # for errors, qa is the concentration flag
            return "numflag_" + var_id[4::]
        else:
            return "numflag_" + var_id

    def get_fill(self, var_id):
        """
        @brief return the fill value that match the given variable
        """
        if var_id in self.var_ids_conc + self.var_ids_conc_err:
            return self.var_fills_conc
        elif var_id in self.var_ids_env:
            return self.var_fills_env
        elif var_id in self.var_ids_qa:
            return self.var_fills_qa
        else:
            raise ValueError("Unsupported variable " + str(var_id))

    def average(self):
        """
        @brief hourly averages computations
        """
        out_var_ids = self.var_ids_env + self.var_ids_conc + self.var_ids_conc_err
        indata = self.reader.data
        outdata = self.writer.data
        for var_id in out_var_ids:
            # - hide flaggued values in DataFrame
            data = indata[var_id]
            is_invalid = (data == self.get_fill(var_id))
            var_id_qa = self.get_qa_var_id(var_id)
            if var_id_qa is not None:
                data_qa = indata[var_id_qa]
                # is_invalid |= (data_qa != 0)
                is_invalid |= self.get_invalid_mask(data_qa)
            data[is_invalid] = numpy.nan
            outdata[var_id] = data

        # -  update variable names
        for var_id in self.var_ids_conc:
            var_name = self.writer.get_var_name(var_id)
            if not var_name.endswith("Statistics=arithmetic mean"):
                self.writer.rename_var(
                    var_name, var_name + ", Statistics=arithmetic mean", unit="hPa")

        # --- update output data buffer
        # - compute hourly means and std
        outdata = self.get_weighted_stats(outdata)

        # - insert uncertainties
        for var_id in self.var_ids_conc_err:
            # previous variable
            _var_id = var_id[4::]  # remove "err_" prefix
            _var = self.writer.get_var(_var_id)
            elts = _var.var_id.split(", ")
            l1_var_name = "{0:s}, {1:s}, Statistics=uncertainty".format(
                elts[0], elts[1])
            var_name = l1_var_name + ", Measurement uncertainty="
            data = outdata[var_id]

            # - err < LOWER_ERR_LIMIT are considered as missing
            is_below_limit = data < self.LOWER_ERR_LIMIT
            # if numpy.any(is_below_limit):
            # print (var_id, numpy.where(is_below_limit), data[is_below_limit])
            data[is_below_limit] = self.get_fill(var_id)

            # - replace if present
            self.writer.rename_var(l1_var_name, var_name, unit="ug/m3")
            self.writer.data[var_id] = data

        # - add flags
        outdata = self.set_lev2_qa_flags(indata, outdata)

        # - invalidate missing NaN values
        for var_id in out_var_ids:
            data = outdata[var_id]
            is_nan = numpy.isnan(data)
            data[is_nan] = self.get_fill(var_id)

        # - update time axis infos
        start_time = outdata.index[0]
        start_of_year = datetime.datetime(start_time.year, 1, 1, 0, 0, 0)
        v_start_acq = pandas.to_datetime(outdata.index)
        v_start_acq -= start_of_year
        start_acq_days = [float(dt.total_seconds()) / 86400. for dt in v_start_acq]
        end_acq_days = [float(dt.total_seconds() + 3600) / 86400. for dt in v_start_acq]
        outdata[self.START_ACQ_ID] = start_acq_days
        outdata[self.END_ACQ_ID] = end_acq_days

        # - update data buffer
        self.writer.data = outdata

        # - update infos related to new vars
        # n_new_vars =  len(self.var_ids_conc_err) # add uncertainty
        # self.writer.nlin_header += n_new_vars
        # self.writer.nvars += n_new_vars

        # - update metdata infos
        self.writer.set_attr("DATE", start_of_year.date())
        self.writer.set_attr("Set type code", "TU")
        self.writer.set_attr("Startdate", start_time.strftime("%Y%m%d%H%M%S"))
        self.writer.set_attr("Resolution code", "1h")
        self.writer.set_attr("Sample duration", "1h")
        self.writer.dt = 1. / 24.


def main():
    fpath, outdir, options = EbasQuadAcsmConverter.get_args(__APP__)
    prog = EbasQuadAcsmConverter1bto2b(fpath, options.inspected)
    prog.process(outdir)


def test():
    """
    Unit test
    """
    acq_err_log = None

    indir = os.path.abspath(os.path.join(pkg_dir, "..", ".."))
    fpath = glob.glob(indir + "/tests/SIRTA/ref/*.lev1b.nas")
    fpath = fpath[0]
    outdir = os.path.expanduser("~") + "/tmp"
    prog = EbasQuadAcsmConverter1bto2b(fpath, acq_err_log)
    ofpath = prog.process(outdir)
    # os.system("kate " + ofpath)
    os.system("module purge ; meld " + glob.glob(indir + "/tests/SIRTA/ref/*.lev2b.nas")[0] + " " + ofpath)


if __name__ == "__main__":
    # test()
    main()
