import streamlit as st
import sqlite3
import chess.pgn
import streamlit_chess
import io

from dotenv import load_dotenv
load_dotenv()  # Carga las variables del archivo .env


DB_PATH = os.environ.get("CHESS_TRAINER_DB", "chess_trainer.db")

if not DB_PATH or not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"❌ Database not found or CHESS_TRAINER_DB unset: {DB_PATH}")

st.set_page_config(page_title="Elite Game Explorer", layout="wide")
st.title("♟️ Elite Game Explorer")

# Conectar a la base de datos
def get_connection():
    return sqlite3.connect(DB_PATH)

# Cargar opciones únicas para los filtros
def get_filter_options():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT white_player FROM games ORDER BY white_player")
    white_players = [r[0] for r in cursor.fetchall() if r[0]]

    cursor.execute("SELECT DISTINCT black_player FROM games ORDER BY black_player")
    black_players = [r[0] for r in cursor.fetchall() if r[0]]

    cursor.execute("SELECT DISTINCT eco FROM games ORDER BY eco")
    ecos = [r[0] for r in cursor.fetchall() if r[0]]

    cursor.execute("SELECT DISTINCT opening FROM games ORDER BY opening")
    openings = [r[0] for r in cursor.fetchall() if r[0]]

    cursor.execute("SELECT DISTINCT event FROM games ORDER BY event")
    events = [r[0] for r in cursor.fetchall() if r[0]]

    conn.close()
    return white_players, black_players, ecos, openings, events

# Filtros
white_players, black_players, ecos, openings, events = get_filter_options()

with st.sidebar:
    st.header("🔍 Filters")
    wp = st.selectbox("White Player", ["Any"] + white_players)
    bp = st.selectbox("Black Player", ["Any"] + black_players)
    eco = st.selectbox("ECO Code", ["Any"] + ecos)
    opening = st.selectbox("Opening", ["Any"] + openings)
    event = st.selectbox("Event", ["Any"] + events)
    limit = st.slider("Limit results", 1, 100, 10)

# Construir query SQL
query = "SELECT id, white_player, black_player, result, event, date, eco, opening FROM games WHERE 1=1"
params = []
if wp != "Any":
    query += " AND white_player = ?"
    params.append(wp)
if bp != "Any":
    query += " AND black_player = ?"
    params.append(bp)
if eco != "Any":
    query += " AND eco = ?"
    params.append(eco)
if opening != "Any":
    query += " AND opening = ?"
    params.append(opening)
if event != "Any":
    query += " AND event = ?"
    params.append(event)

query += " LIMIT ?"
params.append(limit)

# Ejecutar query y mostrar resultados
conn = get_connection()
cursor = conn.cursor()
cursor.execute(query, params)
results = cursor.fetchall()
conn.close()

st.subheader(f"🔎 Found {len(results)} game(s)")

selected_game = None
for i, row in enumerate(results):
    gid, wp, bp, result, evt, date, eco, opn = row
    with st.expander(f"{wp} vs {bp} ({result}) - {evt}, {date} [{eco} - {opn}]"):
        if st.button(f"View Game #{gid}", key=f"btn_{gid}"):
            selected_game = gid

# Mostrar partida seleccionada
if selected_game:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pgn FROM games WHERE id = ?", (selected_game,))
    pgn_data = cursor.fetchone()[0]
    conn.close()

    st.subheader("📜 PGN")
    st.code(pgn_data, language="pgn")

    st.subheader("♟️ Interactive Board")
    game = chess.pgn.read_game(io.StringIO(pgn_data))
    board = game.board()
    moves = list(game.mainline_moves())

    if "move_index" not in st.session_state:
        st.session_state.move_index = 0

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⏮️ Back") and st.session_state.move_index > 0:
            st.session_state.move_index -= 1
    with col3:
        if st.button("Next ⏭️") and st.session_state.move_index < len(moves):
            st.session_state.move_index += 1

    with col2:
        autoplay = st.checkbox("▶ Auto-play", value=False)

    if autoplay and st.session_state.move_index < len(moves):
        import time
        time.sleep(0.5)
        st.session_state.move_index += 1
        st.experimental_rerun()

    for move in moves[:st.session_state.move_index]:
        board.push(move)

    streamlit_chess.render(board)
    st.caption(f"Showing position after move {st.session_state.move_index} of {len(moves)}")
    if st.session_state.move_index < len(moves):
        next_move = moves[st.session_state.move_index]
        st.markdown(f"**Next Move:** {board.san(next_move)}")
    else:
        st.markdown("**End of Game**")