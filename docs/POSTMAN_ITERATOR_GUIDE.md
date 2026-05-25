# 🔄 Iterador de SHAP Values - Postman

## 📦 Archivos Actualizados

### ✅ **Chess_SHAP_Local.postman_environment.json**
- Variable `token` movida al nivel raíz (no en array values)
- **4 game_ids de partidas reales** entre cmess1315 y manuelfrp79:
  - `game_id_1`: 603 SHAP values (cmess1315 vs manuelfrp79)
  - `game_id_2`: 513 SHAP values (manuelfrp79 vs cmess1315)
  - `game_id_3`: 513 SHAP values (manuelfrp79 vs cmess1315)
  - `game_id_4`: 252 SHAP values (cmess1315 vs manuelfrp79)

### 🆕 **Chess_SHAP_Iterator.postman_collection.json**
- **Request iterativo** que consulta TODOS los game_ids automáticamente
- **Scripts automáticos** para procesar y mostrar resultados
- **Auto-iteración** con pausa de 1 segundo entre requests

---

## 🚀 Uso del Iterador

### 1. Importar en Postman
```
1. Abrir Postman
2. Import → Chess_SHAP_Iterator.postman_collection.json
3. Verificar que environment "Chess SHAP - Local" esté seleccionado
```

### 2. Ejecutar Colección
```
1. Ejecutar "1. Login" (para obtener token)
2. Ejecutar "2. Obtener SHAP de TODAS las partidas"
   → Se ejecutará automáticamente 4 veces (una por cada game_id)
```

### 3. Ver Resultados en Console
Abre la **Postman Console** (Ctrl+Alt+C) para ver:
- ✅ Status de cada partida
- 📊 Distribución de error_labels
- 🎯 Top 5 features con mayor impacto SHAP
- 📋 Progreso (Partida X/4)

---

## 📊 Output Esperado

Para cada partida verás:
```
================================================================================
Partida 1/4
Game ID: aec7f86c250f0248fa65d9e1c5a320609ebe04ce...
SHAP values obtenidos: 603

📊 Distribución de error_labels:
   good              489 ( 81.1%)
   inaccuracy         60 (  9.9%)
   mistake            43 (  7.1%)
   blunder            10 (  1.7%)
   excellent           1 (  0.2%)

🎯 Top 5 features (mayor impacto SHAP):
   Move 12: material_balance          SHAP=0.3521
   Move 8: opponent_mobility          SHAP=0.3102
   Move 15: branching_factor          SHAP=-0.2845
   Move 23: is_center_controlled      SHAP=0.2634
   Move 5: self_mobility              SHAP=0.2511
================================================================================
```

---

## 🔧 Funcionamiento Técnico

### Pre-request Script:
1. Lee todos los `game_id_X` del environment
2. Guarda la lista completa en `all_game_ids`
3. Inicializa contador en 0

### Test Script (después de cada request):
1. Valida status 200
2. Procesa respuesta y muestra stats
3. Calcula distribución de error_labels
4. Muestra top 5 features
5. **Auto-itera** al siguiente game_id (si existe)
6. Detiene cuando procesa todos los IDs

### Variables temporales:
- `all_game_ids`: Array JSON con todos los IDs
- `current_game_index`: Índice actual (0-3)
- `next_request_url`: URL del próximo request (no usado actualmente)

---

## 📝 Personalización

### Agregar más game_ids:
1. Editar `Chess_SHAP_Local.postman_environment.json`
2. Agregar al array `values`:
```json
{
    "key": "game_id_5",
    "value": "NUEVO_GAME_ID_AQUI",
    "type": "default",
    "enabled": true,
    "description": "Descripción de la partida"
}
```
3. Re-importar environment en Postman

### Cambiar pausa entre requests:
En el **Test Script**, línea:
```javascript
setTimeout(() => {
    postman.setNextRequest(pm.info.requestName);
}, 1000); // ← Cambiar 1000 (1 seg) por el valor deseado en ms
```

### Agregar query parameters:
Modificar la URL en el request:
```
{{base_url}}/api/analysis/shap/game/{{game_id_1}}?top_n=5
{{base_url}}/api/analysis/shap/game/{{game_id_1}}?move_number=10
```

---

## 🎯 Ventajas del Iterador

✅ **Automático**: No necesitas ejecutar 4 requests manualmente  
✅ **Estadísticas**: Muestra distribución y top features automáticamente  
✅ **Pausa inteligente**: 1 segundo entre requests para no saturar el servidor  
✅ **Escalable**: Agrega cuantos game_ids quieras  
✅ **Logs detallados**: Todo en Postman Console con formato claro  

---

## 🛑 Detener Iteración

Si quieres detener la iteración antes de terminar:
1. Click en **Cancel** en Postman (durante ejecución)
2. O edita `current_game_index` en el environment para saltar partidas

---

## 📊 Resumen de Partidas Disponibles

| #   | Jugadores                | SHAP Values | Game ID (primeros 40 chars)              |
| --- | ------------------------ | ----------- | ---------------------------------------- |
| 1   | cmess1315 vs manuelfrp79 | 603         | aec7f86c250f0248fa65d9e1c5a320609ebe04ce |
| 2   | manuelfrp79 vs cmess1315 | 513         | 6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60 |
| 3   | manuelfrp79 vs cmess1315 | 513         | c8392462c80815c9c39026a1f6bf4b9d363a6cbc |
| 4   | cmess1315 vs manuelfrp79 | 252         | f195fb3ea8454c9f646eacabe04b4e46990de731 |

**Total SHAP values: 1,881**

---

## 📋 Notas

- Las 37 partidas restantes entre estos jugadores **no tienen features** generadas todavía
- Para generar features: ejecutar `src/scripts/generate_features_with_tactics.py`
- Una vez con features, ejecutar `process_cmess_manuelfrp_games.py` nuevamente

---

**Fecha:** 2026-02-28  
**Partidas procesadas:** 4 de 41 (37 pendientes de features)  
**Total SHAP values disponibles:** 1,881
