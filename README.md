# PIXEL CHECK PRO

Sistema científico multiplataforma para el análisis de píxeles defectuosos y calidad de sensores DSLR/Mirrorless a partir de **dark frames**.

PIXEL CHECK PRO automatiza el flujo completo:

* Conversión de archivos RAW (CR2) a TIFF
* Análisis por lote de imágenes
* Detección de *hot pixels* y *dead pixels*
* Estimación de SNR y bit depth
* Generación de reportes en Excel

---

## ✨ Características principales

* ✅ Multiplataforma: **macOS, Linux y Windows**
* ✅ Flujo automático por carpeta (batch)
* ✅ Compatible con cámaras Canon (CR2) y TIFF
* ✅ Uso de `dcraw` para conversión RAW confiable
* ✅ Entornos virtuales (`venv`) para evitar conflictos
* ✅ Reportes reproducibles y auditables

---

## 📂 Estructura del proyecto

```
PIXEL_CHECK_PRO/
│
├── pixel_check.py        # Motor de análisis
├── requirements.txt     # Dependencias Python
├── run.sh               # macOS / Linux / WSL / Git Bash
├── run.bat              # Windows nativo
├── README.md            # Este archivo
└── resultados/          # Reportes generados
```

---

## 🔧 Requisitos

### Generales

* Python **3.9+** (probado hasta 3.13)
* 8 GB RAM recomendados

### macOS

* Homebrew (`brew`)

### Linux

* `apt` (Ubuntu/Debian recomendado)

### Windows

* Python desde [https://www.python.org](https://www.python.org)
* Para CR2 → TIFF:

  * Usar **WSL** o **Git Bash**, o
  * Convertir previamente a TIFF

---

## 🚀 Uso rápido

### macOS / Linux / WSL / Git Bash

```bash
chmod +x run.sh
./run.sh /ruta/a/carpeta_con_CR2_o_TIFF

o bien

bash run.sh /ruta/a/carpeta_con_CR2_o_TIFF

```

### Windows (CMD / PowerShell)

```bat
run.bat C:\ruta\a\carpeta_con_TIFF
```

> ⚠️ En Windows nativo, el script **analiza TIFF**. La conversión CR2 debe hacerse previamente o usando WSL.

---

## 🔄 Flujo de trabajo

1. El usuario indica **una carpeta**
2. El sistema:

   * crea un entorno virtual (`venv`)
   * instala dependencias automáticamente
   * verifica `dcraw`
   * convierte CR2 → TIFF (si aplica)
3. Se analizan **todos los TIFF de la carpeta**
4. Se genera un reporte Excel por lote

---

## 📊 Resultados generados

Por cada ejecución se crea un archivo:

```
resultados/batch_report_YYYYMMDD_HHMMSS.xlsx
```

Incluye, por imagen:

* Bit depth detectado
* Número y porcentaje de hot pixels
* Número y porcentaje de dead pixels
* SNR (dB)
* Advertencias de validez del dark frame

---

## 🧪 Dark frames: recomendaciones

Para resultados confiables:

* ISO fijo
* Tapa del lente colocada
* Sin luz parásita
* Temperatura estable
* Exposición representativa del uso real

El sistema detecta automáticamente **dark frames no válidos** y emite advertencias.

---

## 🛠️ Notas técnicas importantes

### Entornos virtuales (PEP 668)

En macOS y Linux modernos, Python del sistema está protegido.

PIXEL CHECK PRO usa `venv` automáticamente para:

* evitar errores `externally-managed-environment`
* no romper Homebrew / sistema

### Matplotlib

La primera ejecución puede mostrar:

```
Matplotlib is building the font cache
```

Es normal y ocurre solo una vez.

---

## 🧩 Compatibilidad

| Sistema     | Script  | CR2 → TIFF | Análisis |
| ----------- | ------- | ---------- | -------- |
| macOS       | run.sh  | ✅          | ✅        |
| Linux       | run.sh  | ✅          | ✅        |
| Windows     | run.bat | ⚠️ externo | ✅        |
| Windows WSL | run.sh  | ✅          | ✅        |

---

## 📌 Estado del proyecto

✔️ Estable
✔️ Reproducible
✔️ Multiplataforma real
✔️ Apto para uso técnico / científico

---

## 📄 Licencia

Uso académico, técnico y personal.

---

## 🤝 Créditos

Henry D. Agudelo-Zamora hdagudeloz@unal.edu.co Desarrollado para análisis avanzado de sensores digitales y control de calidad de cámaras.

---

> Para soporte, mejoras o extensiones (otras marcas RAW, análisis térmico, validación cruzada), continúe el desarrollo sobre esta base.
