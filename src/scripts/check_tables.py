import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.environ.get('CHESS_TRAINER_DB_URL')
engine = create_engine(DB_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
    print('📋 Tablas existentes:')
    for row in result:
        print(f'  - {row[0]}')
