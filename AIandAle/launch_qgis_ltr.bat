@echo off
REM C:\Projects\FunGIS\aiandale\launch_qgis_ltr.bat
set PROJECT_PATH=C:\Projects\FunGIS\aiandale\aiandale.qgz

set OSGEO4W_ROOT=C:\Users\corea\AppData\Local\Programs\OSGeo4W
set QGIS_EXE=qgis-ltr-bin.exe
set APP_DIR=qgis-ltr
set QT_DIR=qt5

call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
if exist "%OSGEO4W_ROOT%\apps\grass\grass85\etc\env.bat" (
    call "%OSGEO4W_ROOT%\apps\grass\grass85\etc\env.bat"
)

path %OSGEO4W_ROOT%\apps\%APP_DIR%\bin;%PATH%
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT:\=/%/apps/%APP_DIR%
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\%APP_DIR%\qtplugins;%OSGEO4W_ROOT%\apps\%QT_DIR%\plugins

cd /d "%OSGEO4W_ROOT%\bin"
start "QGIS" "%OSGEO4W_ROOT%\bin\%QGIS_EXE%" "%PROJECT_PATH%"
exit /b 0
