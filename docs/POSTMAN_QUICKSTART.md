# 🚀 QUICKSTART - Postman SHAP API Testing

## ⚡ Pasos Rápidos (5 minutos)

### 1️⃣ Importar Colección en Postman

1. Abrir Postman
2. Click en **Import** (arriba izquierda)
3. Arrastrar o seleccionar: `Chess_SHAP_API.postman_collection.json`
4. Importar también: `Chess_SHAP_Local.postman_environment.json`
5. Seleccionar environment **"Chess SHAP - Local"** (arriba derecha)

### 2️⃣ Ejecutar Requests

**Orden recomendado:**

1. **`1. Authentication > Login - Get Token`**
   - ✅ El token se guarda automáticamente en `{{token}}`
   - ✅ Verás en Console: "Token saved: eyJ0eXAiOiJKV1QiLC..."

2. **`2. SHAP Analysis - Query > Get All SHAP Values (Game 1)`**
   - ✅ Obtendrás 4,149 SHAP values
   - ✅ Verás distribución en Console: {good: 3483, inaccuracy: 333, ...}

3. **`2. SHAP Analysis - Query > Get SHAP Values - Specific Move`**
   - ✅ Obtendrás 9 features de la jugada #10
   - ✅ Verás top features en Console

4. **`2. SHAP Analysis - Query > Get SHAP Values - Top N Features`**
   - ✅ Obtendrás 2,305 SHAP values (top 5 × 461 jugadas)
   - ✅ Verás stats en Console

### 3️⃣ Ver Resultados

Cada request tiene **Tests automáticos** que se ejecutan:
- ✅ Green: Todos los tests pasaron
- ❌ Red: Algo falló (revisar error message)

Los **logs detallados** aparecen en:
- **Postman Console** (View > Show Postman Console)

---

## 📊 Datos de Prueba

### Games con SHAP Values Listos:

| Descripción            | Game ID             | SHAP Values |
| ---------------------- | ------------------- | ----------- |
| **Game 1 (más largo)** | `5daf60d3...4006bb` | 4,149       |
| **Game 2**             | `d42d1c3c...8057b`  | 3,789       |
| **Game 3**             | `666cbd36...f28e6`  | 3,735       |

*Los IDs completos están en la colección.*

---

## 🎯 Endpoints Disponibles

### GET `/api/analysis/shap/game/{game_id}`
**Query params:**
- `move_number` (opcional) - Filtrar por jugada específica
- `top_n` (opcional) - Limitar a top N features por jugada

**Ejemplos:**
```
GET /api/analysis/shap/game/5daf60...?move_number=10
GET /api/analysis/shap/game/5daf60...?top_n=5
GET /api/analysis/shap/game/5daf60...?move_number=10&top_n=3
```

### POST `/api/analysis/run`
Ejecutar nuevo análisis SHAP en un game.

**Body:**
```json
{
    "game_id": "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb"
}
```

---

## 🔍 Tests Automáticos Incluidos

Cada request ejecuta validaciones:

✅ **Status code** correcto (200, 201)  
✅ **Response structure** válida  
✅ **Data types** correctos  
✅ **SHAP values** presentes  
✅ **error_label** no nulo  
✅ **Distribución** realista  

---

## 🎨 Tips de Postman

### Ver Console:
- **Windows:** `Ctrl + Alt + C`
- **Mac:** `Cmd + Alt + C`
- O: `View > Show Postman Console`

### Ejecutar toda la colección:
1. Click derecho en colección
2. `Run collection`
3. Ver resultados consolidados

### Variables de entorno:
Las variables `{{base_url}}` y `{{token}}` se reemplazan automáticamente.

---

## ✅ Checklist de Validación

Después de ejecutar los requests, verifica:

| Test                         | Resultado | Observación                    |
| ---------------------------- | --------- | ------------------------------ |
| Login obtiene token          | ✅         | Token en Console + Environment |
| Query completa retorna 4,149 | ✅         | Array con SHAP values          |
| Distribution es 81% good     | ✅         | Verifica en Console logs       |
| Move #10 retorna 9 features  | ✅         | Todos move_number=10           |
| Top 5 retorna 2,305          | ✅         | 461 moves × 5 features         |
| error_label no es null       | ✅         | Todos los registros            |
| SHAP values son números      | ✅         | Float válidos                  |

---

## 🚨 Troubleshooting

### Error: "Could not validate credentials"
- **Causa:** Token expirado o inválido
- **Solución:** Ejecutar nuevamente `Login - Get Token`

### Error: "No se encontraron SHAP values"
- **Causa:** Game sin análisis SHAP
- **Solución:** Usar uno de los 3 game_ids de prueba

### Error: "Connection refused"
- **Causa:** Backend no está corriendo
- **Solución:** Ejecutar backend:
  ```powershell
  cd src/api
  C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe -m uvicorn main:app --reload --port 8000
  ```

### Backend corriendo pero no responde:
- Verificar puerto:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000
  ```

---

## 📚 Documentación Completa

- **Guía detallada:** `POSTMAN_SHAP_GUIDE.md`
- **API docs interactiva:** http://localhost:8000/docs
- **Sistema SHAP:** `docs/SHAP_ANALYSIS_API_DOCUMENTATION.md`

---

## 🎉 ¡Listo para Testing!

✅ Backend corriendo en `http://localhost:8000`  
✅ 18,999 SHAP values en base de datos  
✅ 3 games de prueba disponibles  
✅ Colección Postman lista con tests automáticos  

**Tiempo estimado:** 2-3 minutos para probar todos los endpoints.

---

**Duda o problema? Revisa:**
1. Backend logs en terminal
2. Postman Console (Ctrl+Alt+C)
3. API docs: http://localhost:8000/docs
