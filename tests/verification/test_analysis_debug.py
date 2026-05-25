# -*- coding: utf-8 -*-
"""Test análisis con captura de logs"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests

BASE_URL = "http://localhost:8000/api"

# Login
login_resp = requests.post(
    f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"}
)
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Ejecutar análisis
game_id = "6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3"
print(f"\nEjecutando análisis SHAP para: {game_id[:32]}...")

response = requests.post(
    f"{BASE_URL}/analysis/run", headers=headers, json={"game_id": game_id}
)

print(f"\nStatus: {response.status_code}")
print(f"Response: {response.json()}")

# Verificar BD
import psycopg2

conn = psycopg2.connect("postgresql://chess:chess_pass@localhost:5432/chess_trainer_db")
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM move_shap_values")
shap_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM analysis_results")
analysis_count = cur.fetchone()[0]

print(f"\n[BD] analysis_results: {analysis_count}")
print(f"[BD] move_shap_values: {shap_count}")

conn.close()
