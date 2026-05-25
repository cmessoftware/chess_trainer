#!/usr/bin/env python3
"""
Script para investigar el estado actual de la base de datos
"""

import pandas as pd
from sqlalchemy import create_engine


def investigate_db():
    try:
        engine = create_engine(
            "postgresql://postgres:password123@localhost:5432/chess_trainer"
        )
        with engine.connect() as conn:
            # Ver tablas
            tables = pd.read_sql(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
                conn,
            )
            print("✅ Tablas en la BD:")
            for table in tables["table_name"]:
                print(f"  - {table}")

            # Si hay tabla moves, investigar
            if "moves" in list(tables["table_name"]):
                count = pd.read_sql("SELECT COUNT(*) as cnt FROM moves", conn).iloc[0][
                    "cnt"
                ]
                print(f"\n📊 Total registros en moves: {count:,}")

                # Ver estructura
                cols = pd.read_sql(
                    """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'moves' 
                    ORDER BY ordinal_position
                """,
                    conn,
                )

                print(f"\n📋 Estructura tabla moves ({len(cols)} columnas):")
                for i, row in cols.iterrows():
                    col_name = row["column_name"]
                    col_type = row["data_type"]
                    print(f"  {i:2d}   {col_name:30} {col_type}")

                # Ver distribución por fuente
                sources = pd.read_sql(
                    "SELECT source_origin, COUNT(*) as cnt FROM moves GROUP BY source_origin",
                    conn,
                )
                print("\n📊 Distribución por fuente:")
                for _, row in sources.iterrows():
                    src = row["source_origin"]
                    cnt = row["cnt"]
                    print(f"  - {src}: {cnt:,}")

                # Muestra de datos
                sample = pd.read_sql("SELECT * FROM moves LIMIT 3", conn)
                print(f"\n📋 Muestra de datos:")
                print(sample.info())

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    investigate_db()
