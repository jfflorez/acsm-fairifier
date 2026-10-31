@echo off
REM set conda_root='C:\\Users\\jepetit\\Anaconda3'
REM echo '- load conda env -'
REM call %conda_root%\\Scripts\\activate.bat %conda_root%
echo '- start process -'
cd C:\\Users\\nowak_n\\Downloads\\ACTRIS_ACSM_CONVERTER_202311\\actris_acsm_converter\\
python src\\rawto012.py data\\JFJ\\in\\JFJ_ACSM-017_2023.txt data\\JFJ\\in\\JFJ_ACSM-017_FLAGS_2023.txt data\\JFJ\\out\\
pause
