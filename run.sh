#!/bin/bash
echo "=== PIXEL CHECK PRO v1.4 ==="
echo "Sistema científico de análisis de sensores DSLR"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 no encontrado"
    exit 1
fi

# Crear/activar entorno virtual
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

source venv/bin/activate

# Instalar dependencias
echo "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Solicitar imagen
echo ""
echo "Ingrese la ruta de la imagen .tif a analizar:"
read -p "Ruta: " image_path

if [ -z "$image_path" ]; then
    echo "No se ingresó ruta"
    exit 0
fi

if [ ! -f "$image_path" ]; then
    echo "Archivo no encontrado: $image_path"
    exit 1
fi

# Ejecutar análisis
echo "Analizando imagen..."
python3 pixel_check.py "$image_path"

# Mostrar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ANÁLISIS COMPLETADO"
    echo "📊 Resultados guardados en Excel y JSON"
else
    echo ""
    echo "❌ ERROR EN EL ANÁLISIS"
    echo "Ver pixel_check.log para detalles"
fi

deactivate
