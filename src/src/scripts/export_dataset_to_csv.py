import os
import argparse
import dotenv
from datetime import datetime

from db.repository.features_repository import FeaturesRepository


dotenv.load_dotenv()

DB_URL = os.getenv("CHESS_TRAINER_DB_URL")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
DEFAULT_OUTPUT_CSV = f"/app/src/data/features_dataset_{timestamp}.csv"


def export_training_dataset(output_csv):

    repo = FeaturesRepository()
    repo.export_features_dataset(output_csv)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export training dataset from database to CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_CSV,
                        help="Output CSV file path (default: %(default)s)")
    args = parser.parse_args()

    export_training_dataset(args.output)
