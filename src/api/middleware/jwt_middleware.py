from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import jwt
from jwt.exceptions import InvalidTokenError
import os
from typing import Optional


class JWTMiddleware:
    """Middleware para validar JWT tokens"""

    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        excluded_paths: list = None,
    ):
        self.secret_key = secret_key or os.getenv(
            "JWT_SECRET_KEY", "chess-trainer-secret-key-2024"
        )
        self.algorithm = algorithm
        self.excluded_paths = excluded_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
        ]

    async def __call__(self, request: Request, call_next):
        """Procesar cada request"""

        # Permitir peticiones OPTIONS (CORS preflight) sin autenticación
        if request.method == "OPTIONS":
            return await call_next(request)

        # Verificar si la ruta está excluida
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Obtener token del header Authorization
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": True,
                    "message": "Token de acceso requerido",
                    "status_code": 401,
                },
            )

        token = auth_header.split(" ")[1]

        try:
            # Validar y decodificar el token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Extraer roles del payload (pueden venir como string "role1,role2" o como sub)
            roles_str = payload.get("roles", "")
            roles_list = roles_str.split(",") if roles_str else []
            username = payload.get("sub", payload.get("username", ""))

            # Agregar información del usuario al request
            request.state.user = {
                "user_id": payload.get("user_id"),
                "username": username,
                "roles": roles_list,
            }

        except InvalidTokenError:
            return JSONResponse(
                status_code=401,
                content={
                    "error": True,
                    "message": "Token inválido o expirado",
                    "status_code": 401,
                },
            )

        # Continuar con el siguiente middleware/handler
        response = await call_next(request)
        return response
