import subprocess
from analyze_games import analyze_game, generate_report
from visualizations import plot_blunders

def main():
    print("Lanzando Stockfish...")
    stockfish = subprocess.Popen(
        ["/usr/local/bin/stockfish"], 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        text=True
    )
    stockfish.stdin.write("uci\n")
    stockfish.stdin.flush()

    print("=== Entrenador de Ajedrez ===")
    file_path = input("Introduce la ruta del archivo PGN de tu partida: ")
    player_name = input("Introduce el nombre del jugador: ")

    if file_path and player_name:
        df = analyze_game(file_path, player_name)
        report = generate_report(df)
        
        print("\n### Informe de Análisis ###")
        print(f"Porcentaje de errores graves: {report['blunder_rate']:.2f}%")
        print(f"Puntuación promedio: {report['avg_score']:.2f}")
        
        plot_blunders(df, "visualizations/plots/blunders.png")
        print("El gráfico de errores graves se ha guardado en 'visualizations/plots/blunders.png'.")

    print(stockfish.stdout.readline())

if __name__ == "__main__":
    main()
