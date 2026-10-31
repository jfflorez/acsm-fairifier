@echo off

REM start process
echo "- start process -"
cd C:\Users\%USERNAME%\actris_acsm_converter\src\uploader
REM python hourly_uploader.py 2021-04-10T00 -v -x
python uploader.py -v
REM pause