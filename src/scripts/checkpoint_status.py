#!/usr/bin/env python3
"""
Utilidad para ver el estado del checkpoint de procesamiento de libros
"""

import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
checkpoint_file = project_root / "data" / "chess_books" / "processing_checkpoint.json"


def show_checkpoint_status():
    """Muestra el estado actual del checkpoint"""

    if not checkpoint_file.exists():
        print("\n📋 ESTADO DEL CHECKPOINT")
        print("=" * 70)
        print("❌ No existe checkpoint")
        print("   Ningún libro ha sido procesado todavía\n")
        return

    try:
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo checkpoint: {e}")
        return

    processed_books = data.get("processed_books", {})
    last_updated = data.get("last_updated", "Desconocido")

    print("\n📋 ESTADO DEL CHECKPOINT")
    print("=" * 70)
    print(f"Última actualización: {last_updated}")
    print(f"Total de libros procesados: {len(processed_books)}")

    # Separar exitosos de fallidos
    successful = {k: v for k, v in processed_books.items() if v.get("success", False)}
    failed = {k: v for k, v in processed_books.items() if not v.get("success", False)}

    print(f"✅ Exitosos: {len(successful)}")
    print(f"❌ Fallidos: {len(failed)}")

    # Mostrar libros exitosos
    if successful:
        print("\n✅ LIBROS PROCESADOS EXITOSAMENTE:")
        print("-" * 70)
        total_chunks = 0
        for book_name, info in sorted(successful.items()):
            chunks = info.get("chunks_count", 0)
            total_chunks += chunks
            processed_at = info.get("processed_at", "N/A")
            print(f"  • {book_name}")
            print(f"    Chunks: {chunks} | Procesado: {processed_at}")

        print(f"\n  📊 Total de chunks: {total_chunks}")

    # Mostrar libros fallidos
    if failed:
        print("\n❌ LIBROS CON ERRORES:")
        print("-" * 70)
        for book_name, info in sorted(failed.items()):
            processed_at = info.get("processed_at", "N/A")
            print(f"  • {book_name}")
            print(f"    Error en: {processed_at}")

    print("\n" + "=" * 70)
    print("\n💡 COMANDOS ÚTILES:")
    print("  Ver este estado:     python checkpoint_status.py")
    print("  Procesar nuevos:     python src/scripts/init_chess_rag.py")
    print("  Reprocesar todo:     python src/scripts/init_chess_rag.py --force")
    print("  Resetear checkpoint: python src/scripts/init_chess_rag.py --reset")
    print()


if __name__ == "__main__":
    show_checkpoint_status()
