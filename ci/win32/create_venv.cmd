rem Short script to initialize virtual environment using venv and pip
rem @echo off

pushd .
cd /D "%~dp0"
py -3.11 -m pip install virtualenv
py -3.11 -m venv ..\..\venv
call ..\..\venv\Scripts\activate.bat
python -m pip install pip-tools setuptools wheel
REM call .\update_dependencies.cmd
call .\install_dependencies.cmd
call .\install_dev.cmd
call .\check_java_jdk.cmd
popd
