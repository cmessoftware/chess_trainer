#!/usr/bin/env python
"""Script temporal para corregir authentication en analysis.py"""

import re

filepath = "src/api/routers/analysis.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: Reemplazar imports con backtick n
content = re.sub(
    r'from fastapi import.*?`nfrom fastapi\.security.*?\n',
    'from fastapi import APIRouter, HTTPException, Depends, Query, status\nfrom fastapi.security import HTTPBearer, HTTPAuthorizationCredentials\n',
    content,
    flags=re.DOTALL
)

# Fix 2: Agregar security = HTTPBearer() después de router
content = re.sub(
    r'(router = APIRouter\(prefix="/api", tags=\["analysis"\]\))\n\n# Instancias',
    r'\1\nsecurity = HTTPBearer()\n\n# Instancias',
    content
)

# Fix 3: Reemplazar get_current_user function
old_get_current_user = r'async def get_current_user\(token: str = Depends\(auth_service\.oauth2_scheme\), db: Session = Depends\(get_db\)\):.*?raise HTTPException\(status_code=401, detail=f"Error autenticación: \{str\(e\)\}"\)'

new_get_current_user = '''async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Extraer usuario actual del token JWT"""
    try:
        payload = auth_service.verify_token(credentials.credentials, db)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error autenticación: {str(e)}")'''

content = re.sub(old_get_current_user, new_get_current_user, content, flags=re.DOTALL)

# Escribir archivo corregido
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Archivo analysis.py corregido:")
print("   - Imports de HTTPBearer agregados")
print("   - security = HTTPBearer() agregado")
print("   - get_current_user actualizado para usar HTTPBearer")
