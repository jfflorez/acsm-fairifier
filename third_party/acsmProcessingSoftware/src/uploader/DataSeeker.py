# -*- coding: utf-8 -*-

import os
import sys
import os.path
from calendar import monthrange
import glob
import re
import string

pkg_dir = os.path.dirname(__file__)
d = os.path.abspath(os.path.join(pkg_dir, ".."))
if d not in sys.path:
    sys.path.append(os.path.join(d))

from misc.FileTools import unix_to_os_path
from MetaObjectFactory import MetaObjectFactory


class DataSeeker(object):
    """
    @class DataSeeker ICARE Archive file seeker
    """
    # path to the archive product paths configuration file
    CFG_FILE = os.path.join(os.path.dirname(__file__),
                            "..", "cfg", "product.cfg")

    # REGEXP of a period tag :  YYYY, YYYY-MM or YYYY-MM-DD
    RE_PERIOD_TAG = re.compile(
        "^(?P<year>[0-9]{4})(((-(?P<month>[0-9]{2}))?)((-(?P<day>[0-9]{2}))?)((T(?P<hours>[0-9]{2})-(?P<minutes>[0-9]{2})-(?P<seconds>[0-9]{2}))?))$")

    @staticmethod
    def unix_to_os_path(unix_path):
        """
        @brief normalize a UNIX like path to the platform one
        """
        os_path = unix_path.replace("~", os.path.expanduser('~'))
        os_path = unix_path.replace("/", os.sep)
        return os_path

    @staticmethod
    def cfg_post_process(obj):
        """
        @brief post treatments after the configuration file has been decoded.
        Mainly regexp compilation, string template creation
        """
        # string templates creation
        # print obj.fdir_tpl
        setattr(obj, "fdir_tpl", string.Template(
            unix_to_os_path(obj.fdir_tpl)))

        # build a file completion pattern based on regex
        # print obj.fdir_tpl
        # (?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})(?P<hour>[0-9]{2})(?P<min>[0-9]{2})
        fname_tpl = obj.regex
        for match, sub in [("(?P<year>[0-9]{4})", "${YYYY}"),
                           ("(?P<month>[0-9]{2})", "${MM}"),
                           ("(?P<day>[0-9]{2})", "${DD}"),
                           ("(?P<hour>[0-9]{2})", "${HH}"),
                           ("(?P<min>[0-9]{2})", "${mm}"),
                           ]:
            fname_tpl = fname_tpl.replace(match, sub)
        setattr(obj, "fname_tpl", string.Template(unix_to_os_path(fname_tpl)))

    def __init__(self):
        """
        @brief constructor
        """
        object.__init__(self)

        # build process configuration
        self.cfg = MetaObjectFactory(
            DataSeeker.CFG_FILE, DataSeeker.cfg_post_process).get()
        # print self.cfg

    @staticmethod
    def get_dates(ts, reverse=False):
        """
        @brief given a period timestamp as YYYY, YYYY-MM, YYYY-MM-DD, return the list of matching dates
        @param ts a timestamp s YYYY, YYYY-MM or YYYY-MM-DD
        @param reverse if True, dates are returned in decreasing order, else increasing order is used
        @return a list of (YYYY, MM, DD) tuples corresponding to the required period, sorted in requested order
        """
        # generate a list of days
        m = DataSeeker.RE_PERIOD_TAG.match(ts.strip())

        dic = m.groupdict()
        year = int(dic["year"])

        months = []
        if dic["month"] is not None:
            # 1 month
            months = [int(dic["month"])]
        else:
            # all months of year
            months = range(1, 13)

        dates = []
        if dic["day"] is not None:
            # 1 specific day
            dates = [(year, int(dic["month"]), int(dic["day"]))]
        else:
            # all months of year
            for month in months:
                ndays = monthrange(year, month)[1]
                for day in xrange(1, ndays + 1):
                    dates.append((year, month, day))

        # manage ordering
        dates.sort(reverse=reverse)
        return dates

    @staticmethod
    def parse_period_tag(ts):
        """
        @brief parse the timestamp and return a 6 values tuple (year, month, day, hours, minutes, seconds) 
        if one info is missing in ts, the field is None
        @param ts a an orbit tiestamp tag as YYYY, YYYY-MM, YYYY-MM-DD, YYYY-MM-DDTHH-MM-SS
        """
        # - parse timestamp infos
        m = DataSeeker.RE_PERIOD_TAG.match(ts.strip())
        if m is None:
            raise ValueError("Invalid timestamp " + ts)

        year = int(m.group("year"))
        day = None
        hours = None
        minutes = None
        seconds = None

        month = None
        s_month = m.group("month")
        if len(s_month) > 0:
            month = int(m.group("month"))

        day = None
        s_day = m.group("day")
        if len(s_day) > 0:
            day = int(m.group("day"))

        hours = None
        s_hours = m.group("hours")
        if len(s_hours) > 0:
            hours = int(m.group("hours"))

        minutes = None
        s_minutes = m.group("minutes")
        if len(s_minutes) > 0:
            minutes = int(m.group("minutes"))

        seconds = None
        s_seconds = m.group("seconds")
        if len(s_seconds) > 0:
            seconds = int(m.group("seconds"))
        return (year, month, day, hours, minutes, seconds)

    def get_infile(self, prod_id, ts):
        """
        @brief return one file given the orbit timestamp
        @param prod_id a product ID
        @param ts a an orbit tiestamp tag as YYYY-MM-DDTHH-MM-SS
        """
        if prod_id not in self.cfg.keys():
            raise ValueError("Invalid product ID")

        # - parse timestamp infos
        year, month, day, hours, minutes, seconds = self.parse_period_tag(ts)
