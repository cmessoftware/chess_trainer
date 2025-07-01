from ..modules.dataset_generator import generate_training_data_from_pgn
import os

def test_dataset_generation():
    generate_training_data_from_pgn("data/sample_game.pgn", "output.csv")
    assert os.path.exists("output.csv")