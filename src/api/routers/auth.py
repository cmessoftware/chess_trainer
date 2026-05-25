from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
import os
from sqlalchemy.orm import Session
from typing import List

from models.schemas import (
    UserLogin,
    TokenResponse,
    UserResponse,
    UserRole,
    BaseRole,
    UserCreate,
    UserUpdate,
    UserPermissionsResponse,
    RoleMatrix,
    RoleInfo,
    ROLE_PERMISSIONS,
)
from services.auth_service import AuthService
from database import get_db

router = APIRouter()
security = HTTPBearer()

# Instancia del servicio de autenticación
auth_service = AuthService()


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Endpoint de autenticación con soporte para roles combinatorios

    Soporta autenticación por base de datos y sistema legacy
    """

    # Authenticate user (database first, then legacy)
    user_data = await auth_service.authenticate_user(
        credentials.username, credentials.password, db
    )

    if not user_data:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Prepare token data
    token_expires = datetime.utcnow() + timedelta(hours=24)
    roles_str = ",".join([role.value for role in user_data.get("roles", [])])

    token_data = {
        "sub": user_data["username"],
        "user_id": user_data["user_id"],
        "roles": roles_str,
        "exp": token_expires,
    }

    # Create access token
    access_token = auth_service.create_access_token(token_data)

    # Create session in database (if available)
    try:
        auth_service.create_user_session(
            db, user_data["user_id"], access_token, token_expires
        )
    except Exception:
        # Session creation failed, but continue with token
        pass

    # Create response with new role system
    user_response = UserResponse(
        id=user_data["user_id"],
        username=user_data["username"],
        email=user_data.get("email", "legacy@example.com"),
        roles=user_data.get("roles", []),
        created_at=datetime.utcnow(),  # For legacy users
        is_active=True,
    )

    return TokenResponse(access_token=access_token, user=user_response)


@router.post("/verify", response_model=UserPermissionsResponse)
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Verificar si un token es válido y devolver información completa del usuario
    """
    user_data = auth_service.verify_token(credentials.credentials, db)

    if not user_data:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Calculate user permissions
    user_permissions = list(
        auth_service.get_user_permissions(user_data.get("roles", []))
    )

    # Create user response
    user_response = UserResponse(
        id=user_data["user_id"],
        username=user_data["username"],
        email=user_data.get("email", "legacy@example.com"),
        roles=user_data.get("roles", []),
        created_at=datetime.utcnow(),  # For legacy users
        is_active=True,
    )

    # Role descriptions
    role_descriptions = {}
    for role in user_data.get("roles", []):
        # Handle both string and BaseRole enum types
        role_name = role.value if hasattr(role, 'value') else str(role)
        role_descriptions[role_name] = f"Role: {role_name.replace('_', ' ').title()}"

    return UserPermissionsResponse(
        user=user_response,
        permissions=user_permissions,
        role_descriptions=role_descriptions,
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Cerrar sesión invalidando el token
    """
    success = auth_service.invalidate_user_session(db, credentials.credentials)

    return {"message": "Sesión cerrada exitosamente", "success": success}


@router.get("/roles/matrix", response_model=RoleMatrix)
async def get_roles_matrix():
    """
    Obtener la matriz completa de roles y permisos para administración
    """
    # First pass: collect all permissions from non-admin roles
    all_permissions = set()
    for role, permissions in ROLE_PERMISSIONS.items():
        if permissions != ["ALL"]:
            all_permissions.update(permissions)
    
    # Second pass: create role info list with admin having all permissions
    role_infos = []
    for role, permissions in ROLE_PERMISSIONS.items():
        role_infos.append(
            RoleInfo(
                name=role,
                description=f"Role: {role.value.replace('_', ' ').title()}",
                permissions=(
                    list(all_permissions) if permissions == ["ALL"] else permissions
                ),
            )
        )

    # Common role combinations
    role_combinations = {
        "Basic User": ["basic_gamer", "tactics_trainer"],
        "Chess Analyst": ["basic_gamer", "analysis_board", "stats_viewer"],
        "Content Creator": ["basic_gamer", "exercise_creator", "pgn_uploader"],
        "Data Scientist": ["eda_analyst", "stats_viewer", "analysis_board"],
        "Advanced User": [
            "basic_gamer",
            "analysis_board",
            "tactics_trainer",
            "stats_viewer",
        ],
        "Content Manager": ["exercise_creator", "pgn_uploader", "stats_viewer"],
    }

    return RoleMatrix(
        available_roles=role_infos,
        all_permissions=list(all_permissions),
        role_combinations=role_combinations,
    )


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_create: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_admin_user()),
):
    """
    Crear un nuevo usuario (solo admins)
    """
    try:
        user = await auth_service.create_user(db, user_create)
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            roles=user.roles,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_admin_user()),
):
    """
    Listar todos los usuarios (solo admins)
    """
    from models.database_models import User

    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            roles=user.roles,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active,
        )
        for user in users
    ]


@router.put("/users/{user_id}/roles", response_model=UserResponse)
async def update_user_roles(
    user_id: int,
    roles: List[BaseRole],
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_admin_user()),
):
    """
    Actualizar roles de un usuario (solo admins)
    """
    from models.database_models import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.roles = roles
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        roles=user.roles,
        created_at=user.created_at,
        last_login=user.last_login,
        is_active=user.is_active,
    )
