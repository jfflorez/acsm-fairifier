# -*- coding: utf-8 -*-
"""
Description :
    This module aggregates some time conversion functions. Especially, it deals with TAI to UTC leap seconds (or obviously try to)

Author(s) :
    AERIS/ICARE Nicolas PASCAL, nicolas-dot-pascal-at-univ-hyphen-lille-dot-fr

License :
  This file must be used under the terms of the CeCILL.
  This source file is licensed as described in the file COPYING, which
  you should have received as part of this distribution.  The terms
  are also available at
  http://www.cecill.info/licences/Licence_CeCILL_V2-en.txt

History :
--------
v0.1.0 : 2012/07/03
    - add a leap second
v0.0.0 : 2009/06/11
    - creation
"""
# import datetime
from datetime import datetime, timedelta
import math
import time
import calendar

import numpy
import pytz

# --- CONSTANTS --- #
# constant number of leap seconds between the TAI93 start (1st of January
# 1993 at 00:00:00) and the UTC start ()
NSEC_TAI93_START_TO_UTC_START = 27

# constant number of seconds between an epoch time and an TAI93 one, that
# starts the 01/01/1993. Both are linear, instead of UTC time that has
# leap seconds discontinuities
NSEC_EPOCH_TO_TAI93 = 725846400

# number of seconds in a day (that does not contain a leap second). Define
# as a constant for speed
NSEC_DAY = 86400  # 24 * 60 * 60

# Table of the leap seconds between TAI and UTC from the 1st of January 1972 at 00:00:00
# each line is :
# (<start of range, included>, <end of range, excluded>, TAI - UTC leap seconds )
# source : ftp://hpiers.obspm.fr/iers/bul/bulc/UTC-TAI.history
tbl_UTC_2_TAI_leap_sec = [
    (datetime(1972, 1, 1), datetime(1972, 7, 1), 10),
    (datetime(1972, 7, 1), datetime(1973, 1, 1), 11),
    (datetime(1973, 1, 1), datetime(1974, 1, 1), 12),
    (datetime(1974, 1, 1), datetime(1975, 1, 1), 13),
    (datetime(1975, 1, 1), datetime(1976, 1, 1), 14),
    (datetime(1976, 1, 1), datetime(1977, 1, 1), 15),
    (datetime(1977, 1, 1), datetime(1978, 1, 1), 16),
    (datetime(1978, 1, 1), datetime(1979, 1, 1), 17),
    (datetime(1979, 1, 1), datetime(1980, 1, 1), 18),
    (datetime(1980, 1, 1), datetime(1981, 7, 1), 19),
    (datetime(1981, 7, 1), datetime(1982, 7, 1), 20),
    (datetime(1982, 7, 1), datetime(1983, 7, 1), 21),
    (datetime(1983, 7, 1), datetime(1985, 7, 1), 22),
    (datetime(1985, 7, 1), datetime(1988, 1, 1), 23),
    (datetime(1988, 1, 1), datetime(1990, 1, 1), 24),
    (datetime(1990, 1, 1), datetime(1991, 1, 1), 25),
    (datetime(1991, 1, 1), datetime(1992, 7, 1), 26),
    (datetime(1992, 7, 1), datetime(1993, 7, 1), 27),
    (datetime(1993, 7, 1), datetime(1994, 7, 1), 28),
    (datetime(1994, 7, 1), datetime(1996, 1, 1), 29),
    (datetime(1996, 1, 1), datetime(1997, 7, 1), 30),
    (datetime(1997, 7, 1), datetime(1999, 1, 1), 31),
    (datetime(1999, 1, 1), datetime(2006, 1, 1), 32),
    (datetime(2006, 1, 1), datetime(2009, 1, 1), 33),
    (datetime(2009, 1, 1), datetime(2012, 7, 1), 34),
    (datetime(2012, 7, 1), datetime(2015, 7, 1), 35),
    (datetime(2015, 7, 1), datetime(2017, 1, 1), 36),
    (datetime(2017, 1, 1), datetime.utcnow(), 37),
]


