# api/routers/analysis.py
"""
Router para análisis ML + SHAP explicable.

Endpoints para:
- Ejecutar análisis ML con SHAP sobre partidas
- Obtener distribución y tendencias de errores
- Acceder a feature importance global y move-level
- Consultar historial de análisis
"""
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal
from sqlalchemy.orm import Session
from datetime import datetime

from api.services.auth_service import AuthService
from api.services.analysis_service import AnalysisService
from api.services.llm_analysis_service import LLMAnalysisService
from api.database import get_db

router = APIRouter(prefix="/api", tags=["analysis"])
security = HTTPBearer()

# Instancias de servicios
auth_service = AuthService()
analysis_service = AnalysisService()
llm_analysis_service = LLMAnalysisService()


# ========================
# Pydantic Schemas
# ========================


class AnalysisRequest(BaseModel):
    """Request para ejecutar análisis ML"""

    game_id: str
    username: Optional[str] = None  # Si None, usa current_user


class AnalysisResponse(BaseModel):
    """Response con ID del análisis creado"""

    analysis_id: int
    status: str
    message: str


class ErrorDistribution(BaseModel):
    """Distribución de errores del usuario"""

    blunder: int
    mistake: int
    inaccuracy: int
    good: int


class ErrorTrendPoint(BaseModel):
    """Punto en evolución temporal de errores"""

    date: str
    blunder_rate: float
    mistake_rate: float
    inaccuracy_rate: float
    accuracy: float


class FeatureImportance(BaseModel):
    """Importancia de una feature (SHAP)"""

    feature_name: str
    mean_abs_shap_value: float
    mean_shap_value: float
    total_samples: int


class FeatureImpact(BaseModel):
    """Impacto de una feature en una jugada específica"""

    feature: str
    impact: float
    value: float


class MoveShapExplanation(BaseModel):
    """Explicación SHAP para una jugada específica"""

    move_number: int
    error_level: str
    top_features: List[FeatureImpact]


class ShapValueWithGame(BaseModel):
    """SHAP value con información del game (desde vista SQL)"""

    shap_id: int
    analysis_id: int
    game_id: str
    username: str
    error_label: str  # CORREGIDO: era error_level
    accuracy_percentage: float
    analyzed_at: datetime
    move_number: int
    feature_name: str
    shap_value: float
    feature_value: float
    # Contexto del movimiento (agregado 2026-02-28)
    move_san: Optional[str] = None
    move_uci: Optional[str] = None
    fen: Optional[str] = None
    player_color: Optional[str] = None


class LLMReportRequest(BaseModel):
    """Request para generar informe pedagógico con LLM"""

    game_id: str
    player_elo: int = Field(
        gt=0, le=4000, description="Rating ELO del jugador (1-4000)"
    )
    player_color: Literal["white", "black"] = Field(
        description="Color del jugador - CRÍTICO para filtrar movimientos. Solo 'white' o 'black'"
    )
    analysis_id: Optional[int] = None  # Si None, ejecuta análisis ML automáticamente
    username: Optional[str] = None  # Si None, usa current_user


class TokenUsage(BaseModel):
    """Uso de tokens en la llamada LLM"""

    prompt: int
    completion: int
    total: int
    paso_1_tokens: Optional[int] = None  # V4: Tokens del paso 1 (JSON)
    paso_2_tokens: Optional[int] = None  # V4: Tokens del paso 2 (Narrativa)


class LLMReportResponse(BaseModel):
    """Response con informe pedagógico generado (arquitectura v6.2: trade sequence analysis)"""

    analysis_id: int
    game_id: str
    player_elo: int
    report: str  # Informe en formato Markdown
    engine_analysis: Optional[Dict] = None  # V3+: Engine data precalculado
    structured_analysis: Optional[Dict] = None  # V4+: JSON validado del Paso 1
    validation_passed: Optional[bool] = None
    validation_warning: Optional[str] = None
    tokens_used: TokenUsage
    model: str
    cost_estimate_usd: float
    generated_at: Optional[datetime] = None
    architecture_version: Optional[str] = "v6.2_trade_analysis"  # V6.2: Detecta intercambios y secuencias


