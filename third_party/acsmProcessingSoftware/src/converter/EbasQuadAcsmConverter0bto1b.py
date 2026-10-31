# -*- coding: utf-8 -*-

"""
Description :
-------------
    EBAS Quad ACSM converter - level 0b to 1b
    remove unused lev0 params, convert concentrations to SCTP

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

pkg_dir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkg_dir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

import misc.UnitsConverter as UnitsConverter
import misc.Standardizer as Standardizer
import converter.EbasQuadAcsmConverter as EbasQuadAcsmConverter

__VERSION__ = "0.0.0"
__APP__ = os.path.splitext(os.path.basename(__file__))[0]
__DEBUG__ = True
__THROW__ = True
__SHOW_BAD_INPUTS__ = False
__SHOW_OUTPUTS__ = False


class EbasQuadAcsmConverter0bto1b(EbasQuadAcsmConverter.EbasQuadAcsmConverter):
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

    var_ids_conc_err = [
        OM_ERR_ID,
        NO3_ERR_ID,
        NO3_F30_ERR_ID,
        NO3_F46_ERR_ID,
        SO4_ERR_ID,
        NH4_ERR_ID,
        CL_ERR_ID,
        OM_F44_ERR_ID,
        OM_F43_ERR_ID,
        OM_F60_ERR_ID,
    ]
    var_ids_conc_frac = [NO3_F30_ID,
                         NO3_F46_ID,
                         OM_F44_ERR_ID,
                         OM_F43_ERR_ID,
                         OM_F60_ERR_ID, ]

    var_ids_conc_no_frac = [
        OM_ID,
        NO3_ID,
        SO4_ID,
        NH4_ID,
        CL_ID,
    ]
    # flag of variables
    var_ids_conc_qa = ["numflag_" + var_id for var_id in var_ids_conc]

    #  output level
    # olvl = "1b"

    def __init__(self, fpath=None, inspected=False):
        """
        @brief constructor
        @param fpath input file path
        @param inspected manually inspected if True
        """
        EbasQuadAcsmConverter.EbasQuadAcsmConverter.__init__(
            self, fpath, inspected)
        # output level
        if self.inspected:
            self.olvl = "1"
        else:
            self.olvl = "1b"

    def convert(self):
        """
        @brief level conversion, set concentrations to SCTP
        """
        self.normalize_units()
        self.to_sctp()
        self.remove_unused_vars()

    def normalize_units(self):
        """
        @brief convert to standard units
        """
        # - temperature: C -> K
        var_id = self.T_IN_ID
        var_name = self.writer.get_var_name(var_id)
        data = self.writer.data[var_id]
        data = UnitsConverter.celsius2kelvin(data)
        self.writer.rename_var(
            var_name, var_name.replace("deg C", "K"), unit="K")

        # - pressure: Torr -> hPa
        var_id = self.INLETP_ID
        var_name = self.writer.get_var_name(var_id)
        data = self.writer.data[var_id]
        # print ("Torr", data)
        data = UnitsConverter.torr2hpa(data)
        self.writer.data[var_id] = data
        # print ("hPa", data)
        self.writer.rename_var(
            var_name, var_name.replace("Torr", "hPa"), unit="hPa")

    def remove_unused_vars(self):
        """
        @brief remove unused vars in output storage structure
        """
        out_var_ids = [self.START_ACQ_ID, self.END_ACQ_ID] + self.var_ids_env + \
            self.var_ids_conc + self.var_ids_conc_err + self.var_ids_conc_qa
        in_var_ids = list(self.writer.data.columns)
        for var_id in in_var_ids:
            if var_id not in out_var_ids:
                self.writer.del_var(var_id)

    def to_sctp(self):
        """
        @brief level conversion, add flags
        """
        s_acq_temp = self.reader.get_attr("Volume std. temperature").strip()
        s_acq_pres = self.reader.get_attr("Volume std. pressure").strip()
        acq_temp = float(s_acq_temp[:-1])  # remove unit K
        acq_pres = float(s_acq_pres[:-3])  # remove unit hPa

        std_temp = Standardizer.T_STD
        std_pres = Standardizer.P_STD
        s_std_temp = "{:.2f}K".format(std_temp)
        s_std_pres = "{:.2f}hPa".format(std_pres)

        # - update writer metadata
        self.writer.set_attr("Volume std. temperature", s_std_temp)
        self.writer.set_attr("Volume std. pressure", s_std_pres)

        # - apply conversion
        indata = self.writer.data
        for var_id in self.var_ids_conc:
            data = indata[var_id]
            # raw data fill value
            fill = self.var_fills_conc
            indata[var_id] = Standardizer.to_std(
                data, acq_temp, acq_pres, is_prop_vol=True, fill=fill)
            # - also normalize errors if present
            err_var_id = "err_" + var_id
            if err_var_id in self.var_ids_conc_err:
                data = indata[err_var_id]
                indata[err_var_id] = Standardizer.to_std(
                    data, acq_temp, acq_pres, is_prop_vol=True, fill=fill)


def main():
    fpath, outdir, options = EbasQuadAcsmConverter.get_args(__APP__)
    prog = EbasQuadAcsmConverter0bto1b(fpath, inspected=options.inspected)
    prog.process(outdir)


def test():
    """
    Unit test
    """
    acq_err_log = None

    indir = os.path.abspath(os.path.join(pkg_dir, "..", ".."))
    infpath = glob.glob(indir + "/tests/SIRTA/ref/FR0020R.20210101000014.20210531065758.aerosol_mass_spectrometer.chemistry_ACSM.pm1_non_refractory.1420mn.30mn.FR01L_ACSM_Aerodyne_Quad_140-142.FR01L_Aerodyne_Quad_GIF.lev0b.nas")
    infpath = infpath[0]
    outdir = os.environ["HOME"] + "/tmp"
    prog = EbasQuadAcsmConverter0bto1b(infpath, acq_err_log)
    ofpath = prog.process(outdir)
    refpath = indir + "/tests/SIRTA/ref/FR0020R.20210101000014.20210531065758.aerosol_mass_spectrometer.chemistry_ACSM.pm1_non_refractory.1420mn.30mn.FR01L_ACSM_Aerodyne_Quad_140-142.FR01L_Aerodyne_Quad_GIF.lev1b.nas"
    os.system("module purge ; meld " + refpath + " " + ofpath)


if __name__ == "__main__":
    # test()
    main()
