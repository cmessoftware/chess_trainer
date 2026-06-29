"""Deterministic coaching renderer (no LLM) — V7 insight-based fallback."""



from __future__ import annotations



from typing import Any



from coaching.lesson_synthesizer import synthesize_lessons





def _render_moment_brief(moment: dict[str, Any]) -> list[str]:

    lines: list[str] = []

    diagnosis_type = moment.get("diagnosis_type", "tactical")

    player_move = moment.get("player_move") or moment.get("move", "?")

    lines.append(f"- Jugada del alumno: {player_move}")



    if diagnosis_type == "tactical" and moment.get("opponent_reply"):

        lines.append(f"  Respuesta rival: {moment['opponent_reply']}")



    summary = moment.get("issue") or moment.get("lesson_hint") or moment.get("lesson", "")

    if summary:

        lines.append(f"  {summary}")

    return lines





def render_deterministic_coaching(

    game: dict[str, Any],

    critical_moves: list[dict[str, Any]],

    *,

    player: str | None = None,

) -> str:

    lines: list[str] = []

    opponent = game.get("opponent") or "el rival"

    player_name = player or "jugador"

    result = game.get("result_description") or game.get("result") or "sin resultado"

    insight = synthesize_lessons(critical_moves, game=game)

    phase_summary = insight["phase_summary"]

    lesson_clusters = insight["lesson_clusters"]



    lines.append(f"Hola {player_name}, revisión de tu partida contra {opponent}.")

    lines.append("")

    lines.append("### Resumen breve")

    lines.append("")

    if game.get("opening"):

        lines.append(

            f"Jugaste {game['opening']} contra {opponent}. Resultado: {result}."

        )

    else:

        lines.append(f"Partida contra {opponent}. Resultado: {result}.")

    if game.get("overall_impression"):

        lines.append(str(game["overall_impression"]))

    for phase_text in phase_summary.values():

        lines.append(phase_text)

    lines.append("")



    lines.append("### Lecciones principales")

    lines.append("")

    for cluster in lesson_clusters:

        lines.append(f"#### Lección: {cluster['title']}")

        lines.append(cluster["why"])

        evidence = ", ".join(cluster.get("evidence_moves") or [])

        if evidence:

            lines.append(f"Ejemplos: {evidence}.")

        lines.append(f"Cómo evitarlo: {cluster['how_to_avoid']}")

        lines.append("")



    lines.append("### Momentos clave")

    lines.append("")

    for moment in critical_moves:

        lines.extend(_render_moment_brief(moment))

        lines.append("")



    lines.append("### Plan de entrenamiento")
    lines.append("")
    training_items = [cluster["how_to_avoid"] for cluster in lesson_clusters[:3]]
    for moment in critical_moves:
        if len(training_items) >= 3:
            break
        hint = moment.get("lesson_hint") or moment.get("lesson")
        if hint and str(hint) not in training_items:
            training_items.append(str(hint))
    while len(training_items) < 3:
        training_items.append("Repasa la partida anotando el plan en cada fase.")
    for item in training_items[:3]:
        lines.append(f"- {item}")

    return "\n".join(lines).strip()

