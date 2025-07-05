from db.repository.study_repository import StudyRepository
from db.repository.chapter_repository import ChapterRepository


def save_study_to_db(study_id, title, chapters, repo: StudyRepository):
    study = repo.create_study(study_id=study_id, title=title, source="lichess")
    for ch in chapters:
        repo.add_chapter(study_id=study.id,
                         title=ch["title"], pgn=ch["pgn"], tags=ch["tags"])
