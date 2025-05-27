#!/bin/bash

# Ejecutar el pipeline completo
python tag_games.py
python analyze_errors_from_db.py
python generate_exercises_from_elite.py
pytest tests/
