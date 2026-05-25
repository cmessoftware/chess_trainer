#!/usr/bin/env python3
"""
Script para inicializar el sistema RAG de ajedrez
Procesa libros PDF y los carga en ChromaDB

Uso:
    python src/scripts/init_chess_rag.py              # Procesar solo libros nuevos
    python src/scripts/init_chess_rag.py --force      # Forzar reprocesamiento completo
    python src/scripts/init_chess_rag.py --reset      # Resetear checkpoint
"""

import sys
import argparse
from pathlib import Path

# Agregar src al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai_coach.rag import ChessRAG, PDFProcessor
import logging

logger = logging.getLogger(__name__)


def main(
    force_reprocess: bool = False, reset_checkpoint: bool = False, max_pages: int = None
):
    """Inicializa el sistema RAG procesando todos los libros"""
    print("\n" + "=" * 70)
    print("🚀 INICIALIZACIÓN DEL SISTEMA RAG DE AJEDREZ")
    print("=" * 70)

    if max_pages:
        print(f"⚠️  Modo: OCR limitado a {max_pages} páginas por libro (prueba)")

    if force_reprocess:
        print("⚠️  Modo: REPROCESAMIENTO FORZADO (ignorando checkpoint)")
    elif reset_checkpoint:
        print("🔄 Modo: RESETEAR CHECKPOINT")

    # 1. Inicializar componentes
    print("\n📚 Paso 1: Inicializando procesador de PDFs...")
    processor = PDFProcessor(
        raw_books_dir=str(project_root / "data" / "chess_books" / "raw"),
        processed_dir=str(project_root / "data" / "chess_books" / "processed"),
        checkpoint_file=str(
            project_root / "data" / "chess_books" / "processing_checkpoint.json"
        ),
    )

    # Resetear checkpoint si se solicitó
    if reset_checkpoint:
        processor.reset_checkpoint()
        print("✅ Checkpoint reseteado")

    print("🧠 Paso 2: Inicializando sistema RAG con ChromaDB...")
    rag = ChessRAG(
        collection_name="chess_knowledge",
        persist_directory=str(project_root / "data" / "chess_books" / "chroma_db"),
        embedding_model="all-MiniLM-L6-v2",
    )

    # 2. Procesar libros
    print("\n📖 Paso 3: Procesando libros PDF...")
    pdf_dir = project_root / "data" / "chess_books" / "raw"
    pdf_files = list(pdf_dir.glob("**/*.pdf"))  # Búsqueda recursiva en subcarpetas

    if not pdf_files:
        print(f"\n⚠️  No se encontraron PDFs en {pdf_dir}")
        print("\n💡 Para continuar:")
        print(f"   1. Descarga libros de ajedrez (PDFs)")
        print(f"   2. Guárdalos en: {pdf_dir}")
        print(f"   3. Vuelve a ejecutar este script")
        print("\n📌 Libros recomendados:")
        print("   - My System (Nimzowitsch)")
        print("   - Modern Chess Openings (MCO)")
        print("   - Fundamental Chess Endings")
        print("   - The Art of Attack in Chess (Vukovic)")
        print("\n   Preferiblemente en notación algebraica moderna\n")
        return

    print(f"   Encontrados {len(pdf_files)} PDFs")

    # Mostrar información de checkpoint
    already_processed = sum(1 for pdf in pdf_files if processor.is_book_processed(pdf))
    if not force_reprocess and already_processed > 0:
        print(f"\n💾 Checkpoint detectado:")
        print(f"   ✅ Ya procesados: {already_processed}/{len(pdf_files)}")
        print(
            f"   🔄 Por procesar: {len(pdf_files) - already_processed}/{len(pdf_files)}"
        )
        print(f"\n   💡 Usa --force para reprocesar todos los libros")

    # Procesar todos los libros
    all_chunks = processor.process_all_books(
        force_reprocess=force_reprocess, max_pages=max_pages
    )

    if not all_chunks and not already_processed:
        print("\n❌ No se pudo extraer contenido de los PDFs")
        print("   Verifica que los PDFs no estén corruptos o protegidos")
        return

    if not all_chunks and already_processed > 0:
        print(f"\n✅ Todos los libros ya estaban procesados (checkpoint)")
        print(f"   Total de libros en checkpoint: {already_processed}")
    else:
        print(f"\n✅ Generados {len(all_chunks)} chunks nuevos en esta ejecución")

    # 3. Cargar en ChromaDB (solo si hay chunks nuevos)
    if all_chunks:
        print("\n💾 Paso 4: Cargando chunks en ChromaDB...")
        rag.add_documents(all_chunks)
    else:
        print("\n💾 Paso 4: No hay chunks nuevos para cargar")

    # 4. Verificar y mostrar estadísticas
    print("\n📊 Estadísticas del sistema RAG:")
    stats = rag.get_stats()
    print(f"   Total de documentos: {stats['total_documents']}")
    print(f"   Fuentes únicas: {stats['unique_sources']}")
    print(f"   Libros indexados: {', '.join(stats['sources'])}")
    print(
        f"   Notación algebraica: {stats['notation_types'].get('algebraic', 0)} chunks"
    )
    print(
        f"   Notación descriptiva: {stats['notation_types'].get('descriptive', 0)} chunks"
    )

    # 5. Prueba de recuperación
    print("\n🧪 Paso 5: Probando sistema de recuperación...")
    test_queries = [
        "¿Qué es la Apertura Italiana?",
        "Estrategias para el medio juego",
        "Finales de peones",
    ]

    for query in test_queries:
        print(f"\n   Query: '{query}'")
        results = rag.retrieve_knowledge(query, n_results=2)
        if results:
            print(f"   ✅ Encontrados {len(results)} resultados relevantes")
            print(f"   Primera fuente: {results[0]['metadata']['source']}")
        else:
            print(f"   ⚠️  No se encontraron resultados")

    # 6. Resumen final
    print("\n" + "=" * 70)
    print("✅ SISTEMA RAG INICIALIZADO CORRECTAMENTE")
    print("=" * 70)
    print("\n🎯 Siguiente paso:")
    print("   Ejecutar: python test_rag_integration.py")
    print("   Para probar la integración RAG + LLM\n")


if __name__ == "__main__":
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description="Inicializa el sistema RAG procesando libros de ajedrez"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar reprocesamiento de todos los libros (ignorar checkpoint)",
    )
    parser.add_argument(
        "--reset", action="store_true", help="Resetear checkpoint antes de procesar"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Número máximo de páginas por libro para procesamiento OCR (útil para pruebas)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    main(
        force_reprocess=args.force,
        reset_checkpoint=args.reset,
        max_pages=args.max_pages,
    )
