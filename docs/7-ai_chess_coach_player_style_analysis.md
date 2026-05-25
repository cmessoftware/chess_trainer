Prompt para Generación de Lógica de Análisis de Estilo (ChessTrainer)
Contexto del Sistema
Stack: Python (FastAPI/Ollama), React (Frontend), Base de Datos (PostgreSQL).

Inputs Disponibles:
pgn: Texto estándar del juego.
stockfish_metadata: Evaluación por jugada (centipawns), mejores jugadas vs jugadas hechas, pérdida de ACPL (Average Centipawn Loss).

ml_features: Salida de modelos de árboles (XGBoost/RandomForest) y Redes Neuronales 
que ya clasifican clústeres de jugadores (ej: "agresivo", "especulador", "sólido").

Objetivo: Usar Ollama (Llama 3.2) para orquestar estos datos y devolver un "informe narrativo y estructural" que el usuario humano pueda entender, evitando que la IA intente calcular táctica que ya calculó Stockfish.
Instrucciones para Copilot
Tarea: Crea un endpoint en Python que reciba el ID de una partida, recupere la metadata (Stockfish + ML) y el PGN, y genere un prompt optimizado para Ollama.
Lógica del Prompt para Ollama:
Generá una función generate_llm_analysis_prompt(game_data) donde el prompt resultante para Llama 3.2 sea:
Rol de Sistema: "Eres un psicólogo y entrenador de ajedrez de élite. Tu función no es calcular (para eso usamos Stockfish), sino interpretar datos estadísticos y convertirlos en consejos pedagógicos."
Inyección de Data Técnica:
"Datos de Stockfish: La pérdida de ACPL fue de {acpl}. El jugador cometió {blunders} errores graves."
"Datos de ML: El modelo de clasificación etiqueta a este jugador como '{clúster_estilo}' con una confianza del {confianza}%."
Tarea Específica: "Basado en que el PGN muestra una apertura {apertura}, explica por qué la metadata indica una caída de rendimiento en la jugada {critical_move}. Cruza la información: ¿El error fue por falta de tiempo (metadata clk) o por una debilidad estructural detectada por el modelo de ML?"
Formato de Salida: "Devuelve un JSON estricto con las llaves: resumen_estilo, consejo_entrenamiento, puntos_fuertes y deteccion_de_panico."
Código Requerido:
Implementación de la llamada a Ollama usando la librería requests o el SDK oficial.
Validación del JSON de salida para asegurar compatibilidad con el frontend de React.
Manejo de errores si Llama 3.2 alucina un formato no válido.