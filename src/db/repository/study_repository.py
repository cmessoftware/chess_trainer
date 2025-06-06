import os
import sqlite3
import dotenv
import json
from modules.study_generator import StudyGenerator

dotenv.load_dotenv()
db_path = os.environ.get("CHESS_TRAINER_DB")

if not db_path or not os.path.exists(db_path):
    raise ValueError(f"Ruta de base de datos inválida o no encontrada: {db_path}")

class StudyRepository:
    def __init__(self):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.generator = StudyGenerator(self)

    def get_all_studies(self):
        cursor = self.conn.execute("SELECT study_id, title FROM studies")
        return [dict(row) for row in cursor.fetchall()]

    def get_study_by_id(self, study_id):
        cursor = self.conn.execute("SELECT * FROM studies WHERE study_id = ?", (study_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        study = dict(row)
        study['tags'] = json.loads(study.get('tags', '[]'))
        study['position_sequence'] = self.get_study_positions(study_id)

        # Agregar posiciones desde el PGN si aún no existen
        if not study['position_sequence'] and study.get('pgn'):
            study['position_sequence'] = self.generator.generate_positions_from_pgn(study['pgn'])
            self.save_study(study)

        return study

    def get_study_positions(self, study_id):
        cursor = self.conn.execute("SELECT fen, comment, is_critical FROM study_positions WHERE study_id = ?", (study_id,))
        return [dict(row) for row in cursor.fetchall()]

    def save_study(self, study):
        self.conn.execute("UPDATE studies SET title = ?, description = ?, source = ?, tags = ? WHERE study_id = ?", (
            study['title'], study['description'], study['source'], json.dumps(study['tags']), study['study_id']
        ))
        self.conn.execute("DELETE FROM study_positions WHERE study_id = ?", (study['study_id'],))
        for pos in study['position_sequence']:
            self.conn.execute(
                "INSERT INTO study_positions (study_id, fen, comment, is_critical) VALUES (?, ?, ?, ?)",
                (study['study_id'], pos['fen'], pos.get('comment', ''), pos.get('is_critical', False))
            )
        self.conn.commit()

    def close(self):
        self.conn.close()
