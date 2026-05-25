# API Response Example: SHAP con Move Context

## Endpoint
```
GET /api/analysis/shap/game/{game_id}
Authorization: Bearer <token>
```

## Response ANTES (sin move context)
```json
{
  "game_id": "cmess1315-vs-manuelfrp79-2024-08-18-00-15-00",
  "shap_values": [
    {
      "move_number": 15,
      "feature_name": "opponent_mobility",
      "shap_value": 0.6882,
      "feature_value": 25.0,
      "error_label": "good"
    },
    {
      "move_number": 15,
      "feature_name": "material_balance",
      "shap_value": -0.3421,
      "feature_value": 0.0,
      "error_label": "good"
    }
  ]
}
```

**Problema**: No sabes qué jugada fue (solo `move_number: 15`)

---

## Response DESPUÉS (con move context) ✅
```json
{
  "game_id": "cmess1315-vs-manuelfrp79-2024-08-18-00-15-00",
  "shap_values": [
    {
      "move_number": 15,
      "move_san": "Nf3",
      "move_uci": "g1f3",
      "fen": "rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2",
      "feature_name": "opponent_mobility",
      "shap_value": 0.6882,
      "feature_value": 25.0,
      "error_label": "good"
    },
    {
      "move_number": 15,
      "move_san": "Nf3",
      "move_uci": "g1f3",
      "fen": "rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2",
      "feature_name": "material_balance",
      "shap_value": -0.3421,
      "feature_value": 0.0,
      "error_label": "good"
    },
    {
      "move_number": 15,
      "move_san": "Nf3",
      "move_uci": "g1f3",
      "fen": "rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2",
      "feature_name": "is_center_controlled",
      "shap_value": 0.2156,
      "feature_value": 1.0,
      "error_label": "good"
    }
  ]
}
```

**Beneficios**:
- ✅ Sabes la jugada exacta: **Nf3** (algebraica) y **g1f3** (UCI)
- ✅ Puedes reproducir la posición desde el FEN
- ✅ Puedes enviar todo el contexto a un LLM
- ✅ Human-readable sin consultas adicionales

---

## Uso en Postman (Console Output)

### Script para iterar y mostrar moves:
```javascript
// En Tests tab del request SHAP
const response = pm.response.json();
const shap_values = response.shap_values;

// Agrupar por jugada
const moves = {};
shap_values.forEach(sv => {
    if (!moves[sv.move_number]) {
        moves[sv.move_number] = {
            move_san: sv.move_san,
            move_uci: sv.move_uci,
            fen: sv.fen,
            features: []
        };
    }
    moves[sv.move_number].features.push({
        name: sv.feature_name,
        shap: sv.shap_value,
        value: sv.feature_value
    });
});

// Mostrar en consola
console.log("========== SHAP ANALYSIS WITH MOVES ==========");
Object.keys(moves).sort((a,b) => a-b).forEach(moveNum => {
    const move = moves[moveNum];
    console.log(`\nMove ${moveNum}: ${move.move_san} (${move.move_uci})`);
    console.log(`FEN: ${move.fen}`);
    console.log("Top features:");
    
    move.features
        .sort((a, b) => Math.abs(b.shap) - Math.abs(a.shap))
        .slice(0, 3)
        .forEach((f, i) => {
            console.log(`  ${i+1}. ${f.name}: ${f.shap.toFixed(4)} (value: ${f.value})`);
        });
});
```

### Salida esperada:
```
========== SHAP ANALYSIS WITH MOVES ==========

Move 15: Nf3 (g1f3)
FEN: rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2
Top features:
  1. opponent_mobility: 0.6882 (value: 25)
  2. material_balance: -0.3421 (value: 0)
  3. is_center_controlled: 0.2156 (value: 1)

Move 16: d3 (d2d3)
FEN: rnbqkb1r/ppp1pppp/5n2/3p4/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq d6 0 3
Top features:
  1. num_pieces: 0.4521 (value: 32)
  2. material_total: 0.3890 (value: 78)
  3. opponent_mobility: 0.3012 (value: 27)
```

---

## Uso con LLM (ChatGPT/Claude)

### Prompt generado automáticamente:
```
Analiza esta jugada de ajedrez usando datos del modelo ML:

📍 Jugada 15: Nf3 (g1f3)
🎲 Clasificación: GOOD

🏁 Posición FEN:
rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2

📊 SHAP Values (impacto en la clasificación):
1. opponent_mobility: +0.6882 → contribuye a BUENA jugada (value: 25.0)
2. material_balance: -0.3421 → contribuye a ERROR (value: 0.0)
3. is_center_controlled: +0.2156 → contribuye a BUENA jugada (value: 1.0)

¿Por qué el modelo ML considera Nf3 una buena jugada?
¿Qué principios ajedrecísticos reflejan estos SHAP values?
```

### Respuesta esperada del LLM:
```
El modelo clasifica Nf3 como GOOD principalmente porque:

1. **opponent_mobility (+0.69)**: Nf3 controla casillas centrales (d4, e5)
   y limita opciones del caballo en f6. Es el factor MÁS importante.

2. **is_center_controlled (+0.22)**: El caballo refuerza control del centro,
   cumpliendo principios clásicos de desarrollo.

3. **material_balance (-0.34)**: Aunque hay ligera "penalidad", no afecta
   la clasificación global porque los factores posicionales dominan.

Conclusión: Nf3 es desarrollo sólido que prioriza control posicional sobre 
material (correcto en esta fase de apertura).
```

---

## Comparación: Con vs Sin Move Context

| Pregunta                   | Sin Context                         | Con Context             |
| -------------------------- | ----------------------------------- | ----------------------- |
| ¿Qué jugada era?           | ❌ Necesitas JOIN a tabla `features` | ✅ `move_san: "Nf3"`     |
| ¿Cómo reproducir posición? | ❌ Necesitas buscar FEN por separado | ✅ FEN incluido          |
| ¿Puedes usar con LLM?      | ⚠️ Difícil (solo números)            | ✅ Prompt directo        |
| ¿Human-readable?           | ❌ "Move 15" no dice nada            | ✅ "Nf3" es claro        |
| ¿Debugging?                | ❌ Varios pasos                      | ✅ Todo en una respuesta |

---

## 🚀 Próximos Pasos

1. **Aplicar migrations**: `alembic upgrade head`
2. **Regenerar SHAP** para partidas existentes
3. **Testear desde Postman** con iterator actualizado
4. **Implementar endpoint LLM** (opcional):
   ```
   POST /api/analysis/llm-explain
   Body: {
       "game_id": "...",
       "move_number": 15,
       "llm_provider": "openai"  // o "anthropic"
   }
   ```

---
_Documentado: 2026-02-28_
