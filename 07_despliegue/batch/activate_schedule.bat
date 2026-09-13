@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "BATCHDIR=%~dp0"
set "CONFIG_FILE=%BATCHDIR%config_batch.json"

if not exist "%CONFIG_FILE%" (
    echo [ERROR] No se encuentra config_batch.json en: %CONFIG_FILE%
    exit /b 1
)

for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).task_name"') do set "TASKNAME=%%A"
if "%TASKNAME%"=="" set "TASKNAME=Caso_Agentes_Scoring_Batch"

REM ── Comprobar si la tarea ya existe ─────────
schtasks /Query /TN "%TASKNAME%" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo La tarea "%TASKNAME%" ya existe.
    set /p RESP=Deseas reemplazarla? (S/N):
    if /i "!RESP!"=="S" (
        call "%BATCHDIR%remove_schedule.bat"
        if errorlevel 1 exit /b 1
    ) else (
        echo [INFO] No se modifica la tarea existente.
        endlocal
        exit /b 0
    )
)

REM ── Crear la tarea ─────────
call "%BATCHDIR%create_schedule.bat"
if errorlevel 1 (
    echo [ERROR] Fallo la creacion de la tarea.
    endlocal
    exit /b 1
)

REM ── Verificacion inmediata ─────────
schtasks /Query /TN "%TASKNAME%"
if errorlevel 1 (
    echo [ERROR] No se pudo verificar la tarea tras crearla.
    endlocal
    exit /b 1
)

echo.
echo [OK] Activacion correcta. El sistema queda autonomo segun la programacion.
endlocal
exit /b 0
