# -*- coding: utf-8 -*-

"""
Description :
-------------
    ACTRIS converter abstract class

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
    v0.0.0 : 2013/09/30
    - creation
"""

import io
import os
import glob
import sys
import time
import re
from datetime import datetime
import calendar
from optparse import OptionParser

import numpy

pkgdir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkgdir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

from ProductIdentifier import ProductIdentifier
from product.Product import Product
from product.AcquisitionErrorLogger import AcquisitionErrorLogger
from product.IgorFlagLogger import IgorFlagLogger
from misc.TimeConverter import NSEC_DAY
from misc.Percentile import percentile
from misc.FileTools import check_file, check_dir, get_nlines
import misc.TimeTools as TimeTools
import misc.Standardizer as Standardizer

__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]

__DEBUG__ = True
__THROW__ = True
__SHOW_BAD_INPUTS__ = True
__SHOW_OUTPUTS__ = True


class Converter(object):
    """
    Generic interface for data conversion
    """

    # acquisition conditions
    acq_temp = None  # temperature in K
    acq_pres = None  # pressure in hPa

    QA_FLAGS_ID = "QA_Flags"
    #QA_AGG_FLAGS_ID = "QA_Agg_Flags"  # aggreageted flags, L2

    #QA_FLAGS_VALID = 0.000
    #QA_FLAGS_FILL = 9.999
    #QA_FLAGS_MISSING = 0.999
    #DEFAULT_FILL = 9999.999

    # fill values
    var_fills_conc = 9999999.9999
    var_fills_env = 9999.9999
    var_fills_env_tof = 9999.999
    var_fills_qa = 0.999
    var_fill_airbeam_ie = 9.9999E+99

    # acquisition conditions
    # acq_temp = 273.15  # temperature in K
    # acq_pres = 850.25  # pressure in hPa

    # # output file constants
    # sz_header_base = 66

    # acquisition conditions (set in cfg files)
    acq_temp = None  # temperature in K
    acq_pres = None  # pressure in hPa

    # output file constants
    sz_header_base = None

    re_fname = re.compile(r"^(?P<site>[^_]+)_ACSM-(?P<sn>[^_]*).*\.txt$")
    re_prod_id = re.compile(r"^(?P<station_id>[^_]+)_(?P<instr_id>.+)_RAW(_NRT)?$")

    # specific atributes. Must be implemented by concrete classes
    component = "chemistry_ACSM"
    matrix = None
    instrument = "aerosol_mass_spectrometer"
    brand = "Aerodyne"
    unit = "ug/m3"
    sn = None
    component_extra_tag = None
    submitter = "Pascal, Nicolas, nicolas.pascal@univ-lille.fr, AERIS/ICARE Data and Services Center, AERIS/ICARE,, Universite Lille 1, Bat. M3 Extension - Avenue Carl Gauss, 59650, Villeneuve d'Ascq, France"

    # product identifier utility
    product_identifier = ProductIdentifier()

    def __init__(self, prod_id, reader_interface, year=None, period=None, levels=[1, 2, 3], nrt=False, acq_err_log=None):
        """
        @brief constructor
        @param prod_id input product ID
        @param reader_class data reader class
        @param year year of the eventual yearly synthesis
        @param period period id in case of configuration change over the year (
        @param levels list of supported levels
        @param acq_err_log file that contains the history of acquisition errors with its description, can also be a list of string
        """
        object.__init__(self)
        self.prod_id = prod_id
        self.reader_interface = reader_interface
        self.year = year
        self.period = period
        self.levels = levels
        self.nrt = nrt
        self.acq_err_logger = None  # one log file only
        self.acq_err_loggers = None  # multiple log for one dataset. Should be merged
        if acq_err_log is not None:
            if isinstance(acq_err_log, str):
                check_file(acq_err_log)
                if acq_err_log.endswith(".txt"):
                    # specific to ACSM: flag file build in IGOR app
                    LoggerClass = IgorFlagLogger
                else:
                    # general case
                    LoggerClass = AcquisitionErrorLogger
                self.acq_err_logger = LoggerClass(acq_err_log)
            elif isinstance(acq_err_log, list):
                # be careful, only the last file set in acq_err_logger. Need a
                # specific treatment
                self.acq_err_loggers = []
                for flog in acq_err_log:
                    check_file(flog)
                    if flog.endswith(".txt"):
                        # specific to ACSM: flag file build in IGOR app
                        LoggerClass = IgorFlagLogger
                    else:
                        # general case
                        LoggerClass = AcquisitionErrorLogger
                    self.acq_err_loggers.append(LoggerClass(flog))

        self.infiles = None

    def read_station_and_instr_infos(self):
        """
        @brief based product ID on files stations/*.cfg and instruments/*.cfg, read the instrument and station metadata.
        """
        # based on product ID pattern, read information set in platform.cfg and instrment.cfg files
        station_infos = self.product_identifier.get_platform(self.prod_id)
        instr_infos = self.product_identifier.get_instrument(self.prod_id)
        # set content as attributes
        for infos in [station_infos, instr_infos]:
            mydic = infos.__dict__
            for attr in mydic:
                if attr not in ["sid"]:
                    setattr(self, attr, mydic[attr])

    def set_instr_name_and_method(self):
        """
        @brief set instrument and method name
        """
        self.instr_name = "{brand:s}_{model:s}_{sn:s}".format(
            brand=self.brand, model=self.model, sn=str(self.sn))

        self.method_ref = "{lab:s}_{brand:s}_{model:s}_{gaw_id:s}".format(
            lab=self.lab, brand=self.brand, model=self.model, gaw_id=self.gaw_id)

    def get_time_tags(self, lvl, v_start_acq, v_end_acq, year):
        """
        @brief return the time resolution, level, etc as requested by ACTRIS data format
        @param lvl level of the ACTRIS product
        @param v_start_acq start acquisition time vector
        @return the time tags
        """
        v_diff_acq = numpy.diff(v_start_acq)
        v_diff_sampling = v_end_acq - v_start_acq

        period_tag = TimeTools.get_period_code(v_start_acq[0], v_start_acq[-1])
        dt_res = int(numpy.round(numpy.median(v_diff_acq)))
        dt_raw_tag = TimeTools.get_period_code(0, dt_res)

        if lvl in [0, 1, "0b", "1b", 1.5]:
            if lvl in ["0b", "1b"]:
                # if NRT, use a coarser time resolution in min
                dt_res = (numpy.ceil(dt_res / 60.) + 1) * 60
                dt_raw_tag = TimeTools.get_period_code(0, dt_res)

            dt_tag = dt_raw_tag
            dt = dt_res / (3600. * 24.)
            dt_sampling = int(numpy.round(numpy.median(v_diff_sampling)))
            if dt_sampling == 0:
                # resolution and qsampling duration are the same
                dt_sampling = dt_res
            dt_sampling_tag = TimeTools.get_period_code(0, dt_sampling)

            # - dt raw acq depends of periods : analyze inputs
            # time res in secs between 2 input records
            v_dt = numpy.diff(v_start_acq)
            is_const_dt = True
            if not numpy.all(v_dt == v_dt[0]):
                # multiple input res. Take the more frequent one
                is_const_dt = False

            if not is_const_dt:
                dt = 0

        elif lvl in ["2b", 2]:
            dt_tag = "1h"
            dt = 0.041667  # 1h in decimal day unit
            dt_sampling_tag = "1h"
        else:
            raise ValueError("Unsupported level " + str(lvl))

        return (period_tag, dt_tag, dt, dt_raw_tag, dt_sampling_tag)

    def read_metadata(self, infiles):
        """
        @brief eventually decode metadata from inputs in super classes if implemented
        """
        self.read_station_and_instr_infos()
        self.set_instr_name_and_method()

    def __str__(self):
        """
        print out object content
        """
        s = str(self.__class__) + os.linesep
        s += "levels=" + str(self.fname) + os.linesep
        return s

    def get_readers(self, infiles):
        """
        @brief return all the reader interfaces, instanciated with infiles
        @param a list of input files
        @return the instanciated readers
        """
        return [self.reader_interface(infile) for infile in infiles]

    def build_outfname(self, site, start_time, prod_time, component, matrix, component_extra_tag, period, dt, lvl):
        """
        @brief construct the  standard actris filename for this granule and return it
        @param start_time start acquisition time in the format %Y%m%d%H%M%S"
        @param prod_time production time in the format %Y%m%d%H%M%S"
        @param lvl level of the product : 1 -> no time averaging ; 2 -> average all the year by day range
        """
        lvl_tag = "lev{0:s}".format(str(lvl))

        if component_extra_tag is not None and len(component_extra_tag.strip()) > 0:
            component_extra_tag = "_" + component_extra_tag
        else:
            component_extra_tag = ""

        # fix eventual spaces
        instrument = self.instrument.replace(" ", "_")
        instr_name = self.instr_name.replace(" ", "_")
        method_ref = self.method_ref.replace(" ", "_")

        fname = "{site:s}.{start_time:s}.{prod_time:s}.{instrument:s}.{component:s}{component_extra_tag:s}.{matrix:s}.{period:s}.{dt:s}.{lab:s}_{instr_name:s}.{method_ref:s}.{lvl_tag:s}.nas".format(
            site=site, start_time=start_time, prod_time=prod_time, instrument=instrument, component=component, component_extra_tag=component_extra_tag,
            matrix=matrix, period=period, dt=dt, method_ref=method_ref, instr_name=instr_name, lvl_tag=lvl_tag, lab=self.lab)
        return fname

    def get_outfname(self, start_time, prod_time, lvl, v_start_acq, v_end_acq, year=None):
        """
        @brief construct the  standard actris filename for this granule and return it
        @param start_time start acquisition time in the format %Y%m%d%H%M%S"
        @param prod_time production time in the format %Y%m%d%H%M%S"
        @param lvl level of the product : 1 -> no time averaging ; 2 -> average all the year by day range
        """
        period_tag, dt_tag = self.get_time_tags(lvl, v_start_acq, v_end_acq, year)[:2]
        _lvl = str(lvl)

        return self.build_outfname(self.station, start_time, prod_time, self.component, self.matrix, self.component_extra_tag, period_tag, dt_tag, _lvl)

    def get_acq_time_tags(self, t_start, lvl, year=None, use_real_start_time=False):
        """
        @brief set the acquisition time tags in use in output files
        @param t_start acquisition start time in UNIX epoch time
        @param lvl level on output file
        @param year year of synthesis if level = 2
        @return (start_time, start_day) where start_time the first measurement time ("%Y%m%d%H%M%S") and
            start_day if the reference time axis day (%Y %m %d)
        """
        start_time = None
        start_day = None
        if lvl in [1.5, 2] and not use_real_start_time:
            # if year is None:
            # raise ValueError(
            # "For level synthesis, a year must be specified")
            # hourly synthesis, first day of acq
            start_time = time.strftime(
                "%Y%m%d000000", time.gmtime(numpy.round(t_start)))
            start_day = time.strftime(
                "%Y %m %d", time.gmtime(numpy.round(t_start)))

            # start_time = "%d0101000000" % year
            # start_day = "%d 01 01" % year
        else:
            # advanced data : real first measurement time
            #             dt = datetime.fromtimestamp(t_start)
            #             start_time = time.strftime("%Y%m%d%H%M%S", dt.timetuple())
            #             print("\nstart_time :  ",start_time)
            #             start_day = time.strftime("%Y 01 01", dt.timetuple())
            start_time = time.strftime(
                "%Y%m%d%H%M%S", time.gmtime(numpy.round(t_start)))
            start_day = time.strftime("%Y 01 01", time.gmtime(t_start))

        return start_time, start_day

    def get_prod_time_tags(self):
        """
        @brief set the production time tags in use in output files
        @return (prod_time, prod_day) where prod_time the production time ("%Y%m%d%H%M%S") and
            prod_day if the production (ie revision) day (%Y %m %d)
        """
        prod_time = time.strftime("%Y%m%d%H%M%S", time.gmtime(time.time()))
        prod_day = "%s %s %s" % (prod_time[:4], prod_time[4:6], prod_time[6:8])
        return prod_time, prod_day

    def get_nlin_tpl(self, lvl=None):
        """
        @brief returns the number of lines of the actris template file
        """
        fpath_tpl = self.get_fpath_header_tpl(lvl)
        return get_nlines(fpath_tpl)

    def get_nlin_aux_comments(self, lvl=None):
        """
        @brief returns the number of lines of the auxiliary comments
        """
        return self.get_nlin_tpl(lvl) - 16  # 16 is the number of lines in tpl without vars

    def get_fpath_header_tpl(self, lvl=None):
        """
        @brief return the header template to use
        @param lvl output data level. If none, don't search a specific one
        @return the header as a string template
        """
        # - set the header template to use
        # if a destination product ID is not explicitly set,
        # it is considered that only one input is set for one output product
        if hasattr(self, "dst_prod_id"):
            tpl_prod_id = self.dst_prod_id
        else:
            tpl_prod_id = self.prod_id

        suffix = ".actris_header"
        # try it without level extension
        fheader = os.path.join(os.path.dirname(__file__), "..", "cfg", "actris_header",
                               tpl_prod_id + suffix)

        if not os.path.exists(fheader):
            # try a level specific one
            if lvl is not None:
                fheader += "_l%d" % lvl

        # - handle windows that does not support symlinks
        # - read it
        header = ""
        with io.open(fheader, newline='\n') as fd:
            header = fd.read()
        nlin = header.count('\n')
        if nlin == 0:
            fheader = os.path.join(os.path.dirname(fheader), header)

        return fheader

    def get_header_tpl(self, lvl=None):
        """
        @brief return the header template to use
        @param lvl output data level. If none, don't search a specific one
        @return the header as a string template
        """
        # - set the header template to use
        fheader = self.get_fpath_header_tpl(lvl)

        # - read it
        header = ""
        with io.open(fheader, newline='\n') as fd:
            header = fd.read()
        # # - handle windows that does not support symlinks
        # nlin = header.count('\n')
        # if nlin == 0:
        #     fheader = os.path.join(os.path.dirname(fheader), header)
        #     if os.path.exists(fheader):
        #         header = ""
        #         with io.open(fheader, newline='\n') as fd:
        #             header = fd.read()
        return header

    def get_header(self, t_start, lvl, v_start_acq, v_end_acq, year):
        """
        @brief constructs the header file
        @param lvl level of the product : 1 -> no time averaging ; 2 -> average all the year by day range
        @param v_start_acq start acquisition time vector
        @param year year for L2 synthesis
        @return the output file name and template header filled
        """
        start_time, start_day = self.get_acq_time_tags(t_start, lvl, year)

        d = datetime.strptime(start_day + " 00:00:00", "%Y %m %d 00:00:00")
        ts_day_start = (calendar.timegm(d.timetuple()))

        # - time resolution tags
        period_tag, dt_tag, dt, dt_raw_tag, dt_sampling_tag = self.get_time_tags(
            lvl, v_start_acq, v_end_acq, year)

        # - production time
        prod_time, rev_day = self.get_prod_time_tags()

        # - output filename
        fname = self.get_outfname(
            start_time, prod_time, lvl, v_start_acq, v_end_acq, year)
        fname_ext = "nas"

        # - number of variables
        nvars = self.get_nvars(lvl)

        # - scale factors
        scale_factors = ("1. " * nvars).strip()

        # - number of lines of the header
        nlines = self.get_nlin_tpl(lvl)
        header_size = nlines - 2 + nvars
        nlines_aux_com = self.get_nlin_aux_comments(lvl)

        # variables fill values
        vars_fill = self.get_vars_fill(lvl)

        # variable long names + tags
        vars_long_name, vars_tag = self.get_vars_desc(lvl)

        # set type code + dt value : TU time regulary spaced, TI : irregulary
        set_type_code = "TU"  # should always be
        if lvl not in [1.5, 2, "2b"]:
            # sometimes, time res can change are missing -> TI + dt not constant (so set to 0)
            # -> check constantness
            diff = numpy.diff(v_start_acq).round()
            if (diff.size > 0) and not numpy.all(diff == diff[0]):
                set_type_code = "TI"
                dt = 0

        # sometimes, time res can change are missing -> TI + dt not constant (so set to 0)
        # -> check constantness
        diff = numpy.diff(v_start_acq).round()

        # standard conditions of acquisition
        std_temp = self.acq_temp
        std_pres = self.acq_pres
        if lvl not in [0, "0b"]:
            std_temp = "%.2f" % Standardizer.T_STD
            std_pres = "%.2f" % Standardizer.P_STD

        # --- fill-in the header
        header = self._get_header(lvl, self.nrt, header_size=header_size, nlines_aux_com=nlines_aux_com,
                                  start_day=start_day, rev_day=rev_day, start_time=start_time, prod_time=prod_time, fname=fname, fname_ext=fname_ext,
                                  lab=self.lab, station=self.station, platform=self.platform, gaw_id=self.gaw_id, wdca_id=self.wdca_id, site=self.site,
                                  latitude=self.latitude, longitude=self.longitude, altitude=self.altitude,
                                  wmo_land_use=self.wmo_land_use, wmo_setting=self.wmo_setting, gaw_type=self.gaw_type, wmo_region=self.wmo_region,
                                  period_tag=period_tag, dt_tag=dt_tag, dt=dt, dt_raw_tag=dt_raw_tag, dt_sampling_tag=dt_sampling_tag, submitter=self.submitter,
                                  component=self.component, matrix=self.matrix, unit=self.unit,
                                  instrument=self.instrument, brand=self.brand, model=self.model, sn=self.sn,
                                  nvars=nvars, scale_factors=scale_factors, vars_fill=vars_fill,
                                  vars_long_name=vars_long_name, vars_tag=vars_tag,
                                  set_type_code=set_type_code, std_temp=std_temp, std_pres=std_pres,
                                  method_ref=self.method_ref, instr_name=self.instr_name,
                                  station_name=self.station_name, station_gaw_name=self.station_gaw_name)

        return fname, header, start_day, ts_day_start

    def _get_header(self, lvl=None, nrt=False, **kwargs):
        """
        @brief fill in the header template and return it as a string
        It replace all tags in template like "${tag}" or "$tag" by the corresponding
        value set in kwargs
        @param lvl requested data level
        @param kwargs dictionnary of substitution strings
        """
        sout = self.get_header_tpl(lvl)
        # add level to substitutions
        if lvl is not None:
            kwargs["lvl"] = str(lvl)

        if "instr_name" not in kwargs or kwargs["instr_name"] is None:
            # set a default instrument name
            instr_name = "{0:s}_{1:s}_{2:s}_ambient".format(
                str(kwargs["brand"]).replace(" ", "-"),
                str(kwargs["model"]).replace(" ", "-"),
                str(kwargs["gaw_id"]).replace(" ", "-"))
            kwargs["instr_name"] = instr_name

        if "method_ref" not in kwargs or kwargs["method_ref"] is None:
            # set a default method ref
            method_ref = "{0:s}_{1:s}_{2:s}_{3:s}_lev{4:s}".format(
                str(kwargs["lab"]).replace(" ", "-"),
                str(kwargs["instrument"]).replace(" ", "-"),
                str(kwargs["brand"]).replace(" ", "-"),
                str(kwargs["model"]).replace(" ", "-"),
                str(lvl))
            kwargs["method_ref"] = method_ref

        # process to substitutions
