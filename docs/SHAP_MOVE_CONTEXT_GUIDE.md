# Agregar Contexto de Movimiento a SHAP Analysis

## 🎯 Objetivo

Agregar contexto completo del movimiento a los SHAP values para facilitar:
- Análisis con LLM (GPT-4, Claude, etc.)
- Reportes human-readable
- Debugging y visualización
- Identificación clara del jugador (blancas/negras)

## ✅ Cambios Implementados

### 1. **Modelo `MoveShapValue`**
Agregadas 4 columnas nuevas:
- `move_san` (String, 20): Notación algebraica (e.g., "Nf3", "e4", "O-O")
- `move_uci` (String, 10): Notación UCI (e.g., "e2e4", "g1f3")
- `fen` (String, 100): Posición FEN antes del movimiento
- `player_color` (String, 10): Color del jugador ('white' o 'black')

### 2. **Servicio de Análisis**
- `analysis_service.py` ahora extrae move context de la tabla `Features`
- Los valores se guardan al crear cada `MoveShapValue`
- Convierte `player_color` (0/1 → 'white'/'black') para legibilidad

### 3. **Vista `shap_values_with_games`**
Actualizada para incluir las 4 columnas nuevas en las consultas.

### 4. **Migrations de Alembic**
- `add_move_context_to_shap.py`: Agrega move_san, move_uci, fen
- `update_shap_view_with_moves.py`: Actualiza vista con movimientos
- `add_player_color_to_shap.py`: Agrega player_color
- `update_shap_view_add_player_color.py`: Actualiza vista con player_color

## 📦 Cómo Aplicar los Cambios

### Paso 1: Ejecutar Migrations

```bash
# Activar entorno conda
conda activate chess_trainer

# Ejecutar migrations
cd c:\Users\sergiosal\source\repos\chess_trainer
alemb upgrade head
```

### Paso 2: Verificar Cambios

```python
# tests/verification/test_shap_with_moves.py
import psycopg2

conn = psycopg2.connect(
    dbname='chess_trainer_db',
    user='chess',
    password='chess_pass',
    host='localhost'
)
cur = conn.cursor()

# Verificar nuevas columnas
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'move_shap_values'
    AND column_name IN ('move_san', 'move_uci', 'fen', 'player_color')
""")

print("Nuevas columnas en move_shap_values:")
for col in cur.fetchall():
    print(f"  ✅ {col[0]}: {col[1]}")

conn.close()
```

### Paso 3: Regenerar SHAP para Partidas Existentes

Las partidas con SHAP existente **NO tendrán** los movimientos hasta que se regeneren.

⚠️ **Importante:** Usar SQL directo (no hay endpoint DELETE por seguridad)

```sql
-- Opción A: Ver análisis con campos NULL (necesitan regeneración)
SELECT 
    ar.id,
    ar.game_id,
    COUNT(msv.id) AS total_shap,
    SUM(CASE WHEN msv.move_san IS NULL THEN 1 ELSE 0 END) AS null_count
FROM analysis_results ar
LEFT JOIN move_shap_values msv ON msv.analysis_id = ar.id
GROUP BY ar.id, ar.game_id
HAVING SUM(CASE WHEN msv.move_san IS NULL THEN 1 ELSE 0 END) > 0;

-- Opción B: Limpiar y regenerar todos los análisis
DELETE FROM move_shap_values;     -- PRIMERO (FK constraint)
DELETE FROM analysis_results;      -- DESPUÉS

-- Opción C: Solo regenerar partidas específicas
DELETE FROM move_shap_values WHERE analysis_id IN (
    SELECT id FROM analysis_results WHERE game_id = '<game_id>'
);
DELETE FROM analysis_results WHERE game_id = '<game_id>';
```

📄 **Script completo con todas las opciones:** `tests/verification/manual_delete_shap_analysis.sql`

Luego ejecutar análisis nuevamente desde Postman o Python.

## 🔬 Salida Antes vs Después

### ANTES (sin contexto de movimiento)
```json
{
    "move_number": 15,
    "feature_name": "opponent_mobility",
    "shap_value": 0.6882,
    "feature_value": 25.0,
    "error_label": "good"
}
```
❌ No sabes qué movimiento fue ni qué jugador lo hizo

### DESPUÉS (con contexto completo)
```json
{
    "move_number": 15,
    "feature_name": "opponent_mobility",
    "shap_value": 0.6882,
    "feature_value": 25.0,
    "error_label": "good",
    "move_san": "Nf3",
    "move_uci": "g1f3",
    "fen": "rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2",
    "player_color": "white"
}
```
✅ Contexto completo: movimiento, posición Y jugador

## 🤖 Uso con LLM

### Prompt Ejemplo para GPT-4/Claude:
```
⚪ BLANCAS - Jugada 15: Nf3 (g1f3)
Clasificación ML: GOOD

Posición FEN: 
rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2

SHAP Values (impacto en la clasificación):
1. opponent_mobility: +0.6882 → contribuye a BUENA jugada (Valor: 25.00)
2. material_balance: -0.3421 → contribuye a ERROR (Valor: 0.00)
3. is_center_controlled: +0.2156 → contribuye a BUENA jugada (Valor: 1.00)

¿Por qué el modelo clasificó Nf3 (blancas) como "GOOD"?
¿Qué aspectos posicionales peso más en la evaluación?
¿Los SHAP values reflejan principios ajedrecísticos correctos?
```

