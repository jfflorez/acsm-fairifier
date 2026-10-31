# -*- coding: utf-8 -*-
"""
Description :
    Handle generic system calls


Example:

Author(s) :
    AERIS/ICARE Nicolas PASCAL, nicolas-dot-pascal-at-univ-hyphen-lille-dot-fr

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
--------
    v0.0.0 : 2014/04/17
    - creation
"""
import subprocess

from misc import AppContextController

# also print ignored runs
VERBOSE_FULL = False
# dry run if false
__RUN_PROCESS__ = True


def run_app(exe, app, args, run_it=__RUN_PROCESS__):
    """
    @brief run the given application
    @param exe interpreter
    @param app full path to the application
    @param args command line arguments
    @param run_it if true run the process, if false, just run the command line
    """
    # built the command line
    cmd = "%s %s %s" % (exe, app, args)
#     print cmd
    status = AppContextController.EXIT_SUCCESS
    if run_it:
        status = subprocess.call(cmd, shell=True)

        if status == AppContextController.EXIT_FAILURE:
            print("{0:<8s}: {1:s}".format("FAILED", cmd))
        elif status == AppContextController.EXIT_SUCCESS:
            print("{0:<8s}: {1:s}".format("SUCCESS", cmd))
        elif status == AppContextController.EXIT_NO_INPUT:
            if VERBOSE_FULL:
                print("{0:<8s}: missing inputs {1:s}".format("IGNORE", cmd))
        elif status == AppContextController.EXIT_OUTPUT_EXISTS:
            if VERBOSE_FULL:
                print("{0:<8s}: output already exists {1:s}".format("IGNORE", cmd))
        elif status == AppContextController.EXIT_UNSUPPORTED_INPUT:
            if VERBOSE_FULL:
                print("{0:<8s}: unsupported input {1:s}".format("IGNORE", cmd))
        else:
            print("{0:<8s}: unsupported status %d ; {1:d} {2:s}".format(
                "FAILED", status, cmd))
    else:
        print(cmd)
    return status
