from functools import partial
import os
from sqlalchemy import select
from db.models.games import Games
from concurrent.futures import ProcessPoolExecutor
from db.repository.features_repository import FeaturesRepository
import dotenv

from export_features_dataset_parallel import export_features_to_dataset
dotenv.load_dotenv()


EXPORT_DIR = os.environ.get("EXPORT_DIR", "./data/exports")


def export_features_for_source(output_dir: str, source: str):
    output_path = os.path.join(output_dir, f"features_{source}")
    print(f"🔄 Exporting features for source: {source} to {output_path}")
    export_features_to_dataset(
        output_path=output_path, file_type="parquet", player=None, opening=None)


def export_all_sources_parallel():
    features_repo = FeaturesRepository()
    sources = features_repo.get_unique_sources()
    print(f"🔄 Found {len(sources)} unique sources: {sources}")
    # Export first source for debugging
    with ProcessPoolExecutor() as executor:
        executor.map(partial(export_features_for_source,
                     output_dir=EXPORT_DIR), sources)


if __name__ == "__main__":
    export_all_sources_parallel()
    print("🔄 Exporting features by source in parallel...")