#         m = DataSeeker.RE_PERIOD_TAG.match(ts.strip())
#         if m is None:
#             raise ValueError("Invalid timestamp " + ts)
#
#         year=int(m.group("year"))
#         month=int(m.group("month"))
#         day=int(m.group("day"))
#         hours=int(m.group("hours"))
#         minutes=int(m.group("minutes"))
#         seconds=int(m.group("seconds"))

        # - search path templates
        fdir_tpl = self.cfg[prod_id].fdir_tpl
        fname_tpl = self.cfg[prod_id].fname_tpl

        # - build dynamic tags substitution dictionnary to build glob search path
        subs = {}
        subs["YYYY"] = "{0:d}".format(year)
        subs["MM"] = "{0:02d}".format(month)
        subs["DD"] = "{0:02d}".format(day)
        subs["HH"] = "{0:02d}".format(hours)
        subs["mm"] = "{0:02d}".format(minutes)
        subs["SS"] = "{0:02d}".format(seconds)
        subs["DN"] = "*"

        # - build search path
        fdir = fdir_tpl.safe_substitute(subs)
        fname = fname_tpl.safe_substitute(subs)
        search = os.path.join(fdir, fname)

        # - search files
        # print search
        files = glob.glob(search)
        if len(files) > 1:
            raise ValueError("More than one file found for prod_id={0:s} and timestamp={1:s}\n{2:s}".format(
                prod_id, ts, str(files)))
        elif len(files) == 0:
            # print "No matching file found for prod_id={0:s} and
            # timestamp={1:s}".format(prod_id, ts)
            return None
        return files[0]

    def get_root_dir(self, prod_id):
        """
        @brief get root directory (without date info) of product
        """
        dprod_pattern = self.cfg[prod_id].fdir_tpl.template
        pth, tail = os.path.split(dprod_pattern)
        while tail.find("$") >= 0:
            pth, tail = os.path.split(pth)
        return os.path.join(pth, tail)

    def get_infiles(self, prod_id, ts, reverse=False):
        """
        @brief return a list of files for the given product and the given date
        @param prod_id a product ID
        @param ts a period tag as YYYY, YYYY-MM or YYYY-MM-DD, or ALL
        @param reverse if True, files are returned in decreasing order, else increasing order is used
        """
        if prod_id not in self.cfg.keys():
            raise ValueError("Invalid product ID")

        files = []
        if ts == "ALL":
            # find all matching files
            subs = {}
            subs["YYYY"] = "[0-9][0-9][0-9][0-9]"
            subs["MM"] = "[0-9][0-9]"
            subs["DD"] = "[0-9][0-9]"
            subs["HH"] = "[0-9][0-9]"
            subs["mm"] = "[0-9][0-9]"
            subs["SS"] = "[0-9][0-9]"
            subs["DN"] = "*"
            # - search path templates
            fdir_tpl = self.cfg[prod_id].fdir_tpl
            fname_tpl = self.cfg[prod_id].fname_tpl
            # - build search path
            fdir = fdir_tpl.safe_substitute(subs)
            fname = fname_tpl.safe_substitute(subs)
            search = os.path.join(fdir, fname)
            print (search)
            # - search files
            files = glob.glob(search)
        else:
            # list of dates matching period tag
            dates = DataSeeker.get_dates(ts)
            # -> list of matching filesout_fdir
            for day in dates:
                files += self.get_infiles_day(prod_id, day)

        # make sure elements are unique
        files = list(set(files))
        files.sort(reverse=reverse)
        # print ("\n".join(files))
        return files

    def get_site_id(self, prod_id):
        """
        @brief identify the site id of the given product.
        site ID is the start of filename to the first underscore
        """
        # site ID is the start of product ID to the first underscore

        # fname_tpl = self.cfg[prod_id].fname_tpl.template
        # site_id = fname_tpl.split("_")[0]
        site_id = prod_id.split("_")[0]
        return site_id

    def get_prod_dir_tpl(self, prod_id):
        """
        @brief return the directory pattern of the given product
        @param prod_id a product ID
        """
        return self.cfg[prod_id].fdir_tpl

    def get_prod_fname_tpl(self, prod_id):
        """
        @brief return the filename pattern of the given product
        @param prod_id a product ID
        """
        return self.cfg[prod_id].fname_tpl

    def get_infiles_day(self, prod_id, date_tuple, reverse=False):
        """
        @brief return the list of files of the given product, for the given day
        @param prod_id a product ID
        @param date_tuple a (year, month, day) tuple
        @param reverse if True, files are returned in decreasing order, else increasing order is used
        """
        # - search path templates
        fdir_tpl = self.cfg[prod_id].fdir_tpl
        fname_tpl = self.cfg[prod_id].fname_tpl

        # - build dynamic tags substitution dictionnary to build glob search path
        subs = {}

        year = date_tuple[0]
        month = date_tuple[1]
        day = date_tuple[2]

        subs["YYYY"] = "{0:d}".format(year)
        subs["MM"] = "{0:02d}".format(month)
        subs["DD"] = "{0:02d}".format(day)
        subs["HH"] = "[0-9][0-9]"
        subs["mm"] = "[0-9][0-9]"
        subs["SS"] = "[0-9][0-9]"
        subs["DN"] = "[DN]"

        # - build search path
        fdir = fdir_tpl.safe_substitute(subs)
        fname = fname_tpl.safe_substitute(subs)
        search = os.path.join(fdir, fname).strip()

        # - search files
        #print (search)
        files = glob.glob(search)
        files.sort(reverse=reverse)
        return files

    def get_infiles_dt(self, prod_id, dt, reverse=False):
        """
        @brief return the list of files of the given product, for the given day
        @param prod_id a product ID
        @param dt a datetime object
        @param reverse if True, files are returned in decreasing order, else increasing order is used
        """
        # - search path templates
        fdir_tpl = self.cfg[prod_id].fdir_tpl
        fname_tpl = self.cfg[prod_id].fname_tpl

        # - build dynamic tags substitution dictionnary to build glob search path
        subs = {}

        subs["YYYY"] = "{0:d}".format(dt.year)
        subs["MM"] = "{0:02d}".format(dt.month)
        subs["DD"] = "{0:02d}".format(dt.day)
        subs["HH"] = "{0:02d}".format(dt.hour)
        subs["mm"] = "{0:02d}".format(dt.minute)
        subs["SS"] = "{0:02d}".format(dt.second)
        subs["DN"] = "[DN]"

        # - build search path
        fdir = fdir_tpl.safe_substitute(subs)
        fname = fname_tpl.safe_substitute(subs)
        search = os.path.join(fdir, fname)

        # - search files
        # print search
        files = glob.glob(search)
        files.sort(reverse=reverse)

        return files


"""
Main script
"""


def test():
    app = DataSeeker()
    tag = "2021-04-10T01"
    for prod_id in app.cfg.keys():
        files = app.get_infiles(prod_id, tag)
        print("##### " + prod_id + "[" + tag + "]" + " #####")
        if len(files) > 0:
            for f in iter(files):
                print(os.path.basename(f))
        else:
            print("None")
            sys.exit(0)


def main():
    app = DataSeeker()
    v_files = app.get_infiles(sys.argv[1], sys.argv[2])

    for f in iter(v_files):
        print("\"" + os.path.basename(f) + "\",")


if __name__ == "__main__":
    # main()
    test()
