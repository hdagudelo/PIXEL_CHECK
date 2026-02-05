#!/usr/bin/env bash
set -e

# ======================================
# PIXEL CHECK PRO - MULTIPLATAFORMA
# ======================================

INPUT_DIR="$1"

if [ -z "$INPUT_DIR" ]; then
  echo "Uso:"
  echo "  ./run.sh /ruta/a/carpeta_con_CR2_o_TIFF"
  echo ""
  echo "Windows: usar WSL o Git Bash"
  exit 1
fi

if [ ! -d "$INPUT_DIR" ]; then
  echo "❌ La ruta no existe o no es una carpeta"
  exit 1
fi

cd "$INPUT_DIR"
echo "📂 Carpeta de trabajo: $(pwd)"

# ======================================
# DETECTAR SISTEMA
# ======================================
OS="unknown"
case "$OSTYPE" in
  linux-gnu*) OS="linux" ;;
  darwin*) OS="macos" ;;
  msys*|cygwin*) OS="windows" ;;
esac

echo "🖥️ Sistema detectado: $OS"

# ======================================
# PYTHON
# ======================================
echo "🐍 Verificando Python..."

if command -v python3 &>/dev/null; then
  PYTHON=python3
elif command -v python &>/dev/null; then
  PYTHON=python
else
  echo "❌ Python no encontrado"
  exit 1
fi

echo "✔ Python: $($PYTHON --version)"

# ======================================
# ENTORNO VIRTUAL (CLAVE)
# ======================================
echo "📦 Preparando entorno virtual..."

if [ ! -d "venv" ]; then
  $PYTHON -m venv venv
fi

# Activar venv
source venv/bin/activate

# ======================================
# DEPENDENCIAS PYTHON
# ======================================
echo "📦 Instalando dependencias Python..."

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# ======================================
# DCRAW
# ======================================
echo "🔍 Verificando dcraw..."

if ! command -v dcraw &>/dev/null; then
  echo "⚠️ dcraw no encontrado"

  case "$OS" in
    linux)
      sudo apt update
      sudo apt install -y dcraw
      ;;
    macos)
      if ! command -v brew &>/dev/null; then
        echo "❌ Homebrew no está instalado"
        exit 1
      fi
      brew install dcraw
      ;;
    windows)
      echo "❌ dcraw no soportado automáticamente en Windows"
      echo "👉 Use WSL o convierta CR2 a TIFF previamente"
      ;;
  esac
fi

# ======================================
# CONVERSIÓN CR2 → TIFF (si existen)
# ======================================
echo "🔄 Convirtiendo CR2 a TIFF (si aplica)..."

shopt -s nullglob
CR2_FILES=(*.CR2 *.cr2)

for f in "${CR2_FILES[@]}"; do
  echo "  ▶ $f"
  dcraw -4 -D -T "$f"
done

# ======================================
# VERIFICAR TIFF
# ======================================
TIFF_FILES=(*.tif *.tiff)

if [ ${#TIFF_FILES[@]} -eq 0 ]; then
  echo "❌ No se encontraron archivos TIFF para analizar"
  deactivate
  exit 1
fi

echo "🖼️ TIFF encontrados: ${#TIFF_FILES[@]}"

# ======================================
# PRUEBA OPENCV
# ======================================
echo "🧪 Verificando OpenCV..."

python - <<EOF
import cv2
print("✔ OpenCV OK:", cv2.__version__)
EOF

# ======================================
# ANALISIS
# ======================================
echo "📊 Iniciando análisis por lote..."

python pixel_check.py --batch .

deactivate
echo "✅ PROCESO COMPLETADO"
