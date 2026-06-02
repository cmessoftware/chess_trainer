"""
Arquitectura Orquestada - Módulo Principal

Este módulo implementa la arquitectura orquestada para análisis de partidas:
- Planner: Decide QUÉ analizar
- Executor: Produce EVIDENCIA objetiva
- Critic: Valida COHERENCIA
- Memory: Persiste y aprende PATRONES
- Explainer: LLM solo EXPLICA

Fase 1: Planner + Executor + Memory
"""

from .schemas import (
    AnalysisOptions,
    AnalysisPlan,
    ExecutionResult,
    CriticResult,
    EnrichedResult,
    AnalysisReport,
)

__all__ = [
    "AnalysisOptions",
    "AnalysisPlan",
    "ExecutionResult",
    "CriticResult",
    "EnrichedResult",
    "AnalysisReport",
]
