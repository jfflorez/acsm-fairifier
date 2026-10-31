# -*- coding: utf-8 -*-

"""
Description :
-------------
    Product Identification based on its file pattern. The patterns and the corresponding product ID's are defined in an external file 'product.cfg' situed in the cfg directory of the distribution
    Also identifies the instrument and platform IDs of a product

Copyright (©) 2022:
-------------------
    Université de Lille ;

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
---------
    2012/09/26 : creation
"""

import os.path
import re

# from misc.PcfReader import PcfReader
from misc.FileTools import check_file

from db.ObjectDB import ObjectDB
from db.ProductDB import ProductDB

CFG_DIR = os.path.join(os.path.dirname(__file__), "cfg")


class UnknownFilePattern(Exception):
    """
    @class UnknownFilePattern file pattern does not match
    """

    def __init__(self, fpath, prod_ids):
        Exception.__init__(self)
        self.fpath = fpath
        self.prod_ids = prod_ids
        self.msg = "Unsupported file pattern {0:s}".format(fpath)

    def __str__(self):
        return self.msg


class ProductIdentifier (object):
    """
    Manages the identification of a Product that is supported by the application
    """
    # for speed, caches last regexp matches
    last_match_re = None
    last_match_prod_id = None

    def __init__(self,
                 product_cfg=os.path.join(CFG_DIR, "product.cfg"),
                 platform_cfg=os.path.join(CFG_DIR, "platform.cfg"),
                 instrument_cfg=os.path.join(CFG_DIR, "instrument.cfg"),
                 verbose=False):
        """
        Decode the supported products patterns
        @param product_pattern_file file that sets which products are supported with their pattern
        """
        object.__init__(self)

        # constructs BDs
        check_file(platform_cfg)
        self.platform_db = ObjectDB(platform_cfg)

        check_file(instrument_cfg)
        self.instrument_db = ObjectDB(instrument_cfg)

        check_file(product_cfg)
        self.product_cfg = product_cfg
        self.product_db = ProductDB(product_cfg)

        # build a dictionnary that maps a product_id to its pattern
        self.prod_pattern = {}

        # compiled patterns
        self.prod_re = {}

        self.load_product_pattern()
        self.verbose = verbose

    def load_product_pattern(self):
        """
        decode the product pattern file and update the "file pattern" to "product id" dictionnary
        """
        for k in self.product_db.db.keys():
            s_re = self.product_db.db[k].regex
            if s_re is None:
                # non pattern for that, skip
                continue
            elif isinstance(s_re, bytes):
                s_re = s_re.decode("utf-8")
            # add start/end of line tags
            if s_re[0] != "^":
                s_re = "^" + s_re
            if s_re[-1] != "$":
                s_re = s_re + "$"
            self.prod_pattern[k] = s_re
            self.prod_re[k] = re.compile(s_re)

    def get_prod_id(self, infile):
        """
        return a product ID if the file naming convention matches a known pattern. Raise an exception if not.
        @param infile an input file name. Can be either a full path or just a filename without its path
        @warning does not check the file existence
        """
        infile = os.path.abspath(infile)
        fname = os.path.basename(infile)
        # - for speed : try last matching one
        if self.last_match_re is not None and self.last_match_re.match(fname):
            return self.last_match_prod_id

        for k, compiled_re in self.prod_re.items():
            if compiled_re.match(fname):
                self.last_match_re = compiled_re
                self.last_match_prod_id = k
                return k
        # the file doesn't match any known product pattern -> raise an
        # exception
        raise UnknownFilePattern(infile, list(self.prod_pattern.keys()))
        return None

    def get_prod_re(self, prod_id):
        """
        @brief return the compiled regexp of a filename with a product
        If the Product ID is not given, it will be guessed based on naming convention
        @param prod_id a product ID
        @return the compiled regexp
        """
        return self.prod_re[prod_id]

    def get_match(self, infile, prod_id=None):
        """
        @brief return the regexp match result of a filename with a product
        If the Product ID is not given, it will be guessed based on naming convention
        @param infile a full path file
        @param prod_id a product ID
        @return the match result
        """
        if prod_id is None:
            prod_id = self.get_prod_id(infile)

        return self.prod_re[prod_id].match(os.path.basename(infile))
