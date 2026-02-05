@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo =========================================
echo  PIXEL CHECK PRO - WINDOWS
echo  Analisis cientifico de sensores DSLR
echo =========================================
echo.

:: ===============================
:: ARGUMENTO: CARPETA
:: ===============================
if "%~1"=="" (
    echo Uso:
    echo   run.bat C:\ruta\a\carpeta_con_imagenes
    echo.
    pause
    exit /b 1
)

set INPUT_DIR=%~1

if not exist "%INPUT_DIR%" (
    echo ERROR: La carpeta no existe
    pause
    exit /b 1
)

cd /d "%INPUT_DIR%"
echo Carpeta de trabajo:
echo   %CD%
echo.

:: ===============================
:: VERIFICAR PYTHON
:: ===============================
echo Verificando Python...

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    echo Instale Python desde https://www.python.org
    pause
    exit /b 1
)

:: ===============================
:: ENTORNO VIRTUAL
:: ===============================
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

call venv\Scripts\activate.bat

:: ===============================
:: DEPENDENCIAS
:: ===============================
echo.
echo Instalando dependencias Python...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

:: ===============================
:: VERIFICAR DCRAW
:: ===============================
echo.
echo Verificando dcraw...

where dcraw >nul 2>&1
if errorlevel 1 (
    echo.
    echo ADVERTENCIA:
    echo   dcraw no esta disponible en Windows nativo
    echo.
    echo OPCIONES:
    echo   1) Convertir CR2 a TIFF previamente
    echo   2) Usar WSL o Git Bash
    echo.
    echo Continuando solo con TIFF existentes...
)

:: ===============================
:: VERIFICAR TIFF
:: ===============================
echo.
echo Buscando archivos TIFF...

set TIFF_FOUND=0
for %%f in (*.tif *.tiff) do (
    set TIFF_FOUND=1
)

if "!TIFF_FOUND!"=="0" (
    echo ERROR: No se encontraron archivos TIFF
    echo.
    echo Este script analiza:
    echo   *.tif / *.tiff
    pause
    call venv\Scripts\deactivate.bat
    exit /b 1
)

:: ===============================
:: PRUEBA OPENCV
:: ===============================
echo.
echo Verificando OpenCV...

python - <<EOF
import cv2
print("OpenCV OK:", cv2.__version__)
EOF

if errorlevel 1 (
    echo ERROR: OpenCV no funciona correctamente
    pause
    call venv\Scripts\deactivate.bat
    exit /b 1
)

:: ===============================
:: EJECUTAR ANALISIS
:: ===============================
echo.
echo Iniciando analisis por lote...

python pixel_check.py --batch .

:: ===============================
:: RESULTADO
:: ===============================
if %errorlevel% equ 0 (
    echo.
    echo ANALISIS COMPLETADO
    echo Resultados guardados en la carpeta de salida
) else (
    echo.
    echo ERROR EN EL ANALISIS
    echo Revise los logs generados
)

call venv\Scripts\deactivate.bat
pause