#         for k, v in kwargs.iteritems():
        for k, v in iter(list(kwargs.items())):
            sout = sout.replace("${" + k + "}", str(v))
            sout = sout.replace("$" + k + "", str(v))
#         print("\n sout : ", sout)
        return sout

    def check_infiles(self, infiles, check_fname_year=True, prod_id=None):
        """
        @brief validate the given input files
        It checks if they all match the good file pattern
        and if they are all of the same year than the first valid one.
        The files that do not match these critera are ignored and a message in printed
        @param infiles a list of input files (or a string)
        @param check_year_fname if set, check if the filename has the same timestamp than the synthesis year.
              Should be disabled if one daily file does not contain exactly one day of data for instance
        @param prod_id if None, use the default one, if set,n consider this custom one
        @return the list of valid input files
        """
        # make sure it is a list
        if isinstance(infiles, str):
            infiles = [infiles]

        # set the prod id to consider
        if prod_id is None:
            # use converter main product
            prod_id = self.prod_id

        # check pattern
        product_identifier = self.reader_interface.product_identifier
        v_out = []
        year = None
        for infile in iter(infiles):
            check_file(infile)
            f = os.path.basename(infile)
            m = product_identifier.get_match(f, prod_id)
            if m is None:
                print(
                    ("WARNING: file %s does not match product %s -> ignored" % (infile, prod_id)))
            elif check_fname_year is True:
                _year = int(m.group("year"))
                if year is None:
                    # first valid file -> set the synthesis year
                    year = _year
                if _year != year:
                    print(
                        ("WARNING: file %s is not of the same year %d than previous files -> ignored" % (infile, year)))
                else:
                    #  file is valid
                    v_out.append(infile)
            else:
                v_out.append(infile)
        return v_out

    def get_year_from_fname(self, infile):
        """
        @brief extract year from the given input file. Used for NRT l15 process
        @param infile a file path
        @return the year of the first acquisition of the first file
        """
        product_identifier = self.reader_interface.product_identifier
        m = product_identifier.get_match(
            os.path.basename(infile), self.prod_id)
        if m is None:
            raise ValueError(
                "WARNING: file %s does not match product %s -> ignored" % (infile, self.prod_id))
        return int(m.group("year"))

    def load_indata(self, infiles, var_ids, reader_interface=None, databuf=None, *args, **kwargs):
        """
        @brief load the requested datasets from the given input files, concatenates them file by file and return thme in a buffer dictionnary
        that uses variable IDs as keys and the read data as values
        @param infiles the list of files to read
        @param var_ids the list of variables to read
        @param reader_interface the reader to use. If none set, use the default one
        @param databuf the output databuffer. If none, a new one is created, if not, new data are append to it
        @param args other arguments to pass to the reader interface constructor
        @return a buffer dictionnary
        """
        # make sure infiles is a list
        if isinstance(infiles, str):
            infiles = [infiles]

        # if no databuf set, init a new one
        if databuf is None:
            databuf = {}  # multifile accumulator
        # if no custom reader_interface passed as argument, use the defaut one
        if reader_interface is None:
            reader_interface = self.reader_interface

        # sometimes, metadata need to be extracted from input files
        self.read_metadata(infiles)

        file_databuf = {}  # one file accumulator
        for infile in iter(infiles):
            #             print infile
            invalid_file = False
            file_databuf = {}
            try:
                # load variables of one file
                reader = reader_interface(
                    infile, self.prod_id, *args, **kwargs)
                for var_id in iter(var_ids):
                    data = reader.read_data(var_id)

