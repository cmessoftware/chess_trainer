# SPEC: sdd_engine (Spec-Driven Decision Engine) — UPDATED

## PURPOSE

Build a **decoupled, spec-driven validation engine** that:

- Uses **OpenSpec as the single source of truth (rules)**
- Loads specs at runtime via a **parser**
- Executes rules via a **deterministic validator**
- Persists execution metadata (not rules) in **SQLite (SQLAlchemy)**
- Is **fully independent from ChessInsight**
- Can be:
  - extracted to another repo
  - packaged as a pip module
  - migrated to PostgreSQL without refactor
- Exposes services via **FastAPI**

---

## CORE PRINCIPLE

```text
OpenSpec (WHAT) ≠ Runtime (EXECUTION)

## SDD Validation Board Specs

**Visualize in real-time the compliance status of system specs.**

### MVP Architecture

```
tests + validators
        │
        ▼
verification logs (JSON)
        │
        ▼
aggregator service
        │
        ▼
Streamlit dashboard
```

### Componentes

1. Validator Engine
valida contracts
chequea invariantes
ejecuta reglas Critic

Salida:

```json
{
  "spec_id": "S04c",
  "rule": "no insight without evidence",
  "status": "FAIL",
  "trace_id": "abc123",
  "evidence": null
}
```

2. Verification Store

Formato:
JSON logs (PostgreSQL)

Campos:

- spec_id
- component
- rule
- status
- timestamp
- trace_id
- game_id


3. Aggregator

Responsabilidad:

- consolidar resultados
- calcular métricas

Ejemplo:

- % specs cumplidos
- fallas por componente
- tendencias

4. Dashboard (Streamlit)

Secciones:

A. Overview
- % cumplimiento global
- specs OK vs FAIL

B. Por componente

- PGN
- Features
- ML
- Planner
- Executor
- Critic
- Memory

C. Drill-down

- ver fallas por trace_id
- inspeccionar evidencia

D. Golden Games

- comparación contra baseline

Métricas clave

- spec_compliance_rate
- failed_rules_count
- insights_rejected_rate
- confidence_distribution
- engine_vs_ml_consistency

### MVP mínimo funcional

Debe incluir:

10 PGNs de prueba
- validadores básicos:
  - schema
  - invariantes
  - critic con 3 reglas
  - logs JSON
  
- dashboard Streamlit con:
  - tabla de specs
  - estado
  - filtro por game_id

### Estructura proyecto

```
verification/
├── validators/
├── rules/
├── logs/
├── aggregator/
├── dashboard/
│   └── app.py
└── datasets/
    └── golden_games/
```

### Regla central del Board

- El board no mide actividad.
- Mide cumplimiento de garantías del sistema.

### Extensión futura

alertas automáticas
- integración CI/CD
- gating de deploy si falla Critic
- scoring de calidad del análisis

### Resultado

- el pipeline deja de ser “caja negra”
- cada output es auditable
- el sistema se vuelve verificable
- se elimina ambigüedad estructural
- base sólida para paper o producto