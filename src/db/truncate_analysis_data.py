from db.database import engine
from sqlalchemy import text

tables_to_clean = [
    "features",
    "processed_features",
    "analyzed_tacticals"
]


with engine.begin() as conn:
    for table in tables_to_clean:
        print(f"🧹 Cleaning table {table}...")
        conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
print("✔ Analysis data cleaned.")
