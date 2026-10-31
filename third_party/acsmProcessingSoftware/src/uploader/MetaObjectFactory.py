# -*- coding: utf-8 -*-

"""""
Description :
-------------
    Populate a dictionary of meta-objects from a configuration ini file

Limitations :
-------------
    -

Author(s) :
-----------
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


History:
--------
    v0.0.0: 2015/10/06
    - creation
"""

import os
import configparser

__PATH__ = os.path.abspath(os.path.dirname(__file__))


class MetaObject(object):
    """
    @class Platform platform parameters
    """

    def __init__(self, _id, **kwargs):
        """
        @brief constructor, set a file bootstrap entry
        @param id an internal object ID
        @param in_fpattern input file pattern
        @param out_dir output file directory
        @param out_fpattern output file pattern
        """
        object.__init__(self)
        self.id = _id
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        s = "[{0:s}]".format(self.id) + os.linesep
        for k, v in self.__dict__.items():
            if k != "id":
                s += "{0:s} : {1:s}".format(k, str(v)) + os.linesep
        return s.strip()


class MetaObjectFactory(object):
    """
    @class MetaObjectFactory decode a config file and build a dictionary of object with it
    """
    @staticmethod
    def cfg2dic(parser):
        """
        @brief build a dictionary of configparser section => (elements) and return it
        """
        dic = {}
        for section in parser.sections():
            dic[section] = {}
            items = parser.items(section)
            for option_name, option_value in items:
                dic[section][option_name] = option_value
        return dic

    def __init__(self, cfg_file, fn_post=None):
        """
        @brief constructor, build platforms dictionnary
        @param cfg_file config file that sets the objects to instantiate
        @param fn_post postprocess function. Once an object is instantiated, apply this function on it (for instance, compile a regexp, etc)
        """
        object.__init__(self)
        self.cfg_file = cfg_file
        self.fn_post = fn_post
        self.obj_pool = self.populate()

    def get(self, obj_id=None):
        """
        @brief accessor to built objects
        @param obj_id ID of a constructed object. If None, return the whole objects dictionary
        @return an object if obj_id not None, the dictionary of all objects else
        """
        if obj_id is not None:
            return self.obj_pool[obj_id]
        return self.obj_pool

    def populate(self):
        """
        @brief constructs the dictionary using an external configuration file
        """
        obj_pool = {}

        parser = configparser.ConfigParser()
        parser.read(self.cfg_file)

#         pprint.PrettyPrinter(indent=4).pprint(self.configparser2dic(parser))
        for section in parser.sections():
            # decode section options
            obj_cfg = {}
            for option in parser.options(section):
                obj_cfg[option] = parser.get(section, option)
            # create my object
            obj = MetaObject(section, **obj_cfg)
            # apply eventual post process function
            if self.fn_post is not None:
                self.fn_post(obj)
            obj_pool[section] = obj
        return obj_pool

    def __str__(self):
        s = '|' + '=' * 90 + '|' + os.linesep
        keys = list(self.obj_pool.keys())
        keys.sort()
        for k in keys[::-1]:
            s += str(self.obj_pool[k]) + os.linesep
        s += '|' + '=' * 90 + '|' + os.linesep
        return s


def test():
    """
    Main script
    """
    import re

    cfg_file = os.path.join(__PATH__, "native_aeronet.cfg")

    # init factory
    factory = MetaObjectFactory(cfg_file, lambda obj: setattr(
        obj, "infile_pattern", re.compile(obj.infile_pattern)))
    # get one  object
    obj_id = "AERONET-AOD-NATIVE_L10"
    print("-" * 30 + obj_id + "-" * 30)
    print(factory.get(obj_id))

    # get all objects
    print("-" * 30 + " ALL " + "-" * 30)
    for obj in list(factory.get().values()):
        print(obj)
        print("-" * 65)


if __name__ == "__main__":
    test()