### Respuesta esperada del LLM:
```
El modelo ML clasifica Nf3 como jugada BUENA principalmente porque:

1. **opponent_mobility** (+0.69): Nf3 controla casillas centrales y limita
   las opciones del caballo enemigo en f6. Es el factor más importante.

   
2. **is_center_controlled** (+0.22): El caballo en f3 refuerza el control
   del centro (casillas d4, e5).

3. **material_balance** (-0.34): Ligera desventaja material, pero no 
   afecta la calidad de la jugada en esta posición temprana.

Conclusión: Nf3 es sólido desarrollo que cumple principios de apertura.
```

## 💡 Beneficios

✅ **No requiere JOINs** - El movimiento Y jugador ya están en move_shap_values  
✅ **Contexto completo** - LLM puede "ver" el tablero vía FEN  
✅ **Human-readable** - move_san y player_color son legibles ("⚪ Blancas: Nf3")  
✅ **Debugging** - Puedes reproducir posiciones directamente  
✅ **Reportes** - Tablas y dashboards más claros con identificación de jugador  
✅ **Análisis por color** - Filtrar errores por jugador (blancas vs negras)  

## 🚨 Notas Importantes

- Partidas con SHAP existente necesitan regenerarse
- Las columnas son `nullable=True` (compatibilidad hacia atrás)
- FENs pueden ser largos (~80-100 caracteres)
- move_san puede contener '+', '#', '=Q', etc.
- player_color: 'white' o 'black' (string, no 0/1)

## 📋 Checklist de Implementación

- [x] Modelo MoveShapValue actualizado (4 columnas)
- [x] Servicio de análisis actualizado (extrae player_color)
- [x] Migrations creadas (4 migrations total)
- [x] Vista actualizada (incluye player_color)
- [x] Script de ejemplo actualizado
- [x] Documentación completada
- [x] **Migrations ejecutadas** (alembic upgrade head)
- [x] **Base de datos actualizada** con nuevas columnas
- [x] **API publicado** en http://localhost:8000
- [ ] **Regenerar SHAP** para partidas de test (ver instrucciones abajo)
- [ ] **Verificar** en Postman/API
- [ ] **Testear** con LLM

---

## 🚀 Cómo Probar el API

### 1. **Verificar que el API está corriendo**

```powershell
# El API debe estar corriendo en:
http://localhost:8000

# Docs interactivas:
http://localhost:8000/docs
```

### 2. **Obtener Token (desde Postman)**

```http
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "username": "tu_usuario",
  "password": "tu_password"
}
```

**Respuesta:**
```json
{
  "token": "eyJhbGci...",
  "username": "tu_usuario"
}
```

Guarda el token para los siguientes requests.

### 3. **Verificar SHAP Existentes (con campos NULL)**

```http
GET http://localhost:8000/api/analysis/shap/game/{game_id}
Authorization: Bearer {tu_token}
```

**Respuesta esperada:**
```json
{
  "shap_values": [
    {
      "move_number": 1,
      "feature_name": "opponent_mobility",
      "shap_value": 0.6882,
      "move_san": null,        // ⚠️ NULL hasta regenerar
      "move_uci": null,        // ⚠️ NULL hasta regenerar
      "fen": null,             // ⚠️ NULL hasta regenerar
      "player_color": null     // ⚠️ NULL hasta regenerar
    }
  ]
}
```

### 4. **Regenerar SHAP (para poblar nuevos campos)**

**Paso A: Eliminar análisis anterior (SQL manual)**

⚠️ **Nota:** El endpoint DELETE no está implementado por seguridad. Usa SQL directo en DBeaver/pgAdmin:

```sql
-- Ver análisis de la partida
SELECT ar.id, ar.game_id, COUNT(msv.id) AS shap_count
FROM analysis_results ar
LEFT JOIN move_shap_values msv ON msv.analysis_id = ar.id
WHERE ar.game_id = '5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb'
GROUP BY ar.id, ar.game_id;

-- BORRAR SHAP values (PRIMERO - por FK constraint)
DELETE FROM move_shap_values 
WHERE analysis_id IN (
    SELECT id FROM analysis_results 
    WHERE game_id = '5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb'
);

-- BORRAR análisis (DESPUÉS)
DELETE FROM analysis_results 
WHERE game_id = '5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb';
```

📄 **Script completo:** `tests/verification/manual_delete_shap_analysis.sql`

**Paso B: Generar nuevo análisis**
```http
POST http://localhost:8000/api/analysis/shap
Authorization: Bearer {tu_token}
Content-Type: application/json

{
  "game_id": "{game_id}"
}
```

**Respuesta:**
```json
{
  "message": "SHAP analysis completed",
  "total_shap_values": 603,
  "model_accuracy": 0.853
}
```

**Paso C: Verificar nuevos campos**
```http
GET http://localhost:8000/api/analysis/shap/game/{game_id}
Authorization: Bearer {tu_token}
```

**Respuesta con datos completos:**
```json
{
  "shap_values": [
    {
      "move_number": 1,
      "move_san": "e4",
      "move_uci": "e2e4",
      "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
      "player_color": "white",
      "feature_name": "opponent_mobility",
      "shap_value": 0.6882,
      "error_label": "good"
    }
  ]
}
```

---

## 🔧 Scripts de Verificación

### Script Python: Verificar Campos en API

```bash
# Editar TOKEN en el script con uno válido de Postman
python tests/verification/verify_shap_api_fields.py
```

### Script Python: Análisis Completo con LLM

```bash
# Requiere token válido
python tests/verification/example_llm_shap_analysis.py
```

### Postman Collection

Usa la colección `Chess_SHAP_Iterator.postman_collection.json`:
1. Importar en Postman
2. Configurar environment `Chess_SHAP_Local`
3. Ejecutar colección completa (itera todas las partidas)

---
_Implementado: 2026-02-28_  
_API Publicado: http://localhost:8000_  
_Estado: ✅ Listo para pruebas (regenerar SHAP para poblar campos)_
