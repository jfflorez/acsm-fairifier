@echo off

REM start process
echo "- start process -"
cd C:\Users\%USERNAME%\actris_acsm_converter
REM python hourly_uploader.py 2021-04-10T00 -v -x
python src/rawto012.py tests/SIRTA/in/SIRTA_ACSM-140113_2021.txt tests/SIRTA/in/SIRTA_ACSM-140113_FLAGS_2021.txt ~/test
rem  python3 src/rawto012.py tests/PuydeDome/in/PuydeDome_ACSM-13_2021.txt tests/PuydeDome/in/PuydeDome_ACSM-13_FLAGS_2021.txt  ~/test
pause