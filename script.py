import re
import difflib
import pandas as pd
import streamlit as st
import chardet

# ===== SRT Parsing =====
def extract_subtitle_lines_with_time(file):
    if hasattr(file, "read"):
        raw = file.read()
    else:
        with open(file, "rb") as f:
            raw = f.read()

    detected = chardet.detect(raw)
    encoding = detected['encoding'] if detected['encoding'] else 'utf-8'
    text = raw.decode(encoding, errors="ignore")
    lines = text.splitlines()

    subtitles = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.match(r"^\d+$", line):
            i += 1
            if i >= len(lines):
                break
            time_line = lines[i].strip()
            match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", time_line)
            if match:
                start_str, end_str = match.groups()
                def to_sec(t):
                    h, m, s = t.split(":")
                    s, ms = s.split(",")
                    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
                start, end = to_sec(start_str), to_sec(end_str)
            else:
                start, end = 0, 0
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1
            # Auto-detect visual cue: ALL CAPS or short text (title/sign)
            text_combined = " ".join(text_lines)
            if text_combined.isupper() or len(text_combined.split()) <= 3:
                sub_type = "visual_cue"
            else:
                sub_type = "dialogue"
            subtitles.append({
                "start": start,
                "end": end,
                "text": text_combined,
                "type": sub_type
            })
        i += 1
    return subtitles

# ===== Keyword Check =====
def check_keywords(original, translated, keywords=[]):
    return [kw for kw in keywords if kw.lower() not in translated.lower()]

# ===== Alignment =====
def match_spanish_to_english(spanish_lines, english_lines, window_size=3):
    english_dialogue = [e for e in english_lines if e["type"] == "dialogue"]
    matched_lines = []
    eng_index = 0
    for sp_line in spanish_lines:
        if sp_line["type"] != "dialogue":
            matched_lines.append({
                "spanish": sp_line,
                "english": [],
                "similarity": 1.0
            })
            continue

        best_similarity = -1
        best_len = 1
        for w in range(1, window_size+1):
            if eng_index + w > len(english_dialogue):
                continue
            combined = " ".join([e["text"] for e in english_dialogue[eng_index:eng_index + w]])
            sim = difflib.SequenceMatcher(None, sp_line['text'], combined).ratio()
            if sim > best_similarity:
                best_similarity = sim
                best_len = w

        matched_lines.append({
            "spanish": sp_line,
            "english": english_dialogue[eng_index:eng_index+best_len],
            "similarity": best_similarity
        })
        eng_index += best_len
    return matched_lines

# ===== Comfort Score =====
def compute_comfort_score(sp_text, en_text, duration):
    if duration <= 0:
        return 0
    chars = len(sp_text)
    cps = chars / duration

    # CPS score (ideal 12-17 cps)
    if cps <= 12:
        cps_score = 100
    elif cps <= 17:
        cps_score = 100 - (cps - 12) * 10
    else:
        cps_score = max(0, 100 - (cps - 17) * 10)

    length_ratio = len(sp_text) / len(en_text) if len(en_text) > 0 else 1
    if 0.8 <= length_ratio <= 1.2:
        length_score = 100
    else:
        length_score = max(0, 100 - abs(length_ratio - 1) * 100)

    duration_score = int(duration / 1.0 * 100) if duration < 1 else 100

    score = int((0.5*cps_score + 0.3*length_score + 0.2*duration_score))
    return min(max(score,0),100)

# ===== Export SRT =====
def seconds_to_srt_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def save_srt(subtitles, filename="edited.srt"):
    lines = []
    for idx, sub in enumerate(subtitles, 1):
        start = seconds_to_srt_time(sub["start"])
        end = seconds_to_srt_time(sub["end"])
        lines.append(str(idx))
        lines.append(f"{start} --> {end}")
        lines.append(sub["text"])
        lines.append("")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# ===== QA Report =====
