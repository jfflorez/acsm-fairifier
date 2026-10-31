# -*- coding: utf-8 -*-

"""
Description :
-------------
    EBAS Quad ACSM converter - level 0 to 0b
    Add automatic quality flags

Usage :
-------
    Usage: python3 QuadAcsmConverter.py [options]  <fname> <outdir>

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
    AERIS/ICARE Maximilien Patou, maximilien-dot-patou-at-univ-hyphen-lille-dot-fr
    CEA/LSCE Jean-Eudes Petit, jean-hyphen-eudes-dot-petit-at-lsce-dot-ipsl-dot-fr

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

import numpy
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
__SHOW_OUTPUTS__ = False


class EbasQuadAcsmConverter0to0b(EbasQuadAcsmConverter.EbasQuadAcsmConverter):
    """
    data converter
    """

    # --- used input vars (column names)
    # - acq conditions
    INLETP_ID = "inletP"
    INLETPOPEN_ID = "InletPopen"
    INLETPCLOSED_ID = "InletPclosed"
    CHAMBERT_ID = "ChamberT"
    T_IN_ID = "T_in"
    T_OUT_ID = "T_OutC"
    RH_IN_ID = "RH_in"
    RH_OUT_ID = "RH_out"
    VAPT_ID = "VapT"
    VAPV_ID = "VapV"
    AIRBEAM_ID = "Airbeam"
    SEMVOL_ID = "SEM_voltage"
    HEATERBIAS_ID = "HeaterBias"
    EMCURRENT_ID = "EmCurrent"
    SAMPLING_FLOWRATE_ID = "Sampling_Flowrate"
    TP1_S_ID = "TP1_S"
    TP1_W_ID = "TP1_W"
    TP1_T_ID = "TP1_T"
    TP2_S_ID = "TP2_S"
    TP2_W_ID = "TP2_W"
    TP2_T_ID = "TP2_T"
    TP3_S_ID = "TP3_S"
    TP3_W_ID = "TP3_W"
    TP3_T_ID = "TP3_T"
    NEWSTART_EVENTS_ID = "newStartEvents"
    # - concentrations
    OM_ID = "Org"
    OM_ERR_ID = "err_Org"
    NO3_ID = "NO3"
    NO3_ERR_ID = "err_NO3"
    NO3_F30_ID = "NO3_30"
    NO3_F30_ERR_ID = "err_NO3_30"
    NO3_F46_ID = "NO3_46"
    NO3_F46_ERR_ID = "err_NO3_46"
    SO4_ID = "SO4"
    SO4_ERR_ID = "err_SO4"
    NH4_ID = "NH4"
    NH4_ERR_ID = "err_NH4"
    CL_ID = "Chl"
    CL_ERR_ID = "err_Chl"
    OM_F44_ID = "Org_44"
    OM_F43_ID = "Org_43"
    OM_F60_ID = "Org_60"
    OM_F44_ERR_ID = "err_Org_44"
    OM_F43_ERR_ID = "err_Org_43"
    OM_F60_ERR_ID = "err_Org_60"

    # - onization_efficiency
    IE_NO3_ID = "IE_NO3"
    RIE_OM_ID = "RIE_OM"
    RIE_NO3_ID = "RIE_NO3"
    RIE_SO4_ID = "RIE_SO4"
    RIE_NH4_ID = "RIE_NH4"
    RIE_CL_ID = "RIE_Chl"

    # - groups of param of same kind
    var_ids_conc = [
        OM_ID,
        NO3_ID,
        SO4_ID,
        NH4_ID,
        CL_ID,
        OM_F44_ID,
        OM_F43_ID,
        OM_F60_ID,
    ]

    # - all LOD fixed To default Value (source Jean-Eudes IPSL)
    lod_ids_conc = {}  # Jean-Eude default Value
    lod_ids_conc[NO3_ID] = 0.12
    lod_ids_conc[NO3_F30_ID] = 0.1
    lod_ids_conc[NO3_F46_ID] = 0.1
    lod_ids_conc[SO4_ID] = 0.28
    lod_ids_conc[NH4_ID] = 0.51
    lod_ids_conc[CL_ID] = 0.1
    lod_ids_conc[OM_ID] = 0.1
    lod_ids_conc[OM_F44_ID] = 0.1
    lod_ids_conc[OM_F43_ID] = 0.1
    lod_ids_conc[OM_F60_ID] = 0.1

    #  output level
    # olvl = "0b"

    def __init__(self, fpath=None, inspected=None):
        """
        @brief constructor
        @param fpath input file path
        @param inspected manually inspected if True
        """
        EbasQuadAcsmConverter.EbasQuadAcsmConverter.__init__(
            self, fpath, inspected)
        # output level
        if self.inspected:
            self.olvl = "0a"
        else:
            self.olvl = "0b"

    def convert(self):
        """
        @brief level conversion, add flags
        """
        self.set_invalid()

    def set_invalid(self):
        """
        @brief identify the invalid data values and return it in 2 dictionary buffers : one with invalid, one with NaNs
        @param indata input data buffer
        @return 3 buffers : one with mask of invalids, one with mask of NaNs, one with the manually invalidated values
        """
        start_acq = self.writer.start_acq
        end_acq = self.writer.end_acq
        indata = self.writer.data

        # - manually invalidated records
        # print (indata)
        invalid_acq, invalid_acq_val = self.get_invalid_acq(
            start_acq, end_acq)
        is_invalid_acq = numpy.isfinite(invalid_acq_val)

        # --- invalid acquisition conditions
        # - air beam : invalid if >= .6*10**-6
        air_beam = indata[self.AIRBEAM_ID]
        is_missing_airbeam = (air_beam == self.var_fills_airbeam_ie)
        is_zero_airbeam = (air_beam == 0)
        if numpy.all(is_zero_airbeam | is_missing_airbeam):
            # always null, not recorded
            is_invalid_airbeam = numpy.zeros_like(is_invalid_acq)
        else:
            is_invalid_airbeam = (~is_missing_airbeam) & (air_beam < (0.6 * 1e-7))

        # - turbo pump speed / dryer : ignored at the moment
        #is_invalid_turbo_pump_speed = (indata[self.TP1_S_ID] == self.var_fills_env)
        is_invalid_turbo_pump_speed = numpy.zeros_like(is_invalid_acq) # IGNORED AT THE MOMENT

        # - invalid RH if out > in and RH not missing
        is_missing_rh = (indata[self.RH_OUT_ID] == self.var_fills_env) | (indata[self.RH_IN_ID] == self.var_fills_env)
        is_invalid_rh = (~is_missing_rh) & (indata[self.RH_OUT_ID] > indata[self.RH_IN_ID])
        # - invalid filament current: if < 0
        is_negative_emission_current = (indata[self.EMCURRENT_ID] < 0)
        # - inlet pressure : invalid if 2 consecutive diff is > 0.2
        inlet_pressure = indata[self.INLETP_ID]
        inlet_pressure_diff = numpy.diff(inlet_pressure)
        is_invalid_inlet_pressure_diff = numpy.zeros(
            start_acq.shape, dtype=bool)
        is_invalid_inlet_pressure_diff[1:] = (
            numpy.abs(inlet_pressure_diff) > 0.2)
        #print ("is_invalid_airbeam", is_invalid_airbeam)
        #print ("is_invalid_turbo_pump_speed", is_invalid_turbo_pump_speed)
        #print ("is_invalid_rh", is_invalid_rh)
        #print ("is_negative_emission_current", is_negative_emission_current)
        #print ("is_invalid_inlet_pressure_diff", is_invalid_inlet_pressure_diff)

        # - global acq state invalidity conditions: if invalid, set QA flags to 0.459
        is_invalid_acq_state = (is_invalid_airbeam | is_invalid_turbo_pump_speed | is_invalid_rh | is_negative_emission_current | is_invalid_inlet_pressure_diff)

        # --- acquisition conditions, instrument issue suspected, PI needs to be contacted
        # - invalid RH: recoreded and > 60 %
        is_invalid_high_rh = (~is_missing_rh) & (indata[self.RH_OUT_ID] > 60)

        # - flowrate: invalid if out of [2.5, 3.5] and not all 0. If all 0, considered as not recorded and so, valid
        flowrate = indata[self.SAMPLING_FLOWRATE_ID]
        is_missing_flowrate = (flowrate == self.var_fills_env)
        is_zero_flowrate = (flowrate == 0)
        if numpy.all(is_zero_flowrate | is_missing_flowrate):
            # always null, not recorded
            is_invalid_flowrate = numpy.zeros_like(is_invalid_acq)
        else:
            is_invalid_flowrate = (~is_missing_flowrate) & ((flowrate < 2.5) | (flowrate > 3.5))

        # - emission current: invalid if absolute successive diff > 0.1
        emission_current = indata[self.EMCURRENT_ID]
        emission_current_diff = numpy.diff(emission_current)
        is_invalid_emission_current_diff = numpy.zeros(
            start_acq.shape, dtype=bool)
        is_invalid_emission_current_diff[1:] = (
            numpy.abs(emission_current_diff) > 0.1)

        # - heater bias voltage: invalid if absolute successive diff > 0.5, and not new start event
        is_not_new_start_event = (indata[self.NEWSTART_EVENTS_ID] == 0)
        heater_bias_voltage = indata[self.HEATERBIAS_ID]
        heater_bias_voltage_diff = numpy.diff(heater_bias_voltage)
        is_invalid_heater_bias_voltage_diff = numpy.zeros(
            start_acq.shape, dtype=bool)
        is_invalid_heater_bias_voltage_diff[1:] = (
            numpy.absolute(heater_bias_voltage_diff) > 0.5)
        is_invalid_heater_bias_voltage_diff &= is_not_new_start_event

        # - SEM voltage: invalid if not new start event and sudden change (eg diff ==abs(100)) (source Jean_Eudes IPSL)
        sem_voltage = indata[self.SEMVOL_ID]
        sem_voltage_diff = numpy.diff(sem_voltage)
        is_invalid_sem_voltage_diff = numpy.zeros(
            start_acq.shape, dtype=bool)
        is_invalid_sem_voltage_diff[1:] = (
            numpy.absolute(sem_voltage_diff) == 100)
        is_invalid_sem_voltage_diff &= is_not_new_start_event

        # - global instr state invalidity conditions: if invalid, set QA flags to 0.456 (and contact PI ?)
        is_invalid_instr_state = (is_invalid_high_rh | is_invalid_flowrate | is_invalid_emission_current_diff | is_invalid_heater_bias_voltage_diff | is_invalid_sem_voltage_diff)

        #print ("is_invalid_acq_state", is_invalid_acq_state)
        #print ("is_invalid_high_rh", is_invalid_high_rh)
        #print ("is_invalid_flowrate", is_invalid_flowrate)
        #print ("flow_rate", indata[self.SAMPLING_FLOWRATE_ID])
        #print ("is_invalid_emission_current_diff", is_invalid_emission_current_diff)
        #print ("is_invalid_heater_bias_voltage_diff", is_invalid_heater_bias_voltage_diff)
        #print ("is_invalid_sem_voltage_diff", is_invalid_sem_voltage_diff)
        #print ("is_invalid_instr_state", is_invalid_instr_state)

        # - concentration: invalid if
        #      * < -3 * limit of detection
        #      * NaN
        #      * Fill
        #      * out of [-2, 100] range
        #      * invalid instrument
        #      * manually invalidated in lev0
        for var_id in self.var_ids_conc:
            if var_id not in indata:
                print("WARNING: variable not in data buffer" + var_id)
                continue
            # WARNING changes expected when will be specified
            lod = self.lod_ids_conc[var_id]
            conc = indata[var_id]
            # missing values
            is_conc_nan = numpy.isnan(conc)
            is_conc_fill = (conc == self.var_fills_conc)
            is_missing = (is_conc_nan | is_conc_fill)
            # out of validity range
            is_conc_below_lod = (conc < (-3 * lod))
            is_conc_out_of_range = (conc < -2) | (conc > 100)
            

            # - set flag values, if not already done manually
            if not self.inspected:
                var_id_qa = "numflag_" + var_id
                qa_flags = indata[var_id_qa]

                is_not_already_flagged = (qa_flags == 0)
                qa_flags[is_not_already_flagged & is_missing] = self.var_fills_qa  # 0.999
                qa_flags[is_not_already_flagged & (is_invalid_acq_state | is_conc_out_of_range | is_conc_below_lod)] = 0.459
                qa_flags[is_not_already_flagged & is_invalid_instr_state] = 0.456

                #print ("--- " + var_id + " ---")
                #print ("is_invalid_acq_state", is_invalid_acq_state)
                #print ("is_invalid_instr_state", is_invalid_instr_state)
                #print ("is_missing", is_missing)
                #print ("is_conc_below_lod", is_conc_below_lod)
                #print ("is_conc_out_of_range", is_conc_out_of_range)
                #print ("qa_flags", qa_flags)

                # - update data storage
                indata[var_id_qa] = qa_flags


def main():
    fpath, outdir, options = EbasQuadAcsmConverter.get_args(__APP__)
    prog = EbasQuadAcsmConverter0to0b(fpath, inspected=options.inspected)
    prog.process(outdir)


def test():
    """
    Unit test
    """

    indir = os.path.abspath(os.path.join(pkg_dir, "..", ".."))
    fpath = glob.glob(indir + "/tests/SIRTA/ref/FR0020R.20210101000014.20210614142430.aerosol_mass_spectrometer.chemistry_ACSM.pm1_non_refractory.1420mn.30mn.FR01L_ACSM_Aerodyne_Quad_140-142.FR01L_Aerodyne_Quad_GIF.lev0.nas")
    fpath = fpath[0]
    outdir = os.path.expanduser("~") + "/tmp"
    prog = EbasQuadAcsmConverter0to0b(fpath)
    ofpath = prog.process(outdir)
    os.system("module purge ; meld " + fpath + " " + ofpath)


if __name__ == "__main__":
    # test()
    main()
