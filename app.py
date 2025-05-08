import streamlit as st
from analyze_games import analyze_game, generate_report
from visualizations import plot_blunders

st.title("Entrenador de Ajedrez")

uploaded_file = st.file_uploader("Carga tu partida (PGN)", type="pgn")
player_name = st.text_input("Nombre del jugador")

if uploaded_file and player_name:
    with open("data/uploads/game.pgn", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    df = analyze_game("data/uploads/game.pgn", player_name)
    report = generate_report(df)
    
    st.write("### Informe de Análisis")
    st.write(f"Porcentaje de errores graves: {report['blunder_rate']:.2f}%")
    st.write(f"Puntuación promedio: {report['avg_score']:.2f}")
    
    plot_blunders(df, "visualizations/plots/blunders.png")
    st.image("visualizations/plots/blunders.png")