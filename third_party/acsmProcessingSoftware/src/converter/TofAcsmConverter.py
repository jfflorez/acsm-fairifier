# -*- coding: utf-8 -*-

"""
Description :
-------------
    Quad ACSM data converter

Usage :
-------
    Usage: python3 TofAcsmConverter.py [options]  <fname> <outdir>

    with :
        <fname>  full pathes to the files to convert
        <outdir> output directory where will be wrote the ACTRIS files

    Options:
      -h, --help            show this help message and exit
      -y YEAR, --year=YEAR  Year of the eventual Level 2 synthesis (Default :
                            Disabled)

Example :
---------


for y in {2015..2016}
do
    mkdir -p ~/test/GIF_ACSM_ACTRIS/${y}
    python3 ~/depot/ground_data_manager/src/converter/GifAcsmConverter.py ~/depot/ground_data_manager/data/PUY/ACSM/PUY_ACSM_RAW_${y}_V1-01.csv ~/test/PUY_ACSM_ACTRIS/${y} -y ${y}
done


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
    v0.0.0 : 2021/03/01
    - creation
"""
import io
import os.path
import sys
import time
import numpy

pkgdir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkgdir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))


from product.Product import Product
from product.AcsmRawProduct import AcsmRawProduct

import converter.Converter as Converter

# import misc.UnitsConverter as UnitsConverter

__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]
__DEBUG__ = False
__THROW__ = True
__SHOW_BAD_INPUTS__ = False
__SHOW_OUTPUTS__ = False


