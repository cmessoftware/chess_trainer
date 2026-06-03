from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class BaseRole(str, Enum):
    """Roles base del sistema que se pueden combinar"""

    ADMIN = "admin"
    BASIC_GAMER = "basic_gamer"
    ANALYSIS_BOARD = "analysis_board"
    EXERCISE_CREATOR = "exercise_creator"
    STATS_VIEWER = "stats_viewer"
    TACTICS_TRAINER = "tactics_trainer"
    PGN_UPLOADER = "pgn_uploader"
    EDA_ANALYST = "eda_analyst"


# Permissions mapping for each role
ROLE_PERMISSIONS = {
    BaseRole.ADMIN: ["ALL"],  # Admin has all permissions
    BaseRole.BASIC_GAMER: [
        "chess_board",
        "play_stockfish",
        "view_own_games",
        "import_pgn",
        "personal_upload",
        "generate_features",
    ],
    BaseRole.ANALYSIS_BOARD: ["chess_board", "analysis_engine", "deep_analysis"],
    BaseRole.EXERCISE_CREATOR: ["create_exercises", "edit_exercises", "view_exercises"],
    BaseRole.STATS_VIEWER: ["view_stats", "advanced_stats", "reports"],
    BaseRole.TACTICS_TRAINER: [
        "tactics_training",
        "view_exercises",
        "progress_tracking",
    ],
    BaseRole.PGN_UPLOADER: ["bulk_upload", "import_pgn", "manage_sources"],
    BaseRole.EDA_ANALYST: ["eda_analysis", "data_mining", "pattern_analysis"],
}


class UserRole(str, Enum):
    """Roles legacy del sistema (mantenidos para compatibilidad)"""

    ADMIN = "admin"
    ANALISTA = "analista"
    USUARIO = "usuario"


class UserBase(BaseModel):
    """Modelo base de usuario"""

    username: str
    email: EmailStr
    roles: List[BaseRole] = []
    is_active: bool = True

    @validator("username")
    def username_alphanumeric(cls, v):
        assert (
            v.replace("_", "").replace("-", "").isalnum()
        ), "Username must be alphanumeric with optional _ or -"
        return v


class UserCreate(UserBase):
    """Modelo para crear usuario"""

    password: str

    @validator("password")
    def password_strength(cls, v):
        assert len(v) >= 8, "Password must be at least 8 characters"
        return v


