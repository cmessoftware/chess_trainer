# 🚀 Guía Completa: Testing SHAP API con Postman

## ✅ Backend Status
**Estado:** ✅ Corriendo en `http://localhost:8000`  
**Documentación:** http://localhost:8000/docs

---

## 📋 Colección de Requests de Postman

### 1️⃣ **LOGIN** - Obtener Token de Autenticación

**Request:**
```
POST http://localhost:8000/api/auth/login
```

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "username": "admin",
    "password": "admin123"
}
```

**Respuesta esperada:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@chess.com"
    }
}
```

**⚠️ IMPORTANTE:** Copia el valor de `access_token` para los siguientes requests.

---

### 2️⃣ **CONSULTAR TODOS LOS SHAP VALUES DE UN GAME**

**Request:**
```
GET http://localhost:8000/api/analysis/shap/game/5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb
```

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```
*(Reemplaza con tu token del paso 1)*

**Respuesta esperada:**
```json
[
    {
        "shap_id": 12345,
        "analysis_id": 21,
        "game_id": "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb",
        "username": "admin",
        "error_label": "good",
        "accuracy_percentage": 95.5,
        "analyzed_at": "2026-02-27T10:30:00",
        "move_number": 1,
        "feature_name": "branching_factor",
        "shap_value": 0.3026,
        "feature_value": 42.0
    },
    {
        "shap_id": 12346,
        "analysis_id": 21,
        "game_id": "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb",
        "username": "admin",
        "error_label": "good",
        "accuracy_percentage": 95.5,
        "analyzed_at": "2026-02-27T10:30:00",
        "move_number": 1,
        "feature_name": "is_center_controlled",
        "shap_value": 0.2003,
        "feature_value": 1.0
    }
    // ... más resultados (total: 4,149)
]
```

**Total de registros:** 4,149 SHAP values

---

### 3️⃣ **CONSULTAR SHAP VALUES DE UNA JUGADA ESPECÍFICA**

**Request:**
```
GET http://localhost:8000/api/analysis/shap/game/5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb?move_number=10
```

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Respuesta esperada:**
```json
[
    {
        "shap_id": 12400,
        "analysis_id": 21,
        "game_id": "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb",
        "username": "admin",
        "error_label": "inaccuracy",
        "accuracy_percentage": 95.5,
        "analyzed_at": "2026-02-27T10:30:00",
        "move_number": 10,
        "feature_name": "material_total",
        "shap_value": 0.2706,
        "feature_value": 19.0
    },
    {
        "shap_id": 12401,
        "analysis_id": 21,
        "game_id": "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb",
        "username": "admin",
        "error_label": "inaccuracy",
        "accuracy_percentage": 95.5,
        "analyzed_at": "2026-02-27T10:30:00",
        "move_number": 10,
        "feature_name": "opponent_mobility",
        "shap_value": 0.2494,
        "feature_value": 25.0
    }
    // ... 7 features más (total: 9)
]
```

**Total de registros:** 9 features para la jugada #10

---

### 4️⃣ **CONSULTAR TOP N FEATURES POR JUGADA**

**Request:**
```
GET http://localhost:8000/api/analysis/shap/game/5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb?top_n=5
```

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Respuesta esperada:**
```json
[
    {
        "shap_id": 12345,
        "analysis_id": 21,
        "game_id": "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb",
        "username": "admin",
        "error_label": "good",
        "accuracy_percentage": 95.5,
        "analyzed_at": "2026-02-27T10:30:00",
        "move_number": 1,
        "feature_name": "branching_factor",
        "shap_value": 0.3026,
        "feature_value": 42.0
    }
    // ... Top 5 features para cada una de las 461 jugadas
    // Total: 2,305 registros (461 jugadas × 5 features)
]
```

**Total de registros:** 2,305 SHAP values (5 features por jugada, 461 jugadas)

---

### 5️⃣ **EJECUTAR NUEVO ANÁLISIS SHAP EN UN GAME**

**Request:**
```
POST http://localhost:8000/api/analysis/run
```

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "game_id": "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb"
}
```

**Respuesta esperada:**
```json
{
    "analysis_id": 27,
    "game_id": "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb",
    "status": "completed",
    "message": "✅ Análisis ML + SHAP completado exitosamente",
    "shap_values_count": 4149,
    "error_distribution": {
        "good": 3483,
        "inaccuracy": 333,
        "mistake": 261,
        "blunder": 63,
        "excellent": 9
    }
}
```