#                     print var_id, data
                    file_databuf[var_id] = data
            except Exception as e:
                msg = "WARNING: Error while reading file " + \
                    infile + " : " + str(e) + " -> ignored"
                print(msg)
                invalid_file = True
#                 file_databuf = {}
#                 continue

            # accumulate multiple files data only if whole file is clean
            if not invalid_file:
                for var_id in iter(var_ids):
                    #                     print var_id
                    if var_id not in databuf:
                        databuf[var_id] = file_databuf[var_id]
                    else:
                        #                         print databuf[var_id].shape
                        # print file_databuf[var_id].shape
                        databuf[var_id] = numpy.concatenate(
                            (databuf[var_id], file_databuf[var_id]))

        return databuf

    def trim_end_acq(self, v_start_acq, v_end_acq):
        """
        @brief trims the end of acquisition time to the next acquisitio start if needed
    ometimes an end of acquisition time can be bigger than time of the next acq (mainly duer to rounding effects or time resolution setting change)
        @param v_start_acq acquisition start times, increasing order
        @param v_end_acq acquisition end times, increasing order
        @return the eventually corretced end_acq_time
        """
        # - delta that can be observed sometimes between 2 acquisitions in end_time
        v_dt = numpy.empty_like(v_start_acq)
        v_dt[:-1] = numpy.diff(v_start_acq)
        v_dt[-1] = v_dt[-2]  # hypothesis : same dt for 2 last records
        #  - change end acq time when start of next record is earlier
        is_end_acq_high = ((v_end_acq - v_start_acq) > v_dt)
        if numpy.any(is_end_acq_high):
            v_end_acq[is_end_acq_high] = v_start_acq[
                is_end_acq_high] + v_dt[is_end_acq_high]
        return v_end_acq

    def get_stats_mean(self, indata, s_infill, s_time):
        """
        @brief compute the mean of valid input values in a time subset
        @param indata native resolution input data
        @param s_infill mask of invalid input values
        @param s_time mask of input values that are in the time subset
        @return the mean of valid input values in the requested time range. None if none found
        """

        t = indata[s_time & ~s_infill & numpy.isfinite(indata)]