class UserUpdate(BaseModel):
    """Modelo para actualizar usuario"""

    email: Optional[EmailStr] = None
    roles: Optional[List[BaseRole]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

    @validator("password")
    def password_strength(cls, v):
        if v is not None:
            assert len(v) >= 8, "Password must be at least 8 characters"
        return v


class UserLogin(BaseModel):
    """Modelo para login de usuario"""

    username: str
    password: str


class UserResponse(UserBase):
    """Modelo de respuesta de usuario"""

    id: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserPermissionsResponse(BaseModel):
    """Modelo de respuesta con permisos calculados del usuario"""

    user: UserResponse
    permissions: List[str]
    role_descriptions: Dict[str, str]


class RoleInfo(BaseModel):
    """Información de rol base"""

    name: BaseRole
    description: str
    permissions: List[str]


class RoleMatrix(BaseModel):
    """Matriz completa de roles y permisos para administración"""

    available_roles: List[RoleInfo]
    all_permissions: List[str]
    role_combinations: Dict[str, List[str]]  # Ejemplos de combinaciones comunes


class TokenResponse(BaseModel):
    """Modelo de respuesta de token"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GameBase(BaseModel):
    """Modelo base de partida de ajedrez"""

    white: Optional[str] = None
    black: Optional[str] = None
    result: Optional[str] = None
    event: Optional[str] = None
    site: Optional[str] = None
    date: Optional[str] = None


class GameResponse(GameBase):
    """Modelo de respuesta de partida"""

    game_id: str
    moves: List[str] = []
    white_elo: Optional[str] = None
    black_elo: Optional[str] = None
    eco: Optional[str] = None
    opening: Optional[str] = None
    source: Optional[str] = None


class GamesListResponse(BaseModel):
    """Modelo de respuesta para lista de partidas"""

    games: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class AnalysisRequest(BaseModel):
    """Modelo para solicitud de análisis"""

    fen: str
    depth: int = 10


class AnalysisResponse(BaseModel):
    """Modelo de respuesta de análisis"""

    fen: str
    best_move: Optional[str]
    evaluation: Optional[float]
    depth: int
    analysis_time: float


class MoveValidationRequest(BaseModel):
    """Modelo para validación de movimiento"""

    move: str


class MoveValidationResponse(BaseModel):
    """Modelo de respuesta de validación"""

    valid: bool
    move: Optional[str]
    message: Optional[str]


# =======================================
# MODELOS DE CONTRATOS PGN/API BASE
# =======================================


class PgnUploadResponse(BaseModel):
    """Respuesta al subir archivo PGN/ZIP/GZ"""

    jobId: str
    filename: str
    size: int
    status: str
    estimatedGames: int


class PgnUploadJobStatus(BaseModel):
    """Estado de un job de upload"""

    id: str
    filename: str
    original_filename: Optional[str] = None
    file_path: Optional[str] = None
    size: int
    source: str
    imported_by: Optional[str] = None
    status: str
    uploaded_at: Optional[str] = None
    estimated_games: int


class PgnUploadsListResponse(BaseModel):
    """Listado de uploads"""

    uploads: List[PgnUploadJobStatus]
    total: int


class PgnBatchImportRequest(BaseModel):
    """Request para importación batch de PGN"""

    fileIds: List[str]
    source: str = "personal"


class PgnBatchImportResponse(BaseModel):
    """Respuesta al encolar importación batch"""

    jobId: str
    status: str
    totalFiles: int
    estimatedGames: int


class PgnPreviewGame(BaseModel):
    """Preview de partida PGN"""

    white: str
    black: str
    result: str
    date: str


class PgnPreviewResponse(BaseModel):
    """Respuesta de preview de archivo"""

    games: List[PgnPreviewGame]
    total_shown: int
    filename: str


class PgnImportHistoryJob(BaseModel):
    """Entrada de historial de upload/import"""

    id: str
    type: str
    status: str
    source: Optional[str] = None
    filename: Optional[str] = None
    file_ids: Optional[List[str]] = None
    files: Optional[List[str]] = None
    uploaded_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_files: Optional[int] = None
    processed_files: Optional[int] = None
    estimated_games: Optional[int] = None
    imported_games: Optional[int] = None
    error: Optional[str] = None


class PgnImportHistoryResponse(BaseModel):
    """Respuesta paginada de historial"""

    jobs: List[PgnImportHistoryJob]
    total: int
    page: int
    limit: int
    totalPages: int


class PgnUploadStats(BaseModel):
    """Estadísticas de upload"""

    total: int
    completed: int
    success_rate: float


class PgnImportStats(BaseModel):
    """Estadísticas de importación"""

    total: int
    completed: int
    success_rate: float


class PgnGamesStats(BaseModel):
    """Estadísticas de partidas"""

    estimated: int
    imported: int


class PgnImportStatsResponse(BaseModel):
    """Respuesta de estadísticas consolidadas"""

    uploads: PgnUploadStats
    imports: PgnImportStats
    games: PgnGamesStats


class PersonalPgnImportResponse(BaseModel):
    """Respuesta de importación personal directa"""

    success: bool
    filename: str
    imported: int
    skipped: int
    batch_id: str
    username: str
    message: str


# =======================================
# MODELOS DE LOGGING
# =======================================


class LogEvent(BaseModel):
    """Modelo para evento de logging"""

    module: str  # 'chess', 'games', 'analysis', etc.
    action: str  # 'board_move', 'game_load', 'position_analysis', etc.
    user_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class LogEventResponse(BaseModel):
    """Modelo de respuesta de evento de logging"""

    log_id: int
    module: str
    action: str
    user_id: Optional[str]
    data: Optional[Dict[str, Any]]
    timestamp: str


class LogsListRequest(BaseModel):
    """Modelo para filtrar logs"""

    module: Optional[str] = None
    action: Optional[str] = None
    user_id: Optional[str] = None
    limit: int = 50
    offset: int = 0


class LogsListResponse(BaseModel):
    """Modelo de respuesta para lista de logs"""

    logs: List[LogEventResponse]
    total: int
    limit: int
    offset: int
