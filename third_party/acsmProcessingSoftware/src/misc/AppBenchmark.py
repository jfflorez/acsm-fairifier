# -*- coding: utf-8 -*-

"""""

Description :
-------------
    Benchmark decorators

Usage :
-------------
    use decorators around the main function to profile or benchmark execution time

        import AppBenchmark
        ...
        @AppBenchmark.exec_time
        @AppBenchmark.profile

        def main():
            ...
        if __name__ == "__main__":
            main()

Limitations :
-------------

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
    v0.0.0: 2018/01/09
    - creation
"""
import os.path
import time
import cProfile


######################
# Runtime Decorators #
######################

# decorator for high level timing benchmarks
def exec_time(fnct):
    """
    @brief decorator for function time benchmarks
    @param function to be decorated
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        out = fnct(*args, **kwargs)
#         exec_time = time.strftime(
#             "%H:%M:%S", time.gmtime(time.time() - start_time))
        exec_time = time.time() - start_time
#         print exec_time
#         print dir(fnct)
        fnct_id = os.path.basename(fnct.__module__) + "." + fnct.__name__
        print("{exec_time: 12f} : {fnct_id:s}".format(
            fnct_id=fnct_id, exec_time=exec_time))
        return out
    return wrapper

# decorator for high level profiling


def profile(func):
    """
    @brief decorator for function profiling
    @param function to be decorated
    """
    def wrapper(*args, **kwargs):
        prof = cProfile.Profile()
        prof.enable()
        retval = prof.runcall(func, *args, **kwargs)
        prof.disable()
        print()
        prof.print_stats(sort=2)
        return retval
    return wrapper


######################
#     Usage Demo     #
######################

@profile
@exec_time
def test():
    print("> starting...", end=' ')
    time.sleep(5)
    print("done")


if __name__ == "__main__":
    test()
