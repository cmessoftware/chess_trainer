# /app/src/db/repository/feature_repository.py

from db.models.features import Feature


class FeatureRepository:
    def __init__(self, session):
        self.session = session

    def get_all(self):
        return self.session.query(Feature).all()

    def get_by_game_id(self, game_id):
        return self.session.query(Feature).filter(Feature.game_id == game_id).all()

    def get_by_game_and_move(self, game_id, move_number):
        return self.session.query(Feature).filter_by(game_id=game_id, move_number=move_number).first()

    def add_feature(self, feature: Feature):
        self.session.add(feature)
        self.session.commit()

    def delete_by_game_id(self, game_id):
        self.session.query(Feature).filter_by(game_id=game_id).delete()
        self.session.commit()

    def update_feature(self, feature_id, **kwargs):
        self.session.query(Feature).filter_by(id=feature_id).update(kwargs)
        self.session.commit()
