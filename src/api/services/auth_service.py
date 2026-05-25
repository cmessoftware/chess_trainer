import os
from typing import Optional, List, Set
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt  # Use bcrypt directly instead of passlib
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.database_models import User, UserSession
from models.schemas import BaseRole, ROLE_PERMISSIONS, UserCreate
from database import get_db


class AuthService:
    """
    Servicio para manejar autenticación y autorización

    Soporta sistema de roles combinatorios y autenticación por base de datos
    """

    def __init__(self):
        # Remove passlib, use bcrypt directly
        self.secret_key = os.getenv("JWT_SECRET_KEY", "chess-trainer-secret-key-2024")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 1440  # 24 hours

        # Legacy users for backward compatibility
        self.legacy_users = {
            "admin": {"password": "admin123", "roles": [BaseRole.ADMIN], "user_id": 1},
            "analista": {
                "password": "analista123",
                "roles": [
                    BaseRole.BASIC_GAMER,
                    BaseRole.ANALYSIS_BOARD,
                    BaseRole.STATS_VIEWER,
                ],
                "user_id": 2,
            },
            "usuario": {
                "password": "usuario123",
                "roles": [BaseRole.BASIC_GAMER, BaseRole.TACTICS_TRAINER],
                "user_id": 3,
            },
        }

    def get_user_permissions(self, roles: List[BaseRole]) -> Set[str]:
        """Obtiene todos los permisos basados en los roles del usuario"""
        permissions = set()

        for role in roles:
            role_perms = ROLE_PERMISSIONS.get(role, [])
            if "ALL" in role_perms:
                # Admin role has all permissions
                permissions.update(
                    [
                        perm
                        for perms in ROLE_PERMISSIONS.values()
                        for perm in perms
                        if perm != "ALL"
                    ]
                )
                break
            permissions.update(role_perms)

        return permissions

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica una contraseña plana contra su hash usando bcrypt directamente"""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception as e:
            print(f"Password verification error: {e}")
            return False

    def get_password_hash(self, password: str) -> str:
        """Genera un hash de contraseña usando bcrypt directamente"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    async def authenticate_user_db(
        self, db: Session, username: str, password: str
    ) -> Optional[User]:
        """Autentica usuario contra base de datos"""
        user = (
            db.query(User)
            .filter(User.username == username, User.is_active == True)
            .first()
        )

        # Check if user exists first, then verify password
        if not user:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        return user

    async def authenticate_user_legacy(
        self, username: str, password: str
    ) -> Optional[dict]:
        """Autentica usuario contra sistema hardcodeado (legacy)"""
        user_data = self.legacy_users.get(username)
        if user_data and user_data["password"] == password:
            return {
                "user_id": user_data["user_id"],
                "username": username,
                "roles": user_data["roles"],
            }
        return None

    async def authenticate_user(
        self, username: str, password: str, db: Optional[Session] = None
    ) -> Optional[dict]:
        """
        Autenticar usuario (intenta BD primero, luego legacy)
        """
        # Try database authentication first
        if db:
            try:
                user = await self.authenticate_user_db(db, username, password)
                if user:
                    # Convert role strings from DB to BaseRole enums
                    role_enums = []
                    for role_str in user.roles:
                        try:
                            role_enums.append(BaseRole(role_str))
                        except ValueError:
                            print(
                                f"Warning: Unknown role '{role_str}' for user {user.username}"
                            )
                            continue

                    return {
                        "user_id": user.id,
                        "username": user.username,
                        "roles": role_enums,
                        "email": user.email,
                    }
            except Exception as e:
                print(f"Database authentication error: {e}")
                # Continue to legacy if database auth fails

        # Fallback to legacy authentication
        legacy_result = await self.authenticate_user_legacy(username, password)
        if legacy_result:
            return legacy_result

        return None

    def has_permission_roles(
        self, user_roles: List[BaseRole], required_permission: str
    ) -> bool:
        """
        Verificar si los roles del usuario tienen un permiso específico
        """
        user_permissions = self.get_user_permissions(user_roles)
        return required_permission in user_permissions

    def has_permission(self, user_role: str, required_feature: str) -> bool:
        """
        Verificar si un rol legacy tiene permisos (para compatibilidad)
        """
        # Map legacy roles to new permission system
        legacy_permissions = {
            "admin": [
                "chess_board",
                "games_browser",
                "analysis",
                "import",
                "ml_pipeline",
                "admin",
            ],
            "analista": ["chess_board", "games_browser", "analysis", "ml_pipeline"],
            "usuario": ["chess_board", "games_browser"],
        }

        return required_feature in legacy_permissions.get(user_role, [])

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Crea un token JWT de acceso"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_user_session(
        self, db: Session, user_id: int, token: str, expires_at: datetime
    ) -> UserSession:
        """Crea una sesión de usuario en la base de datos"""
        session = UserSession(
            user_id=user_id,
            token_jti=token,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def invalidate_user_session(self, db: Session, token: str) -> bool:
        """Invalida una sesión de usuario"""
        session = db.query(UserSession).filter(UserSession.token_jti == token).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False

    def verify_token(self, token: str, db: Optional[Session] = None) -> Optional[dict]:
        """Verifica un token JWT y devuelve los datos del usuario"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")

            if username is None:
                return None

            # If database available, try to get user from database
            if db and user_id:
                # Try to verify session exists (but don't fail if it doesn't)
                session = (
                    db.query(UserSession)
                    .filter(
                        and_(
                            UserSession.token_jti == token,
                            UserSession.expires_at > datetime.utcnow(),
                        )
                    )
                    .first()
                )

                # Get user from database (regardless of session)
                user = (
                    db.query(User)
                    .filter(User.id == user_id, User.is_active == True)
                    .first()
                )
                if user:
                    return {
                        "username": user.username,
                        "user_id": user.id,
                        "roles": user.roles,
                        "email": user.email,
                    }

            # Fallback to token data if user not found in DB
            roles_str = payload.get("roles", "")
            roles = (
                [BaseRole(role) for role in roles_str.split(",") if role]
                if roles_str
                else []
            )

            return {"username": username, "user_id": user_id, "roles": roles}

        except JWTError:
            return None

    async def create_user(self, db: Session, user_create: UserCreate) -> User:
        """Crea un nuevo usuario en la base de datos"""
        # Check if user already exists
        existing_user = (
            db.query(User)
            .filter(
                (User.username == user_create.username)
                | (User.email == user_create.email)
            )
            .first()
        )

        if existing_user:
            raise ValueError("Username or email already exists")

        # Create new user
        hashed_password = self.get_password_hash(user_create.password)
        user = User(
            username=user_create.username,
            email=user_create.email,
            password_hash=hashed_password,
            roles=user_create.roles,
            is_active=user_create.is_active,
            created_at=datetime.utcnow(),
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_current_user(self, credentials: str, db: Session) -> Optional[dict]:
        """Obtiene el usuario actual desde token"""
        return self.verify_token(credentials, db)

    def get_current_admin_user(self):
        """Dependency que verifica que el usuario actual sea admin"""

        def admin_checker(
            credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
            db: Session = Depends(get_db),
        ):
            from fastapi import HTTPException, status

            user_data = self.verify_token(credentials.credentials, db)
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
                )

            user_roles = user_data.get("roles", [])
            if BaseRole.ADMIN not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Se requieren permisos de administrador",
                )

            return user_data

        return admin_checker

    def require_roles(self, required_roles: List[BaseRole]):
        """Decorator factory que requiere roles específicos"""

        def role_checker(credentials: str, db: Session):
            from fastapi import HTTPException, status

            user_data = self.get_current_user(credentials, db)
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
                )

            user_roles = user_data.get("roles", [])

            # Admin always has access
            if BaseRole.ADMIN in user_roles:
                return user_data

            # Check if user has any of the required roles
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Se requieren roles: {[role.value for role in required_roles]}",
                )
            return user_data

        return role_checker

    def require_permissions(self, required_permissions: List[str]):
        """Decorator factory que requiere permisos específicos"""

        def permission_checker(credentials: str, db: Session):
            from fastapi import HTTPException, status

            user_data = self.get_current_user(credentials, db)
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
                )

            user_permissions = self.get_user_permissions(user_data.get("roles", []))

            # Check if user has all required permissions
            missing_permissions = set(required_permissions) - user_permissions
            if missing_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permisos faltantes: {list(missing_permissions)}",
                )
            return user_data

        return permission_checker
