# ⚡ AI Chess Coach - Quick Start

Guía rápida para implementar el sistema de AI Chess Coach según el [roadmap](0-ai_chess_coach_roadmap.md).

---

## 🚀 Instalación en 3 Pasos

### 1️⃣ Instalar Dependencias Python

```powershell
# CRITICAL: Activar ambiente conda
conda activate chess_trainer

# Instalar dependencias
pip install -r requirements_ai_coach.txt
```

### 2️⃣ Instalar Ollama (Servidor LLM)

```powershell
# Opción A: Con winget
winget install Ollama.Ollama

# Opción B: Descargar manualmente
# https://ollama.ai/download

# Verificar instalación
ollama --version

# Descargar modelo recomendado (3GB)
ollama pull llama3.2:3b
```

### 3️⃣ Configurar Proyecto

```powershell
# Ejecutar script de setup automático
.\setup_ai_coach.ps1 -InstallAll
```

---

## ✅ Verificar Instalación

```powershell
# Probar todos los componentes
python src/scripts/test_ai_coach_pipeline.py
```

**Salida esperada:**
```
✅ imports: PASS
✅ embedding_model: PASS
✅ vector_database: PASS
✅ ollama: PASS
✅ pdf_processing: PASS
✅ project_structure: PASS

🎉 All tests passed! AI Coach system is ready.
```

---

## 📂 Estructura Creada

```
src/ai_coach/
├── feature_summarizer.py    # ⏳ TODO: Implementar
├── coach_pipeline.py         # ⏳ TODO: Implementar
├── rag/
│   └── chess_rag.py         # ⏳ TODO: Implementar
├── llm/
│   └── coaching_llm.py      # ⏳ TODO: Implementar
└── prompts/

data/
├── chess_books/
│   ├── raw/                 # 📚 Agregar PDFs aquí
│   └── processed/
└── vectorstore/             # 🗄️ Base de datos vectorial

tests/ai_coach/              # 🧪 Tests unitarios
```

---

## 🎯 Próximos Pasos de Implementación

### Fase 2: Feature Summarizer
```python
# src/ai_coach/feature_summarizer.py
# Implementar conversión de features ML → summaries para LLM
```

### Fase 3: RAG System
```python
# src/ai_coach/rag/chess_rag.py
# Implementar ChromaDB + SentenceTransformers
# Indexar libros de ajedrez y recuperar conocimiento
```

### Fase 4: LLM Integration
```python
# src/ai_coach/llm/coaching_llm.py
# Implementar Ollama + Langchain
# Generar reportes de coaching estructurados
```

### Fase 5: Complete Pipeline
```python
# src/ai_coach/coach_pipeline.py
# Orquestar: Features → Summarizer → RAG → LLM → Output
```

---

## 🧪 Flujo de Testing

```powershell
# 1. Test de componentes individuales
pytest tests/ai_coach/test_feature_summarizer.py -v
pytest tests/ai_coach/test_rag.py -v
pytest tests/ai_coach/test_llm.py -v

# 2. Test de integración
pytest tests/ai_coach/test_pipeline.py -v

# 3. Test end-to-end
python src/scripts/test_ai_coach_pipeline.py
```

---

## 📚 Libros de Ajedrez Recomendados (RAG)

Agregar PDFs en `data/chess_books/raw/`:

| Libro                      | Autor                | Tema       |
| -------------------------- | -------------------- | ---------- |
| My System                  | Aron Nimzowitsch     | Estrategia |
| Logical Chess Move by Move | Irving Chernev       | Táctica    |
| The Art of Attack in Chess | Vladimir Vukovic     | Ataque     |
| Endgame Strategy           | Mikhail Shereshevsky | Finales    |

---

## 🔧 Comandos Útiles

```powershell
# Iniciar servidor Ollama (si no está corriendo)
ollama serve

# Ver modelos instalados
ollama list

# Probar modelo interactivamente
ollama run llama3.2:3b

# Verificar estado de instalación
.\setup_ai_coach.ps1 -CheckDependencies

# Re-crear estructura de directorios
.\setup_ai_coach.ps1 -CreateStructure
```

---

## 🚨 Troubleshooting

### Error: "conda environment not activated"
```powershell
conda activate chess_trainer
```

### Error: "Cannot connect to Ollama"
```powershell
# Iniciar servidor Ollama
ollama serve

# O verificar si está corriendo
Invoke-WebRequest http://localhost:11434
```

### Error: "Model not found"
```powershell
# Descargar modelo
ollama pull llama3.2:3b

# Ver modelos disponibles
ollama list
```

### Error: "Import errors"
```powershell
# Reinstalar dependencias
pip install -r requirements_ai_coach.txt --force-reinstall
```

---

## 📖 Documentación Completa

| Documento                                                            | Descripción                     |
| -------------------------------------------------------------------- | ------------------------------- |
| [AI_COACH_IMPLEMENTATION_GUIDE.md](AI_COACH_IMPLEMENTATION_GUIDE.md) | Guía completa de implementación |
| [0-ai_chess_coach_roadmap.md](0-ai_chess_coach_roadmap.md)           | Roadmap general del sistema     |
| [1-ai_chess_coach_rag_design.md](1-ai_chess_coach_rag_design.md)     | Diseño del sistema RAG          |
| [2-ai_chess_coach_module_spec.md](2-ai_chess_coach_module_spec.md)   | Especificación de módulos       |

---

## 💡 Stack Tecnológico

| Componente     | Tecnología           | Propósito                 |
| -------------- | -------------------- | ------------------------- |
| Embeddings     | SentenceTransformers | Vectorización de texto    |
| Vector DB      | ChromaDB             | Almacenamiento y búsqueda |
| LLM            | Ollama (Llama 3.2)   | Generación de reportes    |
| Framework      | Langchain            | Orquestación LLM          |
| PDF Processing | PyPDF2, pdfplumber   | Extracción de libros      |

---

## 📊 Modelos LLM Disponibles

| Modelo      | Tamaño | RAM  | Velocidad | Uso                |
| ----------- | ------ | ---- | --------- | ------------------ |
| llama3.2:3b | 3GB    | 8GB  | ⚡⚡⚡       | Desarrollo/Testing |
| mistral:7b  | 4.1GB  | 16GB | ⚡⚡        | Producción         |
| llama3.1:8b | 4.7GB  | 16GB | ⚡⚡        | Producción         |
| phi3:medium | 7.9GB  | 32GB | ⚡         | Enterprise         |

---

**Estado:** ✅ Listo para implementación  
**Última actualización:** 2026-03-13  
**Siguiente paso:** Implementar `feature_summarizer.py`
