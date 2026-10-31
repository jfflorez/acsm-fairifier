# -*- coding: utf-8 -*-

"""
Description :
    This file implements a class for reading pcf files. This format is the one used to drive the applications at Icare.
    The class reads the pcf file and build a dictionnary of it after reformation of the parametres

    example : python3 pcf_reader.py /home/pascal/depot/calipso_framework/pcf_reader/test.pcf

Author(s) :
    AERIS/ICARE Nicolas PASCAL, nicolas-dot-pascal-at-univ-hyphen-lille-dot-fr

License :
  This file must be used under the terms of the CeCILL.
  This source file is licensed as described in the file COPYING, which
  you should have received as part of this distribution.  The terms
  are also available at
  http://www.cecill.info/licences/Licence_CeCILL_V2-en.txt

History:
--------
v0.0.2 : 12/06/2009
 - Move static attributes to instance ones.

v0.0.1 : 29/05/2009
 - Update to fix a Deprecation Warning when raising exceptions
 - change some constants names EXIT_SUCCESS -> EXIT_SUCCESS
 - aggregate ERROR_FLAGS (ERROR_FLAG_INPUTS, ERROR_FLAG_PROCESS, ERROR_FLAG_GENERIC) into EXIT_FAILURE
 - change tabulations to 4 spaces

v0.0.0 : 02/04/2007
 - creation
"""

import os.path
import sys

__VERSION__ = "0.0.2"
__AUTHOR__ = "Nicolas PASCAL (nicolas.pascal@icare.univ-lille1.fr)"

##### RETURN CODES #####
EXIT_FAILURE = 1  # unsuccessful return code
EXIT_SUCCESS = 0  # successful return code


class PcfReader:
    @staticmethod
    def reencode(txt, encoding="utf-8"):
        """
        @brief format the given variable ID to manage non ascii characters, strip it, replace break returns by spaces
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

    def __init__(self, pcf_file="", enable_seq=True):
        """
        @brief constructor
        @param pcf_file the configuration to decode, in an ascii format
        @param enable_seq if True, automatically parse list entries
        """
        # init the configuration entries dictionnary
        self.cfg_dic = {}
        # list of dictionary keys, in the ordzer they had been encountered
        self.cfg_dic_order = []
        # sets the file tokens to use
        self.seq_start = '('  # the character that starts a sequence
        self.seq_end = ')'  # the character that ends a sequence
        self.seq_separator = ','  # the character that separates 2 values of a sequence
        self.key_val_separator = '='  # the character that separates a key from a value
        self.comment = '#'  # the character that begins a comment

        # validate inputs
        if (pcf_file == "" or not os.path.exists(pcf_file)):
            raise ValueError("Invalid PCF File : " + pcf_file)
        self.enable_seq = enable_seq
        self.parse_pcf_file(pcf_file)

    def parse_pcf_file(self, pcf_file):
        """
        parse the pcf file and fill the config dictionnary
        """
        f = None  # read file pointer
        try:
            f = open(pcf_file)
            line = f.readline()
            while (line != ""):
                # remove trailing and heading whitespaces and EOF
                line = line.strip(" " + os.linesep)
                if (line != "" and line[0] != self.comment):
                    # the line contains significant data (not a comment or an
                    # empty line)
                    # 1 split max must be done if the value also contains a
                    # separator
                    elts = line.split(self.key_val_separator, 1)
#                     print elts
                    key = elts[0].strip()
                    val = elts[1]
                    # now parse the value
                    tmp_val = val.strip()  # remove whitespaces
                    if (tmp_val != ""):  # not EOF
                        # valid value
                        if (not self.enable_seq or tmp_val[0] != self.seq_start):
                            # the value is not a sequence or sequence disabled
                            # -> will be directly added to the dictionnary
                            val = tmp_val
                        else:
                            # the value is a sequence -> read the lines until
                            # an end sequence character is found
                            val = ""
                            # remove EOL decorations
                            tmp_val = tmp_val.strip(" " + os.linesep)
                            while (not tmp_val.endswith(self.seq_end)):
                                val += tmp_val
                                # read next line
                                line = (f.readline())
                                if (line == ""):  # EOF reached
                                    # wrong file format : sequence started but
                                    # never ended until the EOF
                                    raise ValueError(
                                        "ParsePcfFileError while reading " + pcf_file)
                                tmp_val = line.strip(" " + os.linesep)
                            if not tmp_val.endswith(self.seq_end):
                                # EOF reached or end of sequence not found ->
                                # error
                                raise ValueError(
                                    "ParsePcfFileError while reading " + pcf_file)
                            val += tmp_val
                            # format the sequence
                            val = self.format_sequence(val)
#                             print "aps "+val
                        # add the "decoded" value to the dictionnary
                        self.cfg_dic[key] = val
                        self.cfg_dic_order.append(key)
                # prepare for next line
                line = f.readline()
        except:
            f.close()
            raise
        f.close()

    def format_sequence(self, _s):
        """
        format a string that represents a sequence : mainly remove spaces between ',', eventually remove the last ','...
        """
        s = _s  # local copy of s
        elt = ""  # an element of the sequence

        # eventually remove start_sequence and end_of_sequence tokens
        s = s.strip(" " + self.seq_start + self.seq_end + os.linesep)
        # split the sequence string using the sequence separator token
        elt_seq = s.split(self.seq_separator)
        # reconstruct the sequence without excedent characters
        cleaned_s = self.seq_start
        for elt in elt_seq:
            elt = elt.strip(" " + os.linesep + self.seq_separator)
            if (elt != ""):
                cleaned_s += elt.strip() + self.seq_separator  # also remove element whitespaces
        # remove last sequence separator token, which is excedent
        if cleaned_s.endswith(self.seq_separator):
            cleaned_s = cleaned_s[:-1]
        # close the sequence
        cleaned_s += self.seq_end
        return cleaned_s

    def get(self, key):
        """
        Access to a decoded parametre
        If the key is invalid, throws a KeyError exception
        """
        return self.cfg_dic[key]

    def v_get(self, key):
        """
        Access to a decoded parametre which contains a sequence. The method will return a python3 sequence object
        If the key parametre contain no data, will return an empty sequence
        If the key is invalid, throws a KeyError exception
        """
        return self.cfg_dic[key][1:-1].split(",")

    def show(self):
        """
        prints out the configuration dictionnary
        """
        for key in list(self.cfg_dic.keys()):
            print((key + "->" + self.cfg_dic[key]))

##############  MAIN  ###############


def main():
    """
    Main script
    """

    pcf_file = "/home/pascal/depot/calipso_framework/pcf_reader/test/test2.pcf"
    pcf_reader = PcfReader(pcf_file)
#     pcf_reader.show()

    # non empty sequence
    print((pcf_reader.v_get("CAL_IIR_L2_Track")))
    # empty sequence
    print((pcf_reader.v_get("CAL_LID_L2_05kmCLay")))

    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
