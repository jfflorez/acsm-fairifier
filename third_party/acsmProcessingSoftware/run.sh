#!/bin/bash

#  AERIS/ICARE production script. Useful only in ACMCC centralized infrastructure

SCRIPTDIR=$( dirname $(readlink -f $0))

# --- NRT process of a bunch of instruments
# prod_ids="GIF_ACSM_140113_RAW_NRT"
# for prod_id in ${prod_ids}
# do
#     echo "python3 ${SCRIPTDIR}/src/uploader/uploader.py -p ${prod_id} -v"
#     python3 ${SCRIPTDIR}/src/uploader/uploader.py -p ${prod_id} -v
# done

# --- process one data sample, NRT submissions
python3 src/rawto012b.py tests/PuydeDome/in/PuydeDome_ACSM-13_2021.txt ~/test

python3 src/rawto012b.py /DATA/LIENS/GROUND-BASED/SIRTA_Palaiseau/ACSM-140113/ACSM_RAW-NRT/2023/2023_03_02/SIRTA_ACSM-140113_2023030218*.txt ~/test


# --- process one data sample, regular yearly process
# python3 src/rawto012.py tests/PuydeDome/in/PuydeDome_ACSM-13_2021.txt tests/PuydeDome/in/PuydeDome_ACSM-13_FLAGS_2021.txt  ~/test





