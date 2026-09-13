@echo off
setlocal EnableExtensions

set "BATCHDIR=%~dp0"
set "CONFIG_FILE=%BATCHDIR%config_batch.json"

if not exist "%CONFIG_FILE%" (
    echo [ERROR] No se encuentra config_batch.json en: %CONFIG_FILE%
    exit /b 1
)

for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).task_name"') do set "TASKNAME=%%A"
if "%TASKNAME%"=="" set "TASKNAME=Caso_Agentes_Scoring_Batch"

echo Eliminando tarea programada: %TASKNAME%
schtasks /Delete /TN "%TASKNAME%" /F

if errorlevel 1 (
    echo [ERROR] No se pudo eliminar la tarea (puede que no exista).
    exit /b 1
)

echo [OK] Tarea eliminada.
endlocal
exit /b 0
