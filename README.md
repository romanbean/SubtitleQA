# Subtitle QA & Editor (English + Spanish)

**Subtitle QA & Editor** is a Python-based tool for **subtitle quality assurance and editing**, designed for **English-Spanish media localization**. It helps content creators, localization teams, and accessibility engineers ensure subtitles are accurate, readable, and comfortable for viewers — especially for **deaf and hard-of-hearing audiences**.  

---

## Features

- **Editable English & Spanish subtitles**  
  - Edit dialogue lines and visual cues directly in the app.
- **Visual cue detection**  
  - Automatically detects **titles, signs, captions, and short all-caps text**.  
  - Skips visual cues during QA to avoid false mismatch reports.  
- **Subtitle QA metrics**  
  - **Line similarity** between English and Spanish subtitles  
  - **Length ratio and reading speed (CPS)**  
  - **Comfort score** (0–100) indicating viewer reading comfort  
  - **Keyword presence checks** (optional)  
- **Color-coded QA table** for easy identification of issues:  
  - ✅ OK  
  - ⚠️ Reading speed too high  
  - ❌ Length issue  
  - 🟡 Missing keywords  
  - ℹ️ Visual cues / skipped  
- **Export functionality**  
  - Download **edited SRT files** (English & Spanish)  
  - Download **QA report as CSV**  

---

## Demo Screenshot

<img width="1231" height="844" alt="SubtitleQAEditorDemo" src="https://github.com/user-attachments/assets/ae859578-c4b2-42d7-a6e7-757b4e1cf8f4" />

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/subtitle-qa-editor.git
cd subtitle-qa-editor
```
2. Create a virual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```
3. Install dependencies
```bash
pip install -r requirements.txt
```
4. Run the app
```bash
streamlit run script.py
```

## Usage
- Upload English (.srt) and Spanish (.srt) subtitle files.
- Optionally enter keywords to verify in translations.
- Edit subtitle text and type (dialogue or visual_cue).
- Click Run QA to:
- - Highlight issues
- - Calculate CPS and comfort score
- - Generate a CSV report
- - Export edited subtitles and QA report.

## How it Works

Parsing subtitles:

- Automatically handles BOM & encoding detection.

- Detects visual cues for skipping in alignment.

Alignment & QA:

- Matches Spanish lines with English dialogue using sliding window similarity.

- Skips visual cues to prevent false positives.

- Computes length ratio, reading speed, similarity, and comfort score.

Export:

- Full SRT export for both languages.

- CSV export of QA metrics.

## Why This Project Matters

**Accessibility:** Improves subtitle reading comfort for deaf and hard-of-hearing viewers.

**Efficiency:** Automates repetitive QA tasks for localization teams.

**Accuracy:** Highlights potential translation or formatting issues before publishing content.

## Future Improvements

Timeline view to visualize dialogue vs visual cues over time.

Automated suggestions for line splits or speed adjustments.

Integration with machine translation APIs for instant QA of translations.

## Tech Stack

Python 3.x

Streamlit
 for UI

Pandas
 for data processing

difflib
 for text similarity

chardet
 for encoding detection
