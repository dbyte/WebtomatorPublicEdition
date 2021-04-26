#!/usr/bin/env bash
# Starts the Webtomator app on mac os

function exitOnError {
  echo "Error: $1"
  exit
}

cd "$(dirname "$0")" || exitOnError "Could not change to directory."

echo "Activating Python's virtual environment."
source venv_3_8_2/bin/activate || exitOnError "Could not activate python virtual environment."

echo "Starting Webtomator app."
echo "::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::"

python3 webtomator/webtomator.py || exitOnError "Could not start Webtomator."
deactivate
echo "::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::"
echo "Exiting bash script."
