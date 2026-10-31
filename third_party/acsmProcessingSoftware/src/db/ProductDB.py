# -*- coding: utf-8 -*-

"""
Description :
    Set the supported Product IDs. Also maps a product to its site and instrument IDs

Author(s) :
    CGTD/UDEV Nicolas PASCAL nicolas.pascal@icare.univ-lille1.fr

License :
  This file must be used under the terms of the CeCILL.
  This source file is licensed as described in the file COPYING, which
  you should have received as part of this distribution.  The terms
  are also available at
  http://www.cecill.info/licences/Licence_CeCILL_V2-en.txt

History :
    2012/09/26 : creation
"""
import os.path

from ObjectDB import ObjectDB


class ProductDB(ObjectDB):
    """
    Enumeration used to defined the valid product IDs
    """

    def __init__(self, product_cfg=os.path.join(os.path.dirname(__file__), "..", "..", "cfg", "product.cfg")):
        """
        @brief load the database from an external configuration file
        @param product_cfg file thta sets the supported product IDs
        """
        ObjectDB.__init__(self, product_cfg)

    def get_platform_id(self, prod_id):
        """
        @brief identify the platform ID matching the given product
        @param prod_iod a product ID
        @return the platform ID
        """
        return self.get_obj_attr(prod_id, "platform_sid")

    def get_instrument_id(self, prod_id):
        """
        @brief identify the instrument ID matching the given product
        @param prod_iod a product ID
        @return the instrument ID
        """
        return self.get_obj_attr(prod_id, "instrument_sid")


def main():
    """
    Unit test
    """
    prog = ProductDB()
    for prod_id in iter(prog.get_v_id()):
        print(("*** %s ***" % prod_id))
        print(("\tplatform=%s" % prog.get_platform_id(prod_id)))
        print(("\tinstrument=%s" % prog.get_instrument_id(prod_id)))


if __name__ == "__main__":
    main()
