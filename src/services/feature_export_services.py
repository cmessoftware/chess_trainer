import os
import pandas as pd

from db.repository.features_repository import FeaturesRepository


def export_features_to_parquet(
    output_path: str,
    player: str | None = None,
    opening: str | None = None,
    min_elo: int | None = None,
    max_elo: int | None = None,
    limit: int | None = None,
):
    """
    Exporta un subconjunto de la tabla `features` a un archivo Parquet
    aplicando filtros opcionales por jugador, apertura, ELO y límite de partidas.
    """
    print("🔄 Exportando dataset de features...")
    print(f"Filtros aplicados:  \n")
    print(f"  - Jugador: {player if player else 'Todos'}\n")
    print(f"  - Min elo: {min_elo}\n")
    print(f"  - Max elo: {max_elo} \n")
    print(f"  - Limit games: {limit}\n")

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
    print(df.head(5))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"✅ Dataset exportado a {output_path} con {len(df)} filas.")
