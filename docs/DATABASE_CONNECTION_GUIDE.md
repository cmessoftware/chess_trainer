# =============================================================================
# Guía de Conexión a PostgreSQL - chess_trainer_db
# =============================================================================

## ✅ Estado Verificado del Servidor

- **Contenedor:** chess_trainer-postgres-1
- **Estado:** Running (Up 3 days)
- **Puerto:** 5432 (expuesto en localhost)
- **Conexión:** Aceptando conexiones ✅

## 📋 Credenciales de Conexión

```
Host:     localhost
Port:     5432
Database: chess_trainer_db
User:     chess
Password: chess_pass
```

## 🔧 Configuración por Herramienta

### DBeaver (RECOMENDADO)

1. **Nueva Conexión → PostgreSQL**
2. **Main Tab:**
   ```
   Host:     localhost
   Port:     5432
   Database: chess_trainer_db
   Username: chess
   Password: chess_pass
   ```
3. **PostgreSQL Tab:**
   - Show all databases: ❌ (dejar desmarcado)
4. **Test Connection**
   - Si falla, instalar driver PostgreSQL desde DBeaver

### pgAdmin

1. **Register → Server**
2. **General Tab:**
   ```
   Name: Chess Trainer Local
   ```
3. **Connection Tab:**
   ```
   Host name:        localhost
   Port:             5432
   Maintenance DB:   chess_trainer_db
   Username:         chess
   Password:         chess_pass
   Save password:    ✅
   ```

### psql (Command Line)

```bash
# Opción A: Desde fuera del contenedor
psql -h localhost -p 5432 -U chess -d chess_trainer_db
# Password: chess_pass

# Opción B: Desde dentro del contenedor
docker exec -it chess_trainer-postgres-1 psql -U chess -d chess_trainer_db
```

### Python (psycopg2)

```python
import psycopg2

# Connection string
conn = psycopg2.connect(
    "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db"
)

# O con parámetros separados
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="chess_trainer_db",
    user="chess",
    password="chess_pass"
)

# Verificar conexión
cur = conn.cursor()
cur.execute("SELECT version()")
print(cur.fetchone())
conn.close()
```

### SQLAlchemy (usado en el proyecto)

```python
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db"
engine = create_engine(DATABASE_URL)

# Test connection
with engine.connect() as conn:
    result = conn.execute("SELECT COUNT(*) FROM analysis_results")
    print(f"Análisis: {result.fetchone()[0]}")
```

## 🚨 Troubleshooting

### Error: "Connection refused" (puerto 5432)

```bash
# Verificar que el contenedor está corriendo
docker ps | grep postgres

# Reiniciar contenedor si está detenido
docker-compose restart postgres

# O iniciar todo el stack
docker-compose up -d
```

### Error: "FATAL: password authentication failed"

- Verificar credenciales: `chess` / `chess_pass`
- Revisar archivo `.env` en la raíz del proyecto
- Variables de entorno:
  ```
  POSTGRES_USER=chess
  POSTGRES_PASSWORD=chess_pass
  POSTGRES_DB=chess_trainer_db
  ```

### Error: "database does not exist"

```bash
# Verificar databases disponibles
docker exec chess_trainer-postgres-1 psql -U chess -c "\l"

# Crear database si no existe
docker exec chess_trainer-postgres-1 psql -U chess -c "CREATE DATABASE chess_trainer_db;"
```

### Error: "could not translate host name" o "Name or service not known"

Usar **IP directa** en lugar de `localhost`:
```
Host: 127.0.0.1  (en lugar de localhost)
Port: 5432
```

### Firewall bloqueando puerto 5432

```powershell
# Verificar si el puerto está en uso
netstat -ano | Select-String ":5432"

# Debería mostrar:
# TCP    0.0.0.0:5432    0.0.0.0:0    LISTENING    [PID]
```

## 📊 Consultas de Verificación Rápida

```sql
-- Ver todas las tablas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Count de registros principales
SELECT 
    'analysis_results' AS table_name, COUNT(*) AS count FROM analysis_results
UNION ALL
SELECT 
    'move_shap_values', COUNT(*) FROM move_shap_values
UNION ALL
SELECT 
    'features', COUNT(*) FROM features
UNION ALL
SELECT 
    'games', COUNT(*) FROM games;

-- Verificar columnas nuevas en move_shap_values
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'move_shap_values'
AND column_name IN ('move_san', 'move_uci', 'fen', 'player_color');

-- Ver análisis recientes
SELECT 
    id,
    game_id,
    username,
    accuracy_percentage,
    analyzed_at
FROM analysis_results
ORDER BY analyzed_at DESC
LIMIT 5;
```

## 🔍 Comandos de Diagnóstico

```powershell
# 1. Verificar contenedor corriendo
docker ps -a --filter "name=postgres"

# 2. Ver logs del contenedor (últimas 50 líneas)
docker logs chess_trainer-postgres-1 --tail 50

# 3. Verificar que acepta conexiones
docker exec chess_trainer-postgres-1 pg_isready -U chess -d chess_trainer_db

# 4. Ver procesos PostgreSQL dentro del contenedor
docker exec chess_trainer-postgres-1 ps aux | grep postgres

# 5. Verificar puerto expuesto
docker port chess_trainer-postgres-1 5432

# 6. Test de conexión desde Python
C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe -c "import psycopg2; conn = psycopg2.connect('postgresql://chess:chess_pass@localhost:5432/chess_trainer_db'); print('✅ Conexión exitosa'); conn.close()"
```

## 🔄 Reiniciar Servicios (si necesario)

```bash
# Solo PostgreSQL
docker-compose restart postgres

# Todo el stack (postgres + notebooks + chess_trainer)
docker-compose restart

# Parar y reiniciar todo
docker-compose down
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f postgres
```

## 📝 Estado Actual Verificado

```
✅ Contenedor: chess_trainer-postgres-1 (Up 3 days)
✅ Puerto 5432: Accesible
✅ PostgreSQL: Aceptando conexiones
✅ Database: chess_trainer_db (23 análisis)
✅ Versión: PostgreSQL 13.22
```

---

**Última verificación:** 2026-02-28  
**Estado:** ✅ Operacional  
**Registros en DB:** 23 análisis, múltiples SHAP values
