# 🧪 Guía de Testing - Sistema de Autenticación y Filtros por Rol

## 📋 Resumen
Este documento proporciona instrucciones detalladas para reproducir todas las pruebas del sistema de autenticación JWT y filtros por rol implementados en **Sprint 1: Database Browser + Authentication**.

**Versión**: v0.1.122-f8e6b29  
**Fecha**: 14 de Febrero, 2026  
**Branch**: `feature/frontend-sprint1-database-browser`

---

## 🔧 Prerequisitos

### **1. Servicios Requeridos**
Asegúrate de que los siguientes servicios estén corriendo:

```powershell
# Verificar servicios Docker
docker-compose ps

# Deberías ver:
# - postgres (puerto 5432)
# - notebooks (puerto 8888, 5000)
```

### **2. Conda Environment**
**CRÍTICO**: Todas las operaciones deben usar el environment `chess_trainer`:

```powershell
# Activar environment
conda activate chess_trainer

# Verificar que está activo
conda info --envs
# Debe mostrar * en chess_trainer
```

### **3. Iniciar Backend y Frontend**

**Backend API (Terminal 1)**:
```powershell
# Desde la raíz del proyecto
cd src/api
conda activate chess_trainer
python -m uvicorn main:app --reload --port 8000

# Salida esperada:
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**Frontend React (Terminal 2)**:
```powershell
# Desde la raíz del proyecto
cd src/frontend
npm run dev

# Salida esperada:
# VITE ready in X ms
# Local: http://localhost:5173/
```

### **4. Verificar Base de Datos**

```powershell
conda activate chess_trainer
python

# En Python REPL:
from src.database.db_connector import DatabaseConnector

db = DatabaseConnector()
result = db.execute_query("SELECT COUNT(*) FROM games")
print(f"Total games in DB: {result[0][0]}")
# Debe mostrar: Total games in DB: 237250

# Verificar usuarios de prueba:
db.execute_query("SELECT username, role FROM users")
# Debe mostrar:
# [('admin', 'admin'), ('analyst', 'analyst'), ('user', 'user')]
```

---

## 👥 Usuarios de Prueba

### **Credenciales Configuradas**

| Usuario   | Contraseña   | Rol     | Permisos                             |
| --------- | ------------ | ------- | ------------------------------------ |
| `admin`   | `admin123`   | admin   | Ver todas las partidas + gestión     |
| `analyst` | `analyst123` | analyst | Ver todas las partidas               |
| `user`    | `user123`    | user    | Ver solo partidas propias (33 games) |

### **Crear Usuarios de Prueba (Si no existen)**

```powershell
conda activate chess_trainer
cd src/scripts
python create_test_users.py

# Salida esperada:
# Usuario admin creado exitosamente
# Usuario analyst creado exitosamente
# Usuario user creado exitosamente
```

---

## 🧪 Test Suite Completa

### **TEST 1: Registro de Usuario (API)**

**Endpoint**: `POST /auth/register`

```powershell
# Usando PowerShell
$body = @{
    username = "testuser"
    password = "test123"
    full_name = "Test User"
    email = "test@example.com"
    role = "user"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/auth/register" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

**Resultado Esperado**:
```json
{
    "id": 4,
    "username": "testuser",
    "full_name": "Test User",
    "email": "test@example.com",
    "role": "user",
    "is_active": true,
    "created_at": "2026-02-14T..."
}
```

---

### **TEST 2: Login de Usuario (API)**

**Endpoint**: `POST /auth/login`

```powershell
# Login con user admin
$credentials = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
    -Method Post `
    -Body $credentials `
    -ContentType "application/json"

# Guardar token para siguientes pruebas
$token = $response.access_token
Write-Host "Token: $token"
```

**Resultado Esperado**:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
        "id": 1,
        "username": "admin",
        "role": "admin"
    }
}
```

---

### **TEST 3: Verificar Usuario Actual (API)**

**Endpoint**: `GET /auth/me`

```powershell
# Usando el token del login anterior
$headers = @{
    "Authorization" = "Bearer $token"
}

Invoke-RestMethod -Uri "http://localhost:8000/auth/me" `
    -Method Get `
    -Headers $headers