#         print("\n t : ", t)

        if t.size > 0:
            #             print("\n outdata : ", t.mean())
            return t.mean()
        return None

    def set_stats_mean(self, indata, s_infill, s_time, iout, outdata):
        """
        @brief compute the mean of valid input values in a time subset and fill the corresponding output record(s)
        @param indata native resolution input data
        @param s_infill mask of invalid input values
        @param s_time mask of input values that are in the time subset
        @param iout indice of the output record
        @param outdata output array of means
        @return the mean of valid input values in the requested time range. None if none found
        """

        mean = self.get_stats_mean(indata, s_infill, s_time)
        if mean is not None:
            outdata[iout] = mean

    def get_stats_min(self, indata, s_infill, s_time):
        """
        @brief compute the min of valid input values in a time subset
        @param indata native resolution input data
        @param s_infill mask of invalid input values
        @param s_time mask of input values that are in the time subset
        @return the min of valid input values in the requested time range. None if none found
        """
        t = indata[s_time & ~s_infill & numpy.isfinite(indata)]
        if t.size > 0:
            return t.min()
        return None

    def set_stats_min(self, indata, s_infill, s_time, iout, outdata):
        """
        @brief compute the min of valid input values in a time subset and fill the corresponding output record(s)
        @param indata native resolution input data
        @param s_infill mask of invalid input values
        @param s_time mask of input values that are in the time subset
        @param iout indice of the output record
        @param outdata output array of mins
        @return the min of valid input values in the requested time range. None if none found
        """
        vmin = self.get_stats_min(indata, s_infill, s_time)
        if vmin is not None:
            outdata[iout] = vmin

    def get_stats_max(self, indata, s_infill, s_time):
        """
        @brief compute the max of valid input values in a time subset
        @param indata native resolution input data
        @param s_infill mask of invalid input values
        @param s_time mask of input values that are in the time subset
        @return the max of valid input values in the requested time range. None if none found
        """
        t = indata[s_time & ~s_infill & numpy.isfinite(indata)]
        if t.size > 0:
            return t.max()
        return None

    def set_stats_max(self, indata, s_infill, s_time, iout, outdata):
        """
        @brief compute the max of valid input values in a time subset and fill the corresponding output record(s)
        @param indata native resolution input data
        @param s_infill mask of invalid input values
        @param s_time mask of input values that are in the time subset
        @param iout indice of the output record
        @param outdata output array of maxs
        @return the max of valid input values in the requested time range. None if none found
        """
        vmax = self.get_stats_max(indata, s_infill, s_time)
        if vmax is not None:
            outdata[iout] = vmax

    def get_stats_std(self, indata, s_infill, s_time):
        """
        @brief compute the standard deviation of valid input values in a time subset
        @param indata native resolution input data
        @param s_infill mask of invalid input values
        @param s_time mask of input values that are in the time subset
        @return the std of valid input values in the requested time range. None if none found
        """

        t = indata[s_time & ~s_infill & numpy.isfinite(indata)]
        if t.size > 0:
            return t.std()
        return None

    def set_stats_std(self, indata, s_infill, s_time, iout, outdata):
        """
        @brief compute the standard deviation of valid input values in a time subset and fill the corresponding output record(s)
        @param indata native resolution input data
        @param s_infill mask of invalid input values
        @param s_time mask of input values that are in the time subset
        @param iout indice of the output record
        @param outdata output array of stds
        @return the std of valid input values in the requested time range. None if none found
        """
        vstd = self.get_stats_std(indata, s_infill, s_time)
        if vstd is not None:
            outdata[iout] = vstd

    def get_stats_pc(self, indata, s_infill, s_time, invalidate_unique_val=False):
        """
        @brief compute the 15.87 and 84.13 percentiles of valid input values in a time subset
        @param indata native resolution input data
        @param s_infill mask of invalid input values
        @param s_time mask of input values that are in the time subset
        @param invalidate_unique_val if True, return a fill value if only value is in the time range
        @return the mean 15.87 and 84.13 percentiles of valid input values in the requested time range. (None, None) if none found
        """
        t = indata[s_time & ~s_infill & numpy.isfinite(indata)]
        if invalidate_unique_val and t.size == 1:
            return (None, None)
        if t.size > 0:
            return (percentile(t, 15.87), percentile(t, 84.13))
        return (None, None)

    def set_stats_pc(self, indata, s_infill, s_time, iout, outdata_pc16, outdata_pc84, invalidate_unique_val=False):
        """
        @brief compute the 15.87 and 84.13 percentiles of valid input values in a time subset and fill the corresponding output record(s)
        @param indata native resolution input data
        @param s_infill mask of invalid input values
        @param s_time mask of input values that are in the time subset
        @param iout indice of the output record
        @param outdata output array of means
        @param invalidate_unique_val if True, return a fill value if only value is in the time range
        @return the mean 15.87 and 84.13 percentiles of valid input values in the requested time range. (None, None) if none found
        """
        pc16, pc84 = self.get_stats_pc(
            indata, s_infill, s_time, invalidate_unique_val)
        if pc16 is not None:
            outdata_pc16[iout] = pc16
