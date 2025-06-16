import os
import pandas as pd

from db.repository.features_repository import FeaturesRepository


def export_features_to_dataset(
    output_path: str,
    player: str | None = None,
    opening: str | None = None,
    min_elo: int | None = None,
    max_elo: int | None = None,
    limit: int | None = None,
    file_type: str = "parquet"
):
    """
    Exporta un subconjunto de la tabla `features` a un archivo Parquet
    aplicando filtros opcionales por jugador, apertura, ELO y límite de partidas.
    """
    print("🔄 Exportando dataset de features...")
    print(f"Filtros aplicados:  ")
    print(f"  - Jugador: {player if player else 'Todos'}")
    print(f"  - Min elo: {min_elo}")
    print(f"  - Max elo: {max_elo} ")
    print(f"  - Limit games: {limit}")
    print(f"  - File type: {file_type}")

    features_repo = FeaturesRepository()

    df = features_repo.get_features_with_filters(
        player_name=player,
        opening=opening,
        min_elo=min_elo,
        max_elo=max_elo,
        limit=limit
    )

    if df is None:
        print("⚠️ No se encontraron datos con esos filtros.")
        return

    print(f"🔄 Total de features encontradas: {len(df)}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if file_type == "parquet":
        output_path = output_path + ".parquet"
        df.to_parquet(output_path, index=False)
    elif file_type == "csv":
        output_path = output_path + ".csv"
        df.to_csv(output_path, index=False)

    print(
        f"✅ Exported {len(df)} rows ({df['game_id'].nunique()} games) to {output_path}")
