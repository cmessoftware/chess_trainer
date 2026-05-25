# =============================================================================
# Guía para Regenerar Análisis SHAP con Nuevos Campos
# =============================================================================
# Fecha: 2026-02-28
# Estado: Base de datos limpiada - 0 análisis, 0 SHAP values
# =============================================================================

## ✅ Borrado Completado

- ✅ 28,458 SHAP values eliminados
- ✅ 23 análisis eliminados
- ✅ Base de datos lista para regeneración

## 🚀 Paso 1: Verificar API Corriendo

El API debe estar corriendo en: http://localhost:8000

```powershell
# Verificar si está corriendo
Invoke-RestMethod -Uri "http://localhost:8000/docs" -Method GET

# Si no responde, iniciar con:
cd c:\Users\sergiosal\source\repos\chess_trainer\src\api
C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe -m uvicorn main:app --reload --port 8000
```

## 🔑 Paso 2: Obtener Token en Postman

**Request:**
```http
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "username": "admin"
}
```

Copia el `access_token` y guárdalo en tu environment de Postman como `{{token}}`

## 🎯 Paso 3: Regenerar SHAP para Partidas

Necesitas el `game_id` de cada partida que quieres analizar.

### Opción A: Regenerar UNA partida (Prueba)

**Request:**
```http
POST http://localhost:8000/api/analysis/shap
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "game_id": "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb"
}
```

**Response esperada:**
```json
{
  "analysis_id": 1,
  "status": "success",
  "message": "SHAP analysis completed successfully"
}
```

⏱️ **Tiempo:** ~15-30 segundos por partida

### Opción B: Regenerar Múltiples Partidas (Postman Collection)

Si tienes una colección de Postman con múltiples game_ids:

1. **Abrir Collection:** `Chess_SHAP_Iterator.postman_collection.json`
2. **Variables requeridas:**
   ```json
   {
     "game_id": "{{game_id}}",
     "token": "{{token}}"
   }
   ```
3. **Ejecutar Collection** (Runner)
   - Iterations: Según cantidad de partidas
   - Delay: 2000ms entre requests
   - Data file: CSV con game_ids (opcional)

### Opción C: Script Python para Batch

```python
import requests
import time

BASE_URL = "http://localhost:8000"
TOKEN = "tu_token_aqui"

game_ids = [
    "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb",
    "otro_game_id_aqui",
    # ... más game_ids
]

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

for i, game_id in enumerate(game_ids, 1):
    print(f"\n[{i}/{len(game_ids)}] Analizando {game_id[:20]}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analysis/shap",
            headers=headers,
            json={"game_id": game_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Completado - Analysis ID: {data['analysis_id']}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
    
    # Delay para no sobrecargar
    time.sleep(2)

print(f"\n🎉 Regeneración completada: {len(game_ids)} partidas")
```

## ✅ Paso 4: Verificar Nuevos Campos

**Request:**
```http
GET http://localhost:8000/api/analysis/shap/game/5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb?move_number=1
Authorization: Bearer {{token}}
```

**Response esperada (CON NUEVOS CAMPOS):**
```json
[
  {
    "shap_id": 1,
    "analysis_id": 1,
    "game_id": "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb",
    "username": "admin",
    "error_label": "good",
    "accuracy_percentage": 84.16,
    "analyzed_at": "2026-02-28T19:00:00Z",
    "move_number": 1,
    "feature_name": "opponent_mobility",
    "shap_value": 0.6882,
    "feature_value": 22.0,
    
    // ✅ NUEVOS CAMPOS POBLADOS:
    "move_san": "e4",                                              // ← Notación algebraica
    "move_uci": "e2e4",                                           // ← Notación UCI
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  // ← Posición FEN
    "player_color": "white"                                       // ← Color del jugador
  }
]
```

## 📊 Paso 5: Verificar en Base de Datos

