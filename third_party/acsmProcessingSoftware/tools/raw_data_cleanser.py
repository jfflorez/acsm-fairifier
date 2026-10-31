# -*- coding: utf-8 -*-

"""
Description :
-------------
    Tool to sort raw ACSM data by increasing acquisition times

Limitations :
-------------
    -

Usage :
-------
    python3 raw_data_sorter.py <infile>
    
Example:
--------
    python3 ../tests/Milan/in/Milan_ACSM-090_2023.txt
        

Copyright (©) 2023:
-------------------
    Université de Lille ;
    Commissariat à l'énergie atomique et aux énergies alternatives (CEA) ;
    Centre national de la recherche scientifique (CNRS)

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
--------
    v0.0.0 : 2023/03/27
    - creation
"""
import os
import os.path
import sys
import datetime
from collections import OrderedDict

sep = "\t"
ts_fmt = "%Y/%m/%d %H:%M:%S"

# --- read
ifpath = sys.argv[1]
header = ""
data = OrderedDict()
with open(ifpath, "rb") as fd:
    for ilin, lin in enumerate(fd):
        # skip dummy lines
        if ilin == 0:
            header = lin
            continue
        if len(lin.strip()) == 0:
            continue
        # extract timestamp
        s_ts = lin[: lin.find(b"\t")]
        ts = datetime.datetime.strptime(s_ts.decode("utf-8"), ts_fmt)
        # check if record already exists
        if ts in data.keys():
            prev_ilin, prev_lin = data[ts]
            if data[ts][1] == lin:
                msg = "INFO : duplicated record" + os.linesep
            else:
                msg = "WARNING : record with the same timestamp and different data => keep the most recent one" + os.linesep
            msg += "< [L{0:d}]: {1:s}".format(prev_ilin, prev_lin.decode("utf-8"))
            msg += "> [L{0:d}]: {1:s}".format(ilin, lin.decode("utf-8"))
            print (msg)
        data[ts] = (ilin, lin)

# --- write
ofpath = ifpath + "-cleansed"
with open(ofpath, "wb") as fd:
    fd.write(header)
    for key, elts in data.items():
        fd.write(elts[1])

#os.system("meld " + ifpath + " " + ofpath)
