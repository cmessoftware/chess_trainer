```mermaid
ChessTrainer Analysis System
│
├── [Kasparov-Inspired Analysis Module](8.1-ai_chess_coach_kasparov_inspired_functional.md)
│     (pipeline conceptual)
│
│     PGN
│      ↓
│     feature extraction
│      ↓
│     critical moment detection
│      ↓
│     candidate generation
│      ↓
│     engine evaluation
│      ↓
│     error classification
│      ↓
│     dataset generation
│
└── [Kasparov Decision Engine](8.2-ai_chess_coach_kasparov_technical_design.md)
      (implementación interna del pipeline)

      ├ Position Interpreter
      ├ Critical Moment Detector
      ├ Plan Inference Engine
      ├ Candidate Generator
      ├ Candidate Ranking Engine
      ├ Decision Classification Engine
      ├ Coach Narrative Engine
      └ Pattern Memory Engine`
```