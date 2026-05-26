# Integración del módulo Survivorship Bias en chess_trainer

## Contexto general
Este proyecto (`chess_trainer`) ya cuenta con:
- datasets de partidas (features por jugada y metadata por partida),
- modelos ML para clasificar errores (`error_label`, `error_level`),
- recomendadores tácticos y de entrenamiento,
- arquitectura por capas (analysis / training / recommender / api / ui).

Se requiere integrar un nuevo módulo llamado **Survivorship Bias Analyzer**.

Este módulo NO entrena modelos ML.
Su función es **detectar errores catastróficos ignorados por el dataset** (sesgo de supervivencia), priorizar entrenamiento y actuar como *gatekeeper* antes del uso de ML.

---  

## Objetivo del módulo
Detectar y reportar:
- derrotas tempranas (≤ 15 jugadas),
- mates en 1 y mates en 2,
- colapsos en la apertura,
- aperturas con baja tasa de supervivencia,
- posiciones/jugadas ausentes porque la partida terminó antes.

El módulo debe devolver un **reporte estructurado (JSON)** consumible por:
- API,
- UI,
- training_recommender,
- sanity checks del pipeline ML.

---

## Ubicación del código
Crear el archivo:

chess_trainer/analysis/survivorship_bias.py

yaml
Copiar código

No debe ir en `training/` ni en `recommender/`.

---

## Input esperado
El módulo trabaja con:
- `features_df`: DataFrame con una fila por jugada  
  (game_id, ply, score_cp, mate_in, error_label, tags, etc.)
- `metadata_df`: DataFrame con una fila por partida  
  (game_id, result, opening, ply_count, elo, etc.)

---

## Funcionalidades mínimas requeridas

### 1. Detectar derrotas tempranas
Una partida es derrota temprana si:
- result == derrota del usuario
- ply_count ≤ 30
- o min(score_cp) ≤ -300 en plies tempranos
- o mate_in < 0 detectado antes del ply 20

Debe devolver una lista con:
- game_id
- opening
- ply_count
- min_eval_cp
- mate_in (si aplica)
- fatal_reason (ej: mate_in_1, early_collapse)

---

### 2. Calcular tasa de supervivencia por apertura
Para cada apertura:
- total_games
- early_deaths
- survival_rate (partidas que llegan al menos a ply 40)

---

### 3. Detectar posiciones ausentes
Para cada partida:
- identificar plies esperados (ej: 1–40)
- listar los plies que no existen en features
- esto representa zonas críticas nunca alcanzadas

---

### 4. Detectar patrones graves
Contar y resumir:
- mates en 1
- mates en 2
- error_label == "blunder" en derrotas tempranas
- tags tácticos frecuentes (si existen)

---

### 5. Generar reporte JSON
Implementar un método tipo:

```python
generate_report() -> dict
Con estructura:

json
Copiar código
{
  "summary": {
    "total_games": int,
    "early_losses": int,
    "early_loss_rate": float,
    "mate_in_1_count": int,
    "mate_in_2_count": int,
    "worst_phase": "opening"
  },
  "critical_losses": [],
  "opening_survival": [],
  "patterns": {
    "tactical": [],
    "error_labels": []
  }
}
Lógica de priorización
Implementar función:

python
Copiar código
compute_priority(report) -> str
Reglas:

Si mate_in_1_count > 0 → "CRITICAL"

Si early_loss_rate > 0.15 → "HIGH"

Caso contrario → "NORMAL"

Esta prioridad se usa como gate antes del ML.

Integración con API
Agregar endpoint:

bash
Copiar código
GET /analysis/survivorship
Que:

cargue datos del usuario,

ejecute el analyzer,

calcule priority_level,

devuelva el JSON completo.

Integración con recommender
En training_recommender:

Si priority == "CRITICAL":

devolver plan de emergencia (mates, defensa básica, aperturas)

Si priority == "HIGH":

priorizar táctica defensiva y apertura

Si priority == "NORMAL":

usar modelos ML existentes

Errores catastróficos pisan al ML.

Tests requeridos
Agregar tests que validen:

detección de mate en 1

prioridad CRITICAL bloquea entrenamiento ML

datasets con muchas derrotas tempranas no pasan como NORMAL

Consideraciones finales
Este módulo es diagnóstico y preventivo.

No optimizar para performance, sino claridad y robustez.

Pensar este módulo como un "lint" del dataset y del entrenamiento.

Documentar brevemente en README.md y actualizar ROADMAP_TECHNICAL con este propósito.

Fin de instrucciones.