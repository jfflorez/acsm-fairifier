# -*- coding: utf-8 -*-

"""
Description :
    Object factory that decode a database file based on python's ConfigParser syntax and fills a
    generic container with that

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
import sys
try:
    from configparser import ConfigParser  # python3 2 version
    from ordereddict import OrderedDict
except Exception:
    from configparser import ConfigParser  # python3 3 version
    from collections import OrderedDict
import numpy

d = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

from misc.FileTools import check_file


class Container(object):
    """
    generic container class
    """

    def __init__(self):
        """
        @brief generic constructor
        """
        object.__init__(self)
        # object unique identifier. Can be viewed as a primary key
        # self.uuid = None
        self.sid = None

    def __str__(self):
        """
        print out object content
        """
        s = ""
#         if "uuid" in self.__dict__ and self.__dict__["uuid"] is not None:
#             s += "uuid : " + str(self.__dict__["uuid"]) + os.linesep
#         s += "sid=" + str(self.sid) + os.linesep
        for k, v in self.__dict__.items():
            if k[0] != "_" and k != "id":
                s += str(k) + " : " + str(v) + os.linesep
        return s

    def get_items(self):
        """
        @brief return the lists of custom attribute names and values
        """
        keys = []
        vals = []
        for k, v in self.__dict__.items():
            if k[0] != "_":
                keys.append(k)
                vals.append(v)
        return keys, vals

    def add_item(self, key, val):
        """
        @brief add an tiem
        """
        self.__dict__[key] = val


class DBReader(object):
    """
    Manages the DB file decoding
    """
    @staticmethod
    def interpret_cast(s, force_str=False):
        """
        @brief interpret the eventual casts in the argument
        @param s a string that can be "float(12.5)", "aze", "int(12)"
        @param force_str always interpret as a string, even if numeric
        @return s interpreted as python3 code
        """
        if force_str is True:
            return str(s)
        try:
            return eval(s)
        except NameError:
            # v is a string or None
            if s.lower() == "none":
                return None
            else:
                return s
        except SyntaxError:
            # string by default
            return str(s)

        except AttributeError:
            # string by default
            return str(s)

    @staticmethod
    def decode(fname, constructor=Container):
        """
        @brief decode the file and constructs a dictionnary where the keys are the [ID] found in the
        file and the values are the objects constructed with the parametres. Each parametre becomes an
        attribute of the constructed object
        @param db_file database file
        @param container class that contains the decoded params
        @return a disctionnary of the decoded objects
        """
        # parse DB file
        check_file(fname)
#         parser = ConfigParser.ConfigParser()
        parser = ConfigParser()

        parser.read(fname)

        # fills dictionnary with decoded objetcs
        dic = {}
        for objid in iter(parser.sections()):
            # construct object
            obj = constructor()
            sec_items = parser.items(objid)
            obj.sid = objid
            for k, v in iter(sec_items):

                # interpret explicit cast in file
                force_str = False
                if k == "doi":
                    # in case of DOI, can be an operation like string (ie
                    # 25367/14). We want to keep a string
                    force_str = True
                v = DBReader.interpret_cast(v, force_str)
                setattr(obj, k, v)
            # print obj
            # check unicity
#             if dic.has_key(objid):
#                 raise ValueError("Object already exists %s" % objid)
            if objid in dic:  # python2 -> python3
                raise ValueError("Object already exists %s" % objid)
            dic[objid] = obj

        return dic

    @staticmethod
    def encode(dic, outfname, t_obj=Container):
        """
        @brief write the given dictionnary in the given output file
        @param db_file database file
        @param container class of the dictionnary values
        """
#         parser = ConfigParser.ConfigParser()
        parser = ConfigParser()

        # fills parser with dictionnary items
        for secid in dic.keys():
            parser.add_section(secid)
            obj = dic[secid]
            # print dir(obj)
            for k, v in obj.__dict__.items():
                # print v, type(v)
                if k != "id":
                    if isinstance(v, float) or isinstance(v, numpy.float32) or isinstance(v, numpy.float64):
                        v = "float(%s)" % str(v)
                    elif isinstance(v, int) or isinstance(v, numpy.int32):
                        v = "int(%s)" % str(v)
                    elif isinstance(v, int) or isinstance(v, numpy.int64):
                        v = "long(%s)" % str(v)
                    elif isinstance(v, str):
                        v = "str(\"%s\")" % str(v)
                    elif isinstance(v, numpy.ndarray):
                        v = "%s" % str(v)
                    elif v is None:
                        v = "%s" % str(v)
                    else:
                        raise ValueError(
                            "Unsupported dtype %s for value %s" % (type(v), str(v)))
                    parser.set(secid, k, v)

        # dump parser
        f = open(outfname, "w")
        try:
            parser.write(f)
        finally:
            f.close()

        return dic

    @staticmethod
    def dump(dic, outfname, t_obj=Container):
        """
        @brief write the given dictionnary in the given output file
        @param db_file database file
        @param container class of the dictionnary values
        """
#         parser = ConfigParser.ConfigParser()
        parser = ConfigParser()

        # fills parser with dictionnary items
        for secid in dic.keys():
            parser.add_section(secid)
            obj = dic[secid]
            # print dir(obj)
            for k, v in obj.__dict__.items():
                # print v, type(v)
                if k == "id" or (v is None):
                    # not relevant, skip
                    continue

                if isinstance(v, float) or isinstance(v, numpy.float32) or isinstance(v, numpy.float64):
                    v = "{:f}".format(v)
                elif isinstance(v, int) or isinstance(v, numpy.int32):
                    v = "{:d}".format(v)
                elif isinstance(v, int) or isinstance(v, numpy.int64):
                    v = "{:d}".format(v)
                elif isinstance(v, str):
                    v = str(v)
                elif isinstance(v, numpy.ndarray):
                    v = "{:s}".format(str(v))
                elif v is None:
                    v = "None"
                else:
                    raise ValueError(
                        "Unsupported dtype %s for value %s" % (type(v), str(v)))
                parser.set(secid, k, v)

        # dump parser
        f = open(outfname, "w")
        try:
            parser.write(f)
        finally:
            f.close()

        return dic


def main():
    """
    Unit test
    """

    db_file = os.path.join(os.path.dirname(__file__),
                           "..", "..", "cfg", "platform.cfg")
    dic = DBReader.decode(db_file)
    DBReader.encode(dic, "/home/pascal/test.db")


if __name__ == "__main__":
    main()
