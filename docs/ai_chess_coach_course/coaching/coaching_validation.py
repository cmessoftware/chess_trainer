"""Post-generation validation for Gemini coaching responses (V7)."""



from __future__ import annotations



import re

from dataclasses import dataclass, field

from typing import Any



BANNED_GENERIC_PHRASES = (

    "jaques, capturas y amenazas",

    "jca",

    "revisa tácticas",

    "seguridad del rey",

    "rey expuesto",

    "enroque tardío",

    "rey en el centro",

)



_REQUIRED_SECTIONS = (

    "### resumen breve",

    "### lecciones principales",

    "### momentos clave",

    "### plan de entrenamiento",

)



_MOMENT_ENTRY_PATTERN = re.compile(

    r"jugada del alumno\s*:",

    re.IGNORECASE,

)

_LESSON_HEADER_PATTERN = re.compile(

    r"####\s*lecci[oó]n\s*:",

    re.IGNORECASE,

)

_MOVE_NUMBER_PATTERNS = (

    re.compile(r"(?:jugada|movimiento)\s*(?:del alumno\s*)?(?:n[°º]?\s*)?(\d+)", re.IGNORECASE),

    re.compile(r"\b(\d+)\.\s*[A-Za-z]", re.MULTILINE),

    re.compile(r"\b(\d+)\.\.\.", re.MULTILINE),

)





@dataclass

class CoachingResponseValidation:

    ok: bool

    errors: list[str] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)

    mentioned_move_numbers: set[int] = field(default_factory=set)

    extra_move_numbers: set[int] = field(default_factory=set)





def _allowed_move_numbers(critical_moves: list[dict[str, Any]]) -> set[int]:

    """Move numbers that may appear anywhere in the coaching text."""

    allowed: set[int] = set()

    for item in critical_moves:

        if "move_number" in item:

            allowed.add(int(item["move_number"]))

        for field in ("player_move", "opponent_reply", "issue", "consequence", "context_pgn", "lesson_hint"):

            value = item.get(field)

            if value:

                allowed.update(_extract_move_numbers_from_text(str(value)))

    return allowed





def _critical_moment_numbers(critical_moves: list[dict[str, Any]]) -> set[int]:

    return {int(item["move_number"]) for item in critical_moves if "move_number" in item}





def _extract_move_numbers_from_text(text: str) -> set[int]:

    found: set[int] = set()

    for pattern in _MOVE_NUMBER_PATTERNS:

        for match in pattern.finditer(text):

            try:

                found.add(int(match.group(1)))

            except (ValueError, IndexError):

                continue

    return found





def _extract_mentioned_move_numbers(text: str) -> set[int]:

    return _extract_move_numbers_from_text(text)





def _extract_student_moment_numbers(text: str) -> set[int]:

    """Move numbers introduced as a key student moment (not just in a sequence)."""

    found: set[int] = set()

    header_pattern = re.compile(

        r"jugada del alumno\s*:\s*(\d+)\.",

        re.IGNORECASE,

    )

    for match in header_pattern.finditer(text):

        found.add(int(match.group(1)))

    return found





def _section_slice(text: str, header: str, next_headers: tuple[str, ...]) -> str:

    lowered = text.lower()

    start = lowered.find(header)

    if start < 0:

        return ""

    end = len(text)

    for next_header in next_headers:

        index = lowered.find(next_header, start + len(header))

        if index >= 0:

            end = min(end, index)

    return text[start:end]





def validate_coaching_response(

    text: str,

    critical_moves: list[dict[str, Any]],

    *,

    allowed_context: str = "",

) -> CoachingResponseValidation:

    result = CoachingResponseValidation(ok=True)

    allowed = _allowed_move_numbers(critical_moves)

    critical_only = _critical_moment_numbers(critical_moves)

    mentioned = _extract_mentioned_move_numbers(text)

    student_moments = _extract_student_moment_numbers(text)

    result.mentioned_move_numbers = mentioned

    result.extra_move_numbers = mentioned - allowed

    invented_moments = student_moments - critical_only

    lowered = text.lower()



    for section in _REQUIRED_SECTIONS:

        if section not in lowered:

            result.ok = False

            result.errors.append(f"Missing required section: {section.replace('### ', '### ').title()}")



    entry_count = len(_MOMENT_ENTRY_PATTERN.findall(text))

    if entry_count != len(critical_moves):

        result.ok = False

        result.errors.append(

            f"Expected {len(critical_moves)} 'Jugada del alumno' entries, found {entry_count}"

        )



    lesson_count = len(_LESSON_HEADER_PATTERN.findall(text))

    if lesson_count < 2:

        result.warnings.append(

            f"Expected 2-3 lesson subsections (#### Lección:), found {lesson_count}"

        )

    elif lesson_count > 4:

        result.warnings.append(f"Many lesson subsections ({lesson_count}); V7 expects 2-3")



    summary_text = _section_slice(

        lowered,

        "### resumen breve",

        ("### lecciones principales",),

    )

    if summary_text and _extract_move_numbers_from_text(summary_text):

        result.warnings.append("Resumen breve mentions individual move numbers; V7 prefers phase-level summary")



    if invented_moments:

        result.ok = False

        extras = ", ".join(str(number) for number in sorted(invented_moments))

        result.errors.append(

            f"Response lists extra student key moments not in critical_moves: {extras}"

        )



    if result.extra_move_numbers:

        result.ok = False

        extras = ", ".join(str(number) for number in sorted(result.extra_move_numbers))

        result.errors.append(f"Response mentions move numbers not in payload context: {extras}")



    context_blob = f"{allowed_context}\n{text}".lower()

    for phrase in BANNED_GENERIC_PHRASES:

        if phrase in text.lower() and phrase not in context_blob.replace(text.lower(), ""):

            payload_text = allowed_context.lower()

            if phrase not in payload_text:

                result.warnings.append(f"Generic phrase detected: {phrase!r}")



    return result

