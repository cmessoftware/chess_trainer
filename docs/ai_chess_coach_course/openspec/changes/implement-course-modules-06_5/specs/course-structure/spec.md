# Delta: course-structure

## ADDED Requirements

### Requirement: Module 6.5 Canonical Delivery
Module 6.5 SHALL be implemented as an independently trackable course change between Module 06 and Module 07.

#### Scenario: Module 6.5 implementation check
- Given change implement-course-modules-06_5 is active
- When implementation artifacts are reviewed
- Then notebook `06_5_llm_coaching_recommendations.ipynb` SHALL exist and reflect Module 6.5 objectives.

### Requirement: Provider-Agnostic LLM Layer
Module 6.5 SHALL implement an `LLMProvider` abstraction with Gemini 2.5 Flash as the default provider via `google-genai` and `GEMINI_API_KEY`.

#### Scenario: Gemini provider isolation
- Given the coaching pipeline code is reviewed
- When imports are traced
- Then only `llm/gemini_provider.py` SHALL import the Google GenAI SDK.

### Requirement: Structured Coaching Context
Module 6.5 SHALL build LLM prompts from structured JSON context only; raw SHAP arrays and engine-proxy features SHALL NOT be sent to the LLM.

#### Scenario: Context payload validation
- Given a sample context artifact is generated
- When the JSON is inspected
- Then it SHALL contain coaching patterns and metadata but SHALL NOT contain SHAP value arrays or `score_cp` fields.

### Requirement: First Course Version Arc
Module 6.5 SHALL complete the first shippable explainability-to-coaching arc without requiring RAG (Module 07) or local LLM runtime (Module 08).

#### Scenario: Dependency boundary
- Given Module 6.5 is marked complete
- When Module 07 RAG is not yet implemented
- Then students SHALL still obtain a coaching recommendation from the 6.5 notebook using Gemini.
