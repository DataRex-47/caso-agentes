@echo off
setlocal EnableExtensions

set "BATCHDIR=%~dp0"
set "CONFIG_FILE=%BATCHDIR%config_batch.json"

if not exist "%CONFIG_FILE%" (
    echo [ERROR] No se encuentra config_batch.json en: %CONFIG_FILE%
    exit /b 1
)

REM ── Lectura de configuracion (PowerShell + ConvertFrom-Json) ─────────
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).working_dir.Replace('/', '\\')"') do set "WORKDIR=%%A"
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).task_name"') do set "TASKNAME=%%A"
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).schedule.frequency"') do set "FREQ=%%A"
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).schedule.time"') do set "TIMEX=%%A"

if "%WORKDIR%"=="" (
    echo [ERROR] WORKDIR no definido en config_batch.json
    exit /b 1
)
if "%TASKNAME%"=="" set "TASKNAME=Caso_Agentes_Scoring_Batch"
if "%FREQ%"=="" set "FREQ=DAILY"
if "%TIMEX%"=="" set "TIMEX=09:00"

REM ── Ruta absoluta al wrapper (el scheduler solo ejecuta el wrapper) ─────────
set "WRAPPER=%WORKDIR%\07_despliegue\batch\run_manual.bat"

if not exist "%WRAPPER%" (
    echo [ERROR] No existe el wrapper: %WRAPPER%
    exit /b 1
)

echo Creando tarea programada...
echo   Tarea:        %TASKNAME%
echo   Wrapper:      %WRAPPER%
echo   Frecuencia:   %FREQ%
echo   Hora:         %TIMEX%
echo.

REM NO se usa /WD (no soportado en todas las versiones de Windows).
REM NO se usa /RL HIGHEST por defecto.
schtasks /Create ^
  /TN "%TASKNAME%" ^
  /TR "\"%WRAPPER%\"" ^
  /SC %FREQ% ^
  /ST %TIMEX% ^
  /F

if errorlevel 1 (
    echo [ERROR] schtasks devolvio un error al crear la tarea.
    exit /b 1
)

echo.
echo [OK] Tarea programada creada.
endlocal
exit /b 0