#         pattern = self.prod_pattern[prod_id]
#         infile = os.path.basename(infile)
#         return re.match(pattern, infile)

    def is_matching(self, infile, prod_id):
        """
        @brief check if the given file matches the given product ID
        @param infile a full path file
        @param prod_id a product ID
        @return True they are matching
        """
        return (self.get_match(infile, prod_id) is not None)

    def get_version(self, infile, prod_id=None):
        """
        @brief extract the version from the filename
        @return the version set in the filename, None else
        """
        m = self.get_match(infile, prod_id)
        if m is None:
            return None

        # - full version set
        d = m.groupdict()
        k = "version"
        if k in list(d.keys()):
            return d[k]

        # - handle eventual major version only
        major_version = None
        k = "major_version"
        if k in list(d.keys()):
            major_version = int(d[k])
        else:
            # - no version -> default
            return None

        # - minor version can be missing : 0 in this case
        minor_version = 0
        k = "minor_version"
        if k in list(d.keys()):
            minor_version = int(d[k])

        # - build <major>-<2-digits-minor> tag
        version = "{0:d}-{1:02d}".format(major_version, minor_version)
        return version

    def get_prod_patterns(self):
        """
        @brief returns the list of supported file patterns
        """
        return [v for v in self.prod_pattern.values()]

    def get_platform(self, prod_id):
        """
        @brief given a product ID, return its platform parametres
        @param prod_id a product to read ID
        @return the platform params
        """
        platform_id = self.product_db.get_platform_id(prod_id)
        return self.platform_db.get_obj(platform_id)

    def get_instrument(self, prod_id):
        """
        @brief given a product ID, return its instrument parametres
        @param prod_id a product to read ID
        @return the instrument params
        """
        instrument_id = self.product_db.get_instrument_id(prod_id)
        return self.instrument_db.get_obj(instrument_id)

    def get_start_acq(self, infile, prod_id=None):
        """
        @brief guess the start acquisition time from filename and return it as a string
        """
        if prod_id is None:
            prod_id = self.get_prod_id(infile)
        re_m = self.get_match(infile, prod_id)
        gdic = re_m.groupdict()
        start_acq = ""
        if "year" in gdic:
            if len(gdic["year"]) <= 2:
                # on 2 digits
                gdic["year"] = "20" + gdic["year"]
            start_acq += gdic["year"]
        if "month" in gdic:
            start_acq += "-" + gdic["month"]
        if "day" in gdic:
            start_acq += "-" + gdic["day"]
        for k in ["hour", "hours"]:
            if k in gdic:
                start_acq += "T" + gdic[k]
        for k in ["min", "minute", "minutes"]:
            if k in gdic:
                start_acq += "-" + gdic[k]
        for k in ["sec", "second", "seconds"]:
            if k in gdic:
                start_acq += "-" + gdic[k]
        return start_acq

    def __str__(self):
        """
        print out object content
        """
        s = '-' * 5 + ' ' + self.__class__.__name__ + ' ' + '-' * 5 + os.linesep
        s += "product_cfg=" + \
            str(self.product_cfg) + os.linesep
        s += '-' * 5 + " product patterns " + '-' * 5 + os.linesep
#         for k, v in self.prod_pattern.iteritems():
        for k, v in iter(list(self.prod_pattern.items())):
            s += "[" + k + "]" + " => " + v + os.linesep
        return s


def main():
    """
    Unit test
    """
    import random

    prog = ProductIdentifier()
    print(prog)

#     fname = "FR0020R.20140930234344.20160729103604.aerosol_mass_spectrometer.chemistry_ACSM.pm1_non_refractory.9m.29mn.Aerodyne_Q-ACSM_140-113.FR01L_Ng_2011.lev0.nas"
#     print prog.get_prod_id ( fname )
#     aa

    # Unit tests
    # vector of tuple (product_id, valid_fname)
    v_prod_name = [("CHC_AETHA_L1", "BC20111215.txt"),
                   ("CHC_NEPHE_L1", "NEPH120125.dat"),
                   ]
    for prod_id, fname in iter(v_prod_name):
        print(('-' * 5 + " " + prod_id + " " + '-' * 5))

        print(("Check filename ...",))
        if prog.get_prod_id(fname) == prod_id:
            print(" SUCCESS")
        else:
            print(" FAILED")

        print(("Check filename (full path) ...",))
        if prog.get_prod_id(os.path.join("/dummy", fname)) == prod_id:
            print(" SUCCESS")
        else:
            print(" FAILED")

        # set a dummy file name, randomly splitted
        i = random.randint(0, len(fname) - 1)
        fname = fname[:i]

        print(("Check dummy filename ...",))
        try:
            prog.get_prod_id(fname)
        except ValueError:
            print(" SUCCESS")
        else:
            print(" FAILED")

        print(("Check dummy filename (full path) ...",))
        try:
            prog.get_prod_id(os.path.join("/dummy", fname))
        except ValueError:
            print(" SUCCESS")
        else:
            print(" FAILED")


if __name__ == "__main__":
    main()
