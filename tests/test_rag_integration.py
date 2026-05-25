#!/usr/bin/env python3
"""
Prueba de integración RAG + LLM
Demuestra cómo usar el sistema completo
"""

import sys
from pathlib import Path

# Agregar src al path (subir desde tests/ a raíz del proyecto)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai_coach.rag import ChessRAG
from langchain_ollama import OllamaLLM


def test_rag_retrieval():
    """Prueba solo el sistema RAG"""
    print("\n" + "=" * 70)
    print("🧪 PRUEBA 1: Sistema RAG (Recuperación de Conocimiento)")
    print("=" * 70)

    rag = ChessRAG(
        collection_name="chess_knowledge",
        persist_directory=str(project_root / "data" / "chess_books" / "chroma_db"),
        embedding_model="all-MiniLM-L6-v2",
    )
    stats = rag.get_stats()

    print(f"\n📊 Base de conocimiento: {stats['total_documents']} documentos")

    if stats["total_documents"] == 0:
        print("\n⚠️  La base de conocimiento está vacía")
        print("   Ejecuta primero: python src/scripts/init_chess_rag.py")
        return False

    # Probar recuperación
    query = "¿Qué es la Apertura Italiana y cuáles son sus principales variantes?"
    print(f"\n📝 Query: {query}")

    results = rag.retrieve_knowledge(query, n_results=3)

    if results:
        print(f"\n✅ Encontrados {len(results)} documentos relevantes:")
        for i, doc in enumerate(results, 1):
            print(f"\n--- Documento {i} ---")
            print(f"Fuente: {doc['metadata']['source']}")
            print(f"Notación: {doc['metadata']['notation_type']}")
            print(f"Texto (primeros 200 chars):")
            print(doc["text"][:200] + "...")
        return True
    else:
        print("\n❌ No se encontraron documentos relevantes")
        return False


def test_rag_with_llm():
    """Prueba integración completa RAG + LLM"""
    print("\n" + "=" * 70)
    print("🤖 PRUEBA 2: RAG + LLM (Sistema Completo)")
    print("=" * 70)

    # Inicializar componentes
    rag = ChessRAG(
        collection_name="chess_knowledge",
        persist_directory=str(project_root / "data" / "chess_books" / "chroma_db"),
        embedding_model="all-MiniLM-L6-v2",
    )
    llm = OllamaLLM(
        model="llama3.2:3b", base_url="http://localhost:11434", temperature=0.3
    )

    # Query del usuario
    user_question = "Explica la Apertura Italiana con sus principales variantes"
    print(f"\n❓ Pregunta del usuario: {user_question}")

    # 1. Recuperar contexto relevante
    print("\n🔍 Paso 1: Recuperando contexto relevante del RAG...")
    context = rag.get_context_for_prompt(user_question, n_results=3)

    if "No se encontró" in context:
        print("\n⚠️  No hay contexto disponible en la base de conocimiento")
        print("   La respuesta será solo del conocimiento del modelo (puede alucinar)")
        context = ""
    else:
        print(f"✅ Contexto recuperado ({len(context)} caracteres)")

    # 2. Construir prompt con contexto
    prompt = f"""
Eres un experto entrenador de ajedrez. Responde la pregunta del usuario usando SOLO la información del contexto proporcionado.

{context}

PREGUNTA: {user_question}

INSTRUCCIONES:
1. Usa SOLO información del contexto anterior
2. Si el contexto contiene notación de ajedrez, valídala antes de usarla
3. Si no hay información suficiente en el contexto, dilo claramente
4. Estructura tu respuesta de forma clara y educativa
5. Menciona las fuentes cuando sea posible

RESPUESTA:
"""

    # 3. Generar respuesta con LLM
    print("\n💬 Paso 2: Generando respuesta con LLM...")
    print("   (Esto puede tardar unos segundos...)\n")

    response = llm.invoke(prompt)

    print("=" * 70)
    print("📖 RESPUESTA DEL AI COACH:")
    print("=" * 70)
    print(response)
    print("=" * 70)

    return True


def test_comparison_without_rag():
    """Muestra la diferencia sin RAG"""
    print("\n" + "=" * 70)
    print("⚖️  PRUEBA 3: Comparación SIN RAG vs CON RAG")
    print("=" * 70)

    llm = OllamaLLM(
        model="llama3.2:3b", base_url="http://localhost:11434", temperature=0.3
    )

    question = "¿Cuáles son las principales ideas estratégicas del Gambito Evans?"

    # Sin RAG
    print(f"\n❌ SIN RAG (solo conocimiento del modelo):")
    print(f"   Pregunta: {question}\n")
    response_without = llm.invoke(question)
    print(response_without[:300] + "...\n")

    # Con RAG
    print(f"\n✅ CON RAG (conocimiento + contexto verificado):")
    rag = ChessRAG(
        collection_name="chess_knowledge",
        persist_directory=str(project_root / "data" / "chess_books" / "chroma_db"),
        embedding_model="all-MiniLM-L6-v2",
    )
    context = rag.get_context_for_prompt(question, n_results=2)

    prompt_with = f"""
Contexto verificado:
{context}

Pregunta: {question}

Responde usando SOLO el contexto anterior.
"""

    response_with = llm.invoke(prompt_with)
    print(response_with[:300] + "...\n")

    print("📊 CONCLUSIÓN:")
    print("   Sin RAG: Puede tener información incorrecta o inventada")
    print("   Con RAG: Respuesta basada en fuentes verificadas")


def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "=" * 70)
    print("🚀 PRUEBAS DE INTEGRACIÓN: RAG + LLM para AI Chess Coach")
    print("=" * 70)

    # Test 1: RAG solo
    rag_ok = test_rag_retrieval()

    if not rag_ok:
        return

    input("\n⏸️  Presiona ENTER para continuar con la integración completa...")

    # Test 2: RAG + LLM
    test_rag_with_llm()

    input("\n⏸️  Presiona ENTER para ver la comparación SIN vs CON RAG...")

    # Test 3: Comparación
    test_comparison_without_rag()

    print("\n" + "=" * 70)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 70)
    print("\n🎯 Sistema listo para:")
    print("   1. Análisis de partidas con contexto teórico")
    print("   2. Recomendaciones de aperturas basadas en libros")
    print("   3. Explicaciones de conceptos con fuentes verificadas")
    print("\n💡 Siguiente paso:")
    print("   Implementar coach_pipeline.py para integración completa\n")


if __name__ == "__main__":
    main()