**⚠️ NOTA:** Si ya existe un análisis reciente (< 7 días), retornará el existente:
```json
{
    "analysis_id": 21,
    "status": "cached",
    "message": "♻️ Análisis existente encontrado (menos de 7 días)",
    "shap_values_count": 4149
}
```

---

## 🎯 Games de Ejemplo con SHAP Values

Estos games ya tienen SHAP values generados:

| Game ID                                                            | SHAP Values | Jugadas |
| ------------------------------------------------------------------ | ----------- | ------- |
| `5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb` | 4,149       | 461     |
| `d42d1c3c9bd2736fbc4898a3a6cc1be2e4e239b80ff3a615f317c3077018057b` | 3,789       | 421     |
| `666cbd367dce06ea2e4901f002bd33576e65418079c579b2bb6f7b244b9f28e6` | 3,735       | 415     |

---

## 📊 Análisis de Respuestas

### Distribución de error_labels esperada:
```
good:       81.3% (mayoría de jugadas)
inaccuracy: 10.0% (errores menores)
mistake:     6.9% (errores moderados)
blunder:     1.6% (errores graves)
excellent:   0.1% (jugadas brillantes)
book:        0.1% (jugadas de apertura)
```

### Features principales (mayor impacto SHAP):
1. **branching_factor** - Complejidad táctica de la posición
2. **material_total** - Balance material en el tablero
3. **opponent_mobility** - Movilidad de las piezas rivales
4. **is_center_controlled** - Control del centro
5. **move_number_global** - Fase de la partida

---

## 🔍 Validaciones en Postman

### ✅ Checklist de Tests:

1. **Login exitoso:**
   - Status: 200 OK
   - Body contiene: `access_token`

2. **Query completa funciona:**
   - Status: 200 OK
   - Array con 4,149 elementos
   - Cada elemento tiene: `error_label`, `shap_value`, `feature_name`

3. **Filtro por move_number:**
   - Status: 200 OK
   - Array con 9 elementos (9 features por jugada)
   - Todos tienen `move_number: 10`

4. **Filtro top_n:**
   - Status: 200 OK
   - Array con 2,305 elementos (461 × 5)
   - Solo top 5 features por jugada

5. **Análisis nuevo:**
   - Status: 200 OK (o 201 Created)
   - Body contiene: `analysis_id`, `shap_values_count`

### ❌ Errores comunes:

**401 Unauthorized:**
```json
{"detail": "Could not validate credentials"}
```
→ Token expirado o inválido. Hacer login nuevamente.

**404 Not Found:**
```json
{"detail": "No se encontraron SHAP values para el game especificado"}
```
→ El game_id no tiene análisis SHAP. Usar uno de los ejemplos o ejecutar análisis nuevo.

**403 Forbidden:**
```json
{"detail": "No autorizado para acceder a este análisis"}
```
→ El game pertenece a otro usuario. Solo puedes ver tus propios games.

---

## 🎨 Tips de Postman

### Configurar Environment Variable:
1. En Postman: `Environments` → `Create Environment`
2. Variables:
   - `base_url`: `http://localhost:8000`
   - `token`: (vacío inicialmente)
3. Usar en requests: `{{base_url}}/api/auth/login`

### Auto-guardar Token:
En request de Login, agregar en `Tests`:
```javascript
pm.test("Login successful", function () {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.environment.set("token", jsonData.access_token);
});
```

Luego en otros requests, usar en Headers:
```
Authorization: Bearer {{token}}
```

---

## 🔧 Troubleshooting

### Backend no responde:
```powershell
# Verificar si está corriendo
Get-NetTCPConnection -LocalPort 8000

# Reiniciar backend
cd src/api
C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe -m uvicorn main:app --reload --port 8000
```

### Ver logs del backend:
Los logs aparecen en la terminal donde ejecutaste uvicorn.

### Base de datos:
Si necesitas verificar datos directamente:
```powershell
conda activate chess_trainer
python check_latest_analysis.py
```

---

**✅ Sistema listo para testing en Postman**  
**📊 18,999 SHAP values disponibles**  
**🎯 Distribución realista de error_labels**