class TofAcsmConverter(Converter.Converter):
    """
    Puy ECOC data converter
    """
    model = "ToF-ACSM"

    # variable IDs by categories
    # var IDs that differs from Quad
    #IE_NO3_ID = "IENO3"

    # - concentrations
    var_ids_conc = [
        AcsmRawProduct.OM_ID,
        AcsmRawProduct.NO3_ID,
        AcsmRawProduct.SO4_ID,
        AcsmRawProduct.NH4_ID,
        AcsmRawProduct.CL_ID,
    ]

    # - concentrations uncertainties
    var_ids_conc_err = [var_id + "_err" for var_id in var_ids_conc]

    # - ionization efficiencies
    var_ids_ie = [
        AcsmRawProduct.IE_NO3_ID,
        AcsmRawProduct.RIE_OM_ID,
        AcsmRawProduct.RIE_NO3_ID,
        AcsmRawProduct.RIE_SO4_ID,
        AcsmRawProduct.RIE_NH4_ID,
        AcsmRawProduct.RIE_CL_ID,
    ]

    # - environment variables
    var_ids_env = [
        AcsmRawProduct.TOF_INLETP_ID,
        AcsmRawProduct.T_IN_ID,
        # AcsmRawProduct.T_OUT_ID,
        AcsmRawProduct.RH_IN_ID,
        # AcsmRawProduct.RH_OUT_ID,
    ]

    # - ancillary variables
    var_ids_anc = [
        AcsmRawProduct.SAMPLING_FLOWRATE_ID,
    ]

    # - tof specific variables
    # var_ids_tof = [
    # AcsmRawProduct.TOF_ABREF_ID,
    # AcsmRawProduct.TOF_AB_TOTAL_ID,
    # AcsmRawProduct.TOF_FLOW_CSS_ID,
    # AcsmRawProduct.TOF_N_TOTAL_ID,
    # AcsmRawProduct.TOF_N_BKGD_ID,
    # AcsmRawProduct.TOF_BASELINE_ID,
    # AcsmRawProduct.TOF_THRESHOLD_ID,
    # AcsmRawProduct.TOF_MZCAL_P1_ID,
    # AcsmRawProduct.TOF_MZCAL_P2_ID,
    # AcsmRawProduct.TOF_RATIO40DIV28_ID,
    # AcsmRawProduct.TOF_LENS_ID,
    # AcsmRawProduct.TOF_PULSER_ID,
    # AcsmRawProduct.TOF_LENS2_ID,
    # AcsmRawProduct.TOF_IONEX_ID,
    # AcsmRawProduct.TOF_LENS1_ID,
    # AcsmRawProduct.TOF_HB_ID,
    # AcsmRawProduct.TOF_IONCHAMBER_ID,
    # AcsmRawProduct.TOF_FILAMENT_EMM_ID,
    # AcsmRawProduct.TOF_TURBO_SPEED_ID,
    # AcsmRawProduct.TOF_TURBO_POWER_ID,
    # AcsmRawProduct.TOF_FORE_PC_ID,
    # AcsmRawProduct.TOF_PRESS_INLET_ID,
    # AcsmRawProduct.TOF_HEATER_PWM_ID,
    # AcsmRawProduct.TOF_HEATER_I_ID,
    # AcsmRawProduct.TOF_HEATER_V_ID,
    # AcsmRawProduct.TOF_HEATER_T_ID,
    # ]

    # flag of variables
    var_ids_flag = [
        var_id + "_flag" for var_id in var_ids_conc + var_ids_ie + var_ids_env]

    # ALL LOD FIXED To default Value (source Jean-Eudes IPSL)
    lod_ids_conc = {}  # Jean-Eude default Value
    lod_ids_conc[AcsmRawProduct.NO3_ID] = 0.12
    lod_ids_conc[AcsmRawProduct.SO4_ID] = 0.28
    lod_ids_conc[AcsmRawProduct.NH4_ID] = 0.51
    lod_ids_conc[AcsmRawProduct.CL_ID] = 0.1
    lod_ids_conc[AcsmRawProduct.OM_ID] = 0.1

    # input fill values
    in_var_fills_conc = 999.999
    in_var_fills_env = 99.999  # T, RH

    def __init__(self, prod_id=None, interface=AcsmRawProduct, acq_err_log=None):
        """
        @brief constructor
        """
        Converter.Converter.__init__(
            self, prod_id, interface, acq_err_log=acq_err_log)

    def process(self, infiles, outdir, year=None, nrt=False):
        """
        @brief convert a list of files
        @param infiles the files to convert
        @param outdir output directory
        @param year year of the eventual yearly synthesis
        @param nrt generate NRT l15 products instead of annual regular submissions
        """
        outdir = os.path.abspath(outdir)

        # validate input files
        infiles = self.check_infiles(infiles)

        # identify levels and nrt status
        self.nrt = nrt
        if self.nrt is True:
            # self.levels = ["0b", "1b", "2b"]
            self.levels = [0]
            year = self.get_year_from_fname(infiles[0])
        else:
            self.levels = [0]

        for lvl in self.levels:
            start_time = time.time()
            if __DEBUG__:
                print("*" * 20 + " LEVEL %s " % str(lvl) + "*" * 20)
            try:
                self.process_lvl(infiles, outdir, lvl, year)
            except Exception as e:
                if __DEBUG__:
                    msg = " > " + str(e) + " : " + "\n" + "ABORT"
                    print(msg)
                if __THROW__:
                    raise
            if __DEBUG__:
                print("*" * 20 + " LEVEL %s" % str(lvl) + " : " + time.strftime("%H:%M:%S ",
                                                                                time.gmtime(time.time() - start_time)) + "*" * 20)

    def get_vars_desc(self, lvl):
        """
        @brief constructs the variables long names and column names
        @param lvl level
        @return (vars_long_name, vars_tags)
        """
        vars_long_name = ""

        if lvl in [0, "0b"]:
            var_ids_added = ["pressure", "temperature", "relative_humidity", ]

            var_ids_added_metaInfo = [", Location=instrument inlet", ", Location=chamber", ", Location=before dryer", ]

            var_ids_unit = ["Torr", "deg C", "%", ]
            for i in range(len(var_ids_added)):
                var_id = var_ids_added[i]
                unit = var_ids_unit[i]
                metaInfo = var_ids_added_metaInfo[i]
                vars_long_name += "{0:s}, {1:s}, Matrix=instrument{2:s}".format(
                    var_id, unit, metaInfo) + "\n"
                vars_long_name += "numflag " + var_id + \
                    ", no unit, Matrix=instrument" + metaInfo + "\n"

        var_ids = ["organic_mass", "nitrate", "sulphate_total", "ammonium", "chloride"]
        units = ["ug/m3", "ug/m3", "ug/m3", "ug/m3", "ug/m3"]

        # LOD giving by Jean Eudes Maximilien MODIFICATION
        lod_desc = ["0.1", "0.12", "0.28", "0.51", "0.1"]
        units_and_lod = zip(units, lod_desc)
        for var_id, unit_lod in zip(var_ids, units_and_lod):
            unit = unit_lod[0]
            lod = unit_lod[1]
            vars_long_name += "{0:s}, {1:s}, Detection limit={2:s} {1:s}".format(
                var_id, unit, lod) + "\n"
            vars_long_name += "{0:s}, {1:s}, Statistics=uncertainty".format(
                var_id, unit) + "\n"
            vars_long_name += "numflag {0:s}, no unit".format(
                var_id) + "\n"

        vars_long_name += "ionization_efficiency, A/ug/m3, Reference component=nitrate" + "\n"
        vars_long_name += "numflag ionization_efficiency, no unit, Reference component=nitrate" + "\n"

        ref_componentRIE = ['organic_mass', 'nitrate',
                            "sulphate_total", "ammonium", "chloride"]
        for var_rie in ref_componentRIE:
            vars_long_name += "{0:s}, {1:s}, Reference component={2:s}".format(
                "relative_ionization_efficiency", "no unit", var_rie) + "\n"
            vars_long_name += "numflag " + "{0:s}, {1:s}, Reference component={2:s}".format(
                "relative_ionization_efficiency", "no unit", var_rie) + "\n"

        vars_long_name = vars_long_name.strip()

        # tags
        vars_tag = ""
        var_ids = ["inletP", "numflag_inletP",
                   # "InletPopen", "numflag_InletPopen",
                   # "InletPclosed", "numflag_InletPclosed",
                   # "ChamberT", "numflag_ChamberT",
                   "T_in", "numflag_T_in",
                   # "T_Out", "numflag_T_Out",
                   # "RH_in", "numflag_RH_in",
                   "RH_out", "numflag_RH_out",
                   # "VapT", "numflag_VapT",
                   # "VapV", "numflag_VapV",
                   # "Airbeam", "numflag_Airbeam",
                   # "SEM_voltage", "numflag_SEM_voltage",
                   # "HeaterBias", "numflag_HeaterBias",
                   # "EmCurrent", "numflag_EmCurrent",
                   # "Sampling_Flowrate", "numflag_Sampling_Flowrate",
                   # "TP1_S", "numflag_TP1_S",
                   # "TP1_W", "numflag_TP1_W",
                   # "TP1_T", "numflag_TP1_T",
                   # "TP2_S", "numflag_TP2_S",
                   # "TP2_W", "numflag_TP2_W",
                   # "TP2_T", "numflag_TP2_T",
                   # "TP3_S", "numflag_TP3_S",
                   # "TP3_W", "numflag_TP3_W",
                   # "TP3_T", "numflag_TP3_T",
                   # "newStartEvents", "numflag_newStartEvents",
                   "Org", "err_Org", "numflag_Org",
                   "NO3", "err_NO3", "numflag_NO3",
                   # "NO3_30", "err_NO3_30", "numflag_NO3_30",
                   # "NO3_46", "err_NO3_46", "numflag_NO3_46",
                   "SO4", "err_SO4", "numflag_SO4",
                   "NH4", "err_NH4", "numflag_NH4",
                   "Chl", "err_Chl", "numflag_Chl",
                   # "Org_44", "err_Org_44", "numflag_Org_44",
                   # "Org_43", "err_Org_43", "numflag_Org_43",
                   # "Org_60", "err_Org_60", "numflag_Org_60",
                   "IE_NO3", "numflag_IE_NO3",
                   "RIE_OM", "numflag_RIE_OM",
                   "RIE_NO3", "numflag_RIE_NO3",
                   "RIE_SO4", "numflag_RIE_SO4",
                   "RIE_NH4", "numflag_RIE_NH4",
                   "RIE_Chl", "numflag_RIE_Chl",
                   ]

        for var_id in var_ids:
            vars_tag += "{0:<28s}".format(var_id)

        vars_tag = vars_tag.strip()

        return (vars_long_name, vars_tag)

    def get_fill(self, var_id):
        """
        @brief return the fill value to use for the given variable
        @param var_id a variable ID
        @return the fill value
        """
        # if var_id in [AcsmRawProduct.IE_NO3_ID, AcsmRawProduct.AIRBEAM_ID]:
        # very small values, dedicated fill values
        # return self.var_fill_airbeam_ie
        if var_id == self.QA_FLAGS_ID or var_id in self.var_ids_flag : #var_id.endswith("_flag"):
            return self.var_fills_qa
        elif var_id in self.var_ids_env + [AcsmRawProduct.SAMPLING_FLOWRATE_ID, ]:
            return self.var_fills_env_tof
        else:
            return self.var_fills_conc

    def get_vars_fill(self, lvl):
        """
        @brief constructs the list of variable fill values separated by spaces
        @param lvl level of the product : 1 -> no time averaging ; 2 -> average all the year by day range
        @return the list of variable fill values as a string
        """
        s = "9999.999999 "  # end time
        # fill values concentration + flag except for newtartEvents and err_conc
        for var_id in self.var_ids_env:
            fill = self.get_fill(var_id)
            s += "{0:.3f} {1:s} ".format(fill, "9.999")
            # if var_id in [AcsmRawProduct.AIRBEAM_ID]:
            # s += "{0:.4E} {1:s} ".format(fill, "9.999")
            # else:
            # s += "{0:.4f} {1:s} ".format(fill, "9.999")
        # Org, NO3, NO3_30, NO3_46, SO4, NH4, Chl, Org_44, Org_43, Org_60 :
        # conc, err_conc, flag
        fill = self.get_fill(self.var_ids_conc[0])
        s += ("{0:.4f} {1:.4f} {2:s} ".format(fill, fill, "9.999")) * len(self.var_ids_conc)
        # IE/RIE : conc, flag
        for var_id in self.var_ids_ie:
            fill = self.get_fill(var_id)
            if var_id in [AcsmRawProduct.IE_NO3_ID]:
                s += "{0:.4E} {1:s} ".format(fill, "9.999")
            else:
                s += "{0:.4f} {1:s} ".format(fill, "9.999")
        return s.strip()

    def get_nvars(self, lvl):
        """
        @brief return the number of output variables
        @param lvl level of the product : 1 -> no time averaging ; 2 -> average all the year by day range
        @return the the number of output variables
        """
        nvars = 1  # end time
        nvars += (len(self.var_ids_env) * 2)  # val + flags
        # nvars += (len(self.var_ids_ForValidity) * 2)  # val + flags
        nvars += (len(self.var_ids_conc) * 3)  # conc + err + flags
        nvars += (len(self.var_ids_ie)) * 2  # val + flags
        return nvars

    def process_lvl(self, infiles, outdir, lvl, year=None):
        """
        @brief construct the ACTRIS data file of the given target product and save it to the output directory
        @param outdir output directory
        @param lvl level of the product : 1 -> no time averaging ; 2 -> average all the year by day range
        @param isheet one wavelength is set per sheet. Treat them separatly in 2 different output files
        @param year year for L2 synthesis
        """
        if isinstance(infiles, str):
            infiles = [infiles]

        if lvl == 2 and year is None:
            raise ValueError("year not specified")

        # --- load input data
        if __DEBUG__:
            print("--- Load inputs ---")

        invar_ids = [Product.START_ACQ_ID, Product.END_ACQ_ID] + \
            self.var_ids_conc + self.var_ids_conc_err + self.var_ids_ie + self.var_ids_env + self.var_ids_anc  # + self.var_ids_tof

        indata = self.load_indata(infiles, invar_ids)

        # - sometimes, concentration or other variables can be NaN in raw data -> set to fill
        for var_id in self.var_ids_conc + self.var_ids_conc_err:
            data = indata[var_id]
            is_fill = (data == self.in_var_fills_conc) | numpy.isnan(data)
            indata[var_id][is_fill] = self.get_fill(var_id)

        for var_id in self.var_ids_env + [AcsmRawProduct.SAMPLING_FLOWRATE_ID, ]:
            data = indata[var_id]
            is_fill = (data == self.in_var_fills_env) | numpy.isnan(data)
            indata[var_id][is_fill] = self.get_fill(var_id)

        # --- eventual normalizations
        # - trim end acq time, when not well rounded
        indata[Product.END_ACQ_ID] = self.trim_end_acq(
            indata[Product.START_ACQ_ID], indata[Product.END_ACQ_ID])

        # ---- eventual unit conversions

        # - acquisition time
        v_start_acq_in = indata[Product.START_ACQ_ID]
        v_end_acq_in = indata[Product.END_ACQ_ID]
        t_start = v_start_acq_in.min()

        # --- fill-in the header
        fname, sout, start_day = self.get_header(
            t_start, lvl, v_start_acq_in, v_end_acq_in, year)[:3]

        # --- compute output vars,
        if __DEBUG__:
            print("--- Computing ---")

        # --- set output data buffer
        shape = indata[Product.START_ACQ_ID].shape
        outdata = indata

        # --- init qa buffers
        for var_id in invar_ids:
            var_id_qa = var_id + "_flag"
            outdata[var_id_qa] = numpy.zeros(shape, dtype=numpy.float64)

        # --- eventually handle manual QA for concentrations
        if self.acq_err_logger is not None:
            for var_id in self.var_ids_conc:
                var_id_log = None
                if var_id in [AcsmRawProduct.OM_ID,
                              ]:
                    var_id_log = self.acq_err_logger.OM_QA_FLAG_ID
                elif var_id in [AcsmRawProduct.NO3_ID,
                                ]:
                    var_id_log = self.acq_err_logger.NO3_QA_FLAG_ID
                elif var_id in [AcsmRawProduct.SO4_ID]:
                    var_id_log = self.acq_err_logger.SO4_QA_FLAG_ID
                elif var_id in [AcsmRawProduct.NH4_ID]:
                    var_id_log = self.acq_err_logger.NH4_QA_FLAG_ID
                elif var_id in [AcsmRawProduct.CL_ID]:
                    var_id_log = self.acq_err_logger.CL_QA_FLAG_ID
                else:
                    raise ValueError("Unsupported var ID " + str(var_id))
                data_qa = numpy.cast[numpy.float64](self.acq_err_logger.read_data(var_id_log))
                data_qa[data_qa != 0] /= 1000.
                outdata[var_id + "_flag"] = data_qa

        # --- identify missing data cases
        for var_id in self.var_ids_env + [AcsmRawProduct.SAMPLING_FLOWRATE_ID, ]:
            data = indata[var_id]
            is_fill = (data == self.get_fill(var_id))
            var_id_qa = var_id + "_flag"
            outdata[var_id_qa][is_fill] = self.get_fill(var_id_qa)

        for var_id in self.var_ids_conc:
            data = indata[var_id]
            is_fill = (data == self.get_fill(var_id))
            var_id_qa = var_id + "_flag"
            outdata[var_id_qa][is_fill] = self.get_fill(var_id_qa)

        # --- write data to output
        if __DEBUG__:
            print("--- Write outputs ---")

        # --- write data to output
        v_start_acq_out = outdata[Product.START_ACQ_ID]
        v_end_acq_out = outdata[Product.END_ACQ_ID]
        v_ts_start, v_ts_end = self.get_time_vars(
            start_day, v_start_acq_out, v_end_acq_out)[:2]
        sz = v_start_acq_out.size
        for i in range(sz):
            # - time vars
            lin = "{0:<15.6f}{1:<15.6f}".format(
                v_ts_start[i], v_ts_end[i])

            for var_id in self.var_ids_env:
                # if var_id in [AcsmRawProduct.AIRBEAM_ID, ]:
                # lin += "{0:<28.4E}".format(outdata[var_id][i])
                # else:
                lin += "{0:<28.3f}".format(outdata[var_id][i])
                lin += "{0:<28.3f}".format(outdata[var_id + "_flag"][i])

            for var_id in self.var_ids_conc:
                lin += "{0:<28.4f}".format(outdata[var_id][i])
                lin += "{0:<28.4f}".format(outdata[var_id + "_err"][i])
                lin += "{0:<28.3f}".format(outdata[var_id + "_flag"][i])

            for var_id in self.var_ids_ie:
                if var_id in [AcsmRawProduct.IE_NO3_ID, ]:
                    lin += "{0:<28.4E}".format(outdata[var_id][i])
                else:
                    lin += "{0:<28.4f}".format(outdata[var_id][i])
                lin += "{0:<28.3f}".format(outdata[var_id + "_flag"][i])

            sout += lin.strip() + "\n"

        # write out data
        outfname = os.path.join(outdir, fname)
        f = io.open(outfname, "w", newline='\n')
        try:
            f.writelines(sout)
            if __DEBUG__:
                print("ACTRIS file %s wrote" % outfname)
        finally:
            f.close()
        if __SHOW_OUTPUTS__:
            os.system("kate %s &" % outfname)
        return sout


