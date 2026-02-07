import difflib
import pandas as pd
import streamlit as st
import chardet

# ===== Extract Spoken Lines with Encoding Detection =====
def extract_subtitle_text(file):
    if hasattr(file, "read"):  # Streamlit UploadedFile
        raw = file.read()
    else:
        with open(file, "rb") as f:
            raw = f.read()

    detected = chardet.detect(raw)
    encoding = detected['encoding'] if detected['encoding'] else 'utf-8'
    text = raw.decode(encoding, errors="ignore")
    lines = text.splitlines()

    text_lines = []
    for line in lines:
        line = line.strip().lstrip('\ufeff')
        if not line or line.isdigit() or '-->' in line:
            continue
        text_lines.append(line)
    return text_lines

# ===== Keyword Check =====
def check_keywords(original, translated, keywords=[]):
    return [kw for kw in keywords if kw.lower() not in translated.lower()]

# ===== Sliding Window Similarity Match =====
def match_spanish_to_english(spanish_lines, english_lines, window_size=3):
    """
    For each Spanish line, find the best match among next 'window_size' English lines combined.
    Returns a list of matched English lines.
    """
    matched_lines = []
    eng_index = 0
    while_spanish = len(spanish_lines)

    for sp_line in spanish_lines:
        best_similarity = -1
        best_text = ''
        best_len = 1

        # Try next 1..window_size English lines
        for w in range(1, window_size+1):
            if eng_index + w > len(english_lines):
                continue
            combined = " ".join(english_lines[eng_index:eng_index + w])
            sim = difflib.SequenceMatcher(None, sp_line, combined).ratio()
            if sim > best_similarity:
                best_similarity = sim
                best_text = combined
                best_len = w

        matched_lines.append((sp_line, best_text, best_similarity))
        eng_index += best_len  # skip matched English lines

    return matched_lines

# ===== Compare subtitles =====
def compare_subtitles(original_file, translated_file, keywords=[]):
    english_lines = extract_subtitle_text(original_file)
    spanish_lines = extract_subtitle_text(translated_file)

    matched = match_spanish_to_english(spanish_lines, english_lines)

    report = []
    for i, (sp_line, en_line, similarity) in enumerate(matched):
        length_ratio = len(sp_line)/len(en_line) if len(en_line) > 0 else 0
        length_issue = length_ratio < 0.5 or length_ratio > 2
        missing_keywords = check_keywords(en_line, sp_line, keywords)

        report.append({
            'Line #': i+1,
            'Original (English)': en_line,
            'Translated (Spanish)': sp_line,
            'Length Issue': length_issue,
            'Similarity': round(similarity, 2),
            'Missing Keywords': ', '.join(missing_keywords) if missing_keywords else ''
        })

    return pd.DataFrame(report)

# ===== Style the DataFrame =====
def style_subtitle_df(df):
    def highlight_row(row):
        color = ''
        if row['Length Issue']:
            color = '#FF4C4C'  # red
        elif row['Similarity'] < 0.7:
            color = '#FFA500'  # orange
        elif row['Missing Keywords']:
            color = '#FFFF66'  # yellow
        else:
            color = '#C6F7D0'  # green
        return [f'background-color: {color}']*len(row)
    return df.style.apply(highlight_row, axis=1)

# ===== Streamlit App =====
st.title("Subtitle QA Testing")
st.markdown("""
- Handles BOM & auto-detects encoding  
- Matches Spanish lines to multiple English lines if condensed  
- Ignores non-dialogue lines (all-caps/short)  
- Color-coded: red=length, orange=similarity, yellow=missing keywords, green=ok
""")

original_file = st.file_uploader("Original Subtitle (.srt)", type="srt")
translated_file = st.file_uploader("Translated Subtitle (.srt)", type="srt")
keywords_input = st.text_input("Keywords to check (comma separated, optional)", "")

if st.button("Run QA"):
    if not original_file or not translated_file:
        st.error("Please upload both files!")
    else:
        keywords = [k.strip() for k in keywords_input.split(",")] if keywords_input else []
        report_df = compare_subtitles(original_file, translated_file, keywords=keywords)
        st.success("QA Complete!")
        st.dataframe(style_subtitle_df(report_df))

        csv = report_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report as CSV", csv, "subtitle_qc_report.csv", "text/csv")