# ========================
# Dependency: Current User
# ========================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Extraer usuario actual del token JWT"""
    try:
        payload = auth_service.verify_token(credentials.credentials, db)

        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido")

        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error autenticación: {str(e)}")


# ========================
# Endpoints
# ========================


@router.post("/analysis/run", response_model=AnalysisResponse)
async def run_ml_analysis(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    🧠 Ejecutar análisis ML + SHAP sobre una partida.

    Workflow:
    1. Obtener features de la partida
    2. Ejecutar predicción ML
    3. Calcular SHAP values
    4. Persistir en analysis_results + move_shap_values
    5. Actualizar player_feature_importance

    Permissions: Requiere autenticación
    """
    try:
        username = request.username or current_user["username"]

        # Ejecutar análisis
        analysis_id = analysis_service.analyze_game(
            db=db, game_id=request.game_id, username=username
        )

        return AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            message=f"Análisis ML + SHAP completado para game_id={request.game_id}",
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error ejecutando análisis ML: {str(e)}"
        )


@router.get("/stats/error-distribution", response_model=ErrorDistribution)
async def get_error_distribution(
    days: int = Query(30, description="Últimos N días a analizar"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    📊 Obtener distribución de errores del usuario.

    Returns:
        Conteo de {blunder, mistake, inaccuracy, good} en últimos N días.

    Usado por: ErrorDistributionChart (PieChart)
    Permissions: Requiere autenticación
    """
    try:
        username = current_user["username"]

        distribution = analysis_service.get_error_distribution(
            db=db, username=username, days=days
        )

        return ErrorDistribution(**distribution)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo distribución: {str(e)}"
        )


