import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from db.postgres_utils import read_postgres_sql

load_dotenv()  # Carga las variables del archivo .env

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")

if not DB_URL:
    raise ValueError("❌ CHESS_TRAINER_DB_URL environment variable not set")

st.set_page_config(page_title="Elite Stats", layout="wide")
st.title("📊 Elite Game Statistics")

# Conectar a la base de datos y cargar como DataFrame


def load_data():
    return read_postgres_sql("SELECT * FROM games")


df = load_data()

# Filtros en sidebar
with st.sidebar:
    st.header("🔍 Filters")
    players = sorted(set(df['white_player']).union(set(df['black_player'])))
    selected_player = st.selectbox("Filter by Player", ["Any"] + players)
    selected_opening = st.selectbox(
        "Filter by Opening", ["Any"] + sorted(df['opening'].dropna().unique()))
    selected_event = st.selectbox(
        "Filter by Event", ["Any"] + sorted(df['event'].dropna().unique()))
    search_term = st.text_input("Search text in opening/player/event")

# Aplicar filtros
if selected_player != "Any":
    df = df[(df['white_player'] == selected_player) |
            (df['black_player'] == selected_player)]
if selected_opening != "Any":
    df = df[df['opening'] == selected_opening]
if selected_event != "Any":
    df = df[df['event'] == selected_event]
if search_term:
    search_lower = search_term.lower()
    df = df[df.apply(lambda row: search_lower in str(row['white_player']).lower() or
                     search_lower in str(row['black_player']).lower() or
                     search_lower in str(row['opening']).lower() or
                     search_lower in str(row['event']).lower(), axis=1)]

# Exportación
st.sidebar.markdown("---")
if not df.empty:
    csv = df.to_csv(index=False)
    st.sidebar.download_button(
        "⬇ Export as CSV", csv, "filtered_games.csv", "text/csv")
    pgns = "\n\n".join(df['pgn'].dropna().tolist())
    st.sidebar.download_button(
        "⬇ Export as PGN", pgns, "filtered_games.pgn", "text/plain")

# Mostrar KPIs
st.markdown("### 🔢 Key Stats")
col1, col2, col3 = st.columns(3)
col1.metric("Total Games", len(df))
col2.metric("Unique Players", len(
    set(df['white_player']).union(df['black_player'])))
col3.metric("Distinct Openings", df['opening'].nunique())

# Gráficos
st.markdown("### 📌 Stats Breakdown")
tabs = st.tabs(["Openings", "Results", "ELO", "Events"])

with tabs[0]:
    st.subheader("Most Played Openings")
    top_openings = df['opening'].value_counts().head(10)
    fig, ax = plt.subplots()
    top_openings.plot(kind='barh', ax=ax)
    ax.invert_yaxis()
    ax.set_xlabel("Games")
    st.pyplot(fig)

with tabs[1]:
    st.subheader("Results Distribution")
    results = df['result'].value_counts()
    fig, ax = plt.subplots()
    results.plot(kind='pie', autopct='%1.1f%%', ax=ax)
    ax.set_ylabel("")
    st.pyplot(fig)

with tabs[2]:
    st.subheader("Average ELO by Color")
    white_elo_avg = df['white_elo'].dropna().mean()
    black_elo_avg = df['black_elo'].dropna().mean()
    fig, ax = plt.subplots()
    ax.bar(['White', 'Black'], [white_elo_avg,
           black_elo_avg], color=['#eee', '#444'])
    ax.set_ylabel("Average ELO")
    st.pyplot(fig)

with tabs[3]:
    st.subheader("Top Events by Game Count")
    event_counts = df['event'].value_counts().head(10)
    fig, ax = plt.subplots()
    event_counts.plot(kind='bar', ax=ax)
    ax.set_ylabel("Games")
    ax.set_xlabel("Event")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    st.pyplot(fig)
# Mostrar DataFrame filtrado
st.markdown("### 📊 Filtered Games Data")
if not df.empty:
    st.dataframe(df)
else:
    st.warning("No games match the selected filters.")
# Mostrar FEN de la primera partida filtrada
if not df.empty:
    st.markdown("### ♟️ FEN of First Filtered Game")
    first_fen = df.iloc[0]['fen']
    st.code(first_fen, language='text')
# Mostrar PGN de la primera partida filtrada
if not df.empty:
    st.markdown("### 📜 PGN of First Filtered Game")
    first_pgn = df.iloc[0]['pgn']
    st.code(first_pgn, language='text')