#         else:
#             outdata_pc16[iout] = numpy.nan
        if pc84 is not None:
            outdata_pc84[iout] = pc84
#         else:
#             outdata_pc16[iout] = numpy.nan

    def aggregate_flag_val(self, indata):
        """
        @brief aggregates L1 flag values into L2
        @param indata native resolution input flags list
        @param s_infill mask of invalid input values
        @param s_time mask of input values that are in the time subset
        """
#         if indata.size == 0:
#             # - no invalid in range
#             return self.QA_FLAGS_MISSING
        # select only meaningful flags in subset
        flag_vals = indata[numpy.isfinite(indata) & (indata != 0.) & (indata != self.QA_FLAGS_FILL)]
        if flag_vals.size == 0:
            # - all valid
            return self.QA_FLAGS_VALID

        # --- some relevant invalid found
        flag_vals = numpy.unique(flag_vals)
        flag_vals *= 1e3  # -> 0.XXX to XXX form
        # aggregates values
        agg_flag_val = 0
        for ival, val in enumerate(flag_vals):
            agg_flag_val += int(val) * 10 ** (3 * ival)

        # -> XXX to 0.XXX form
        ndigit = len(str(agg_flag_val))
        agg_flag_val = agg_flag_val * 10 ** (-(ndigit))
        return agg_flag_val

    def get_invalid(self, indata, var_ids=None):
        """
        @brief identify the invalid data values and return it in 2 dictionnary buffers : one with invalid, one with NaNs
        By default data are set as invalid if NaN or negative
        @param indata input data buffer
        @param var_ids list of variables to check. If None, all variables that have been loaded in indata will be checked
        @return 2 buffers : one with mask of invalids, one with mask of NaNs
        """
        #  - manually invalidated records
        invalid_acq = False
        if self.acq_err_logger is not None:
            invalid_acq = self.get_invalid_acq(
                indata[Product.START_ACQ_ID], indata[Product.END_ACQ_ID])

        # - automatic flags
        invalid_databuf = {}
        nan_databuf = {}
        if var_ids is None:
            var_ids = list(indata.keys())
        for var_id in iter(var_ids):
            data = indata[var_id]
            is_nan_data = numpy.isnan(data)
            nan_databuf[var_id] = is_nan_data
            invalid_databuf[var_id] = is_nan_data | (data < 0) | invalid_acq
        return invalid_databuf, nan_databuf

    def get_invalid_acq(self, v_start_acq, v_end_acq, end_time_included=False,
                        start_time_included=False):
        """
        @brief build the mask and the values of acquisition errors as set in the error logger file
        @param v_start_acq vector of acquisition starts, using UNIX UTC EPOCH time
        @param v_end_acq vector of acquisition ends, using UNIX UTC EPOCH time
        @param end_time_included if True, end time is considered as invalid too
        @return mask of invalidated records
        """
        if self.acq_err_logger is not None:
            return self.acq_err_logger.get_invalid_acq(v_start_acq, v_end_acq, end_time_included, start_time_included)
        else:
            #  all considered as valid
            return numpy.zeros(v_start_acq.shape, dtype=bool), numpy.empty(v_start_acq.shape, dtype=float) + numpy.nan

