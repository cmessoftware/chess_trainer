import os
import dotenv
import json
from modules.study_generator import StudyGenerator
from db.postgres_utils import get_postgres_connection

dotenv.load_dotenv()
db_url = os.environ.get("CHESS_TRAINER_DB_URL")

if not db_url:
    raise ValueError(
        f"CHESS_TRAINER_DB_URL environment variable not set")


class StudyRepository:
    def __init__(self):
        self.conn = get_postgres_connection()
        self.generator = StudyGenerator(self)

    def get_all_studies(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT study_id, title FROM studies")
        return [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]

    def get_study_by_id(self, study_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM studies WHERE study_id = %s", (study_id,))
        row = cursor.fetchone()
        if row is None:
            return None

        # Convert row to dict
        study = dict(zip([desc[0] for desc in cursor.description], row))
        study['tags'] = json.loads(study.get('tags', '[]'))
        study['position_sequence'] = self.get_study_positions(study_id)

        # Agregar posiciones desde el PGN si aún no existen
        if not study['position_sequence'] and study.get('pgn'):
            study['position_sequence'] = self.generator.generate_positions_from_pgn(
                study['pgn'])
            self.save_study(study)

        return study

    def get_study_positions(self, study_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT fen, comment, is_critical FROM study_positions WHERE study_id = %s", (study_id,))
        return [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]

    def save_study(self, study):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE studies SET title = %s, description = %s, source = %s, tags = %s WHERE study_id = %s", (
            study['title'], study['description'], study['source'], json.dumps(
                study['tags']), study['study_id']
        ))
        cursor.execute(
            "DELETE FROM study_positions WHERE study_id = %s", (study['study_id'],))
        for pos in study['position_sequence']:
            cursor.execute(
                "INSERT INTO study_positions (study_id, fen, comment, is_critical) VALUES (%s, %s, %s, %s)",
                (study['study_id'], pos['fen'], pos.get(
                    'comment', ''), pos.get('is_critical', False))
            )
        self.conn.commit()

    def close(self):
        self.conn.close()