```

**Resultado Esperado**:
```json
{
    "id": 1,
    "username": "admin",
    "full_name": "Administrator",
    "role": "admin",
    "is_active": true
}
```

---

### **TEST 4: Filtros por Rol - Usuario ADMIN**

**Endpoint**: `GET /games?page=1&page_size=10`

```powershell
# Login como admin
$credentials = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
    -Method Post `
    -Body $credentials `
    -ContentType "application/json"

$tokenAdmin = $response.access_token

# Obtener partidas
$headers = @{
    "Authorization" = "Bearer $tokenAdmin"
}

$games = Invoke-RestMethod -Uri "http://localhost:8000/games?page=1&page_size=10" `
    -Method Get `
    -Headers $headers

Write-Host "Total games visible to admin: $($games.total)"
Write-Host "Pages: $($games.pages)"
```

**Resultado Esperado**:
```json
{
    "total": 237250,
    "pages": 23725,
    "current_page": 1,
    "page_size": 10,
    "items": [
        {
            "id": 1,
            "white_player": "Player1",
            "black_player": "Player2",
            "imported_by": null,
            ...
        },
        ...
    ]
}
```

**✅ Validación**: Admin debe ver **TODAS** las 237,250 partidas.

---

### **TEST 5: Filtros por Rol - Usuario ANALYST**

```powershell
# Login como analyst
$credentials = @{
    username = "analyst"
    password = "analyst123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
    -Method Post `
    -Body $credentials `
    -ContentType "application/json"

$tokenAnalyst = $response.access_token

# Obtener partidas
$headers = @{
    "Authorization" = "Bearer $tokenAnalyst"
}

$games = Invoke-RestMethod -Uri "http://localhost:8000/games?page=1&page_size=10" `
    -Method Get `
    -Headers $headers

Write-Host "Total games visible to analyst: $($games.total)"
```

**Resultado Esperado**: `total: 237250`

**✅ Validación**: Analyst debe ver **TODAS** las 237,250 partidas.

---

### **TEST 6: Filtros por Rol - Usuario USER (Crítico)**

```powershell
# Login como user
$credentials = @{
    username = "user"
    password = "user123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
    -Method Post `
    -Body $credentials `
    -ContentType "application/json"

$tokenUser = $response.access_token

# Obtener partidas
$headers = @{
    "Authorization" = "Bearer $tokenUser"
}

$games = Invoke-RestMethod -Uri "http://localhost:8000/games?page=1&page_size=10" `
    -Method Get `
    -Headers $headers

Write-Host "Total games visible to user: $($games.total)"
Write-Host "First game imported_by: $($games.items[0].imported_by)"
```

**Resultado Esperado**: 
```json
{
    "total": 33,
    "pages": 4,
    "current_page": 1,
    "page_size": 10,
    "items": [
        {
            "id": ...,
            "white_player": "...",
            "black_player": "...",
            "imported_by": "user",
            ...
        },
        ...
    ]
}
```

**✅ Validación CRÍTICA**: User debe ver **SOLO 33 partidas** (las importadas por él mismo). Todas deben tener `imported_by: "user"`.

---

### **TEST 7: Paginación Funcional**

```powershell
# Verificar paginación como admin
$headers = @{
    "Authorization" = "Bearer $tokenAdmin"
}

# Página 1
$page1 = Invoke-RestMethod -Uri "http://localhost:8000/games?page=1&page_size=5" `
    -Method Get `
    -Headers $headers

# Página 2
$page2 = Invoke-RestMethod -Uri "http://localhost:8000/games?page=2&page_size=5" `
    -Method Get `
    -Headers $headers

# Verificar que los IDs son diferentes
Write-Host "Page 1 first game ID: $($page1.items[0].id)"
Write-Host "Page 2 first game ID: $($page2.items[0].id)"
```

**✅ Validación**: Los IDs de la página 1 y página 2 deben ser diferentes.

---

### **TEST 8: Acceso Sin Autenticación (Debe Fallar)**

```powershell
# Intentar acceder sin token
Invoke-RestMethod -Uri "http://localhost:8000/games?page=1&page_size=10" `
    -Method Get
```

**Resultado Esperado**: Error 401 Unauthorized
```json
{
    "detail": "Not authenticated"
}
```

**✅ Validación**: El endpoint debe rechazar solicitudes sin token.

---

## 🌐 Pruebas en Frontend (React UI)

### **TEST 9: Login en UI**

1. Abrir navegador: `http://localhost:5173`
2. Deberías ver la página de Login
3. Ingresar credenciales:
   - **Username**: `admin`
   - **Password**: `admin123`
4. Click en "Login"

**Resultado Esperado**:
- Redirección a `/database-browser`
- Token guardado en `localStorage`
- Nombre de usuario visible en navbar

**Verificar en DevTools (F12)**:
```javascript
localStorage.getItem('token')
// Debe mostrar: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

JSON.parse(localStorage.getItem('user'))
// Debe mostrar: { id: 1, username: "admin", role: "admin", ... }
```

---

### **TEST 10: Database Browser - Admin View**

Con sesión activa como `admin`:

1. Navegar a: `http://localhost:5173/database-browser`
2. Verificar encabezado: "Database Browser"
3. Verificar contador: "Total Games: 237,250"
4. Verificar tabla con 10 partidas por página
5. Verificar botones de paginación funcionales

**✅ Validación**: Admin ve todas las 237,250 partidas.

---

### **TEST 11: Database Browser - User View (Filtrado)**

1. Cerrar sesión (click en "Logout" si está disponible)
2. O borrar tokens:
   ```javascript
   // En DevTools Console
   localStorage.clear()
   ```
3. Recargar página: `http://localhost:5173`
4. Login con:
   - **Username**: `user`
   - **Password**: `user123`
5. Navegar a Database Browser

**Resultado Esperado**:
- Contador: "Total Games: 33"
- Solo 4 páginas de paginación (33 games / 10 per page)
- Todas las partidas tienen `imported_by: "user"`

**✅ Validación CRÍTICA**: User **NO** debe ver las 237,250 partidas, **SOLO** sus 33 partidas.

---

### **TEST 12: Protección de Rutas**

1. Borrar tokens en DevTools:
   ```javascript
   localStorage.clear()
   ```
2. Intentar acceder directamente: `http://localhost:5173/database-browser`

**Resultado Esperado**:
- Redirección automática a `/login`
- Mensaje: "Please log in to continue"

**✅ Validación**: Rutas protegidas redirigen a login sin sesión activa.

---

## 🔍 Verificación en Base de Datos

### **TEST 13: Verificar Datos en PostgreSQL**

```powershell
conda activate chess_trainer
python

# En Python REPL:
from src.database.db_connector import DatabaseConnector

db = DatabaseConnector()

# 1. Total de partidas
total = db.execute_query("SELECT COUNT(*) FROM games")[0][0]
print(f"Total games: {total}")
# Esperado: 237250

# 2. Partidas del usuario 'user'
user_games = db.execute_query(
    "SELECT COUNT(*) FROM games WHERE imported_by = 'user'"
)[0][0]
print(f"User's games: {user_games}")
# Esperado: 33

# 3. Verificar usuarios
users = db.execute_query("SELECT username, role FROM users")
print(f"Users: {users}")
# Esperado: [('admin', 'admin'), ('analyst', 'analyst'), ('user', 'user')]

# 4. Ver una partida del user
user_game = db.execute_query(
    "SELECT id, white_player, black_player, imported_by FROM games WHERE imported_by = 'user' LIMIT 1"
)[0]
print(f"Sample user game: {user_game}")
# Esperado: (id, 'player_name', 'player_name', 'user')
```

---

## 📊 Validación Final

### **Checklist de Validación Completa**

- [ ] ✅ Backend API corriendo en puerto 8000
- [ ] ✅ Frontend corriendo en puerto 5173
- [ ] ✅ PostgreSQL con 237,250 partidas
- [ ] ✅ 3 usuarios de prueba creados (admin, analyst, user)
- [ ] ✅ 33 partidas importadas por 'user'
- [ ] ✅ Login API funciona para los 3 usuarios
- [ ] ✅ Endpoint `/auth/me` retorna datos correctos
- [ ] ✅ Admin ve 237,250 partidas
- [ ] ✅ Analyst ve 237,250 partidas
- [ ] ✅ User ve **SOLO** 33 partidas (CRÍTICO)
- [ ] ✅ Paginación funciona en todos los casos
- [ ] ✅ Acceso sin token es rechazado (401)
- [ ] ✅ Login UI funciona y guarda tokens
- [ ] ✅ Database Browser UI muestra filtros correctos
- [ ] ✅ Rutas protegidas redirigen a login
- [ ] ✅ Verificación en PostgreSQL confirma datos

---

## 🐛 Troubleshooting

### **Problema: API no responde**
```powershell
# Verificar que el proceso está corriendo
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# Si no está corriendo, iniciar API:
cd src/api
conda activate chess_trainer
python -m uvicorn main:app --reload --port 8000
```

### **Problema: Frontend no carga**
```powershell
# Verificar proceso Node
Get-Process | Where-Object {$_.ProcessName -like "*node*"}

# Si no está corriendo:
cd src/frontend
npm run dev
```

### **Problema: "Database connection failed"**
```powershell
# Verificar Docker containers
docker-compose ps

# Si postgres no está corriendo:
docker-compose up -d postgres

# Esperar 10 segundos para que PostgreSQL inicie
Start-Sleep -Seconds 10
```

### **Problema: "User already exists"**
```powershell
# Eliminar usuarios y recrear
conda activate chess_trainer
python

from src.database.db_connector import DatabaseConnector
db = DatabaseConnector()
db.execute_query("DELETE FROM users WHERE username IN ('admin', 'analyst', 'user')")

# Luego ejecutar create_test_users.py nuevamente
```

### **Problema: User ve todas las partidas (237,250) en vez de sus 33**
**Esto indica un bug en el filtrado. Verificar**:

1. **Backend - `src/api/routers/games.py`**:
   ```python
   # Debe tener esta lógica:
   if current_user.role == "user":
       query = query.filter(Game.imported_by == current_user.username)
   ```

2. **Verificar en DB que el campo `imported_by` existe**:
   ```powershell
   python
   from src.database.db_connector import DatabaseConnector
   db = DatabaseConnector()
   
   # Ver estructura de la tabla
   db.execute_query("""
       SELECT column_name, data_type 
       FROM information_schema.columns 
       WHERE table_name = 'games'
   """)
   # Debe incluir: ('imported_by', 'character varying')
   ```

3. **Verificar que hay 33 partidas con imported_by='user'**:
   ```python
   count = db.execute_query("SELECT COUNT(*) FROM games WHERE imported_by = 'user'")
   print(count)  # Debe ser 33
   ```

---

## 📚 Referencias

- **Backend API**: [src/api/main.py](../src/api/main.py)
- **Routers**: [src/api/routers/](../src/api/routers/)
- **Frontend Auth**: [src/frontend/src/contexts/AuthContext.jsx](../src/frontend/src/contexts/AuthContext.jsx)
- **Database Models**: [src/database/models.py](../src/database/models.py)
- **Create Test Users Script**: [src/scripts/create_test_users.py](../src/scripts/create_test_users.py)
- **Roadmap Funcional**: [ROADMAP_FUNCTIONAL_CHESS_TRAINER.md](ROADMAP_FUNCTIONAL_CHESS_TRAINER.md)
- **Roadmap Técnico**: [ROADMAP_TECHNICAL.md](ROADMAP_TECHNICAL.md)

---

## ✅ Conclusión

Este test suite valida completamente:
1. ✅ Sistema de autenticación JWT funcional
2. ✅ Registro y login de usuarios
3. ✅ Role-Based Access Control (RBAC)
4. ✅ Filtros por rol en Database Browser
5. ✅ Paginación funcional
6. ✅ Protección de rutas en frontend
7. ✅ Persistencia de sesión con tokens

**Todas las pruebas deben pasar para considerar Sprint 1 completado exitosamente.**

---

_Documento creado: 14 de Febrero, 2026_  
_Versión: v0.1.122-f8e6b29_  
_Autor: Chess Trainer Development Team_