#     def get_invalid_acq_vals(self, v_start_acq, v_end_acq):
#         """
#         @brief build the values of acquisition errors flags as set in the error logger file
#         @param v_start_acq vector of acquisition starts, using UNIX UTC EPOCH time
#         @param v_end_acq vector of acquisition ends, using UNIX UTC EPOCH time
#         @return invalidated records flags values
#         """
#         if self.acq_err_logger is None:
#             raise ValueError("No Acquisition Error Logger set")
# return self.acq_err_logger.get_invalid_acq_vals(v_start_acq, v_end_acq)

    @staticmethod
    def get_time_vars(start_day, v_start_acq_out, v_end_acq_out):
        """
        @brief computes the output time axis variables in decimal days
        @param start_day time axis origin in format "YYYY MM DD". Most of the time, the 1st second of a year
        @param v_start_acq_out start of acquisition range, unix epoch time
        @param v_end_acq_out end of acquisition range, unix epoch time
        @return (v_ts_start, v_ts_end, v_start_year, v_end_year) where :
                - v_ts_start, v_ts_end are the start/end of acquisition in decimal days from ts_day_start;
                - v_start_year, v_end_year the matching years
        """
        # compute start time in decimal days for file reference time
        # start of day in seconds
        d = datetime.strptime(start_day + " 00:00:00", "%Y %m %d 00:00:00")
        ts_day_start = (calendar.timegm(d.timetuple()))

        # - compute start time in decimal days for file reference time
        # measure start
        v_ts_start = v_start_acq_out - ts_day_start  # sec from day start
        v_ts_start = v_ts_start / float(NSEC_DAY)  # to days

        # - compute end time in decimal days for file reference time
        # measure end
        v_ts_end = v_end_acq_out - ts_day_start  # sec from day end
        v_ts_end = v_ts_end / float(NSEC_DAY)  # to days

        # for start, end in zip(v_start_acq_out, v_end_acq_out):
        # print "start/end", time.gmtime(start), time.gmtime(end)

        # - compute start time in decimal days for file reference time
        # measure start
        v_ts_start = v_start_acq_out - ts_day_start  # sec from day start
        v_ts_start = v_ts_start / float(NSEC_DAY)  # to days
        # measure start year
        v_start_year = numpy.array(
            [time.gmtime(ts).tm_year for ts in v_start_acq_out], numpy.uint16)

        # - compute end time in decimal days for file reference time
        # measure end
        v_ts_end = v_end_acq_out - ts_day_start  # sec from day end
        v_ts_end = v_ts_end / float(NSEC_DAY)  # to days
        # measure end year
        v_end_year = numpy.array(
            [time.gmtime(ts).tm_year for ts in v_end_acq_out], numpy.uint16)

        # make sure to control floating point rouding artefacts :
        # after the 7th decimal, we are under the second precision
