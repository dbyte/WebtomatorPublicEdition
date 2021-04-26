:: Starts the Webtomator app on Windows
@echo off

:: Store the script's parent directory path
SET parent=%~dp0

echo Switching to directory %parent%
cd %parent% || CALL :exitOnError "Could not change to directory."

echo Activating python virtual environment.
CALL venv_3_7_7\Scripts\activate || CALL :exitOnError "Could not activate python virtual environment."

echo Starting Webtomator app. Happy scraping!
echo ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
python webtomator/webtomator.py || CALL :exitOnError "Could not start Webtomator."

echo Deactivating virtual environment.
CALL deactivate
echo ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

CALL :exit


:: Functions ::

:exitOnError
echo ERROR: %~1
CALL :exit

:exit
:: cd back to user's home directory
cd %HOMEDRIVE%%HOMEPATH%

:: Leave terminal window open after finishing.
cmd /k