def main():
    infiles, outdir, options = Converter.get_args(__APP__)
    prod_id = Converter.Converter.product_identifier.get_prod_id(infiles[0])

    prog = TofAcsmConverter(prod_id, AcsmRawProduct, acq_err_log=options.err_log)
    prog.process(infiles[0], outdir, nrt=options.nrt, year=options.year)


# def test_nrt():
    # """
    # Unit test, NRT process
    # """
    # import glob
    # infiles = glob.glob(
    # "/DATA/LIENS/GROUND-BASED/COPDD_Palaiseau/ACSM/ACSM_RAW-NRT/2021/2021_01_01/*.txt")
    # infiles.sort()
    # outdir = os.path.expanduser("~") + "/test/PUY_ACSM_ACTRIS"

    # prod_id = "PUY_ACSM_0018_RAW_NRT"

    # prog = TofAcsmConverter(prod_id, AcsmRawProduct, acq_err_log=None)
    # prog.process(infiles, outdir, nrt=True)


def test_regular():
    """
    Unit test, regular yearly synthesis
    """
    prod_id = "PUY_ACSM_0018_RAW_NRT"
    year = 2021

    indir = os.path.join(pkgdir, "..", "..", "tests", "COPDD", "in")
    acq_err_log = os.path.join(indir, "PuydeDome_ACSM-0018_FLAGS_2021.txt")

    infiles = [os.path.join(indir, "PuydeDome_ACSM-0018_2021.txt")]
    outdir = os.path.expanduser("~") + "/test"

    prog = TofAcsmConverter(prod_id, AcsmRawProduct, acq_err_log=acq_err_log)
    prog.process(infiles, outdir, year=year)


if __name__ == "__main__":
    # test_nrt()
    # test_regular()
    main()
