# -*- coding: utf-8 -*-

"""
Description :
    Generic object IDs management, based on a configuration file

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

from DBReader import DBReader


class ObjectDB(object):
    """
    Enumeration used to defined the valid object IDs
    """

    def __init__(self, db_cfg):
        """
        @brief load the database from an external configuration file
        @param product_cfg file thta sets the supported IDs
        """
        object.__init__(self)

        self.db = self.read_db(db_cfg)

    def get_obj(self, objid):
        """
        @brief access to the object instance
        @param objid an object ID
        @return the object ID
        """
        self.check_id(objid)
        return self.db[objid]

    def get_obj_attr(self, objid, attr_name):
        """
        @brief access the attribute of an object using its name
        @param objid an object ID
        @param attr_name name of the attribute to access
        @return the attribute value
        """
        return getattr(self.get_obj(objid), attr_name)

    def read_db(self, cfg_file):
        """
        @brief decode the database file
        @param cfg_file the database file
        @return the constructed database
        """
        db = DBReader.decode(cfg_file)
        # set Ids as attribute
#         for k in db.iterkeys():
        for k in iter(list(db.keys())):  # python3 2 -> python3
            setattr(self, k, k)
        return db

    def get_v_id(self):
        """
        @brief return the list of valid product IDs
        """
        return list(self.db.keys())

    def check_id(self, objid):
        """
        @brief check if the given ID is valid. If not, raise a ValueError exception
        @param objid an object ID
        """
#         if not self.db.has_key(objid) :
        if not objid in self.db:
            raise ValueError("Invalid ID " + str(objid) +
                             ". Must be one of " + str(self.get_v_id()))


def main():
    """
    Unit test
    """
    prog = ObjectDB()
    for objid in iter(prog.get_v_id()):
        print(("*** %s ***" % objid))
        print((prog.db))
        print(("\tplatform=%s" % prog.get_platform_id(objid)))
        print(("\tinstrument=%s" % prog.get_instrument_id(objid)))


if __name__ == "__main__":
    main()
