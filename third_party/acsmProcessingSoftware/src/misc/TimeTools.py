# -*- coding: utf-8 -*-

"""
Description :
    Set of time manipulation tools

Author(s) :
    CGTD/UDEV Nicolas PASCAL nicolas.pascal@icare.univ-lille1.fr

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
    2018/09/04 : creation
"""

import re
import datetime
import calendar
import numpy
import dateutil.relativedelta

from . TimeConverter import ts2dt


class TimeTools(object):
    # few regexp
    re_year = re.compile("^(?P<year>[0-9]{4})$")
    re_month = re.compile("^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})$")
    re_day = re.compile(
        "^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})$")
    re_time_iso8601 = re.compile(
        "^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})T(?P<hours>[0-9]{2}):(?P<minutes>[0-9]{2}):(?P<seconds>[0-9]{2})Z$")

    s_time_sql_fmt = "%Y-%m-%d %H:%M:%S"
    s_time_iso8601_fmt = "%Y-%m-%dT%H:%M:%SZ"

    s_time_iso8601 = "{year:d}-{month:02d}-{day:02d}T{hours:02d}:{minutes:02d}:{seconds:02d}Z"

    def __init__(self):
        object.__init__(self)

    @staticmethod
    def get_ndays(year, month=None):
        """
        @brief return the number of days of the given year or month if month is not None
        """
        if month is None:
            # number of days in year
            ndays = 365
            if calendar.isleap(year):
                ndays += 1
            return ndays
        else:
            # number of days in month
            return calendar.monthrange(year, month)[1]

    @staticmethod
    def get_range(tstart, tend=None, outfmt=s_time_iso8601_fmt):
        """
        @brief based on tstart, tend, build the time range limits as iso UTC seconds
        @param tstart requested UTC time range, start of range if tend is specified. Can be YYYY, YYYY-MM, YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
        @param tend requested UTC end of time range, if tstart is YYYY-MM-DDTHH:MM:SSZ
        @param output format, using strptime convention
        @return (tstart, tend) as formatted strings
        """
        # make sure of input type (so year can be passed as integer)
        if not isinstance(tstart, str):
            tstart = str(tstart)

        # yearly range
        re_m = TimeTools.re_year.match(tstart)
        if re_m is not None:
            year = int(re_m.group("year"))
            start = datetime.datetime(year, 1, 1, 0, 0, 0)
            ndays = TimeTools.get_ndays(year)
            dt = datetime.timedelta(days=ndays)
            end = start + dt
            return (start.strftime(outfmt), end.strftime(outfmt))

        # monthly range
        re_m = TimeTools.re_month.match(tstart)
        if re_m is not None:
            year = int(re_m.group("year"))
            month = int(re_m.group("month"))
            start = datetime.datetime(year, month, 1, 0, 0, 0)
            ndays = TimeTools.get_ndays(year, month)
            dt = datetime.timedelta(days=ndays)
            end = start + dt
            return (start.strftime(outfmt), end.strftime(outfmt))

        # daily range
        re_m = TimeTools.re_day.match(tstart)
        if re_m is not None:
            year = int(re_m.group("year"))
            month = int(re_m.group("month"))
            day = int(re_m.group("day"))
            start = datetime.datetime(year, month, day, 0, 0, 0)
            ndays = 1
            dt = datetime.timedelta(days=ndays)
            end = start + dt
            return (start.strftime(outfmt), end.strftime(outfmt))

        # explicit time range limits
#         try:
        if TimeTools.re_time_iso8601.match(tstart) is None or tend is None or TimeTools.re_time_iso8601.match(tend) is None:
            raise ValueError(
                "ERROR: invalid time range [{0:s}, {1:s}]".format(str(tstart), str(tend)))

        start = datetime.datetime.strptime(
            tstart, TimeTools.s_time_iso8601_fmt)
        end = datetime.datetime.strptime(
            tend, TimeTools.s_time_iso8601_fmt)

        if (start > end):
            raise ValueError("ERROR: start of time range ({0:s}) if after end {1:s}".format(
                str(start), str(end)))

        return (start.strftime(outfmt), end.strftime(outfmt))

    @staticmethod
    def build_end_acq(start_acq, dt):
        """
        @brief when no end_acq set, compute it based of next record tart time and dt
        @param start_acq start of acquisition time vector (unix epoch time)
        @param dt default dt. For end_acq - start_acq gretaer than 2*dt, end_acq of start + dt will be used
        @return the reconstructed end of acquisition

        """
        diff_start_acq = numpy.diff(start_acq)
        end_acq = numpy.empty_like(start_acq)
        end_acq[:-1] = start_acq + diff_start_acq
        end_acq[-1] = start_acq[-1] + dt

        # if end of acquisition time higher than next record start time detected, set end time
        # to next record start time
        diff_acq_range = end_acq - start_acq
        s_end_acq_too_high = diff_acq_range[:-1] > (2 * dt)
        if numpy.any(s_end_acq_too_high):
            end_acq[:-1][s_end_acq_too_high] = start_acq[:-
                                                         1][s_end_acq_too_high] + dt
        return end_acq


