@echo off
setlocal EnableExtensions

REM ── Localizacion de la configuracion ─────────
set "BATCHDIR=%~dp0"
set "CONFIG_FILE=%BATCHDIR%config_batch.json"

if not exist "%CONFIG_FILE%" (
    echo [ERROR] No se encuentra config_batch.json en: %CONFIG_FILE%
    exit /b 1
)

REM ── Lectura de configuracion (PowerShell + ConvertFrom-Json) ─────────
REM NOTA: .Replace('/', '\') es obligatorio en TODAS las rutas para normalizar barras mixtas JSON -> Windows.
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).working_dir.Replace('/', '\\')"') do set "WORKDIR=%%A"
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).python_executable.Replace('/', '\\')"') do set "PYTHON=%%A"
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).script_path.Replace('/', '\\')"') do set "SCRIPT=%%A"
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).artifact_path.Replace('/', '\\')"') do set "ARTIFACT=%%A"
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).data_source.path.Replace('/', '\\')"') do set "INPUT_DIR=%%A"
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).data_source.filename"') do set "INPUT_FILE=%%A"
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).data_sink.path.Replace('/', '\\')"') do set "OUTPUT_REL=%%A"
for /f "delims=" %%A in ('powershell -NoProfile -Command "(Get-Content '%CONFIG_FILE%' | Out-String | ConvertFrom-Json).data_sink.filename"') do set "FILENAME_PATTERN=%%A"

REM ── Comprobacion de variables criticas ─────────
if "%WORKDIR%"=="" (
    echo [ERROR] WORKDIR no definido en config_batch.json
    exit /b 1
)
if "%PYTHON%"=="" (
    echo [ERROR] python_executable no definido en config_batch.json
    exit /b 1
)
if "%SCRIPT%"=="" (
    echo [ERROR] script_path no definido en config_batch.json
    exit /b 1
)
if "%INPUT_DIR%"=="" (
    echo [ERROR] data_source.path no definido en config_batch.json
    exit /b 1
)
if "%INPUT_FILE%"=="" (
    echo [ERROR] data_source.filename no definido en config_batch.json
    exit /b 1
)
if "%OUTPUT_REL%"=="" (
    echo [ERROR] data_sink.path no definido en config_batch.json
    exit /b 1
)
if "%FILENAME_PATTERN%"=="" set "FILENAME_PATTERN=resultados.csv"

REM ── Composicion de rutas ABSOLUTAS (no dependen del directorio de invocacion) ─────────
set "ABS_SCRIPT=%WORKDIR%\%SCRIPT%"
set "ABS_ARTIFACT=%WORKDIR%\%ARTIFACT%"
set "ABS_INPUT=%WORKDIR%\%INPUT_DIR%\%INPUT_FILE%"
set "ABS_OUTPUT_DIR=%WORKDIR%\%OUTPUT_REL%"
set "OUTPUT_FILE=%ABS_OUTPUT_DIR%\%FILENAME_PATTERN%"

REM ── Validacion de rutas existentes ─────────
if not exist "%ABS_SCRIPT%" (
    echo [ERROR] No existe el script: %ABS_SCRIPT%
    exit /b 1
)
if not exist "%ABS_INPUT%" (
    echo [ERROR] No existe el archivo de entrada: %ABS_INPUT%
    exit /b 1
)
if not exist "%ABS_ARTIFACT%" (
    echo [ERROR] No existe el artefacto del pipeline: %ABS_ARTIFACT%
    exit /b 1
)
if /i not "%PYTHON%"=="python" (
    if not exist "%PYTHON%" (
        echo [ERROR] No existe el ejecutable Python: %PYTHON%
        exit /b 1
    )
)

REM ── Creacion robusta de la carpeta de salida (y todas las intermedias) ─────────
powershell -NoProfile -Command "try { New-Item -ItemType Directory -Force -Path '%ABS_OUTPUT_DIR%' -ErrorAction Stop | Out-Null; exit 0 } catch { Write-Host '[ERROR] No se pudo crear carpeta de salida:' $_.Exception.Message; exit 1 }"
if errorlevel 1 exit /b 1
if not exist "%ABS_OUTPUT_DIR%" (
    echo [ERROR] La carpeta de salida no existe y no se pudo crear: %ABS_OUTPUT_DIR%
    echo Comprueba permisos, antivirus u OneDrive sobre esa ruta.
    exit /b 1
)

REM ── Mensaje de inicio ─────────
echo === [BATCH] Inicio ejecucion: %DATE% %TIME% ===
echo Script: %ABS_SCRIPT%
echo Input:  %ABS_INPUT%
echo Output: %OUTPUT_FILE%
echo.

REM ── Ejecucion del proceso batch ─────────
cd /d "%WORKDIR%"
"%PYTHON%" "%ABS_SCRIPT%" --input "%ABS_INPUT%" --output "%OUTPUT_FILE%"
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
    echo [ERROR] El proceso termino con error. Codigo: %EXITCODE%
    exit /b %EXITCODE%
) else (
    echo [OK] Proceso finalizado correctamente.
)

endlocal
exit /b 0
