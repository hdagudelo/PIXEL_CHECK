# PIXEL CHECK PRO

Sistema científico multiplataforma para el análisis de píxeles defectuosos y evaluación  
de la calidad de sensores DSLR/Mirrorless a partir de **dark frames**.

PIXEL CHECK PRO automatiza el flujo completo:

- Conversión de archivos RAW (CR2) a TIFF
- Análisis por lote de imágenes
- Detección de *hot pixels* y *dead pixels*
- Estimación de SNR y profundidad de bits
- Generación de reportes en Excel

English documentation: [README_EN.md](README_EN.md)

---

## ✨ Características principales

- Multiplataforma: **macOS, Linux y Windows**
- Flujo automático por carpeta (batch)
- Compatible con Canon RAW (CR2) y TIFF
- Conversión RAW confiable usando `dcraw`
- Entornos virtuales automáticos (`venv`)
- Reportes reproducibles y auditables
- Sistema multilingüe (`i18n/`)

---

## 📂 Estructura del proyecto

```
PIXEL_CHECK/
├── pixel_check.py      # Motor de análisis
├── requirements.txt    # Dependencias Python
├── run.sh              # macOS / Linux / WSL / Git Bash
├── run.bat             # Windows nativo
├── i18n/               # Archivos de idioma
├── config/             # Configuración del sistema
├── EJEMPLO_USO.md      # Guía de uso
├── README_EN.md        # Documentación en inglés
├── README_ES.md        # Documentación en español
└── LICENSE
```

---

## 🔧 Requisitos

### Generales
- Python **3.9+** (probado hasta 3.13)
- 8 GB RAM recomendados

### macOS
- Homebrew (`brew`) para dependencias externas

### Linux
- `apt` (Ubuntu/Debian recomendado)

### Windows
- Python desde https://www.python.org  
- CR2 → TIFF:
  - Usar **WSL** o **Git Bash**
  - O convertir previamente

---

## 🚀 Uso

### macOS / Linux / WSL / Git Bash

```bash
chmod +x run.sh
./run.sh /ruta/a/carpeta_con_CR2_o_TIFF
```

### Windows (CMD / PowerShell)

```bat
run.bat C:\ruta\a\carpeta_con_TIFF
```

⚠️ Windows nativo analiza solo TIFF.

---

## 🔄 Flujo de trabajo

1. El usuario indica una carpeta
2. El sistema:
   - crea un entorno virtual
   - instala dependencias automáticamente
   - verifica `dcraw`
   - convierte CR2 → TIFF si aplica
3. Se analizan los TIFF
4. Se genera un reporte Excel por lote

---

## 📊 Resultados generados

```
resultados/batch_report_YYYYMMDD_HHMMSS.xlsx
```

Incluye:
- Profundidad de bits detectada
- Hot pixels y dead pixels
- SNR (dB)
- Advertencias de validez

---

## 🧪 Recomendaciones para dark frames

- ISO fijo
- Tapa del lente colocada
- Sin luz parásita
- Temperatura estable
- Exposición representativa

---

## 📄 Licencia

Uso académico, técnico y personal.

---

## 🤝 Créditos

Henry D. Agudelo-Zamora  
hdagudeloz@unal.edu.co
