"""
Schemas para Arquitectura Orquestada

Define los modelos Pydantic que sirven de contrato entre módulos.
Basado en la especificación técnica de Fase 0.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


# ============================================================================
# 1. ANALYSIS OPTIONS (Input)
# ============================================================================

class AnalysisOptions(BaseModel):
    """Opciones de configuración del análisis."""

    depth: int = Field(
        default=20,
        ge=10,
        le=40,
        description="Profundidad de análisis de Stockfish",
    )

    enable_ml: bool = Field(
        default=True,
        description="Activar predicción ML",
    )

    enable_rag: bool = Field(
        default=True,
        description="Activar recuperación RAG",
    )

    enable_cv: bool = Field(
        default=False,
        description="Activar extracción CV",
    )

    elo_threshold: Optional[int] = Field(
        default=None,
        ge=800,
        le=3000,
        description="ELO del jugador para adaptación",
    )

    focus_mode: Literal["critical", "full", "tactical", "positional"] = Field(
        default="critical",
        description="Modo de enfoque",
    )

    @validator("depth")
    def depth_must_be_multiple_of_5(cls, v):
        """Depth debe ser múltiplo de 5 para eficiencia."""
        if v % 5 != 0:
            raise ValueError("depth must be multiple of 5")
        return v

    class Config:
        schema_extra = {
            "example": {
                "depth": 20,
                "enable_ml": True,
                "enable_rag": True,
                "enable_cv": False,
                "elo_threshold": 1800,
                "focus_mode": "critical",
            }
        }


# ============================================================================
# 2. ANALYSIS PLAN (Planner Output)
# ============================================================================

class AnalysisPlan(BaseModel):
    """Plan de análisis generado por Planner."""

    game_id: UUID = Field(description="ID de la partida")

    target_moves: List[int] = Field(
        description="Índices de jugadas a analizar (0-based)"
    )

    analysis_modes: List[Literal["engine", "features", "ml", "rag", "cv"]] = Field(
        min_items=1,
        description="Modos de análisis activos",
    )

    priorities: Dict[int, Literal["high", "medium", "low"]] = Field(
        default_factory=dict,
        description="Prioridades por índice de jugada",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata adicional",
    )

    options: AnalysisOptions = Field(description="Opciones originales")

    class Config:
        schema_extra = {
            "example": {
                "game_id": "550e8400-e29b-41d4-a716-446655440000",
                "target_moves": [5, 12, 18, 23, 31],
                "analysis_modes": ["engine", "features", "ml", "rag"],
                "priorities": {
                    "5": "low",
                    "12": "high",
                    "18": "medium",
                    "23": "high",
                    "31": "medium",
                },
                "metadata": {
                    "total_moves": 45,
                    "player_color": "white",
                    "result": "1-0",
                },
            }
        }


# ============================================================================
# 3. EXECUTION RESULT (Executor Output)
# ============================================================================

class MLPrediction(BaseModel):
    """Predicción del modelo ML."""

    predicted_error: Literal["good", "inaccuracy", "mistake", "blunder"]
    confidence: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    contributing_features: List[Dict[str, Any]] = Field(default_factory=list)


class RAGContext(BaseModel):
    """Contexto recuperado por RAG."""

    similar_positions: List[Dict[str, Any]] = Field(default_factory=list)
    book_excerpts: List[str] = Field(default_factory=list)
    player_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    total_retrieved: int = Field(ge=0)
    relevance_scores: List[float] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    """Resultado de ejecución de análisis de una jugada."""

    # Identificación
    game_id: UUID
    ply: int = Field(ge=0)
    move_san: str
    fen_before: str
    fen_after: str

    # Evaluación Engine
    engine_eval_before: float
    engine_eval_after: float
    score_diff: float
    best_move: str
    best_line: List[str] = Field(default_factory=list)

    # Features
    features: Dict[str, float] = Field(default_factory=dict)
    tactical_tags: List[str] = Field(default_factory=list)
    phase: Literal["opening", "middlegame", "endgame"]

    # ML + RAG
    ml_prediction: Optional[MLPrediction] = None
    rag_context: Optional[RAGContext] = None

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_time: float = Field(ge=0.0)

    @validator("score_diff", always=True)
    def compute_score_diff(cls, v, values):
        """Auto-calcula score_diff si no está presente."""
        if v is None and "engine_eval_after" in values and "engine_eval_before" in values:
            return values["engine_eval_after"] - values["engine_eval_before"]
        return v

    class Config:
        schema_extra = {
            "example": {
                "game_id": "550e8400-e29b-41d4-a716-446655440000",
                "ply": 12,
                "move_san": "Bxf7+",
                "fen_before": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq -",
                "fen_after": "r1bqkb1r/pppp1Bpp/2n2n2/4p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq -",
                "engine_eval_before": 50,
                "engine_eval_after": -150,
                "score_diff": -200,
                "best_move": "Nc3",
                "best_line": ["Nc3", "d6", "d4", "exd4"],
                "features": {
                    "king_safety": 0.3,
                    "material_balance": 0.0,
                    "center_control": 0.6,
                },
                "tactical_tags": ["sacrifice", "discovered_check"],
                "phase": "middlegame",
                "execution_time": 2.35,
            }
        }


# ============================================================================
# 4. CRITIC RESULT (Critic Output)
# ============================================================================

class ValidationIssue(BaseModel):
    """Problema detectado por el Critic."""

    rule_name: str
    severity: Literal["error", "warning", "info"]
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)


class CriticResult(BaseModel):
    """Resultado de validación del Critic."""

    is_consistent: bool = Field(description="¿Pasa validación?")
    confidence: float = Field(ge=0.0, le=1.0, description="Confianza 0-1")
    issues: List[ValidationIssue] = Field(default_factory=list)
    passed_rules: List[str] = Field(default_factory=list)
    failed_rules: List[str] = Field(default_factory=list)

    @validator("is_consistent", always=True)
    def consistent_if_no_errors(cls, v, values):
        """is_consistent debe ser False si hay issues con severity=error."""
        issues = values.get("issues", [])
        has_errors = any(issue.severity == "error" for issue in issues)

        if has_errors and v:
            raise ValueError("Cannot be consistent with error-level issues")

        return v

    class Config:
        schema_extra = {
            "example": {
                "is_consistent": False,
                "confidence": 0.65,
                "issues": [
                    {
                        "rule_name": "BlunderScoreThreshold",
                        "severity": "error",
                        "message": "ML predice blunder pero score_diff muy bajo",
                        "context": {"score_diff": -50},
                    }
                ],
                "passed_rules": ["PositionLegalityCheck", "TacticalEvidenceRequired"],
                "failed_rules": ["BlunderScoreThreshold"],
            }
        }


# ============================================================================
# 5. ENRICHED RESULT (Final Output per Move)
# ============================================================================

class EnrichedResult(BaseModel):
    """Resultado enriquecido con explicación y crítica."""

    execution_result: ExecutionResult
    explanation: str = Field(description="Explicación pedagógica")
    critic_result: CriticResult
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_high_quality(self) -> bool:
        """Helper: resultado de alta calidad."""
        return (
            self.critic_result.is_consistent
            and self.critic_result.confidence >= 0.85
        )

    @property
    def requires_review(self) -> bool:
        """Helper: requiere revisión manual."""
        return (
            not self.critic_result.is_consistent
            or self.critic_result.confidence < 0.70
        )

    class Config:
        schema_extra = {
            "example": {
                "execution_result": {
                    "game_id": "550e8400-e29b-41d4-a716-446655440000",
                    "ply": 12,
                    "move_san": "Nc3",
                    "score_diff": 30,
                    "best_move": "Nc3",
                    "phase": "opening",
                },
                "explanation": "Nc3 desarrolla el caballo hacia el centro con tempo.",
                "critic_result": {
                    "is_consistent": True,
                    "confidence": 0.95,
                    "issues": [],
                    "passed_rules": ["BlunderScoreThreshold", "EngineSupportRequired"],
                },
                "metadata": {
                    "plan_priority": "medium",
                    "version": "v2.0-orchestrated",
                    "requires_review": False,
                },
            }
        }


# ============================================================================
# 6. ANALYSIS REPORT (Final Output)
# ============================================================================

class AnalysisReport(BaseModel):
    """Reporte completo de análisis de partida."""

    game_id: UUID
    player_id: int
    total_moves_analyzed: int = Field(ge=0)
    enriched_results: List[EnrichedResult]
    player_patterns: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def consistency_rate(self) -> float:
        """% de resultados consistentes."""
        if not self.enriched_results:
            return 0.0
        consistent = sum(
            1 for r in self.enriched_results if r.critic_result.is_consistent
        )
        return consistent / len(self.enriched_results)

    @property
    def avg_confidence(self) -> float:
        """Confianza promedio."""
        if not self.enriched_results:
            return 0.0
        confidences = [r.critic_result.confidence for r in self.enriched_results]
        return sum(confidences) / len(confidences)

    class Config:
        schema_extra = {
            "example": {
                "game_id": "550e8400-e29b-41d4-a716-446655440000",
                "player_id": 42,
                "total_moves_analyzed": 15,
                "enriched_results": [],
                "metadata": {
                    "analysis_duration": 45.2,
                    "total_consistent": 14,
                    "avg_confidence": 0.92,
                    "error_distribution": {
                        "good": 8,
                        "inaccuracy": 5,
                        "mistake": 2,
                        "blunder": 0,
                    },
                },
            }
        }


# ============================================================================
# 7. PLAYER PATTERNS (Memory Output)
# ============================================================================

class PlayerPatterns(BaseModel):
    """Patrones agregados de un jugador."""

    player_id: int
    total_games_analyzed: int = Field(ge=0, default=0)
    total_moves_analyzed: int = Field(ge=0, default=0)
    error_distribution: Dict[str, float] = Field(default_factory=dict)
    frequent_tactics: List[Dict[str, Any]] = Field(default_factory=list)
    weak_phases: List[Literal["opening", "middlegame", "endgame"]] = Field(
        default_factory=list
    )
    phase_error_rates: Dict[str, float] = Field(default_factory=dict)
    improvement_trend: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    recent_avg_error_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    error_clusters: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

    class Config:
        schema_extra = {
            "example": {
                "player_id": 42,
                "total_games_analyzed": 25,
                "total_moves_analyzed": 650,
                "error_distribution": {
                    "good": 0.72,
                    "inaccuracy": 0.18,
                    "mistake": 0.08,
                    "blunder": 0.02,
                },
                "frequent_tactics": [
                    {"tactic": "fork", "count": 23},
                    {"tactic": "pin", "count": 15},
                ],
                "weak_phases": ["endgame"],
                "phase_error_rates": {
                    "opening": 0.12,
                    "middlegame": 0.08,
                    "endgame": 0.22,
                },
                "improvement_trend": 0.15,
                "recent_avg_error_rate": 0.18,
            }
        }
