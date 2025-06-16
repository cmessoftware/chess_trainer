from modules.lichess_study_api import download_study_pgn
from modules.study_parser import extract_chapters
from db.repository.study_repository import StudyRepository
from services.study_importer_service import save_study_to_db

study_id = "AbC123"
token = "YOUR_TOKEN"
pgn_text = download_study_pgn(study_id, token)
chapters = extract_chapters(pgn_text)
save_study_to_db(study_id, "Mi estudio Lichess", chapters, StudyRepository())
