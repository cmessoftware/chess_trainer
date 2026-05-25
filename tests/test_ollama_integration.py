#!/usr/bin/env python3
"""
Script de prueba para verificar integración con Ollama en Docker
"""

import os
import sys
from langchain_ollama import OllamaLLM

# Configurar URL de Ollama
OLLAMA_BASE_URL = "http://localhost:11434"

def test_ollama_connection():
    """Verificar que Ollama está accesible"""
    print("🔍 Verificando conexión con Ollama...")
    
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=5)
        if response.status_code == 200:
            print(f"✅ Ollama conectado: {response.json()}")
            return True
        else:
            print(f"❌ Error de conexión: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar a Ollama: {e}")
        print(f"   Asegúrate de que el contenedor esté corriendo: docker ps | grep ollama")
        return False

def test_llama_model():
    """Probar modelo llama3.2:3b con una pregunta de ajedrez"""
    print("\n🧪 Probando modelo llama3.2:3b...")
    
    try:
        # Inicializar modelo
        llm = OllamaLLM(
            model="llama3.2:3b",
            base_url=OLLAMA_BASE_URL,
            temperature=0.7
        )
        
        # Prueba 1: Pregunta simple sobre ajedrez
        print("\n📝 Pregunta 1: ¿Qué es un mate pastor?")
        response1 = llm.invoke("Explica en español de forma breve qué es un mate pastor en ajedrez (máximo 2 párrafos)")
        print(f"\n💬 Respuesta:\n{response1}\n")
        
        # Prueba 2: Análisis de apertura
        print("\n📝 Pregunta 2: Consejos sobre la Apertura Italiana")
        response2 = llm.invoke("Dame 3 consejos clave para jugar la Apertura Italiana en ajedrez")
        print(f"\n💬 Respuesta:\n{response2}\n")
        
        # Prueba 3: Análisis de posición (simulado)
        print("\n📝 Pregunta 3: Análisis de posición")
        position_context = """
        Posición después de 1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5
        - Material: Igualado
        - Control del centro: Blancas controlan e4, Negras e5
        - Desarrollo: 2 piezas desarrolladas por bando
        """
        response3 = llm.invoke(f"Analiza esta posición de ajedrez y sugiere el siguiente movimiento para las blancas:\n{position_context}")
        print(f"\n💬 Respuesta:\n{response3}\n")
        
        print("=" * 70)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ Error al ejecutar el modelo: {e}")
        print(f"   Verifica que el modelo esté descargado: docker exec chess_trainer_ollama ollama list")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "=" * 70)
    print("🚀 PRUEBA DE INTEGRACIÓN OLLAMA + LLAMA3.2:3B")
    print("=" * 70)
    
    # Test 1: Conexión
    if not test_ollama_connection():
        sys.exit(1)
    
    # Test 2: Modelo
    if not test_llama_model():
        sys.exit(1)
    
    print("\n💡 Siguiente paso: Implementar el AI Coach en src/ai_coach/")
    print("   - chess_rag.py: Sistema de recuperación de conocimiento")
    print("   - coaching_llm.py: Integración con LLM")
    print("   - coach_pipeline.py: Pipeline completo\n")

if __name__ == "__main__":
    main()
