# 🎛️ FL Studio Project Name Manager

A sleek **CustomTkinter** desktop app that scans your FL Studio project folders and instantly shows you what's inside — no more clicking through dozens of `Project_1`, `Project_2`, `Project_3`… directories just to find your beat names.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2+-purple)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📂 **Browse & Scan** | Select your FL Studio projects root folder and scan all subdirectories |
| 🔄 **Refresh (F5)** | Re-scan the same folder after editing — no need to browse again |
| 🔍 **Deep Scan** | Recursively search nested folder structures |
| 🏷️ **Smart Status** | **Named ✓** (has audio/MIDI exports) · **Unnamed** (FLP only) · **Empty** |
| 🎼 **MIDI Support** | Recognizes `.mid` / `.midi` files as finished project indicators |
| 📦 **Export Names** | Prominently displays exported file names on each project card |
| 🔎 **Search & Filter** | Live search bar + filter by status (All / Named / Unnamed / Empty) |
| 📊 **Excel Export** | One-click export to a color-coded `.xlsx` report with summary sheet |
| 🌙 **Dark Theme** | Beautiful dark UI with hover effects and color-coded status badges |

---

## 📸 How It Works

1. **Select** your FL Studio projects folder (e.g. `E:\FL_Projects\2026\`)
2. **Scan** — the app reads every subfolder looking for `.flp` files
3. **Status detection** — if a folder has `.mp3`, `.wav`, `.mid`, `.ogg`, `.flac`, or `.aiff` files alongside the `.flp`, it's marked as **Named ✓** (exported/finished)
4. **Browse results** — each project gets a visual card showing the project name, FLP count, export file names, and status
5. **Export** — save everything to a styled Excel spreadsheet

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher

### Installation

```bash
# Clone the repo
git clone https://github.com/ChumaSuey/FLStudioProjectNameManager.git
cd FLStudioProjectNameManager

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

---

## 📁 Project Structure

```
FLStudioProjectNameManager/
├── main.py                 # GUI application (CustomTkinter)
├── fl_project_scanner.py   # Core scanner module
├── excel_exporter.py       # Excel export with openpyxl
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🎹 Supported File Types

### Project Files
| Extension | Type |
|---|---|
| `.flp` | FL Studio Project |

### Export Indicators (marks project as "Named ✓")
| Extension | Type |
|---|---|
| `.mp3` | MP3 Audio |
| `.wav` | WAV Audio |
| `.ogg` | OGG Vorbis |
| `.flac` | FLAC Audio |
| `.aiff` / `.aif` | AIFF Audio |
| `.mid` / `.midi` | MIDI |

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `F5` | Refresh / re-scan current folder |

---

## 📊 Excel Export

The exported `.xlsx` file includes:
- **FL Studio Projects** sheet — color-coded table with folder name, project names, FLP count, audio files, status, and full path
- **Summary** sheet — totals for named, unnamed, and empty projects

Status cells are color-coded:
- 🟢 **Green** — Named (has exports)
- 🔴 **Red** — Unnamed (no exports)
- 🟡 **Yellow** — Empty (no FLP files)

---

## 🛠️ Built With

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — Modern UI toolkit for Python
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel file generation
- [Pillow](https://python-pillow.org/) — Image support

---

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

---

Made with 🎶 for FL Studio producers who have too many projects and too little time.
