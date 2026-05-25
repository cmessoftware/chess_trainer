# Chess Trainer - Pages Architecture Analysis and Recommendations

## Summary
The repository is currently in a **migration phase**: the active UI is still Streamlit, while the target architecture is a dedicated **React + Vite frontend** consuming backend APIs.

## Current State

### What exists today
- `src/app.py` is still the main UI entrypoint and uses Streamlit page navigation.
- `/src/pages/` still contains the legacy Python UI pages.
- `src/architecture.md` still describes Streamlit pages connected close to the data layer.
- Docker still exposes the main application on port `8501`, which aligns with the current Streamlit runtime.
- The repository documents React as the target presentation layer, but the reviewed snapshot does **not** yet show a clearly established Vite frontend structure.

### Legacy UI inventory
#### Game data
- `upload_pgn.py`
- `tag_games _ui.py`

#### Analysis and prediction
- `analyze_feedback.py`
- `prediction_history.py`
- `predictor_error_label.py`

#### Training and tactical
- `tactics.py`
- `tactics_viewer.py`
- `elite_training.py`
- `streamlit_tacticals_viewer.py`

#### Exploration and study
- `elite_explorer.py`
- `elite_stats.py`
- `streamlit_eda.py`
- `summary_viewer.py`
- `streamlit_study_viewer.py`

## Short Issue List

### High priority
1. **Incomplete frontend migration**  
   Streamlit is still the active UI entrypoint while React + Vite is the target architecture.

2. **Docs and runtime are inconsistent**  
   Some docs describe React as current, but the executable UI still runs through Streamlit.

3. **No single frontend boundary**  
   The repository still mixes “current UI” and “future UI” concepts without a formal migration boundary.

4. **Legacy page duplication remains**  
   Tactical, analysis, and exploration features are spread across overlapping pages.

5. **API contracts for React are not documented enough**  
   The frontend target is defined conceptually, but not yet as a concrete contract table.

6. **Frontend testing strategy is missing**  
   There is no explicit testing plan for React routes, hooks, components, and API integration.

### Medium priority
1. **Outdated architecture diagrams**  
   `src/architecture.md` still describes Streamlit-centered flow.

2. **Naming inconsistencies**  
   Example: `tag_games _ui.py` contains a space in the filename.

3. **Deployment semantics still reflect Streamlit**  
   Port `8501` and current container assumptions should be reviewed during migration.

4. **Feature ownership is unclear**  
   It is not yet explicit which legacy pages map to which React routes.

## Target Architecture

```text
⚛️ React + Vite Frontend
    ↓ HTTP / REST
🪝 Frontend Hooks + API Client Layer
    ↓
🔧 Backend Service Layer
    ↓
🗄️ Repository Layer
    ↓
💾 PostgreSQL + Files + ML artifacts
```

### Rule
The frontend must **never** access repositories, raw files, CSVs, or database connections directly.
It should only consume backend APIs.

## Legacy-to-React Route Mapping

| Legacy page(s) | Target React route/page |
|---|---|
| `upload_pgn.py` | `UploadPGNPage.tsx` |
| `tag_games _ui.py` | `TagGamesPage.tsx` |
| `analyze_feedback.py`, `prediction_history.py`, `predictor_error_label.py` | `AnalysisDashboardPage.tsx` |
| `tactics.py`, `tactics_viewer.py`, `elite_training.py`, `streamlit_tacticals_viewer.py` | `TacticalTrainingPage.tsx` |
| `elite_explorer.py`, `elite_stats.py`, `streamlit_eda.py`, `summary_viewer.py` | `DataExplorerPage.tsx` |
| `streamlit_study_viewer.py` | `StudyViewerPage.tsx` |

## Recommended API Endpoint Table

### 1. Upload / Import
Used by: `UploadPGNPage.tsx`

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/games/uploads` | Upload one or more PGN files |
| `GET` | `/api/games/uploads` | List upload jobs / uploaded files |
| `GET` | `/api/games` | List imported games |
| `GET` | `/api/games/{game_id}` | Get game details |
| `DELETE` | `/api/games/{game_id}` | Remove an imported game if supported |

#### Suggested request/response
- `POST /api/games/uploads`
  - request: multipart form-data with one or more PGN files
  - response:
```json
{
  "upload_id": "upl_123",
  "files_received": 2,
  "games_imported": 48,
  "warnings": []
}
```

### 2. Game Tagging
Used by: `TagGamesPage.tsx`

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/games` | Search/filter games |
| `GET` | `/api/games/{game_id}/tags` | Get current tags |
| `PUT` | `/api/games/{game_id}/tags` | Replace tags for a game |
| `PATCH` | `/api/games/{game_id}` | Update metadata fields |
| `POST` | `/api/games/bulk-tags` | Apply tags in bulk |

