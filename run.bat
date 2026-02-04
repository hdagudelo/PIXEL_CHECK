@echo off
echo === PIXEL CHECK PRO v1.0 ===
echo Sistema científico de análisis de sensores DSLR
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    pause
    exit /b 1
)

:: Crear entorno virtual
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

call venv\Scriptsctivate.bat

:: Instalar dependencias
echo Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt

:: Solicitar imagen
echo.
set /p image_path=Ingrese la ruta de la imagen .tif a analizar: 

if "%image_path%"=="" (
    echo No se ingresó ruta
    pause
    exit /b 0
)

if not exist "%image_path%" (
    echo Archivo no encontrado: %image_path%
    pause
    exit /b 1
)

echo Analizando imagen...
python pixel_check.py "%image_path%"

:: Resultado
if %errorlevel% equ 0 (
    echo.
    echo ✅ ANÁLISIS COMPLETADO
    echo 📊 Resultados guardados en Excel y JSON
) else (
    echo.
    echo ❌ ERROR EN EL ANÁLISIS
    echo Ver pixel_check.log para detalles
)

call venv\Scripts\deactivate.bat
pause