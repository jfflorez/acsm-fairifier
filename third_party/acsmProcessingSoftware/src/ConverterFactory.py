# -*- coding: utf-8 -*-

"""
Description :
-------------
    Initialize the ACTRIS converter interfaces

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
    2013/09/30 : creation
"""

import ProductIdentifier

from converter.QuadAcsmConverter import QuadAcsmConverter
from converter.EbasQuadAcsmConverter0to0b import EbasQuadAcsmConverter0to0b
from converter.EbasQuadAcsmConverter0bto1b import EbasQuadAcsmConverter0bto1b
from converter.EbasQuadAcsmConverter1bto2b import EbasQuadAcsmConverter1bto2b

from converter.TofAcsmConverter import TofAcsmConverter
from converter.EbasTofAcsmConverter0to0b import EbasTofAcsmConverter0to0b
from converter.EbasTofAcsmConverter0bto1b import EbasTofAcsmConverter0bto1b
from converter.EbasTofAcsmConverter1bto2b import EbasTofAcsmConverter1bto2b

class ConverterFactory(object):
    """
    Manages the identification of a Product that is supported by the application
    """
    product_identifier = ProductIdentifier.ProductIdentifier()
    # ACSM model tags
    Q_ACSM_ID = "Q-ACSM"
    ToF_ACSM_ID = "ToF-ACSM"


    def __init__(self):
        object.__init__(self)

    def get_class(self, prod_id):
        """
        @brief given a product ID, return the class of reader to use
        @param prod_id a product to read ID
        @return the reader class
        """
        # validate product ID
        self.product_identifier.product_db.check_id(prod_id)
        # get type of ACSM
        model_id = self.product_identifier.get_instrument(prod_id).model
        # select the good converter class
        if model_id == self.Q_ACSM_ID:
            return QuadAcsmConverter
        elif model_id == self.ToF_ACSM_ID:
            return TofAcsmConverter
        else:
            raise ValueError(
                "No interface implemented for ACSM model %s" % model_id)

    def get_model_by_fname(self, fname):
        """
        @brief return the model of ACSM (Quad or ToF
        """
        prod_id = self.get_prod_id(fname)
        return self.product_identifier.get_instrument(prod_id).model
        

    def get_prod_id(self, fname):
        """
        @brief fname to product ID helper
        """
        return self.product_identifier.get_prod_id(fname)

    def get_class_by_fname(self, fname):
        """
        @brief given a filename, return the class of converter to use
        @param fname the file to read
        @return the converter class
        """
        prod_id = self.get_prod_id(fname)
        return self.get_class(prod_id=prod_id)

    def get_class_by_level(self, lvl, model=Q_ACSM_ID):
        """
        @brief given a level, return the class of converter to use (ACSM ONLY)
        @param lvl the level of the file to read
        @param model type of ACSM
        @return the converter class
        """
        if  model == self.Q_ACSM_ID and lvl in ["0a", "0b"]:
            return EbasQuadAcsmConverter0to0b
        elif model == self.Q_ACSM_ID and lvl in [1, "1", "1b"]:
            return EbasQuadAcsmConverter0bto1b
        elif model == self.Q_ACSM_ID and lvl in [2, "2", "2b"]:
            return EbasQuadAcsmConverter1bto2b
        elif model == self.ToF_ACSM_ID and lvl in ["0a", "0b"]:
                return EbasTofAcsmConverter0to0b
        elif model == self.ToF_ACSM_ID and lvl in [1, "1", "1b"]:
            return EbasTofAcsmConverter0bto1b
        elif model == self.ToF_ACSM_ID and lvl in [2, "2", "2b"]:
            return EbasTofAcsmConverter1bto2b
        else:
            raise ValueError("Unsupported couple model/level " + str(model) + "/" + str(lvl))

        return self.get_class(prod_id)

    def get_instance(self, fname, acq_err_log=None):
        """
        @brief given a file, instantiate the product
        @param fname the file to read
        @return the instantiated reader
        """
        prod_id = self.get_prod_id(fname)
        my_class = self.get_class(prod_id)
        return my_class(prod_id=prod_id, acq_err_log=acq_err_log)
