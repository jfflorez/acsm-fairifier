# -*- coding: utf-8 -*-
"""
Description :
    from a lev0 file, genertaes all higher levels

Usage:
    python3 raw_to_012b.py <input-files>
    
Example:
    python3 test_0_to_012b.py /data_push/ground_based/pull/ACMCC/sirta-acsm/lev0/2021/10/05/FR0020R.20211005105110.20211005123115.aerosol_mass_spectrometer.chemistry_ACSM.pm1_non_refractory.57mn.30mn.FR01L_ACSM_Aerodyne_Quad_140-113.FR01L_Aerodyne_Quad_GIF.lev0.nas
    
    for f in $( find /data_push/ground_based/pull/ACMCC/sirta-acsm/lev0 -name "*.nas" ) ; do python3 test_0_to_012b.py ${f} ; done 2>&1 >~/acsm-nrt.log
    
    for f in $( find /work_dev/data/pascal/incoming/ACMCC/melpitz-acsm/lev0 -name "*.nas" ) ; do python3 test_0_to_012b.py ${f} ; done 2>&1 >~/acsm-nrt.log
    
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
    v0.0.0 : 2013/06/21
    - creation
"""

import tempfile
import glob
import shutil
import sys
import os.path

PKG_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "src"))
if PKG_ROOT not in sys.path:
    sys.path.append(os.path.join(PKG_ROOT))

from ConverterFactory import ConverterFactory

# print read data to standard output
TRACE = False
DATA_ROOT = os.path.abspath(os.path.dirname(__file__))


class Application(object):
    factory = ConverterFactory()

    def __init__(self):
        object.__init__(self)

    def process(self, infile, outdir=os.path.join(os.environ["HOME"], "test")):
        """
        @brief generate all levels upon infile in outdir
        """
        # init temp dir
        with tempfile.TemporaryDirectory() as tmpdir:
            # --- lev0 -> lev0b --- #
            print("> processing " + str(infile))
            converter = self.factory.get_class_by_level("0b")(infile)
            converter.process(tmpdir)

            # --- lev0b -> lev1b --- #
            infile = glob.glob(os.path.join(tmpdir, "*.lev0b.nas"))[0]
            # print ("> processing " + str(infile))
            converter = self.factory.get_class_by_level("1b")(infile)
            converter.process(tmpdir)

            # --- lev1b -> lev2b --- #
            infile = glob.glob(os.path.join(tmpdir, "*.lev1b.nas"))[0]
            # print ("> processing " + str(infile))
            converter = self.factory.get_class_by_level("2b")(infile)
            converter.process(tmpdir)

            # --- move all files to output dir
            # print ("> move into " + outdir)
            for infile in glob.glob(os.path.join(tmpdir, "*.nas")):
                shutil.move(infile, outdir)
            # print ("> written " + os.path.join(outdir, infile) )


def main():
    """
    Unit test
    """
    infile = sys.argv[1]

    app = Application()
    app.process(infile)


if __name__ == "__main__":
    main()
