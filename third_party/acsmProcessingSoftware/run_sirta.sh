#!/bin/bash

#  AERIS/ICARE production script. Useful only in ACMCC centralized infrastructure

SCRIPTDIR=$( dirname $(readlink -f $0))

# list of product to handle
#prod_ids="GIF_ACSM_140113_RAW_NRT MEL_ACSM_140143_RAW_NRT VDA_ACSM_140157_RAW_NRT SMR_ACSM_140104_RAW_NRT BRC_ACSM_140110_RAW_NRT ATH_ACSM_140139_RAW_NRT"
# prod_ids="VDA_ACSM_140157_RAW_NRT"
# prod_ids="DUB_ACSM_140133_RAW_NRT"
# prod_ids="GIF_ACSM_140113_RAW_NRT MEL_ACSM_140143_RAW_NRT"
prod_ids="GIF_ACSM_140113_RAW_NRT"

for prod_id in ${prod_ids}
do
    echo "python3 ${SCRIPTDIR}/src/uploader/uploader.py -p ${prod_id} -v"
    python3 ${SCRIPTDIR}/src/uploader/uploader.py -p ${prod_id} -v
done
