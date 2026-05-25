# -*- coding: utf-8 -*-
"""Ejemplos de consultas SHAP via API REST"""
print(
    """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     CONSULTAS SHAP VIA API REST                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

🔑 AUTENTICACIÓN:
   POST http://localhost:8000/api/auth/login
   Body: {"username": "admin", "password": "admin123"}
   → Devuelve: {"access_token": "..."}

📊 EJECUTAR ANÁLISIS SHAP:
   POST http://localhost:8000/api/analysis/run
   Headers: Authorization: Bearer {token}
   Body: {"game_id": "6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3"}
   → Devuelve: {"analysis_id": 12, "status": "completed", "message": "..."}

🔍 CONSULTAR SHAP DE UNA JUGADA ESPECÍFICA:
   GET http://localhost:8000/api/analysis/game/{game_id}/shap?move_number=1
   Headers: Authorization: Bearer {token}
   Ejemplo:
   GET http://localhost:8000/api/analysis/game/6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3/shap?move_number=1
   
   → Devuelve:
   {
     "move_number": 1,
     "error_level": "unknown",
     "top_features": [
       {"feature": "material_balance", "impact": 0.1636, "value": 0.0},
       {"feature": "is_center_controlled", "impact": -0.1227, "value": 0.0},
       {"feature": "material_total", "impact": 0.1166, "value": 78.0},
       ...
     ]
   }

📈 FEATURE IMPORTANCE GLOBAL:
   GET http://localhost:8000/api/analysis/global-feature-importance
   Headers: Authorization: Bearer {token}
   → Devuelve lista de features ordenadas por importancia

📋 HISTORIAL DE ANÁLISIS:
   GET http://localhost:8000/api/analysis/history
   Headers: Authorization: Bearer {token}
   → Devuelve todos los análisis del usuario

╔═══════════════════════════════════════════════════════════════════════════════╗
║                           EJEMPLOS CON CURL                                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝

# 1. Login
curl -X POST http://localhost:8000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d "{\\"username\\":\\"admin\\",\\"password\\":\\"admin123\\"}"

# 2. Guardar token (Windows PowerShell)
$token = (curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | ConvertFrom-Json).access_token

# 3. Ejecutar análisis
curl -X POST http://localhost:8000/api/analysis/run \\
  -H "Authorization: Bearer $token" \\
  -H "Content-Type: application/json" \\
  -d "{\\"game_id\\":\\"6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3\\"}"

# 4. Consultar SHAP del movimiento 1
curl -X GET "http://localhost:8000/api/analysis/game/6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3/shap?move_number=1" \\
  -H "Authorization: Bearer $token"

╔═══════════════════════════════════════════════════════════════════════════════╗
║                        DOCUMENTACIÓN INTERACTIVA                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝

🌐 Swagger UI (recomendado):
   http://localhost:8000/docs
   
   → Interfaz interactiva donde puedes:
     - Ver todos los endpoints disponibles
     - Probar requests directamente desde el navegador
     - Ver schemas de request/response
     - Autenticarte y guardar el token

📘 ReDoc (alternativa):
   http://localhost:8000/redoc
   → Documentación estilo libro

╔═══════════════════════════════════════════════════════════════════════════════╗
║                          BASE DE DATOS DIRECTA                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Puedes consultar directamente con SQL:

-- Ver todos los análisis
SELECT * FROM analysis_results ORDER BY analyzed_at DESC;

-- Ver SHAP values de un análisis  
SELECT * FROM move_shap_values WHERE analysis_id = 12 ORDER BY move_number, ABS(shap_value) DESC;

-- Top features globalmente
SELECT 
    feature_name,
    AVG(ABS(shap_value)) as avg_impact,
    COUNT(*) as samples
FROM move_shap_values
GROUP BY feature_name
ORDER BY AVG(ABS(shap_value)) DESC;

-- Player feature importance
SELECT * FROM player_feature_importance WHERE username = 'admin';

═══════════════════════════════════════════════════════════════════════════════

💡 TIP: Abre http://localhost:8000/docs en tu navegador para la forma más fácil
        de explorar los resultados SHAP interactivamente.
"""
)