def days2dt(days, origin="1970:01:01T00:00:00"):
    """
    @brief convert a time in decimal days to a unix epoch time
    @param days datetime to convert, in decimal days from origin
    @param origin time axis origin, format : %Y-%m-%dT:%H:%M:%S
    """
    dt_origin = datetime.strptime(origin, "%Y-%m-%dT%H:%M:%S")

    frac, ndays = math.modf(days)
    frac, hours = math.modf(frac * 24)
    frac, minutes = math.modf(frac * 60)
    frac, seconds = math.modf(frac * 60)

    dt = dt_origin + timedelta(days=ndays, hours=hours,
                               minutes=minutes, seconds=seconds)
    return dt


def doy2dt(year, doy):
    """
    @brief convert a day of year in decimal day unit and return a datetime
    """
    frac, jday = math.modf(doy)
    frac, hours = math.modf(frac * 24)
    frac, minutes = math.modf(frac * 60)
    frac, seconds = math.modf(frac * 60)
    fmt = "%Y-%jT%H:%M:%SZ"
    dt = datetime.strptime("{0:d}-{1:03d}T{2:02d}:{3:02d}:{4:02d}Z".format(
        year, int(jday), int(hours), int(minutes), int(seconds)), fmt)
    return dt


def matlab2dt(matlab_datenum):
    """
    @brief convert a matlab datenum to a python3 datetime
    """
    day = datetime.fromordinal(int(matlab_datenum))
    dayfrac = timedelta(
        days=matlab_datenum % 1) - timedelta(days=366)
    return day + dayfrac


def matlab2ts(matlab_datenum):
    """
    @brief convert a matlab datenum to a UTC UNIX EPOCH time
    """
    return dt_to_ts(matlab2dt(matlab_datenum))


def local2utc_epoch(local_epoch_time):
    """
    @brief given a naive datetime object, convert it to a UTC datetime. DST changes are managed (if pytz is up to date)
    @param local_epoch_time a local UNIX epoch time
    @param tz a pytz timezone object. Defalut is french tz
    @return utc_epoch_time a UTC datetime
    """
    local_dt = datetime.utcfromtimestamp(local_epoch_time)
    utc_dt = local2utc_dt(local_dt)
    utc_ts = dt_to_ts(utc_dt)
    return utc_ts


