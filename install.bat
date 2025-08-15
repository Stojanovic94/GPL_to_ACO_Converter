@echo off
REM Set path to your Anaconda installation
set ANACONDA_PATH=C:\Users\%USERNAME%\anaconda3
set PATH=%ANACONDA_PATH%;%ANACONDA_PATH%\Scripts;%ANACONDA_PATH%\Library\bin;%PATH%

pip install -r requirements.txt

pause