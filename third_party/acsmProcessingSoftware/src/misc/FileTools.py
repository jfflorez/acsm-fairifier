# -*- coding: utf-8 -*-

"""

Description :
    Contains some functions to operate on files :
       check_file : test if the file exists and if it can be opened in a given mode

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
v0.0.0 : 8/06/2009
 - creation

"""
import io
import os
import os.path
import time


def unix_to_os_path(unix_path):
    """
    @brief normalize a UNIX like path to the platform one
    """
    os_path = unix_path.replace("~", os.path.expanduser('~'))
    os_path = os_path.replace("/", os.sep)
    return os_path


def reencode(txt, encoding="utf-8"):
    """
    @brief format the given string to manage non ascii characters, strip it, replace break returns by spaces
    @param var_id variable name
    @return the reformatted variable name
    """
    if isinstance(txt, int):
        return str(txt)

    # replace non unicode characters to "standard unicode replacement
    # character", then remove these unsupported characters
    uni_rpl_chr = chr(0xFFFD)
    if isinstance(txt, str):
        txt = str(txt, encoding, errors="replace")
    txt = txt.replace(uni_rpl_chr, "")
    return str.encode(txt.strip().replace("\n", " "), "utf-8").strip()


def check_dir(dirname, mode="r"):
    """
    Check if the specified directory exists, if it is really a directory or a link to a directory, and not a file or a link to a file, and if it can be accessed in the given mode.
    If one condition is not filled, raise an exception, else return True
    @param dirname a directory path
    @param mode the mode that the dirname can be accessed in. Default is "r". Can be any combination of 'r', 'w' and 'x'
    """
    if dirname is None:
        raise ValueError("Can't open a None directory")

    if not os.path.exists(dirname):
        raise ValueError("Unexisting directory " + dirname)

    if not os.path.isdir(dirname):
        raise ValueError(dirname + " is not a directory")

    try:
        flags = os.F_OK
        if mode.find("r") != -1:
            flags |= os.R_OK
        if mode.find("w") != -1:
            flags |= os.W_OK
        if mode.find("x") != -1:
            flags |= os.X_OK
        if not os.access(dirname, flags):
            raise ValueError("Invalid access rights" + dirname)
    except:
        raise ValueError("Directory " + dirname +
                         " can't be opened in mode '" + mode + "'")
    return True


def check_file(fname, mode="r"):
    """
    Check if the file exists, if it is really a file or a link to a file and not a directory, and if it can be opened in the given mode.
    If one condition is not filled, raise an exception, else return True
    @param fname a file path
    @param mode the mode that the file can be opened in. Default is "r". Can be "r" and/or "w" and/or "x"
    """
    if fname is None:
        raise ValueError("Can't open a None file")

    if not os.path.exists(fname):
        raise ValueError("Unexisting file " + fname)

    if not os.path.isfile(fname):
        raise ValueError(fname + " is not a file or a link to a regular file")

    f = None
    try:
        f = open(fname, mode)
        f.close()
    except:
        raise ValueError("File " + fname +
                         " can't be opened in mode '" + mode + "'")
    # finally :
        # if f is not None :
        # f.close()
    return True


def touch(path):
    """
    @brief equivalent to UNIX touch funcxtion
    @Source : http://code.activestate.com/recipes/576915-touch/
    """
    now = time.time()
    try:
        # assume it's there
        os.utime(path, (now, now))
    except os.error:
        open(path, "w").close()
        os.utime(path, (now, now))


def get_lines(fname):
    """
    @brief read the whole content of the file and return it into a list of lines
    @param fname input file path
    """
    with open(fname) as fd:
        return fd.readlines()


def get_file_content(fname, to_unix_eol=False):
    """
    @brief read the whole content of the file and return it in a buffer
    @param fname input file path
    @param to_unix_eol if True, format to unix end of line
    """
    f = open(fname)
    buf = None
    try:
        buf = f.read()
    finally:
        f.close()
    # - format end of line
    if to_unix_eol:
        buf = "\n".join(buf.splitlines())
    return buf


def write_file_content(fname, buf):
    """
    @brief write the whole content in the file in ascii mode
    @param fname input file path
    # @param buf text content to write
    """
    f = open(fname, "w")
    try:
        buf = f.write(buf)
    finally:
        f.close()


def get_line(fname, ilin, encoding="utf-8"):
    """
    @brief read one line of the file and return it 
    @param fname input file path
    @param ilin indice of the line to read
    @return the line as a string
    """
    with open(fname, "rb") as fd:
        for _ilin, lin in enumerate(fd):
            if _ilin < ilin:
                continue
            if _ilin == ilin:
                return lin.decode(encoding)


def get_nlines(fname):
    """
    @brief return the number of lines of a file
    @param fname input file path
    @return the number of lines
    """
    nlines = 0
    with io.open(fname, errors="ignore", newline='\n') as fd:
        for _ in fd:
            nlines += 1
    return nlines
