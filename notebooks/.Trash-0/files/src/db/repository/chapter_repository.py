# /app/src/db/repository/chapter_repository.py
from sqlalchemy.orm import Session
from db.models.chapter import Chapter


class ChapterRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_chapter(self, study_id: str, title: str, pgn: str, tags: dict = None) -> Chapter:
        chapter = Chapter(
            study_id=study_id,
            title=title,
            pgn=pgn,
            tags=tags or {}
        )
        self.session.add(chapter)
        self.session.commit()
        self.session.refresh(chapter)
        return chapter

    def get_chapters_by_study_id(self, study_id: str) -> list[Chapter]:
        return self.session.query(Chapter).filter(Chapter.study_id == study_id).all()

    def delete_chapter(self, chapter_id: int) -> None:
        chapter = self.session.query(Chapter).get(chapter_id)
        if chapter:
            self.session.delete(chapter)
            self.session.commit()
