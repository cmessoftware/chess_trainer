# 🧠 Chess LLM Pedagogical Reports API - Postman Collection

Colección de Postman para testing de **FUNCIONALIDAD 3.6.1 - Fase 1: LLM Pedagógico MVP**.

## 📋 Descripción

Esta colección permite probar los endpoints de generación de informes pedagógicos personalizados usando GPT-4 con adaptación automática por nivel ELO.

### ✨ Características Principales

- **Adaptación por ELO**: Prompts y lenguaje adaptados a 4 niveles (<1200, 1200-1700, 1700-2100, 2100+)
- **Interpretación SHAP**: Traduce análisis técnico a feedback pedagógico comprensible
- **5 Secciones**: Diagnóstico, Patrones, Recomendaciones, Áreas de Mejora, Aspectos Positivos
- **Token Tracking**: Monitoreo de consumo y costos estimados
- **Batch Processing**: Generación de múltiples informes en una sola llamada

## 🚀 Requisitos Previos

1. **API chess_trainer ejecutándose**:
   ```bash
   # En PowerShell, desde la raíz del proyecto:
   cd src/api
   C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe -m uvicorn main:app --reload --port 8000
   ```

2. **OpenAI API Key configurada**:
   - Obtener key desde: https://platform.openai.com/api-keys
   - Configurar billing (mínimo $5 recomendado)
   - Editar `.env` y reemplazar:
     ```
     OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXX
     ```

3. **Usuario admin creado**:
   - Username: `admin`
   - Password: `admin123`

## 📥 Instalación

### 1. Importar Colección

1. Abrir Postman
2. Click en **Import**
3. Seleccionar `Chess_LLM_Pedagogical_Reports.postman_collection.json`

### 2. Importar Environment

1. Click en **Import**
2. Seleccionar `Chess_LLM_Pedagogical_Local.postman_environment.json`
3. Seleccionar environment "Chess LLM Pedagogical - Local" en el dropdown

### 3. Configurar Variables (Opcional)

Si tus game_ids son diferentes, actualiza las variables en el environment:

- `game_id_beginner`: Game ID para testing con ELO ~1400
- `game_id_intermediate`: Game ID para testing con ELO ~1800
- `game_id_advanced`: Game ID para testing con ELO 2800+
- `existing_analysis_id`: ID de un análisis ML existente (para testing de reuse)

## 🧪 Uso

### Flujo Básico

#### 1. Autenticación
Ejecutar: **1. Authentication > Login - Get Token**

Esto guarda automáticamente el token JWT en la variable de entorno `{{token}}`.

#### 2. Generar Informe Individual

Ejecutar cualquiera de:
- **2. LLM Reports - Individual > Generate Report - ELO 1400 (Beginner)**
- **2. LLM Reports - Individual > Generate Report - ELO 1800 (Intermediate)**
- **2. LLM Reports - Individual > Generate Report - ELO 2200 (Advanced)**

#### 3. Generar Informes en Batch

Ejecutar: **3. LLM Reports - Batch > Generate Batch Reports - 3 Games**

### Respuesta Esperada (Individual)

```json
{
  "analysis_id": 48,
  "game_id": "aec7f86c250f0248...",
  "player_elo": 1400,
  "report": "# 🎯 DIAGNÓSTICO DE TU PARTIDA\n\n## 📊 Resumen General\n...",
  "tokens_used": {
    "prompt": 1520,
    "completion": 980,
    "total": 2500
  },
  "model": "gpt-4",
  "cost_estimate_usd": 0.105,
  "generated_at": "2026-03-01T10:30:00"
}
```

### Respuesta Esperada (Batch)

```json
{
  "total_games": 3,
  "successful": 3,
  "failed": 0,
  "total_cost_usd": 0.312,
  "total_tokens": 7450,
  "reports": [
    {
      "analysis_id": 48,
      "game_id": "aec7f86c...",
      "player_elo": 1600,
      "report": "# 🎯 DIAGNÓSTICO...",
      "tokens_used": { "prompt": 1520, "completion": 980, "total": 2500 },
      "model": "gpt-4",
      "cost_estimate_usd": 0.104
    },
    // ... más informes
  ]
}
```

