#!/usr/bin/env python3
"""
Prueba de Ollama con contexto específico de ajedrez (RAG simulado)
Demuestra la diferencia entre modelo SIN contexto vs CON contexto
"""

from langchain_ollama import OllamaLLM

OLLAMA_BASE_URL = "http://localhost:11434"

# Contexto verificado sobre la Apertura Italiana
ITALIAN_GAME_CONTEXT = """
CONOCIMIENTO VERIFICADO SOBRE LA APERTURA ITALIANA:

La Apertura Italiana (Italian Game) es una apertura de ajedrez que comienza con:
1. e4 e5
2. Nf3 Nc6
3. Bc4

VARIANTES PRINCIPALES:

1. GIUOCO PIANO (Juego Tranquilo)
   - Movimientos: 1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.c3
   - Objetivo blancas: Controlar centro con d4
   - Objetivo negras: Contrajuego en el centro
   
2. GIUOCO PIANISSIMO (Juego Muy Tranquilo)
   - Movimientos: 1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.d3
   - Objetivo: Desarrollo sólido y seguro
   - Popular en ajedrez moderno de élite
   
3. DEFENSA DE LOS DOS CABALLOS
   - Movimientos: 1.e4 e5 2.Nf3 Nc6 3.Bc4 Nf6
   - Negras atacan el peón e4
   - Blancas pueden jugar 4.Ng5 (agresivo) o 4.d3 (posicional)

4. GAMBITO EVANS
   - Movimientos: 1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.b4
   - Sacrificio de peón por desarrollo rápido
   - Muy táctico y agresivo

PRINCIPIOS ESTRATÉGICOS:
- Blancas: Control del centro (e4), desarrollo rápido del alfil (Bc4 apunta a f7)
- Negras: Contrajuego central, desarrollo armonioso
- El alfil en c4 es característico de esta apertura
"""

def test_without_context():
    """Probar modelo SIN contexto (como lo hicimos antes)"""
    print("\n" + "="*70)
    print("❌ PRUEBA 1: MODELO SIN CONTEXTO (Alucinaciones)")
    print("="*70)
    
    llm = OllamaLLM(
        model="llama3.2:3b",
        base_url=OLLAMA_BASE_URL,
        temperature=0.3
    )
    
    prompt = "Explica brevemente la Apertura Italiana en ajedrez y sus principales variantes"
    print(f"\n📝 Prompt: {prompt}\n")
    
    response = llm.invoke(prompt)
    print(f"💬 Respuesta (SIN CONTEXTO):\n{response}\n")
    print("⚠️ PROBLEMA: El modelo puede inventar información incorrecta")

def test_with_context():
    """Probar modelo CON contexto (RAG simulado)"""
    print("\n" + "="*70)
    print("✅ PRUEBA 2: MODELO CON CONTEXTO (RAG Simulado)")
    print("="*70)
    
    llm = OllamaLLM(
        model="llama3.2:3b",
        base_url=OLLAMA_BASE_URL,
        temperature=0.3
    )
    
    prompt_with_context = f"""
Usando SOLO la información del siguiente contexto verificado, responde la pregunta.
NO inventes información que no esté en el contexto.

CONTEXTO:
{ITALIAN_GAME_CONTEXT}

PREGUNTA: Explica la Apertura Italiana y sus principales variantes de forma clara y precisa.

INSTRUCCIONES:
1. Menciona los movimientos iniciales correctos
2. Explica las 4 variantes principales
3. No agregues información que no esté en el contexto
4. Sé preciso con las notaciones de ajedrez
"""
    
    print(f"📝 Prompt: Pregunta con contexto RAG inyectado\n")
    
    response = llm.invoke(prompt_with_context)
    print(f"💬 Respuesta (CON CONTEXTO):\n{response}\n")
    print("✅ SOLUCIÓN: Respuesta basada en conocimiento verificado")

def test_specific_variant():
    """Pregunta específica sobre variante con contexto"""
    print("\n" + "="*70)
    print("🎯 PRUEBA 3: PREGUNTA ESPECÍFICA CON CONTEXTO")
    print("="*70)
    
    llm = OllamaLLM(
        model="llama3.2:3b",
        base_url=OLLAMA_BASE_URL,
        temperature=0.3
    )
    
    prompt = f"""
CONTEXTO:
{ITALIAN_GAME_CONTEXT}

PREGUNTA: ¿Cuál es la diferencia entre el Giuoco Piano y el Giuoco Pianissimo?
Responde usando SOLO la información del contexto.
"""
    
    print("📝 Pregunta: Diferencia entre Giuoco Piano y Pianissimo\n")
    
    response = llm.invoke(prompt)
    print(f"💬 Respuesta:\n{response}\n")

def main():
    print("\n" + "="*70)
    print("🧪 DEMOSTRACIÓN: IMPORTANCIA DE RAG EN AI CHESS COACH")
    print("="*70)
    print("\n📌 Objetivo: Mostrar cómo RAG elimina alucinaciones\n")
    
    # Test 1: Sin contexto (malo)
    test_without_context()
    
    input("\n⏸️  Presiona ENTER para continuar con la prueba CON contexto...")
    
    # Test 2: Con contexto (bueno)
    test_with_context()
    
    input("\n⏸️  Presiona ENTER para ver una pregunta específica...")
    
    # Test 3: Pregunta específica
    test_specific_variant()
    
    print("\n" + "="*70)
    print("📊 CONCLUSIÓN")
    print("="*70)
    print("\n✅ RAG (Contexto inyectado) = Respuestas precisas y verificables")
    print("❌ Sin RAG = Alucinaciones e información incorrecta")
    print("\n🎯 SIGUIENTE PASO:")
    print("   Implementar sistema RAG completo con:")
    print("   - ChromaDB para almacenar conocimiento de ajedrez")
    print("   - Embeddings de libros de ajedrez (PDFs)")
    print("   - Recuperación automática de contexto relevante")
    print("   - Validación con python-chess\n")

if __name__ == "__main__":
    main()