@router.get("/stats/error-trend", response_model=List[ErrorTrendPoint])
async def get_error_trend(
    days: int = Query(90, description="Ventana de análisis en días"),
    interval_days: int = Query(7, description="Intervalo de agrupación (días)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    📈 Obtener evolución temporal de errores (agrupado por intervalos).

    Returns:
        Lista de puntos con {date, blunder_rate, mistake_rate, inaccuracy_rate, accuracy}.

    Usado por: TemporalTrendChart (LineChart)
    Permissions: Requiere autenticación
    """
    try:
        username = current_user["username"]

        trend = analysis_service.get_error_temporal_trend(
            db=db, username=username, days=days, interval_days=interval_days
        )

        return [ErrorTrendPoint(**point) for point in trend]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo tendencia: {str(e)}"
        )


@router.get(
    "/analysis/global-feature-importance", response_model=List[FeatureImportance]
)
async def get_global_feature_importance(
    top_k: int = Query(10, description="Top K features más importantes"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    🧠 Obtener top features más importantes (SHAP agregado por jugador).

    Returns:
        Lista ordenada de {feature_name, mean_abs_shap_value, total_samples}.

    Usado por: GlobalShapChart (BarChart horizontal)
    Permissions: Requiere autenticación
    """
    try:
        username = current_user["username"]

        importance = analysis_service.get_global_feature_importance(
            db=db, username=username, top_k=top_k
        )

        return [FeatureImportance(**item) for item in importance]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo feature importance: {str(e)}"
        )


@router.get("/analysis/game/{game_id}/shap", response_model=MoveShapExplanation)
async def get_move_shap_explanation(
    game_id: str,
    move_number: int = Query(..., description="Número de jugada (1-indexed)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    ♟️ Obtener explicación SHAP para una jugada específica.

    Returns:
        {move_number, error_level, top_features: [{feature, impact, value}]}

    Usado por: MoveShapPanel (panel interactivo)
    Permissions: Requiere autenticación
    """
    try:
        explanation = analysis_service.get_move_shap_explanation(
            db=db, game_id=game_id, move_number=move_number
        )

        return MoveShapExplanation(**explanation)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo SHAP de jugada: {str(e)}"
        )


@router.get("/analysis/history")
async def get_analysis_history(
    limit: int = Query(20, description="Cantidad de análisis a retornar"),
    offset: int = Query(0, description="Offset para paginación"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    📜 Obtener historial de análisis ML del usuario.

    Returns:
        Lista de {analysis_id, game_id, error_level, analyzed_at, ...}.

    Permissions: Requiere autenticación
    """
    try:
        from db.models.analysis_results import AnalysisResult
        from sqlalchemy import desc

        username = current_user["username"]

        # Query con paginación
        history = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.username == username)
            .order_by(desc(AnalysisResult.analyzed_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        # Convertir a dicts
        results = [
            {
                "analysis_id": a.id,
                "game_id": a.game_id,
                "error_level": a.error_level,
                "prediction_confidence": a.prediction_confidence,
                "total_moves": a.total_moves,
                "blunder_count": a.blunder_count,
                "mistake_count": a.mistake_count,
                "inaccuracy_count": a.inaccuracy_count,
                "accuracy_percentage": a.accuracy_percentage,
                "analyzed_at": a.analyzed_at.isoformat() if a.analyzed_at else None,
            }
            for a in history
        ]

        return {
            "total": len(results),
            "limit": limit,
            "offset": offset,
            "results": results,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo historial: {str(e)}"
        )


@router.get("/analysis/{analysis_id}")
async def get_analysis_detail(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    🔍 Obtener detalle completo de un análisis específico.

    Returns:
        Análisis completo con métricas y metadatos.

    Permissions: Requiere autenticación (solo puede ver sus propios análisis)
    """
    try:
        from db.models.analysis_results import AnalysisResult

        username = current_user["username"]

        analysis = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.id == analysis_id,
                AnalysisResult.username == username,  # Security: solo own analysis
            )
            .first()
        )

        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Análisis {analysis_id} no encontrado o sin permisos",
            )

        return analysis.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo análisis: {str(e)}"
        )


@router.get("/analysis/shap/game/{game_id}", response_model=List[ShapValueWithGame])
async def get_shap_values_by_game(
    game_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    move_number: Optional[int] = Query(
        None, description="Filtrar por número de jugada específico"
    ),
    top_n: Optional[int] = Query(
        None, description="Limitar a top N features por jugada", ge=1, le=50
    ),
):
    """
    📊 Obtener todos los SHAP values de una partida específica.

    Consulta la vista shap_values_with_games que combina:
    - move_shap_values
    - analysis_results
    - Información del game

    Query Params:
        - move_number: Filtrar por jugada específica
        - top_n: Limitar a top N features por jugada (ordenado por |shap_value|)

    Returns:
        Lista de SHAP values con contexto completo del game

    Permissions: Requiere autenticación (solo puede ver sus propios análisis)
    """
    try:
        from sqlalchemy import text

        username = current_user["username"]

        # Query base sobre la vista SQL
        query = """
            SELECT 
                shap_id,
                analysis_id,
                game_id,
                username,
                error_label,
                accuracy_percentage,
                analyzed_at,
                move_number,
                feature_name,
                shap_value,
                feature_value,
                move_san,
                move_uci,
                fen,
                player_color
            FROM shap_values_with_games
            WHERE game_id = :game_id
            AND username = :username
        """

        params = {"game_id": game_id, "username": username}

        # Filtro opcional por move_number
        if move_number is not None:
            query += " AND move_number = :move_number"
            params["move_number"] = move_number

        # Si top_n está especificado, usar una subconsulta con RANK
        if top_n is not None:
            query = f"""
                SELECT * FROM (
                    SELECT 
                        shap_id,
                        analysis_id,
                        game_id,
                        username,
                        error_label,
                        accuracy_percentage,
                        analyzed_at,
                        move_number,
                        feature_name,
                        shap_value,
                        feature_value,
                        move_san,
                        move_uci,
                        fen,
                        player_color,
                        RANK() OVER (PARTITION BY move_number ORDER BY ABS(shap_value) DESC) as rank
                    FROM shap_values_with_games
                    WHERE game_id = :game_id
                    AND username = :username
                    {f"AND move_number = :move_number" if move_number is not None else ""}
                ) ranked
                WHERE rank <= :top_n
                ORDER BY move_number, rank
            """
            params["top_n"] = top_n
        else:
            query += " ORDER BY move_number, ABS(shap_value) DESC"

        # Ejecutar query
        result = db.execute(text(query), params)
        rows = result.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron SHAP values para game_id={game_id} o sin permisos",
            )

        # Convertir a lista de objetos ShapValueWithGame
        shap_values = []
        for row in rows:
            shap_values.append(
                ShapValueWithGame(
                    shap_id=row[0],
                    analysis_id=row[1],
                    game_id=row[2],
                    username=row[3],
                    error_label=row[4],  # CORREGIDO: era error_level
                    accuracy_percentage=row[5],
                    analyzed_at=row[6],
                    move_number=row[7],
                    feature_name=row[8],
                    shap_value=row[9],
                    feature_value=row[10],
                    move_san=row[11] if len(row) > 11 else None,
                    move_uci=row[12] if len(row) > 12 else None,
                    fen=row[13] if len(row) > 13 else None,
                    player_color=row[14] if len(row) > 14 else None,
                )
            )

        return shap_values

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo SHAP values: {str(e)}"
        )


# ========================
# FUNCIONALIDAD 3.6.1 - LLM Pedagógico (Fase 1 - MVP)
# ========================


@router.post("/analysis/generate-llm-report", response_model=LLMReportResponse)
async def generate_pedagogical_report(
    request: LLMReportRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    🧠 FUNCIONALIDAD 3.6.1 - Fase 1: Generar informe pedagógico con LLM
    
    Genera un informe de entrenamiento personalizado usando GPT-4, adaptado
    al nivel ELO del jugador. Traduce análisis técnico SHAP en feedback
    pedagógico comprensible.
    
    **Flujo:**
    1. Si no hay analysis_id: Ejecuta análisis ML + SHAP automáticamente
    2. Obtiene resumen SHAP del análisis
    3. Construye prompt adaptado al ELO del jugador
    4. Llama a GPT-4 para generar informe
    5. Retorna informe en Markdown + metadata
    
    **Adaptación por ELO:**
    - <1200: Material, tácticas básicas, lenguaje simple
    - 1200-1700: Desarrollo, iniciativa, conceptos posicionales
    - 1700-2100: Estructura, planes, profilaxis
    - 2100+: Optimización fina, precisión dinámica
    
    **Costos estimados (GPT-4):**
    - Prompt: ~1,500 tokens
    - Completion: ~1,000 tokens
    - Total: ~2,500 tokens → $0.10 por análisis
    
    **Ejemplo de uso:**
    ```bash
    curl -X POST "http://localhost:8000/api/analysis/generate-llm-report" \\
         -H "Authorization: Bearer <token>" \\
         -H "Content-Type: application/json" \\
         -d '{
               "game_id": "5daf60d3cfe938ed...",
               "player_elo": 1420,
               "analysis_id": 49
             }'
    ```
    
    **Nota**: Requiere OPENAI_API_KEY configurada en .env
    """
    try:
        # Usar username del request o del current_user
        username = request.username or current_user.get("username")

        if not username:
            raise HTTPException(
                status_code=400, detail="Username requerido (token o request body)"
            )

        print(f"\n{'='*60}")
        print(f"🧠 GENERANDO INFORME PEDAGÓGICO CON LLM")
        print(f"{'='*60}")
        print(f"   Usuario: {username}")
        print(f"   Game ID: {request.game_id}")
        print(f"   ELO: {request.player_elo}")
        print(f"   Jugador: {request.player_color}")
        print(f"   Analysis ID: {request.analysis_id or 'Auto (ejecutará ML)'}")

        # Generar informe usando LLM service
        result = await llm_analysis_service.generate_pedagogical_report(
            db=db,
            game_id=request.game_id,
            player_elo=request.player_elo,
            player_color=request.player_color,
            username=username,
            analysis_id=request.analysis_id,
        )

        # Preparar respuesta
        response = LLMReportResponse(
            analysis_id=result["analysis_id"],
            game_id=result["game_id"],
            player_elo=result["player_elo"],
            report=result["report"],
            engine_analysis=result.get("engine_analysis"),  # V3
            structured_analysis=result.get("structured_analysis"),
            validation_passed=result.get("validation_passed"),
            validation_warning=result.get("validation_warning"),
            tokens_used=TokenUsage(**result["tokens_used"]),
            model=result["model"],
            cost_estimate_usd=result["cost_estimate_usd"],
            generated_at=datetime.now(),
            architecture_version=result.get(
                "architecture_version", "v3_grounded_deterministic"
            ),
        )

        print(f"\n✅ Informe generado exitosamente")
        print(f"   Tokens: {result['tokens_used']['total']}")
        print(f"   Costo: ${result['cost_estimate_usd']:.4f}")
        print(f"{'='*60}\n")

        return response

    except HTTPException:
        raise
    except ValueError as e:
        # Error de configuración (API key faltante)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generando informe LLM: {str(e)}"
        )


@router.post("/analysis/generate-batch-llm-reports")
async def generate_batch_pedagogical_reports(
    game_ids: List[str],
    player_elo: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    🧠 FUNCIONALIDAD 3.6.1 - Fase 1: Generar informes en batch
    
    Genera múltiples informes pedagógicos para una lista de partidas.
    Útil para análisis de múltiples juegos de un mismo jugador.
    
    **Ejemplo de uso:**
    ```bash
    curl -X POST "http://localhost:8000/api/analysis/generate-batch-llm-reports" \\
         -H "Authorization: Bearer <token>" \\
         -H "Content-Type: application/json" \\
         -d '{
               "game_ids": ["game1...", "game2...", "game3..."],
               "player_elo": 1420
             }'
    ```
    
    **Nota**: El batch procesa secuencialmente para evitar rate limits de OpenAI.
    """
    try:
        username = current_user.get("username")

        print(f"\n{'='*60}")
        print(f"🧠 GENERANDO BATCH DE {len(game_ids)} INFORMES LLM")
        print(f"{'='*60}")
        print(f"   Usuario: {username}")
        print(f"   ELO: {player_elo}")

        # Generar batch de informes
        reports = await llm_analysis_service.generate_batch_reports(
            db=db, game_ids=game_ids, player_elo=player_elo, username=username
        )

        return {
            "total_games": len(game_ids),
            "successful": sum(1 for r in reports if "error" not in r),
            "failed": sum(1 for r in reports if "error" in r),
            "total_cost_usd": sum(r.get("cost_estimate_usd", 0) for r in reports),
            "total_tokens": sum(
                r.get("tokens_used", {}).get("total", 0) for r in reports
            ),
            "reports": reports,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en batch LLM: {str(e)}")


# ========================
# V7 Pipeline Endpoint
# ========================


class V7FeedbackRequest(BaseModel):
    """Request para generar feedback V7 (LLM grounded)."""

    game_id: str
    cp_loss_threshold: int = Field(
        default=90, ge=0, le=1000, description="Threshold cp_loss para jugadas críticas"
    )
    max_items: int = Field(
        default=10, ge=1, le=50, description="Máximo de jugadas críticas a analizar"
    )


class V7FeedbackResponse(BaseModel):
    """Response con feedback V7 generado."""

    game_id: str
    stats: Dict[str, int]
    critical_feedback: List[Dict]
    architecture_version: str = "v7.0_grounded_llm"


@router.post("/analysis/v7-feedback", response_model=V7FeedbackResponse)
async def generate_v7_validated_feedback(
    request: V7FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    🚀 V7 Pipeline: Generar feedback pedagógico con LLM grounded.

    **Paradigma shift**: El LLM NO analiza ajedrez, solo verbaliza JSON validado.

    **Previene alucinaciones mediante**:
    1. Uso exclusivo de Stockfish como ground truth
    2. Validación cruzada ML vs Stockfish
    3. Detección conservadora de patrones
    4. JSON completo autocontenido
    5. Reglas estrictas de seguridad en prompt
    6. Post-validación de output

    **Arquitectura**:
    ```
    DB (Stockfish + ML + temporal)
      ↓
    Validator (cross-check)
      ↓
    PatternEngine (geometry)
      ↓
    ExplanationPack (JSON)
      ↓
    LLMExplainer (verbalizer)
      ↓
    Feedback validado
    ```

    **Ejemplo de uso:**
    ```bash
    curl -X POST "http://localhost:8000/api/analysis/v7-feedback" \\
         -H "Authorization: Bearer <token>" \\
         -H "Content-Type: application/json" \\
         -d '{
               "game_id": "aec7f86c...",
               "cp_loss_threshold": 90,
               "max_items": 10
             }'
    ```

    **Mejoras vs V6**:
    - ✅ Sin falsos positivos de material (usa cp_loss, no material_balance)
    - ✅ Sin alucinaciones (LLM solo verbaliza JSON)
    - ✅ Modular y testeable (funciones puras)
    """
    try:
        from api.services.analysis_pipeline import (
            generate_validated_feedback,
            create_v7_repos,
        )
        from api.services.analysis_pipeline.integration_example import (
            LLMClientWrapper,
        )
        from api import models

        username = current_user.get("username")

        print(f"\n{'='*60}")
        print(f"🚀 GENERANDO FEEDBACK V7 (LLM GROUNDED)")
        print(f"{'='*60}")
        print(f"   Usuario: {username}")
        print(f"   Game ID: {request.game_id}")
        print(f"   Threshold: {request.cp_loss_threshold} cp_loss")
        print(f"   Max items: {request.max_items}")

        # Create V7 repository adapter
        repos = create_v7_repos(db, models)

        # TODO: Replace with actual LLM client
        # For now, use placeholder wrapper
        llm_client_placeholder = type(
            "MockLLMClient",
            (),
            {
                "complete": lambda self, prompt: (
                    "Diagnosis: Error detectado en esta jugada\n"
                    "Better move: Se recomienda alternativa más precisa\n"
                    "Training rule: Analizar consecuencias antes de mover"
                )
            },
        )()
        llm_client = LLMClientWrapper(llm_client_placeholder)

        # Generate V7 feedback
        result = generate_validated_feedback(
            request.game_id,
            repos=repos,
            llm_client=llm_client,
            cp_loss_threshold=request.cp_loss_threshold,
            max_items=request.max_items,
        )

        print(f"\n✅ Feedback V7 generado:")
        print(f"   Jugadas analizadas: {result['stats']['num_moves_analyzed']}")
        print(f"   Jugadas críticas: {result['stats']['num_critical']}")
        print(f"   Desacuerdos ML/Stockfish: {result['stats']['num_disagreements']}")

        return V7FeedbackResponse(
            game_id=result["game_id"],
            stats=result["stats"],
            critical_feedback=result["critical_feedback"],
        )

    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error importando pipeline V7: {str(e)}. Verifica que todos los módulos estén disponibles.",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Error V7: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error generando feedback V7: {str(e)}"
        )
