@echo OFF
rem run a Python script in a given conda environment from a batch file.

rem It doesn't require:
rem - conda to be in the PATH
rem - cmd.exe to be initialized with conda init

rem Define here the path to your conda installation
set CONDAPATH=E:\anaconda3

rem Define here the name of the environment to be used in this script
set ENVNAME=base

rem set the environment path
if %ENVNAME%==base (set ENVPATH=%CONDAPATH%) else (set ENVPATH=%CONDAPATH%\envs\%ENVNAME%)

rem Activate the conda environment with your specified environment
CALL %CONDAPATH%\Scripts\activate.bat %ENVPATH%
E:\anaconda3\python.exe "E:\My Documents\Google Drive\ProgramCode\Python_Projects\NavigationTools\NavigationTools.pyw"
CALL conda deactivate