```sql
-- Ver análisis regenerados
SELECT 
    ar.id,
    ar.game_id,
    ar.username,
    COUNT(msv.id) AS shap_count,
    ar.analyzed_at
FROM analysis_results ar
LEFT JOIN move_shap_values msv ON msv.analysis_id = ar.id
GROUP BY ar.id, ar.game_id, ar.username, ar.analyzed_at
ORDER BY ar.analyzed_at DESC;

-- Verificar campos nuevos poblados
SELECT 
    move_number,
    move_san,
    move_uci,
    LEFT(fen, 40) AS fen_preview,
    player_color,
    feature_name,
    shap_value
FROM move_shap_values
WHERE analysis_id = 1
ORDER BY move_number, ABS(shap_value) DESC
LIMIT 20;

-- Verificar que NO hay NULL en campos nuevos
SELECT 
    COUNT(*) AS total_shap,
    SUM(CASE WHEN move_san IS NULL THEN 1 ELSE 0 END) AS null_move_san,
    SUM(CASE WHEN move_uci IS NULL THEN 1 ELSE 0 END) AS null_move_uci,
    SUM(CASE WHEN fen IS NULL THEN 1 ELSE 0 END) AS null_fen,
    SUM(CASE WHEN player_color IS NULL THEN 1 ELSE 0 END) AS null_player_color
FROM move_shap_values;
-- Debe retornar: 0 NULLs en todas las columnas nuevas
```

## 🤖 Paso 6: Probar Análisis con LLM

Una vez regenerado, puedes usar el siguiente prompt con ChatGPT/Claude:

```
Analiza esta jugada de ajedrez usando los SHAP values del modelo ML:

⚪ BLANCAS - Jugada 1: e4 (e2e4)
Clasificación ML: GOOD
Precisión del modelo: 84.16%

Posición FEN: 
rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1

SHAP Values (impacto en la clasificación):
1. opponent_mobility: +0.6882 → contribuye a BUENA jugada (Valor: 22.00)
2. material_balance: +0.3421 → contribuye a BUENA jugada (Valor: 0.00)
3. is_center_controlled: +0.2156 → contribuye a BUENA jugada (Valor: 1.00)

¿Por qué el modelo clasificó e4 (blancas) como "GOOD"?
¿Los SHAP values reflejan principios ajedrecísticos correctos?
```

## ⚠️ Troubleshooting

### API no responde
```powershell
# Verificar si está corriendo
Get-Process python | Where-Object {$_.ProcessName -eq "python"}

# Matar procesos Python y reiniciar
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
cd c:\Users\sergiosal\source\repos\chess_trainer\src\api
C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe -m uvicorn main:app --reload --port 8000
```

### Token expirado (401 Unauthorized)
- Volver a ejecutar POST /api/auth/login
- Actualizar variable `{{token}}` en Postman

### Análisis tarda mucho (>1 minuto)
- Normal: El análisis SHAP es computacionalmente costoso
- Esperar o verificar logs del API

### Campos siguen NULL después de regenerar
- Verificar que usaste el endpoint CORRECTO: `/api/analysis/shap` (no `/api/analysis/run`)
- Verificar versión del API (debe tener los cambios recientes)
- Verificar que el analysis_service.py tiene la extracción de player_color

## 📋 Checklist de Regeneración

- [ ] API corriendo en http://localhost:8000
- [ ] Token obtenido desde /api/auth/login
- [ ] Primera partida regenerada con POST /api/analysis/shap
- [ ] Campos verificados con GET /api/analysis/shap/game/{game_id}
- [ ] move_san, move_uci, fen, player_color tienen valores (no NULL)
- [ ] Múltiples partidas regeneradas (opcional)
- [ ] Verificación en base de datos (0 NULLs)
- [ ] Prueba con LLM completada

## 🎉 Resultado Final Esperado

```sql
-- Query de verificación final
SELECT 
    'Total análisis' AS metric, COUNT(*) AS value FROM analysis_results
UNION ALL
SELECT 
    'Total SHAP values', COUNT(*) FROM move_shap_values
UNION ALL
SELECT 
    'SHAP con move_san', COUNT(*) FROM move_shap_values WHERE move_san IS NOT NULL
UNION ALL
SELECT 
    'SHAP con player_color', COUNT(*) FROM move_shap_values WHERE player_color IS NOT NULL;
```

Debe retornar:
```
metric                    | value
--------------------------+-------
Total análisis            | 23     (o cuantos regeneraste)
Total SHAP values         | 28458  (depende de partidas)
SHAP con move_san         | 28458  (100% poblados)
SHAP con player_color     | 28458  (100% poblados)
```

---

**Estado:** ✅ BD limpia, lista para regenerar  
**Borrados:** 28,458 SHAP values, 23 análisis  
**Siguiente paso:** Regenerar desde Postman con POST /api/analysis/shap
