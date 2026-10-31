# -*- coding: utf-8 -*-
"""
Description :
    Concrete implementations of Ground Based Data Converter Unit Tests for station products

Author(s) :
    CGTD-ICARE/UDEV-HYGEOS Nicolas PASCAL

License :
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
    v0.0.0 : 2016/10/19
    - creation
"""
import os.path
import unittest
import glob

from TestProductConverter import TestProductConverter, DATA_ROOT

############################
#         SIRTA          ###
############################


class TestSirtaAcsmProductConverter(TestProductConverter):
    gen_ref = False

    def test_lev0_nrt(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "SIRTA/in/SIRTA_ACSM-140113_????????????.txt"))
        self._test_converter("SIRTA", infiles, is_nrt=True, gen_ref=self.gen_ref, lvl=0)

    def test_lev0b_nrt(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "SIRTA/ref/*57mn*lev0.nas"))
        self._test_converter("SIRTA", infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="0b")

    def test_lev1b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "SIRTA/ref/*lev0b.nas"))
        self._test_converter("SIRTA", infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="1b")

    def test_lev2b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "SIRTA/ref/*lev1b.nas"))
        self._test_converter("SIRTA", infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="2b")

    def test_lev0(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "SIRTA/in/SIRTA_ACSM-140113_????.txt"))
        acq_err_log = glob.glob(os.path.join(
            DATA_ROOT, "SIRTA/in/SIRTA_ACSM-140113_FLAGS_????.txt"))[0]
        self._test_converter("SIRTA", infiles, gen_ref=self.gen_ref, lvl=0, acq_err_log=acq_err_log)

    def test_lev0a(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "SIRTA/ref/*10mo*lev0.nas"))
        self._test_converter("SIRTA", infiles, gen_ref=self.gen_ref, lvl="0a", inspected=True)

    def test_lev1(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "SIRTA/ref/*lev0a.nas"))
        self._test_converter("SIRTA", infiles, gen_ref=self.gen_ref, lvl="1", inspected=True)

    def test_lev2(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "SIRTA/ref/*lev1.nas"))
        self._test_converter("SIRTA", infiles, gen_ref=self.gen_ref, lvl="2", inspected=True)


class TestMelpitzAcsmProductConverter(TestProductConverter):
    gen_ref = False
    station_name = "Melpitz"

    def test_lev0(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/in/{station_name:s}_ACSM-*.txt".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl=0)

    def test_lev0b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="0b")

    def test_lev1b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="1b")

    def test_lev2b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev1b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="2b")


class TestAtollAcsmProductConverter(TestProductConverter):
    gen_ref = False
    station_name = "ATOLL"

    def test_lev0(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/in/{station_name:s}_ACSM-*.txt".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl=0)

    def test_lev0b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="0b")

    def test_lev1b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="1b")

    def test_lev2b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev1b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="2b")


class TestBarcelonaAcsmProductConverter(TestProductConverter):
    gen_ref = False
    station_name = "Barcelona"

    def test_lev0(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/in/{station_name:s}_ACSM-*.txt".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl=0)

    def test_lev0b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="0b")

    def test_lev1b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="1b")

    def test_lev2b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev1b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="2b")


class TestHyytialaAcsmProductConverter(TestProductConverter):
    gen_ref = False
    station_name = "Hyytiala"

    def test_lev0(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/in/{station_name:s}_ACSM-*.txt".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl=0)

    def test_lev0b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="0b")

    def test_lev1b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="1b")

    def test_lev2b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev1b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="2b")


class TestAthensAcsmProductConverter(TestProductConverter):
    gen_ref = False
    station_name = "Athens"

    def test_lev0(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/in/{station_name:s}_ACSM-*.txt".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl=0)

    def test_lev0b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="0b")

    def test_lev1b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="1b")

    def test_lev2b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev1b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="2b")


class TestDublinAcsmProductConverter(TestProductConverter):
    gen_ref = False
    station_name = "Dublin"

    def test_lev0(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/in/{station_name:s}*_ACSM-*.txt".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl=0)

    def test_lev0b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="0b")

    def test_lev1b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev0b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="1b")

    def test_lev2b(self):
        infiles = glob.glob(os.path.join(
            DATA_ROOT, "{station_name:s}/ref/*lev1b.nas".format(station_name=self.station_name)))
        self._test_converter(self.station_name, infiles, is_nrt=True, gen_ref=self.gen_ref, lvl="2b")


if __name__ == '__main__':
    print(unittest.main())
