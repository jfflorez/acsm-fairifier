#!/bin/bash

# --- melpitz --- #
user=DE0044
station=melpitz

root=/work_dev/data/pascal/incoming/ACMCC/${station}-acsm/lev0
for f in $( find ${root} -name "*lev0.nas" )
do
    echo ${f}
#     echo "lftp -e \"binary ; cd ACSM ; put ${f} ; ls ; bye\" -u ${user}, sftp://ebas-nrt-submissions.nilu.no"
    lftp -e "cd ACSM ; put ${f} ; bye" -u ${user}, sftp://ebas-nrt-submissions.nilu.no
done