#### Suggested response
```json
{
  "game_id": 101,
  "tags": ["sicilian", "blitz", "needs-review"],
  "updated_at": "2026-05-17T04:00:00Z"
}
```

### 3. Analysis Dashboard
Used by: `AnalysisDashboardPage.tsx`

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/analysis/jobs` | Start a game analysis job |
| `GET` | `/api/analysis/jobs/{job_id}` | Get analysis job status |
| `GET` | `/api/analysis/games/{game_id}` | Get completed analysis result |
| `GET` | `/api/analysis/games/{game_id}/summary` | Get summary metrics |
| `GET` | `/api/analysis/games/{game_id}/critical-moments` | Get critical positions/moments |

#### Suggested async job response
```json
{
  "job_id": "an_456",
  "status": "queued",
  "game_id": 101
}
```

#### Suggested completed result shape
```json
{
  "game_id": 101,
  "status": "completed",
  "summary": {
    "accuracy": 78.4,
    "blunders": 1,
    "mistakes": 3,
    "inaccuracies": 5
  },
  "critical_moments": [
    {
      "ply": 24,
      "fen": "...",
      "label": "blunder",
      "score_diff": 210
    }
  ]
}
```

### 4. Prediction
Used by: `AnalysisDashboardPage.tsx`

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/predictions/error-label` | Predict error label from feature input |
| `GET` | `/api/predictions/history` | Retrieve prediction history |
| `GET` | `/api/predictions/history/{prediction_id}` | Get prediction details |

#### Suggested prediction response
```json
{
  "prediction_id": "pred_999",
  "predicted_label": "mistake",
  "confidence": 0.82,
  "inputs": {
    "score_diff": 96,
    "mate_in": null
  }
}
```

### 5. Tactical Training
Used by: `TacticalTrainingPage.tsx`

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/tactics/sessions/next` | Get next tactical exercise |
| `POST` | `/api/tactics/sessions` | Start a training session |
| `POST` | `/api/tactics/sessions/{session_id}/moves` | Submit a move/answer |
| `GET` | `/api/tactics/sessions/{session_id}` | Get current session state |
| `GET` | `/api/tactics/progress` | Get training progress and stats |

#### Suggested exercise response
```json
{
  "session_id": "sess_321",
  "exercise_id": 77,
  "fen": "...",
  "side_to_move": "white",
  "theme": "fork",
  "difficulty": "medium"
}
```

### 6. Data Explorer / Stats / EDA
Used by: `DataExplorerPage.tsx`

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/exploration/summary` | Dataset summary metrics |
| `GET` | `/api/exploration/elite-games` | Query elite games |
| `GET` | `/api/exploration/stats` | Aggregate stats |
| `GET` | `/api/exploration/charts` | Chart-ready data |
| `GET` | `/api/exploration/filters` | Available filter metadata |

#### Suggested summary response
```json
{
  "games_total": 12500,
  "players_total": 3100,
  "openings_top": [
    {"name": "Sicilian Defense", "count": 1200}
  ]
}
```

### 7. Study Viewer
Used by: `StudyViewerPage.tsx`

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/studies` | List studies |
| `GET` | `/api/studies/{study_id}` | Get study details |
| `GET` | `/api/studies/{study_id}/chapters` | List chapters |
| `GET` | `/api/studies/{study_id}/chapters/{chapter_id}` | Get chapter content |

## Recommended Frontend Structure

```text
frontend/
  src/
    pages/
      UploadPGNPage.tsx
      TagGamesPage.tsx
      AnalysisDashboardPage.tsx
      TacticalTrainingPage.tsx
      DataExplorerPage.tsx
      StudyViewerPage.tsx
    components/
      FileUploader.tsx
      GameViewer.tsx
      StatisticsChart.tsx
      ProgressTracker.tsx
      ErrorState.tsx
      LoadingState.tsx
    hooks/
      useGames.ts
      useAnalysis.ts
      usePredictions.ts
      useTactics.ts
      useExploration.ts
    services/
      apiClient.ts
      gameApi.ts
      analysisApi.ts
      predictionApi.ts
      tacticalApi.ts
      explorationApi.ts
      studyApi.ts
    types/
      game.ts
      analysis.ts
      prediction.ts
      tactic.ts
      study.ts
```

## Minimal Checklist
- [ ] Keep this document aligned with migration reality
- [ ] Define the actual API contract before continuing UI migration
- [ ] Map every legacy page to one React route
- [ ] Implement React route navigation
- [ ] Add frontend test coverage
- [ ] Decommission Streamlit pages after feature parity

## Next Recommendation
Start with:
1. `UploadPGNPage.tsx`
2. `AnalysisDashboardPage.tsx`
3. `TacticalTrainingPage.tsx`

These provide the clearest value while collapsing the most legacy duplication.
