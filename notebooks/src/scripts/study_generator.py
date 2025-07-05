
# modules/study_generator.py

from datetime import datetime
from hashlib import sha256
from db.models import Study, TacticalExercise
from sqlalchemy.orm import Session

def generate_study_and_exercises(pgn: str, session: Session):
    game_id = sha256(pgn.encode("utf-8")).hexdigest()
    study_id = sha256((game_id + "study").encode()).hexdigest()

    study = Study(
        study_id=study_id,
        title="Ataque temático en estructura Maroczy",
        player_color="white",
        tags=[
            "attack_on_castled_king", 
            "dark_square_weakness", 
            "bishop_sacrifice", 
            "file_pressure"
        ],
        opening="Defensa Moderna",
        source="Chess.com",
        result="1-0",
        game_id=game_id,
        is_from_elite=False,
        created_at=datetime.utcnow()
    )

    exercises = [
        TacticalExercise(
            exercise_id=sha256((game_id + "_ex1").encode()).hexdigest(),
            game_id=game_id,
            fen="r2q1rk1/1b1nppbp/p2p1np1/1p1P4/2P1P2B/2N2N1P/PP3PP1/R2Q1RK1 w - - 0 15",
            solution_pgn="15. f4 exf4 16. Rxf4",
            tags=["central_break", "file_pressure"],
            error_label="missed_f4_push"
        ),
        TacticalExercise(
            exercise_id=sha256((game_id + "_ex2").encode()).hexdigest(),
            game_id=game_id,
            fen="r4rk1/1b1nqpbp/p2p2p1/1p1Pp1Q1/2P1p3/2N1P2P/PP3PP1/R4RK1 w - - 0 23",
            solution_pgn="23. Qxh6 f5 24. Qxg5+",
            tags=["queen_sacrifice_threat", "king_exposure"],
            error_label="missed_qxh6_combo"
        ),
        TacticalExercise(
            exercise_id=sha256((game_id + "_ex3").encode()).hexdigest(),
            game_id=game_id,
            fen="5rk1/1b1nqpb1/p2p3p/1p4Q1/2P1p3/2N1P2P/PP3PP1/4RR2 w - - 0 28",
            solution_pgn="28. Re7",
            tags=["rook_infiltration", "mate_threat"],
            error_label="missed_re7"
        )
    ]

    session.add(study)
    session.add_all(exercises)
    session.commit()
    return study_id, [e.exercise_id for e in exercises]
