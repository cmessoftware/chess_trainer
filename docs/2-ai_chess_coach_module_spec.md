# ChessTrainer AI Coach – Module Specification

This document defines the expected architecture, classes and responsibilities for the AI Coach module in ChessTrainer.

The goal is to generate **natural language coaching reports** based on:

- Stockfish analysis
- ML features
- RAG knowledge retrieval
- LLM (Ollama)

The system should be modular and extensible.

---

# Overall Pipeline

PGN  
→ Stockfish analysis  
→ feature extraction  
→ ML predictions  
→ feature summarizer  
→ RAG retrieval  
→ prompt builder  
→ LLM generation  
→ coaching report

---

# Module Layout

chess_trainer/

analysis/
ai_coach/
rag/
llm/

---

# ai_coach Module

Responsible for orchestrating the generation of coaching reports.

Files:

feature_summarizer.py  
prompt_builder.py  
report_generator.py  
coach_service.py  

---

# Class: FeatureSummarizer

Purpose:

Transform raw ML and Stockfish data into a structured summary that the LLM can interpret safely.

Input:

- Stockfish evaluation
- tactical tags
- ML error predictions
- game metadata

Output:

Structured text summary.

Example output:

Opening: Italian Game

Critical moments:
- move 17 mistake
- move 24 blunder

Patterns detected:
- weak king safety
- loss of central control

Tactical motifs:
- fork
- pinned piece

Methods:

summarize_game(game_analysis)

extract_patterns(features)

extract_critical_moments(stockfish_analysis)

detect_tactical_motifs(tactical_tags)

---

# Class: PromptBuilder

Purpose:

Build a constrained prompt for the LLM to reduce hallucinations.

Methods:

build_prompt(summary, retrieved_docs)

generate_system_prompt()

generate_user_prompt(summary, retrieved_docs)

Prompt structure:

System role:
"You are a chess coach."

User input:

Game summary  
Retrieved chess knowledge

Expected output format:

Strengths  
Weaknesses  
Improvement suggestions

---

# Class: ReportGenerator

Purpose:

Call the LLM and produce a final coaching report.

Methods:

generate_report(prompt)

postprocess_output(llm_output)

validate_report(report)

The output should follow a consistent structure.

Example:

Strengths
Weaknesses
Improvement suggestions

---

# Class: CoachService

Purpose:

Main orchestration class.

Pipeline:

1 summarize game
2 retrieve chess knowledge
3 build prompt
4 generate report

Methods:

generate_coaching_report(game_analysis)

Workflow:

summary = feature_summarizer.summarize_game()

docs = rag_retriever.retrieve(summary)

prompt = prompt_builder.build_prompt(summary, docs)

report = report_generator.generate_report(prompt)

return report

---

# rag Module

Responsible for knowledge retrieval.

Files:

document_loader.py  
text_chunker.py  
embedding_generator.py  
vector_store.py  
retriever.py  

---

# Class: DocumentLoader

Load chess books from disk.

Input:

PDF files

Methods:

load_documents(path)

extract_text(pdf_file)

clean_text(text)

---

# Class: TextChunker

Split text into smaller segments for embeddings.

Recommended chunk size:

500–800 tokens

Methods:

chunk_text(text)

create_overlapping_chunks(text)

---

# Class: EmbeddingGenerator

Generate embeddings for text chunks.

Use SentenceTransformers.

Methods:

load_embedding_model()

generate_embedding(text)

batch_generate_embeddings(chunks)

---

# Class: VectorStore

Responsible for storing embeddings.

Use Chroma as default implementation.

Methods:

create_collection()

add_documents(chunks, embeddings)

search(query_embedding, top_k)

---

# Class: Retriever

Perform semantic search.

Methods:

retrieve(query, top_k)

convert_query_to_embedding(query)

return relevant passages

---

# llm Module

Responsible for communication with Ollama.

Files:

ollama_client.py

---

# Class: OllamaClient

Purpose:

Call local LLM via Ollama API.

Methods:

generate(prompt)

generate_with_parameters(prompt, temperature, max_tokens)

health_check()

Model configuration:

llama3  
mistral  
phi3

---

# Data Layout

data/

chess_books/  
embeddings/  
rag_index/

Books should be stored in:

data/chess_books/

---

# Example Flow

1 Load chess books
2 Extract text
3 Chunk text
4 Generate embeddings
5 Store embeddings in vector DB
6 Retrieve relevant passages during coaching

---

# Anti-Hallucination Constraints

The LLM must follow these rules:

- Never analyze PGN directly
- Use structured game summaries
- Use retrieved chess knowledge
- Avoid unsupported claims
- Respond "insufficient data" if context is missing

---

# Expected Output Format

Strengths
- ...

Weaknesses
- ...

Improvement suggestions
- ...

---

# Future Extensions

Possible improvements:

- embeddings for chess positions (FEN)
- clustering common mistakes
- personalized training plans
- conversational chess coach