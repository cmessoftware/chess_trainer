"""Fix alembic version in database"""
from db.database import engine
from sqlalchemy import text

conn = engine.connect()
result = conn.execute(text("UPDATE alembic_version SET version_num = '20260213_231617' WHERE version_num = '20260216_024500'"))
conn.commit()
conn.close()

print("✅ Alembic version updated successfully")
