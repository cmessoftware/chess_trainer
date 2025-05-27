#!/bin/bash
echo "🏁 Ejecutando pipeline completo..."

cd /app/src || exit 1

python scripts/auto_tag_games.py || exit 1
python scripts/analyze_errors_from_db.py || exit 1
python scripts/generate_exercises_from_elite.ý || exit 1
python scripts/generate_full_report.py data/games/lichess_elite_2020-05.pgn training_dataset.csv || exit 1

pytest tests/ || exit 1

echo "✅ Pipeline ejecutado exitosamente."
