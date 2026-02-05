# PIXEL CHECK PRO

Scientific cross-platform system for defective pixel analysis and sensor quality assessment  
in DSLR/Mirrorless cameras using **dark frames**.

PIXEL CHECK PRO automates the full workflow:

- RAW (CR2) to TIFF conversion
- Batch image processing
- Hot pixel and dead pixel detection
- SNR and bit depth estimation
- Excel report generation

Spanish documentation: [README_ES.md](README_ES.md)

---

## ✨ Key Features

- Cross-platform: **macOS, Linux, Windows**
- Folder-based batch workflow
- Canon RAW (CR2) and TIFF support
- Reliable RAW conversion using `dcraw`
- Automatic virtual environments (`venv`)
- Reproducible and auditable reports
- Multilingual system (`i18n/`)

---

## 📂 Project Structure

```
PIXEL_CHECK/
├── pixel_check.py      # Analysis engine
├── requirements.txt    # Python dependencies
├── run.sh              # macOS / Linux / WSL / Git Bash
├── run.bat             # Native Windows
├── i18n/               # Language files
├── config/             # System configuration
├── EJEMPLO_USO.md      # Usage example
├── README.md           # English documentation
├── README_ES.md        # Spanish documentation
└── LICENSE
```

---

## 🔧 Requirements

### General
- Python **3.9+** (tested up to 3.13)
- 8 GB RAM recommended

### macOS
- Homebrew (`brew`) for external dependencies

### Linux
- `apt` (Ubuntu/Debian recommended)

### Windows
- Python from https://www.python.org  
- CR2 → TIFF:
  - Use **WSL** or **Git Bash**
  - Or convert externally beforehand

---

## 🚀 Usage

### macOS / Linux / WSL / Git Bash

```bash
chmod +x run.sh
./run.sh /path/to/folder_with_CR2_or_TIFF
```

### Windows (CMD / PowerShell)

```bat
run.bat C:\path\to\folder_with_TIFF
```

⚠️ Native Windows analyzes TIFF only.

---

## 🔄 Workflow

1. User provides a folder
2. System automatically:
   - creates a virtual environment
   - installs dependencies
   - checks `dcraw`
   - converts CR2 → TIFF if needed
3. TIFF images are analyzed
4. Excel batch report is generated

---

## 📊 Output

Each execution generates:

```
resultados/batch_report_YYYYMMDD_HHMMSS.xlsx
```

Per image:
- Detected bit depth
- Hot pixel and dead pixel counts
- SNR (dB)
- Dark frame validity warnings

---

## 🧪 Dark Frame Recommendations

- Fixed ISO
- Lens cap on
- No stray light
- Stable temperature
- Representative exposure

Invalid dark frames are detected automatically.

---

## 📄 License

Academic, technical and personal use.

---

## 🤝 Credits

Henry D. Agudelo-Zamora  
hdagudeloz@unal.edu.co