## 📊 Tests Automáticos

Cada request incluye tests que verifican:

✅ **Status Code**: 200 OK  
✅ **Response Structure**: Campos requeridos presentes  
✅ **Markdown Format**: Informe en formato Markdown válido  
✅ **Token Tracking**: Consumo de tokens registrado  
✅ **Cost Estimation**: Costo estimado calculado  

Resultados visibles en la pestaña **Test Results** de Postman.

## 💰 Costos Estimados (GPT-4)

| Escenario           | Tokens Estimados | Costo Estimado |
| ------------------- | ---------------- | -------------- |
| Análisis individual | ~2,500           | $0.10          |
| Batch (3 partidas)  | ~7,500           | $0.30          |
| Batch (10 partidas) | ~25,000          | $1.00          |

**Nota**: Los costos reales pueden variar según:
- Longitud del análisis SHAP
- Complejidad de la partida
- Nivel de detalle del informe generado

## 🎯 Adaptación por ELO

### ELO < 1200 (Beginner)
- **Focus**: Material, tácticas básicas
- **Language**: Simple y directo
- **Severity**: Solo errores mayores (≥1.5 pawns)

### ELO 1200-1700 (Intermediate)
- **Focus**: Desarrollo, iniciativa, control del centro
- **Language**: Conceptos posicionales básicos
- **Severity**: Errores moderados (≥1.0 pawns)

### ELO 1700-2100 (Advanced)
- **Focus**: Estructura, planes, profilaxis
- **Language**: Técnico moderado
- **Severity**: Errores pequeños (≥0.7 pawns)

### ELO 2100+ (Expert)
- **Focus**: Optimización fina, precisión dinámica
- **Language**: Técnico completo
- **Severity**: Errores mínimos (≥0.5 pawns)

## 🔍 Troubleshooting

### Error: "OPENAI_API_KEY faltante"
```json
{
  "detail": "OPENAI_API_KEY no configurada en .env"
}
```
**Solución**: Configurar API key en archivo `.env` y reiniciar API.

### Error: "Game ID no encontrado"
```json
{
  "detail": "Game not found: invalid-game-id-12345"
}
```
**Solución**: Verificar que el game_id existe en la base de datos. Usar IDs del environment.

### Error: "Token inválido"
```json
{
  "detail": "Could not validate credentials"
}
```
**Solución**: Ejecutar nuevamente el request de Login para obtener un token válido.

### Error: "Rate limit exceeded" (OpenAI)
```json
{
  "detail": "Error generando informe LLM: Rate limit exceeded"
}
```
**Solución**: Esperar 1 minuto y reintentar. Para batch processing, el sistema procesa secuencialmente para evitar este error.

## 📚 Documentación Adicional

- **Roadmap Técnico**: `docs/ROADMAP_INTEGRACION_LLM.md`
- **Roadmap Funcional**: `docs/ROADMAP_FUNCTIONAL_CHESS_TRAINER.md` (FUNCIONALIDAD 3.6.1)
- **Comparative Analysis**: `COMPARATIVE_ANALYSIS_ELO_1400_vs_2800.md`

## 🛠️ Desarrollo

### Agregar Nuevos Tests

Para agregar tests personalizados, editar el campo `event.test.script.exec`:

```javascript
pm.test("Custom test name", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.report).to.include("expected text");
});
```

### Modificar Variables

Editar el environment `Chess_LLM_Pedagogical_Local.postman_environment.json`:

```json
{
    "key": "nueva_variable",
    "value": "valor",
    "type": "default",
    "enabled": true
}
```

## 📞 Soporte

Para issues o preguntas:
1. Revisar logs de la API (terminal donde corre uvicorn)
2. Verificar Console de Postman (View > Show Postman Console)
3. Consultar documentación en `docs/`

---

**Versión**: 1.0 (Fase 1 - MVP)  
**Última actualización**: 2026-03-01  
**Autor**: Chess Trainer Backend Team
