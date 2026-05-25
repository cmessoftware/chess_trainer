import streamlit as st
import os
import re
from datetime import datetime
from config_utils import get_valid_paths_from_env

LOGS_DIR =  get_valid_paths_from_env(["LOG_DIR"])[0] 

def get_log_files():
    return sorted([f for f in os.listdir(LOGS_DIR) if f.startswith("log_") and f.endswith(".txt")])

def parse_log_line(line):
    match = re.match(r"📘 \[(.*?)\] (\w+) - (.*)", line)
    if match:
        timestamp, level, message = match.groups()
        return {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
    return None

def load_log(file_path):
    entries = []
    with open(file_path, "r", encoding="utf-8") as f:
        current_entry = None
        for line in f:
            line = line.rstrip()
            parsed = parse_log_line(line)
            if parsed:
                if current_entry:
                    entries.append(current_entry)
                current_entry = parsed
                current_entry["traceback"] = []
            elif current_entry and (line.startswith("Traceback") or line.startswith("  File")):
                current_entry["traceback"].append(line)
        if current_entry:
            entries.append(current_entry)
    return entries

st.title("📘 Visor de Logs - ChessTrainer")

log_files = get_log_files()
if not log_files:
    st.warning("No se encontraron archivos de log.")
    st.stop()

selected_log = st.selectbox("Seleccioná una fecha", log_files, format_func=lambda f: f.replace("log_", "").replace(".txt", ""))

log_entries = load_log(os.path.join(LOGS_DIR, selected_log))

for entry in log_entries:
    color = "red" if entry["level"] == "ERROR" else "black"
    st.markdown(f"<span style='color:{color}'><b>[{entry['timestamp']}] {entry['level']}:</b> {entry['message']}</span>", unsafe_allow_html=True)

    if entry["traceback"]:
        with st.expander("📌 Ver traceback"):
            st.code("\n".join(entry["traceback"]), language="python")
