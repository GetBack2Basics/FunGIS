@echo off
REM =========================================================================
REM QGIS MCP Desktop Launcher
REM Launches QGIS with proper OSGeo4W path variables and loads the project.
REM =========================================================================

set PROJECT_PATH=C:\projects\fungis\aiandale\aiandale.qgz

REM 1. Detect OSGeo4W Root Directory
if exist "C:\OSGeo4W\bin\o4w_env.bat" (
    set OSGEO4W_ROOT=C:\OSGeo4W
    set QGIS_BAT_NAME=qgis-dev.bat
    set QGIS_EXE_NAME=qgis-dev-bin.exe
    set APP_DIR=qgis-dev
    set QT_DIR=qt6
) else if exist "C:\Users\corea\AppData\Local\Programs\OSGeo4W\bin\o4w_env.bat" (
    set OSGEO4W_ROOT=C:\Users\corea\AppData\Local\Programs\OSGeo4W
    set QGIS_BAT_NAME=qgis-ltr.bat
    set QGIS_EXE_NAME=qgis-ltr-bin.exe
    set APP_DIR=qgis-ltr
    set QT_DIR=qt5
) else (
    echo [ERROR] OSGeo4W installation not found!
    exit /b 1
)

echo Found OSGeo4W at: %OSGEO4W_ROOT%
echo Using launcher: %QGIS_BAT_NAME%

REM 2. Set QGIS/OSGeo4W Environment Variables
call "%OSGEO4W_ROOT%\bin\o4w_env.bat"

if exist "%OSGEO4W_ROOT%\bin\qt6_env.bat" call "%OSGEO4W_ROOT%\bin\qt6_env.bat"
if exist "%OSGEO4W_ROOT%\bin\gdal-dev-py-env.bat" call "%OSGEO4W_ROOT%\bin\gdal-dev-py-env.bat"
if exist "%OSGEO4W_ROOT%\bin\pdal-dev-env.bat" call "%OSGEO4W_ROOT%\bin\pdal-dev-env.bat"

path %OSGEO4W_ROOT%\apps\%APP_DIR%\bin;%PATH%
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT:\=/%/apps/%APP_DIR%
set GDAL_FILENAME_IS_UTF8=YES
set VSI_CACHE=TRUE
set VSI_CACHE_SIZE=1000000
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\%APP_DIR%\qtplugins;%OSGEO4W_ROOT%\apps\%QT_DIR%\plugins

REM 3. Launch QGIS Detached in separate console window
cd /d "%OSGEO4W_ROOT%\bin"
echo Launching QGIS in background...
start "QGIS" "%OSGEO4W_ROOT%\bin\%QGIS_EXE_NAME%" "%PROJECT_PATH%"
echo QGIS launch command sent! Waiting for startup...
exit /b 0
