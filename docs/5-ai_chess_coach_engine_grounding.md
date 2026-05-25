# ChessTrainer – Engine Grounded RAG for AI Coach

## Objective

Extend the current ChessTrainer RAG pipeline so that the LLM never invents chess moves.

The chess engine (Stockfish) must be the **source of truth for tactical correctness**.

The LLM is only responsible for **explaining the engine analysis**.

---

# Problem

Small LLM models (for example llama3.2:3b running in Ollama) frequently hallucinate chess moves.

Example problems:

- suggesting illegal moves
- suggesting blunders
- missing simple refutations
- inventing variations

Therefore the AI Coach must use **engine-grounded reasoning**.

---

# Architecture

Current pipeline:

PGN
→ feature extraction
→ embeddings
→ vector database
→ retrieve similar positions
→ LLM explanation

Improved pipeline:

PGN
→ feature extraction
→ Stockfish analysis
→ embeddings
→ vector retrieval
→ structured analysis
→ LLM explanation

---

# Engine Grounding

Stockfish provides:

- best move
- top candidate moves
- evaluation
- tactical motifs

Example structured output:

```json
{
  "fen": "...",
  "best_move": "Nxc6",
  "candidate_moves": [
    {"move": "Nxc6", "eval": 1.8},
    {"move": "Qe4", "eval": 1.2},
    {"move": "Rb7", "eval": 1.0}
  ],
  "played_move": "Qxd5+",
  "played_eval": -5.3
}