def local2utc_dt(local_dt, tz=pytz.timezone("Europe/Paris")):
    """
    @brief given a naive datetime object, convert it to a UTC datetime. DST changes are managed (if pytz is up to date)
    @param dt a datetime object
    @param tz a pytz timezone object. Defalut is french tz
    @return utc_dt a UTC datetime
    """
    local_dt = tz.localize(local_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt


def tai93_to_str(tai93, fmt="%Y-%m-%dT%h:%m:%s"):
    """
    @brief convert a TAI93 time into a UTC string using the given format
    @param tai93 a time in TAI93 convention
    @param fmt string format
    """
    dt = from_TAI93(tai93)
    return dt.strftime(fmt)


def smonth_to_snum(s_in):
    """
    @brief in the given string, replace a month as a string in french to its number on 2 digits and return the string
    @brief sin input string
    @return sout output string with eventual substitutions done
    """
    dsub = {"janvier": "01",
            "fevrier": "02",
            "février": "02",
            "mars": "03",
            "avril": "04",
            "mai": "05",
            "juin": "06",
            "juillet": "07",
            "aout": "08",
            "août": "08",
            "septembre": "09",
            "octobre": "10",
            "novembre": "11",
            "decembre": "12",
            "décembre": "12",
            }

    s_out = s_in
    for k, v in dsub.items():
        s_out = s_out.replace(k, v)
    return s_out


def dt_to_ts(dt):
    """
    @brief convert a datetime object to a unix epoch timestamp (UTC)
    @param dt a datetime
    @return a UNIX EPOCH time, UTC
    """
    return calendar.timegm(dt.timetuple())


def ts2dt(ts):
    """
    @brief convert a unix epoch timestamp (UTC) to a datetime object
    @param ts a UNIX EPOCH time, UTC
    @return a datetime
    """
    return datetime.utcfromtimestamp(ts)


def jday_to_dt(year, jday):
    """
    @brief construct a UTC datetime object from a year and a decimal day from start of year
    @warning fractional part of seconds ignored
    @param year year
    @param jday a a day number from start of year. If float, the day fraction is the the time
    """
    frac, jday = numpy.modf(jday)
    hh, mm, ss = 0, 0, 0
    if (frac != 0):
        # a day fraction is present -> decode it
        frac, hh = numpy.modf(24 * frac)
        frac, mm = numpy.modf(60 * frac)
        frac, ss = numpy.modf(60 * frac)
    s_ts = "{0:d}-{1:03d}T{2:02d}:{3:02d}:{4:02d}Z".format(
        int(year), int(jday), int(hh), int(mm), int(ss))
    return datetime.strptime(s_ts, "%Y-%jT%H:%M:%SZ")


def str_to_utc_epoch(s_ts, fmt="%Y-%m-%d %H:%M:%S UTC"):
    """
    @brief convert a string into a UNIX EPOCH UTC time
    """
    # print (s_ts)
    d = datetime.strptime(s_ts, fmt)
    ts = calendar.timegm(d.timetuple())
    return ts


def utc_epoch_to_str(ts, fmt="%Y-%m-%d %H:%M:%S UTC"):
    """
    @brief convert a UNIX EPOCH time to a string
    """
    return time.strftime(fmt, time.gmtime(ts))


def tai93_to_epoch(time_tai93):
    """
    Convert a TAI93 time (in seconds) to a UNIX EPOCH time
    """
    if numpy.any(time_tai93 < 0):
        raise ValueError(
            "Negative TAI93 time encountered : " + str(time_tai93))
    epoch = time_tai93 + NSEC_EPOCH_TO_TAI93
    return epoch


def get_tai93_leap_sec(t):
    """
    return the number of leap seconds for the given date between UTC and TAI93 time (ie : leap = UTC - TAI)
    @param t a datetime object
    """
    return get_leap_sec(t) - NSEC_TAI93_START_TO_UTC_START


def get_leap_sec(t):
    """
    return the number of leap seconds for a given date between UTC and TAI time (ie : leap = UTC - TAI)
    source : http://hpiers.obspm.fr/eop-pc/earthor/utc/TAI-UTC_tab.html
    @warning Only dates after the 1st of January 1972 at 00:00:00 UTC are supported.
    @param t a datetime object
    """
    if not isinstance(t, datetime):
        raise ValueError("input argument must be a datetime instance")

    # check date validity
    start_of_validity_range = tbl_UTC_2_TAI_leap_sec[0][0]
    end_of_validity_range = tbl_UTC_2_TAI_leap_sec[-1][1]

    if t < start_of_validity_range:
        raise ValueError("Unsupported date " + str(t.strftime("%Y-%m-%dT%H:%M:%S")) + " " +
                         "Only dates later than " + start_of_validity_range.strftime("%Y-%m-%dT%H:%M:%S") + " are supported")
    if t > end_of_validity_range:
        raise ValueError("Unsupported date " + str(t.strftime("%Y-%m-%dT%H:%M:%S")) + " " +
                         "Only dates earlier than " + start_of_validity_range.strftime("%Y-%m-%dT%H:%M:%S") + " are supported because leap seconds are not predictible")

    for start, end, leap in iter(tbl_UTC_2_TAI_leap_sec):
        # print "start", start.strftime ("%Y-%m-%dT%H:%M:%S"), "end",
        # end.strftime ("%Y-%m-%dT%H:%M:%S")
        if t >= start and t < end:
            return leap


def from_TAI93(tai93_time):
    """
    construct a datetime object from a TAI93 timestamp
    """
    d = datetime.utcfromtimestamp(tai93_to_epoch(tai93_time))
    return d


def from_epoch(epoch_time):
    """
    construct a datetime object from an EPOCH time
    UTC is assumed
    """
    if isinstance(epoch_time, numpy.ndarray) or isinstance(epoch_time, list):
        # vectorization
        return [datetime.utcfromtimestamp(t) for t in epoch_time]
    else:
        # numeric supposed
        return datetime.utcfromtimestamp(epoch_time)


def from_calipso_utc(cal_utc_time):
    """
    decode the UTC time as given in CALIPSO datasets and return the corresponding datetime object
    This format is yymmdd.ffffffff where
    - yy is the number of year from 2000 year
    - mm the month in range [1,12]
    - dd the day in range [1,31]
    - .ffffffff the fraction of the day
    """
    # print "cal_utc_time ", cal_utc_time

    # fraction of the day
    frac = cal_utc_time % 1
    # floating point number of seconds from start of day
    tmp = frac * NSEC_DAY

    nhour = int(tmp / 3600)
    tmp %= 3600
    # print "nhour ", nhour

    nmin = int(tmp / 60)
    tmp %= 60
    # print "nmin ", nmin

    sec = int(tmp)
    # print "sec ", sec
    tmp %= 1

    microsec = int(tmp * 1e6)
    # print "microsec ", microsec

    # decode the year
    s = str(int(cal_utc_time))

    yy = 2000 + int(s[:-4])
    mm = int(s[-4:-2])
    dd = int(s[-2:])

    # print "yy ",yy
    # print "mm ",mm
    # print "dd ",dd

    return datetime(yy, mm, dd, nhour, nmin, sec, microsec)


def tai93_to_utc(tai93):
    """
    @brief convert a TAI93 time to its UTC representation, corerected from leap seconds
    """
    dt = from_TAI93(tai93)
    leap = get_tai93_leap_sec(dt)
    return dt - timedelta(seconds=leap)


def main():
    """
    Unit test
    """
    tai93 = 5.112321640582002E8
    print((tai93_to_utc(tai93)))

    utc_cal = 90315.03885484028
    print((from_calipso_utc(utc_cal)))

    tai93 = 5.11232160508044E8
    print((from_TAI93(tai93)))
    tai93 = 5.1123530296104395E8
    print((from_TAI93(tai93)))

    # check CALIPSO UTC time decoding
    # cal_utc = 90101.07405461806 # 2009-01-01 01:46:38.319000 UTC
    # cal_tai93 = 5.04928005319E8 # 2009-01-01 01:46:45.319000

    # print datetime_from_calipso_utc (cal_utc)
    # print from_TAI93 (cal_tai93)
    # print get_tai93_leap_sec (from_TAI93 (cal_tai93)) # +7

    # check the TAI 2 UTC leap seconds table
    # s_format = "%Y-%m-%dT%H:%M:%S"
    # vector of UTC times to check
    # v_s_time = [ "1970-01-01T00:00:00", "1972-01-01T00:00:00", "1990-12-31T23:59:59", "1991-01-01T00:00:00", "1993-01-01T00:00:00", "2009-01-01T00:07:47" ]
    # for s_time in iter(v_s_time) :
    # d = datetime.strptime (s_time, s_format)
    # try :
    # print "Date (UTC) " + s_time + " => TAI - UTC = " + str (get_leap_sec (d))
    # except Exception:
    # print "Date (UTC) " + s_time + " unsupported"

    # Test TAI93 to UNIX EPOCH unit conversion

    # The 3 following values have been read in a CALIPSO LIDAR L1 file to be used a reference test values
    # ref_time = "2009-01-01T00-07-47"
    # time_tai93 = 5.04922072268E8

    # print "----- ref_time : %s -----"%ref_time
    # ref_epoch_struct_time = time.strptime     (ref_time, "%Y-%m-%dT%H-%M-%S")
    # ref_epoch_time        = calendar.timegm(ref_epoch_struct_time)

    # Module functions
    # epoch_time        = tai93_to_epoch (time_tai93)
    # epoch_struct_time = time.gmtime (epoch_time)

    # print "check if " + str (epoch_struct_time) + " == " + str (ref_epoch_struct_time) + " ... ",
    # if (epoch_struct_time == ref_epoch_struct_time) :
    # print "SUCCESS"
    # else :
    # print "FAILED"

    # print "check if " + str (epoch_time) + " == " + str (ref_epoch_time) + " ... ",
    # if (epoch_time == ref_epoch_time) :
    # print "SUCCESS"
    # else :
    # print "FAILED"


if __name__ == "__main__":
    main()
