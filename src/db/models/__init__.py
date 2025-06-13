from db.database import Base

from .games import Games
from .features import Features
from .analyzed_tacticals import Analyzed_tacticals
from .processed_features import Processed_features
from .studies import Studies
from .study_positions import Study_positions


__all__ = [
    "Base",
    "Games",
    "Features",
    "Analyzed_tacticals",
    "Processed_features",
    "Studies",
    "Study_positions",
]