def generate_report(spanish_subs, english_subs, keywords=[]):
    matched = match_spanish_to_english(spanish_subs, english_subs)
    report = []
    for i, match in enumerate(matched):
        sp = match["spanish"]
        en_combined_text = " ".join([e["text"] for e in match["english"]])
        duration = sp["end"] - sp["start"]
        chars = len(sp["text"])
        cps = round(chars / duration, 2) if duration > 0 else 0

        if sp["type"] != "dialogue":
            status = "ℹ️ Visual cue / skipped"
            comfort = 100
            missing_keywords = ""
        else:
            length_ratio = len(sp["text"]) / len(en_combined_text) if len(en_combined_text) > 0 else 0
            length_issue = length_ratio < 0.5 or length_ratio > 2
            speed_issue = cps > 20
            missing_keywords = ", ".join(check_keywords(en_combined_text, sp["text"], keywords))

            if length_issue:
                status = "❌ Length issue"
            elif speed_issue:
                status = "⚠️ Speed too high"
            elif missing_keywords:
                status = "🟡 Missing keywords"
            else:
                status = "✅ OK"

            comfort = compute_comfort_score(sp["text"], en_combined_text, duration)

        report.append({
            "Line #": i+1,
            "Status": status,
            "Original (English)": en_combined_text,
            "Translated (Spanish)": sp["text"],
            "Start": sp["start"],
            "End": sp["end"],
            "Duration": round(duration,2),
            "CPS": cps,
            "Comfort Score": comfort,
            "Type": sp["type"],
            "Missing Keywords": missing_keywords,
            "Similarity": round(match["similarity"], 2)
        })
    return pd.DataFrame(report)

# ===== Style =====
def style_subtitle_df(df):
    def highlight_row(row):
        if row['Status'].startswith("❌"):
            color = '#F8D7DA'
        elif row['Status'].startswith("⚠️"):
            color = '#FFF3CD'
        elif row['Status'].startswith("🟡"):
            color = '#FFF9C4'
        elif row['Status'].startswith("ℹ️"):
            color = '#D0E3F0'
        else:
            if row['Comfort Score'] >= 80:
                color = '#E8F5E9'
            elif row['Comfort Score'] >= 50:
                color = '#FFF9C4'
            else:
                color = '#F8D7DA'
        return [f'background-color: {color}; color: #000']*len(row)
    return df.style.apply(highlight_row, axis=1)

# ===== Streamlit =====
st.title("Subtitle QA & Editor (English + Spanish)")

st.markdown("""
- Edit both English & Spanish subtitles  
- Mark visual cues (titles, signs, captions)  
- Run QA: CPS, length, similarity, missing keywords  
- Comfort Score shows reading comfort (0–100)  
- Export edited SRTs and CSV report
""")

original_file = st.file_uploader("Original English Subtitle (.srt)", type="srt")
translated_file = st.file_uploader("Translated Spanish Subtitle (.srt)", type="srt")
keywords_input = st.text_input("Keywords to check (comma separated, optional)", "")

if st.button("Load Subtitles"):
    if not original_file or not translated_file:
        st.error("Please upload both files!")
    else:
        keywords = [k.strip() for k in keywords_input.split(",")] if keywords_input else []
        english_subs = extract_subtitle_lines_with_time(original_file)
        spanish_subs = extract_subtitle_lines_with_time(translated_file)
        st.session_state["english_subs"] = english_subs
        st.session_state["spanish_subs"] = spanish_subs
        st.session_state["keywords"] = keywords
        st.success("Subtitles loaded! Scroll below to edit.")

# ===== Editable tables =====
def subtitle_editor(subs, lang):
    edited_subs = []
    for i, sub in enumerate(subs):
        col1, col2, col3 = st.columns([5,2,2])
        with col1:
            sub_text = st.text_input(f"{lang} Line {i+1}", value=sub["text"], key=f"{lang}_text_{i}")
        with col2:
            sub_type = st.selectbox(f"Type", options=["dialogue","visual_cue"], index=0 if sub["type"]=="dialogue" else 1, key=f"{lang}_type_{i}")
        with col3:
            st.write(f"{round(sub['start'],2)} --> {round(sub['end'],2)} sec")
        sub["text"] = sub_text
        sub["type"] = sub_type
        edited_subs.append(sub)
    return edited_subs

if "english_subs" in st.session_state and "spanish_subs" in st.session_state:
    st.subheader("English Subtitles")
    st.session_state["english_subs"] = subtitle_editor(st.session_state["english_subs"], "English")
    st.subheader("Spanish Subtitles")
    st.session_state["spanish_subs"] = subtitle_editor(st.session_state["spanish_subs"], "Spanish")

    if st.button("Run QA"):
        df_report = generate_report(st.session_state["spanish_subs"], st.session_state["english_subs"], st.session_state["keywords"])
        st.dataframe(style_subtitle_df(df_report), use_container_width=True, height=600)

        csv = df_report.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV Report", csv, "subtitle_qc_report.csv", "text/csv")

        st.download_button("Export Edited English SRT", lambda: save_srt(st.session_state["english_subs"], "edited_english.srt"), "edited_english.srt")
        st.download_button("Export Edited Spanish SRT", lambda: save_srt(st.session_state["spanish_subs"], "edited_spanish.srt"), "edited_spanish.srt")
