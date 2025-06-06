import os
import streamlit as st
import chess
import chess.svg
from pathlib import Path
from modules.utils import render_svg_board
from db.repository.study_repository import StudyRepository
from modules.study_generator import StudyGenerator
from fpdf import FPDF
from pages.components.file_uploader import upload_file

import dotenv
dotenv.load_dotenv()  

#TODO: No funciona el alta de archivos pgn.

PGN_PATH = os.environ.get("PGN_PATH")


# Inicializar repositorio y generador
repo = StudyRepository()
generator = StudyGenerator(repo)
studies = repo.get_all_studies()

# 📥 Uploader en el sidebar
st.sidebar.markdown("---")
st.sidebar.header("📥 Subir nuevo PGN")
uploaded_file = upload_file(label="📂 Subí un archivo PGN", type="pgn",file_path=PGN_PATH, content=True)

if uploaded_file:
    try:
        pgn_text = uploaded_file.read().decode("utf-8")
        if not pgn_text.strip().startswith("[Event"):
            st.sidebar.error("❌ El archivo no parece ser un PGN válido.")
            st.stop()
            
        new_study = generator.generate_positions_from_pgn(pgn_text)
        if not new_study:
            st.sidebar.error("❌ No se pudieron generar posiciones desde el PGN.")
            st.stop()
            
        study = {
            "title": new_study.get("title", "Nuevo Estudio Táctico"),
            "description": new_study.get("description", ""),
            "source": new_study.get("source", ""),
            "tags": new_study.get("tags", []),
            "pgn": pgn_text,
            "position_sequence": new_study.get("position_sequence", [])
        }
        
        repo.save_study(study=study)
        st.sidebar.success("✅ Estudio generado y guardado")
        st.experimental_rerun()
    except Exception as e:
        st.sidebar.error(f"❌ Error al procesar el PGN: {e}")

# Si no hay estudios, detener
if not studies:
    st.error("No se encontraron estudios en la base de datos.")
    st.stop()

# Sidebar: selector de estudio
titles = [study['title'] for study in studies]
selected_title = st.sidebar.selectbox("Seleccionar estudio táctico", titles)

# Obtener estudio completo
study_meta = next((s for s in studies if s['title'] == selected_title), None)
study = repo.get_study_by_id(study_meta['study_id'])

if not study:
    st.error("No se pudo cargar el estudio.")
    st.stop()

# Si no tiene posiciones, generarlas desde el PGN original
if not study.get("position_sequence"):
    study = generator.generate_from_study(study)
    repo.save_study(study)
    st.success("Estudio actualizado con posiciones desde el PGN original.")

st.title(study['title'])
st.markdown(f"**Etiquetas:** {', '.join(study['tags'])}")
st.markdown(f"[🔗 Fuente original]({study['source']})")
st.markdown(study['description'])

# Estado de navegación
pos_seq = study['position_sequence']
if 'study_index' not in st.session_state:
    st.session_state['study_index'] = 0

# Validar índice actual
index = st.session_state['study_index']
if index >= len(pos_seq):
    index = 0
    st.session_state['study_index'] = 0

position = pos_seq[index]
fen = position['fen']

# Visualización única de tablero actual
board = chess.Board(fen)
svg = chess.svg.board(board=board, size=400)
render_svg_board(svg)

# Mostrar comentario editable
comment = position.get('comment', '')
new_comment = st.text_area("✏️ Comentario para esta posición", comment, height=100, key=f"comment_{index}")
if new_comment != comment:
    position['comment'] = new_comment
    st.success("Comentario actualizado (en memoria).")

# Navegación
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⏮️ Anterior") and index > 0:
        st.session_state['study_index'] -= 1
with col2:
    st.markdown(f"**Paso {index + 1} de {len(pos_seq)}**")
with col3:
    if st.button("Siguiente ⏭️") and index < len(pos_seq) - 1:
        st.session_state['study_index'] += 1

# Guardar cambios
to_save = st.button("💾 Guardar cambios en la base de datos")
if to_save:
    repo.save_study(study)
    st.success("Estudio actualizado en la base de datos.")

# Exportar como PDF
REPORT_PATH = Path("reports")
REPORT_PATH.mkdir(parents=True, exist_ok=True)

if st.button("📄 Exportar como PDF"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, study['title'], ln=True)

    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, study['description'])
    pdf.ln()

    for i, pos in enumerate(study['position_sequence']):
        pdf.cell(0, 10, f"FEN {i+1}: {pos['fen']}", ln=True)
        pdf.multi_cell(0, 10, pos.get("comment", ""))
        pdf.ln()

    output_path = REPORT_PATH / f"{study['study_id']}_resumen.pdf"
    try:
        pdf.output(str(output_path))
        st.success(f"PDF exportado en: {output_path}")
    except UnicodeEncodeError:
        st.error("❌ Error al exportar PDF: hay caracteres no compatibles con Latin-1.")

# 🔜 Futuro: jugar con Stockfish desde la posición actual
st.markdown("---")
st.markdown("🧠 *Próximamente: opción para jugar con Stockfish desde esta posición.*")
st.button("🎯 Jugar desde aquí (Stockfish) — próximamente")
