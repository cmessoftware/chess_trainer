import sqlite3


def test_processed_hash_table():
    conn = sqlite3.connect("data/chess_trainer.db")
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='processed_features';")
    assert cursor.fetchone() is not None
    conn.close()