#         v_ts_start -= (v_ts_start % 1e-7)
#         v_ts_end -= (v_ts_end % 1e-7)

        return (v_ts_start, v_ts_end, v_start_year, v_end_year)

    def get_time_axis_bounds(self, v_start_acq_in, v_end_acq_in, year, dt=3600):
        """
        @brief return the start_times/end_times limits for the given year with a time difference of @a dt
        Leap years are treated
        @param v_start_acq_in start of acquisition times, native time resolution
        @param v_end_acq_in end of acquisition times, native time resolution
        @param year the year
        @param dt time lap in seconds. 3600s (1 hour) by default
        @return (v_start_time, v_end_time) in UNIX EPOCH time
        """
        # - set output time axis of level 2 and 1.5 products

        # - number of days between start and end of acquisition
        dt_start_acq = datetime.utcfromtimestamp(v_start_acq_in[0])
        dt_end_acq = datetime.utcfromtimestamp(v_end_acq_in[-1])

        d_start = datetime(dt_start_acq.year,
                           dt_start_acq.month, dt_start_acq.day, 0, 0, 0)
        d_end = datetime(dt_end_acq.year, dt_end_acq.month,
                         dt_end_acq.day, 0, 0, 0)
        ndays = (d_end - d_start).days

        # d_start = datetime(year, 1, 1, 0, 0, 0)
        ts_start = calendar.timegm(d_start.timetuple())
        v_start_time = numpy.arange(
            ts_start, ts_start + (ndays * NSEC_DAY), dt)

        # - end time of averaging range
        v_end_time = v_start_time + dt
        return (v_start_time, v_end_time)

    def check_set_type_code(self, lvl, v_start_acq, dt=None):
        """
        @brief identify the set type code and the diffence of time between 2 records
        set type code : TU -> time regulary spaced, TI -> irregulary
        dt : time between 2 recors in decimal day unit if regulary spaced, 0 if irregulary
        @param lvl level of product
        @param v_start_acq record time vector, unix epoch time
        @param dt presupposed dt. If None, try to guess it
        @return (set_type_code, dt)
        """
        # set type code + dt value : TU time regulary spaced, TI : irregulary
        set_type_code = "TU"  # should always be
        if lvl < 2:
            # sometimes, records are missing -> TI + dt not constant (so set to 0)
            # -> check constantness
            diff = numpy.diff(v_start_acq)
            if (diff.size == 0):
                raise ValueError(
                    "ERROR : Only one record in file. Can't determine dt between 2 records")
            if not numpy.all(diff == diff[0]):
                set_type_code = "TI"
                dt = 0
            elif dt is None:
                # guess dt
                dt = diff[0] / float(86400)
        else:
            # lvl 2
            dt = 0.041667  # 1h in decimal day unit
        return (set_type_code, dt)

    # def get_fill(self, var_id):
        # """
        # @brief return the fill value to use for the given variable
        # @param var_id a variable ID
        # @return the fill value
        # """
        # if var_id == self.QA_FLAGS_ID:
        # return 9.999
        # else:
        # return self.DEFAULT_FILL

    def normalize_time_range(self, start_acq, end_acq):
        """
        @brief make sure there is no overlap between records time range, mostly because of rounding effects
        @param start_acq start of acquisition time vector
        @param end_acq start of acquisition time vector
        @return the (eventually) corrected acquisition range vectors
        """
        diff_acq_range = end_acq - start_acq
        diff_start_acq = numpy.diff(start_acq)

        # if end of acquisition time higher than next record start time detected, set end time
        # to next record start time
        s_end_acq_too_high = diff_acq_range[:-1] > diff_start_acq
        if numpy.any(s_end_acq_too_high):
            end_acq[:-1][s_end_acq_too_high] = start_acq[:-1][s_end_acq_too_high] + diff_start_acq[s_end_acq_too_high]
        return start_acq, end_acq

    def process(self, infiles, outdir, year=None):
        """
        @brief convert a list of files
        @param infiles the files to convert
        @param outdir output directory
        @param year year of the eventual yearly synthesis
        """
        outdir = os.path.abspath(outdir)

        # validate input files
        infiles = self.check_infiles(infiles)

        # level 2
        for lvl in [0, 1, 2]:
            #         for lvl in [2]:
            start_time = time.time()
            if __DEBUG__:
                print(("*" * 20 + " LEVEL %d " % lvl + "*" * 20))
            try:
                self.process_lvl(infiles, outdir, lvl, year)
            except Exception as e:
                if __DEBUG__:
                    msg = " > " + str(e) + " : " + os.linesep + "ABORT"
                    print(msg)
                if __THROW__:
                    raise
            if __DEBUG__:
                print(("*" * 20 + " LEVEL %d" % lvl + " : " + time.strftime("%H:%M:%S ",
                                                                            time.gmtime(time.time() - start_time)) + "*" * 20))


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

    parser.add_option("-y", "--year",
                      action="store", default=None, type="int", dest="year",
                      help="Year of the eventual Level 2 synthesis (Default : Disabled)")
    parser.add_option("-p", "--period",
                      action="store", default=None, type="int", dest="period",
                      help="Period in case of configuration change over the year (Default : Disabled)")
    parser.add_option("-n", "--nrt", action="store_true", default=False, dest="nrt",
                      help="Generate products for NRT submissions instead of regular annual submissions")
    parser.add_option("-e", "--err-log", default=None, dest="err_log", type="str",
                      help="path to the yearly flag file")

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
    infiles = _infiles

    if check_infiles:
        for infile in iter(infiles):
            check_file(infile)
    outdir = args[-1]
    check_dir(outdir)

    return infiles, outdir, options
