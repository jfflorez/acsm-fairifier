# -*- coding: utf-8 -*-

"""
Description :
-------------
    EBAS Quad ACSM converter - level 1b to 15 min means, used only for ATOLL station
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
    v0.0.0 : 2022/01/17
    - creation
"""

import os
import os.path
import glob
import sys
import datetime

import numpy
import pandas
from scipy import interpolate

pkg_dir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkg_dir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

import converter.EbasQuadAcsmConverter as EbasQuadAcsmConverter

__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]
__DEBUG__ = True
__THROW__ = True
__SHOW_BAD_INPUTS__ = False
__SHOW_OUTPUTS__ = True


class EbasQuadAcsmConverter1bto15min(EbasQuadAcsmConverter.EbasQuadAcsmConverter):
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
        T_IN_ID,
        RH_IN_ID
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
    #  output level
    olvl = "1b-15min"

    def __init__(self, fpath=None, acq_err_log=None):
        """
        @brief constructor
        @param fpath input file path
        @param acq_err_log path the error logger (manual QC)
        """
        EbasQuadAcsmConverter.EbasQuadAcsmConverter.__init__(
            self, fpath, acq_err_log)

    def convert(self):
        """
        @brief level conversion, inteprolate to 15min points
        """
        self.resample()

    @staticmethod
    def ames_time_to_numpy_dt(start_date, v_time):
        """
        @brief convert times in NASA AMES format (a start_date origin and decimal days) to a numpy datetime64 array
        """
        dt_start_date = numpy.datetime64(start_date)
        v_time *= 24 * 3600  # to seconds
        v_time = numpy.cast[numpy.int](numpy.round(v_time))
        v_time = numpy.array([numpy.timedelta64(dt, "s") for dt in v_time])
        return dt_start_date + v_time

    def get_interp_stats(self, data):
        """
        @brief compute the time weighted mean and stddev of all data
        """
        # --- start/end of acquisition vectors
        start_date = self.reader.start_date
        v_start_acq = self.ames_time_to_numpy_dt(
            start_date, data['start_time'][:].values)
        v_end_acq = self.ames_time_to_numpy_dt(
            start_date, data['end_time'][:].values)
        # print (v_start_acq)
        # print (v_end_acq)

        # --- iterate over hours
        dt_start_date = datetime.datetime(
            start_date.year, start_date.month, start_date.day)
        # start is the first hour after first record
        dt_start = v_start_acq[0].astype(datetime.datetime)
        dt_start = datetime.datetime(
            dt_start.year, dt_start.month, dt_start.day, dt_start.hour, 0, 0)
        dt_start += datetime.timedelta(hours=1)
        # hour of last record
        dt_end = v_end_acq[-1].astype(datetime.datetime)
        dt_end = datetime.datetime(
            dt_end.year, dt_end.month, dt_end.day, dt_end.hour, 0, 0)
        # sometimes, last record can be missing
        if dt_start == dt_end:
            dt_end += datetime.timedelta(hours=1)
        dt_range = pandas.date_range(start=dt_start, end=dt_end, freq="15min")
        # remove start of next hour
        dt_range = dt_range[:-1]
        # print (dt_start, dt_end)

        # --- compute stats for each hourly window
        outdata = self.get_interp(
            data, dt_range, dt_start_date, v_start_acq, v_end_acq)

        # - buid a time serie with that
        for key in outdata:
            outdata[key] = numpy.array(outdata[key])
        # print (outdata['start_time'])

        v_start_acq_out = self.ames_time_to_numpy_dt(
            start_date, outdata['start_time'])
        outdata = pandas.DataFrame(
            data=outdata, columns=outdata.keys(), index=v_start_acq_out)

        return outdata

    def get_interp(self, indata, dt_range, dt_start_date, v_start_acq, v_end_acq):
        """
        @brief compte time range weighted mean and std for all paramaters in dataframe
        @param indata the full time resolution data frame
        @param dt_range interp datetime range
        @param dt_start_date time axis origin
        @param v_start_acq start of acquisition time vector (precomputed for speed)
        @param v_end_acq end of acquisition time vector (precomputed for speed)
        """
        # --- init storage struct
        outdata = {}

        # time axis to interpolate on
        # to seconds since start date
        v_acq_out = (dt_range - dt_start_date).total_seconds()
        start_time = v_acq_out / 86400.  # to decimal days since start date

        # set time axis or init empty columns
        for col in indata.columns:
            if col == "start_time":
                outdata["start_time"] = start_time
            elif col == "end_time":
                outdata["end_time"] = start_time + (15. / 24.)  # 15min
            else:
                outdata[col] = [numpy.nan]

        # --- interp on new time range
        # v_acq_out = numpy.array(dt_range) # pandas -> numpy ep
        for col in indata.columns:
            # print (col)
            if col in ["start_time", "end_time"] or col.startswith("numflag_"):
                # not relevant datasets
                continue
            # filter NaN
            v_x_out = v_acq_out
            v_y_in = indata[col].values
            v_x_in = indata["start_time"].values
            is_valid = numpy.isfinite(v_y_in)
            if not numpy.any(is_valid):
                outdata[col] = numpy.ones(
                    v_x_out.size, dtype=v_y_in.dtype) + numpy.nan
                continue

            v_y_in = v_y_in[is_valid]
            v_x_in = v_x_in[is_valid]
            # values = numpy.interp(v_x_out, v_x_in, v_y_in)
            func = interpolate.interp1d(
                v_x_in, v_y_in, fill_value="extrapolate")
            values = func(v_x_out)

            outdata[col] = values

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

    def resample(self):
        """
        @brief hourly averages computations
        """
        out_var_ids = self.var_ids_env + self.var_ids_conc + self.var_ids_conc_err
        indata = self.reader.data
        outdata = self.writer.data
        for var_id in out_var_ids:
            # - hide flaggued values in DataFrame
            data = indata[var_id]
            is_invalid = (data == self.var_fills_conc)
            var_id_qa = self.get_qa_var_id(var_id)
            if var_id_qa is not None:
                data_qa = indata[var_id_qa]
                is_invalid |= (data_qa != 0)
            data[is_invalid] = numpy.nan
            outdata[var_id] = data

        # -  update variable names
        for var_id in self.var_ids_conc:
            var_name = self.writer.get_var_name(var_id)
            if not var_name.endswith("Statistics=arithmetic mean"):
                self.writer.rename_var(
                    var_name, var_name + ", Statistics=15min interpolation", unit="hPa")
            else:
                self.writer.rename_var(
                    var_name, var_name.replace("Statistics=arithmetic mean", "Statistics=15min interpolation"))

        # --- update output data buffer
        # - compute 15min interpolation means
        outdata = self.get_interp_stats(outdata)

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
            # - insert if not present
            # self.writer.insert_var_after(_var_id, var_id, var_name, fill_value=self.var_fills_conc, col_size=col_size)
            # ivar = self.writer.get_ivar(var_id)
            # outdata.insert(ivar, var_id, data)
            # - replace if present
            self.writer.rename_var(l1_var_name, var_name, unit="ug/m3")
            self.writer.data[var_id] = data

        # - invalidate missing values
        indata = outdata
        for var_id in out_var_ids:
            # - hide flaggued values in DataFrame
            data = indata[var_id].copy()
            is_nan = numpy.isnan(data)
            # - eventual flag
            var_id_qa = self.get_qa_var_id(var_id)
            if var_id_qa is not None:
                data_qa = indata[var_id_qa]
                data_qa[is_nan] = 0.999
                data_qa[~is_nan] = 0.
                outdata[var_id_qa] = data_qa
            data[is_nan] = self.var_fills_conc
            outdata[var_id] = data

        # - update time axis infos
        start_time = outdata.index[0]
        start_of_day = datetime.datetime(
            start_time.year, start_time.month, start_time.day, 0, 0, 0)
        v_start_acq = pandas.to_datetime(outdata.index)
        v_start_acq -= start_of_day

        start_acq_days = [float(dt.seconds) / 86400. for dt in v_start_acq]
        end_acq_days = [float(dt.seconds + 3600) /
                        86400. for dt in v_start_acq]
        outdata[self.START_ACQ_ID] = start_acq_days
        outdata[self.END_ACQ_ID] = end_acq_days

        # - update data buffer
        self.writer.data = outdata

        # - update infos related to new vars
        # n_new_vars =  len(self.var_ids_conc_err) # add uncertainty
        # self.writer.nlin_header += n_new_vars
        # self.writer.nvars += n_new_vars

        # - update metdata infos
        self.writer.set_attr("DATE", start_time.date())
        self.writer.set_attr("Set type code", "TU")
        self.writer.set_attr("Startdate", start_time.strftime("%Y%m%d%H%M%S"))
        self.writer.set_attr("Resolution code", "15min")
        self.writer.set_attr("Sample duration", "1h")
        self.writer.dt = 0.25 / 24.


def main():
    fpath, outdir, options = EbasQuadAcsmConverter.get_args(__APP__)
    acq_err_log = None
    prog = EbasQuadAcsmConverter1bto15min(fpath, acq_err_log)
    prog.process(outdir)


def test():
    """
    Unit test
    """
    acq_err_log = None

    indir = os.path.abspath(os.path.join(pkg_dir, "..", ".."))
    fpath = glob.glob(indir + "/tests/ATOLL/ref/*.lev1b.nas")
    fpath = fpath[0]
    outdir = os.environ["HOME"] + "/tmp"
    prog = EbasQuadAcsmConverter1bto15min(fpath, acq_err_log)
    ofpath = prog.process(outdir)
    os.system("kate " + ofpath)
    # os.system("module purge ; meld " + glob.glob(indir + "/tests/ATOLL/ref/*.lev2b.nas")[0] + " " + ofpath)


if __name__ == "__main__":
    # test()
    main()