def get_period_code(start, end):
    """
    Returns the closest approximation of a periode code.
    e.g.:

    Parameters:
        start    UTC epoch start time of interval
        end      UTC epoch end time of interval
    Returns:
        rescode
        None if difference is < 0.0005 sec
    Credits:
        adapted from time_period.py file in ebas-io library: https://git.nilu.no/ebas/ebas-io
    """
    start = ts2dt(start)
    end = ts2dt(end)
    tot_sec = (end - start).total_seconds()
    GREGORIAN_DAYS = 365 + (1 / 4) - (1 / 100) + (1 / 400)
    y_real = tot_sec / (GREGORIAN_DAYS * 24 * 60 * 60.0)
    y_est = int(round(y_real))
    # if exact y --> return y
    if y_est and \
       abs((end - (start + dateutil.relativedelta.relativedelta(years=y_est)))
           .total_seconds()) < 1.0:
        return '{}y'.format(y_est)
    # if > 3y --> return rounded y
    if y_est >= 3:
        return '{}y'.format(y_est)

    # if exact month --> return mo
    mo_est = int(round(tot_sec / (GREGORIAN_DAYS * 24 * 60 * 60.0 / 12.0)))
    if mo_est and \
       abs((end - (start + dateutil.relativedelta.relativedelta(months=mo_est)))
           .total_seconds()) < 1.0:
        return '{}mo'.format(mo_est)

    # if exact week --> return w
    w_real = tot_sec / (7 * 24 * 60 * 60.0)
    w_est = int(round(w_real))
    if w_est and abs(tot_sec - w_est * 7 * 24 * 60 * 60.0) < 1.0:
        return '{}w'.format(w_est)

    # 2 y +- 3w -> rounded y
    if y_est == 2 and \
       abs((end - (start + dateutil.relativedelta.relativedelta(years=y_est)))
           .total_seconds()) < (3 * 7 * 24 * 60 * 60.0):
        return '{}y'.format(y_est)
    # 1 y +- 1w -> rounded y
    if y_est == 1 and \
       abs((end - (start + dateutil.relativedelta.relativedelta(years=y_est)))
           .total_seconds()) < (7 * 24 * 60 * 60.0):
        return '{}y'.format(y_est)

    # if >= 2y --> round mo
    if y_est >= 2:
        return '{}mo'.format(mo_est)

    # mo +-0.5d --> round mo
    if mo_est and \
       abs((end - (start + dateutil.relativedelta.relativedelta(months=mo_est)))
           .total_seconds()) <= (12 * 60 * 60.0):
        return '{}mo'.format(mo_est)

    # w +-0.5d --> round w
    if w_est and abs(tot_sec - w_est * 7 * 24 * 60 * 60) <= (12 * 60 * 60.0):
        return '{}w'.format(w_est)

    # mo >= 3 and +-1d --> round mo
    if mo_est >= 3 and \
       abs((end - (start + dateutil.relativedelta.relativedelta(months=mo_est)))
           .total_seconds()) <= (24 * 60 * 60.0):
        return '{}mo'.format(mo_est)

    # w >= 12 and +-1d --> round w
    if w_est >= 12 and abs(tot_sec - w_est * 7 * 24 * 60 * 60) < (24 * 60 * 60.0):
        return '{}w'.format(w_est)

    # mo >= 3 --> round mo
    if mo_est >= 3:
        return '{}mo'.format(mo_est)

    d_real = tot_sec / (24 * 60 * 60.0)
    d_est = int(round(d_real))
    # exact d --> return d
    if d_est and abs(tot_sec - d_est * 24 * 60 * 60.0) < 1.0:
        return '{}d'.format(d_est)

    # w >= 3 and +-2d --> round w
    if w_est >= 3 and abs(tot_sec - w_est * (7 * 24 * 60 * 60.0)) < (2 * 24 * 60 * 60.0):
        return '{}w'.format(w_est)

    # d >= 4 --> return rounded d
    if d_real > 4.0:
        return '{}d'.format(d_est)

    h_real = tot_sec / (60 * 60.0)
    h_est = int(round(h_real))
    # h >= 48 --> return rounded h or
    # h >= 5 +-5mn --> return rounded h
    # h >= 1 +-30sec --> return rounded h
    if h_est >= 24 or \
       (h_est >= 5 and abs(tot_sec - (h_est * (60 * 60.0))) < 300.0) or \
       (h_est >= 1 and abs(tot_sec - (h_est * (60 * 60.0))) < 30):
        return '{}h'.format(h_est)

    mn_real = tot_sec / (60.0)
    mn_est = int(round(mn_real))
    # exact mn --> return mn
    if mn_est and abs(tot_sec - mn_est * 60.0) < 1.0:
        return '{}mn'.format(mn_est)

    # h >= 5 --> return rounded h
    if h_est >= 5:
        return '{}h'.format(h_est)

    # mn +-5s --> return mn
    if mn_est and abs(tot_sec - mn_est * 60) < 5.0:
        return '{}mn'.format(mn_est)

    # h >= 1 --> return rounded h
    if h_est >= 3:
        return '{}h'.format(h_est)

    # if >= 0.5, use s
    if tot_sec >= 0.5:
        return "{}s".format(int(round(tot_sec)))

    # if between 0.5 ms and 500 ms: use ms
    if tot_sec >= 0.0005:
        return "{}ms".format(int(round(tot_sec * 1000)))

    return None


def test():
    """
    Unit test
    """
    for ts in [2018, "2018-01", "2018-01-01", "aaa", ("2018-01-01T12:56:51Z", None), ("2018-01-01T12:56:51Z", "2018-01-12T17:36:03Z"), ("2018-02-01T12:56:51Z", "2018-01-12T17:36:03Z")]:
        tend = None
        if isinstance(ts, tuple):
            tstart, tend = ts
        else:
            tstart = ts
        print("> tstart:", str(tstart), "tend:", str(tend))

        try:
            start, end = TimeTools.get_range(tstart, tend)
            print("  range: ", start, "->", end)
        except ValueError as e:
            print(e)
        print()


if __name__ == "__main__":
    test()
