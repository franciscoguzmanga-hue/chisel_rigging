@echo off

set "MAYA_VERSION=2024"
set "CUSTOM_SCRIPT_PATH=D:\python_advanced\alembic_exporter"
set "MAYA_SCRIPT_PATH=%USERPROFILE%\Documents\maya\%MAYA_VERSION%\scripts;%CUSTOM_SCRIPT_PATH%"

start "" "C:\Program Files\Autodesk\Maya%MAYA_VERSION%\bin\maya.exe"

