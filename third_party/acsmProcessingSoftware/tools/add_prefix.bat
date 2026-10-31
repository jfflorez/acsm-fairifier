for /f %%a IN ('dir /b /s "C:\Users\nico\actris_acsm_converter\tests\COPDD\in\*_ACSM_nativeData.txt"') do copy %%~pa%%~nxa %%~paCOPDD_%%~nxa
pause
