"""
Script para limpiar completamente todos los análisis antiguos
y forzar nuevos análisis con error_labels
"""

import psycopg2


def clean_all_analyses():
    """Eliminar TODOS los análisis para empezar de cero"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="chess_trainer_db",
            user="chess",
            password="chess_pass",
        )
        cursor = conn.cursor()

        # Contar antes
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        count_analyses = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM move_shap_values")
        count_shap = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM player_feature_importance")
        count_features = cursor.fetchone()[0]

        print(f"\n🗑️  Estado actual:")
        print(f"   - analysis_results: {count_analyses}")
        print(f"   - move_shap_values: {count_shap}")
        print(f"   - player_feature_importance: {count_features}")

        # Eliminar todo
        print(f"\n⚠️  ELIMINANDO TODOS LOS DATOS...")

        cursor.execute("DELETE FROM move_shap_values")
        cursor.execute("DELETE FROM player_feature_importance")
        cursor.execute("DELETE FROM analysis_results")

        conn.commit()

        print(f"✅ Todos los análisis eliminados")
        print(f"✅ Base de datos limpia para nuevos análisis con error_labels")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error limpiando datos: {e}")


if __name__ == "__main__":
    print("=" * 80)
    print("LIMPIEZA COMPLETA DE ANÁLISIS")
    print("=" * 80)

    clean_all_analyses()

    print(f"\n{'='*80}")
    print("✅ Listo para ejecutar nuevos análisis")
    print("=" * 80)
