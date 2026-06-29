"""Prompt templates for chess coaching recommendations (V7 insight-based)."""



from __future__ import annotations



import json

from typing import Any



from coaching.critical_move_contract import normalize_critical_move_for_llm

from coaching.lesson_synthesizer import synthesize_lessons



DEFAULT_RESPONSE_LANGUAGE = "es"



CONTROL_RULES = """

CONTROL RULES:

- You must mention only moves listed in critical_moves (as evidence in lessons or in Momentos clave).

- Do not add extra critical moments beyond critical_moves.

- The "Momentos clave" section must contain exactly one entry for each item in critical_moves.

- Each critical_moves item represents the student's move in player_move.

- opponent_reply is only the opponent's tactical punishment (tactical diagnosis_type only).

- Never describe opponent_reply as if it were the student's mistake.

- Merge several critical_moves into one lesson when lesson_clusters groups them together.

- Do not dedicate equal space to every critical move; lessons are the main content.

- Do not use generic filler phrases such as "jaques, capturas y amenazas", "JCA", "revisa tácticas",

  "rey expuesto", "seguridad del rey", or "enroque tardío" unless directly supported by issue,

  consequence, or context_pgn.

""".strip()



OUTPUT_FORMAT_TEMPLATE = """

Your report must have EXACTLY four sections in this order:



### Resumen breve

Two or three short paragraphs describing opening, middlegame, and ending.

Do NOT discuss individual moves yet. Use phase_summary and game metadata only.



### Lecciones principales

Identify the two or three most important lessons (use lesson_clusters as a guide).

For each lesson write a subsection:



#### Lección: {title}

- Explain one recurring idea in natural Spanish.

- Cite one or more evidence_moves from the cluster as examples (not as the main structure).

- Explain why the mistake happened and how to avoid it (why, how_to_avoid).



Example style (do not copy literally):

"Durante el medio juego mejoraste la actividad del alfil negro más que tu propia posición.

La jugada 34.b4 lo ilustra: parecía activa, pero dio al rival mejor coordinación."



### Momentos clave

Concise supporting evidence only. For EVERY critical_moves entry include:

- Jugada del alumno: {player_move}

- (If diagnosis_type is tactical and opponent_reply exists) Respuesta rival: {opponent_reply}

- Una frase breve explicando por qué importa (no párrafos largos).



### Plan de entrenamiento

Exactly three practical recommendations. Each must map to one lesson from Lecciones principales.

No generic advice ("calcula más", "mejora tácticas", "JCA").

""".strip()



SINGLE_GAME_COACHING_RULES = f"""

Eres un entrenador de ajedrez revisando UNA partida concreta con tu alumno.



{CONTROL_RULES}



Reglas obligatorias para tu respuesta:

- Responde SIEMPRE en español (neutro, claro, directo).

- Escribe como un coach humano después de la sesión, no como anotaciones de motor.

- NO uses porcentajes, decimales, fracciones ni recuentos.

- Prioriza lesson_clusters y entradas con root_cause: true en critical_moves.

- NO menciones SHAP, modelos, features, parquet ni evaluaciones numéricas de motor.

- Sé específico de ESTA partida: rival, apertura, resultado, ideas estructurales.

- Saluda al jugador con su nombre de usuario del campo player.

- NO uses placeholders como [alumno], [nombre] o [jugador].

- Las lecciones son el contenido principal; los momentos clave son evidencia secundaria.

- Tono: cercano, concreto, útil.



{OUTPUT_FORMAT_TEMPLATE}

""".strip()





COACHING_RULES = """

Eres un entrenador de ajedrez escribiendo recomendaciones para un jugador amateur.



Reglas obligatorias:

- Responde SIEMPRE en español (neutro, claro, directo).

- Usa SOLO hechos presentes en el JSON de contexto.

- NO uses porcentajes, decimales ni estadísticas en la respuesta al jugador.

- Usa expresiones naturales: "a menudo", "en varias partidas", "de vez en cuando".

- NO menciones SHAP, nombres de features, scores de motor ni jerga técnica de ML.

- NO inventes partidas, rivales ni aperturas que no estén en el contexto.

- Escribe 2-4 párrafos cortos y termina con 2-3 ejercicios de entrenamiento en viñetas.

- Tono: alentador, específico, accionable.

- Saluda al jugador con su player_name del JSON. NO uses placeholders como [alumno].

""".strip()





def prepare_single_game_brief_for_llm(brief: dict[str, Any]) -> dict[str, Any]:

    """Sanitize brief JSON before sending to the LLM (V7 contract)."""

    critical_moves: list[dict[str, Any]] = []

    for moment in brief.get("critical_moves") or []:

        normalized = normalize_critical_move_for_llm(moment)

        if normalized.get("context_pgn"):

            critical_moves.append(normalized)



    game = brief.get("game") or {}

    insight = synthesize_lessons(critical_moves, game=game)



    return {

        "focus": brief.get("focus"),

        "language": brief.get("language"),

        "player": brief.get("player"),

        "game": game,

        "phase_summary": insight["phase_summary"],

        "lesson_clusters": insight["lesson_clusters"],

        "critical_moves": critical_moves,

    }





def build_single_game_coaching_prompt(brief: dict[str, Any]) -> str:

    llm_brief = prepare_single_game_brief_for_llm(brief)

    brief_json = json.dumps(llm_brief, indent=2, ensure_ascii=False)

    game = brief.get("game", {})

    opponent = game.get("opponent", "el rival")

    player = llm_brief.get("player") or brief.get("player") or "el jugador"

    n_moments = len(llm_brief.get("critical_moves") or [])

    n_lessons = len(llm_brief.get("lesson_clusters") or [])

    return (

        f"{SINGLE_GAME_COACHING_RULES}\n\n"

        f"## Brief interno de la partida (no cites el JSON al alumno)\n\n"

        f"```json\n{brief_json}\n```\n\n"

        f"## Tarea\n\n"

        f"Redacta feedback de coaching para **{player}** en su partida contra {opponent}. "

        f"Empieza saludando a {player} por su nombre de usuario (no uses [alumno]). "

        f"Responde en español con las cuatro secciones obligatorias. "

        f"### Lecciones principales debe tener aproximadamente {n_lessons} lecciones "

        f"(fusiona momentos relacionados según lesson_clusters). "

        f"### Momentos clave debe tener exactamente {n_moments} entradas breves, "

        f"una por cada critical_moves."

    )





def build_coaching_prompt(context: dict[str, Any]) -> str:

    context_json = json.dumps(context, indent=2, ensure_ascii=False)

    player = context.get("player_name", "el alumno")

    return (

        f"{COACHING_RULES}\n\n"

        f"## Contexto del jugador (JSON interno)\n\n"

        f"```json\n{context_json}\n```\n\n"

        f"## Tarea\n\n"

        f"Escribe recomendaciones de coaching para **{player}**. "

        f"Saluda a {player} por su nombre de usuario (no uses [alumno]). "

        f"Basándote en las partidas analizadas. Responde en español. "

        f"Sin porcentajes ni estadísticas en el texto final."

    )





def prompt_contains_forbidden_jargon(prompt: str) -> bool:

    lowered = prompt.lower()

    forbidden = ("mean_abs_shap", " contributed 0.", "score_cp", "mate_in", "depth_score_diff")

    return any(term in lowered for term in forbidden)

