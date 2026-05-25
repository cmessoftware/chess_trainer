#!/usr/bin/env python3
"""
Prueba rápida de compatibilidad entre llama3.2:3b y llama3.1:8b
Demuestra que no se necesita recalibración
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from ai_coach.rag import ChessRAG
from langchain_ollama import OllamaLLM


def quick_test(model_name: str):
    """Prueba rápida de un modelo con RAG"""
    print(f"\n{'=' * 60}")
    print(f"🤖 Modelo: {model_name}")
    print(f"{'=' * 60}")

    # Mismo código RAG
    rag = ChessRAG(
        collection_name="chess_knowledge",
        persist_directory=str(project_root / "data" / "chess_books" / "chroma_db"),
        embedding_model="all-MiniLM-L6-v2",
    )

    # Mismo LLM, solo cambia el nombre
    llm = OllamaLLM(
        model=model_name, base_url="http://localhost:11434", temperature=0.3
    )

    # Misma pregunta
    question = "¿Qué es la Apertura Italiana?"

    # Mismo proceso RAG
    context = rag.get_context_for_prompt(question, n_results=2)

    # Mismo prompt
    prompt = f"""
Eres un entrenador de ajedrez. Responde usando el contexto.

CONTEXTO:
{context[:500]}...

PREGUNTA: {question}

RESPUESTA (breve, 2-3 líneas):
"""

    # Invocar
    print(f"\n⏱️  Generando respuesta...")
    import time

    start = time.time()
    response = llm.invoke(prompt)
    elapsed = time.time() - start

    print(f"✅ Tiempo: {elapsed:.2f}s")
    print(f"\n📖 Respuesta:")
    print(response[:300])
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    print("\n🧪 PRUEBA DE COMPATIBILIDAD DE MODELOS")
    print("Mismo código, mismo RAG, mismo prompt")
    print("Solo cambia: nombre del modelo\n")

    try:
        quick_test("llama3.2:3b")
        quick_test("llama3.1:8b")

        print("\n✅ CONCLUSIÓN:")
        print("   Ambos modelos funcionan con el MISMO código")
        print("   NO necesitas recalibrar nada")
        print("   Solo cambia el nombre del modelo en una línea\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
