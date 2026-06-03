# Gitea Issues · Phase 1 core-engine + minimal api

Este documento define un issue padre (epic) y 4 issues hijos relacionados para `01-FEAT-1..4`.

## Creacion automatica (script)

Script:

- `src/tools/create_gitea_issues_from_pack.py`

Variables de entorno requeridas:

- `GITEA_BASE_URL`
- `GITEA_TOKEN`
- `GITEA_OWNER`
- `GITEA_REPO`

Ejemplo dry-run:

`C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe src/tools/create_gitea_issues_from_pack.py --pack docs/ai_chess_coach/roadmap/issues/phase-01-core-engine-minimal-api-gitea-issues.json --dry-run`

Ejemplo creacion real + update roadmap:

`C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe src/tools/create_gitea_issues_from_pack.py --pack docs/ai_chess_coach/roadmap/issues/phase-01-core-engine-minimal-api-gitea-issues.json --roadmap docs/ai_chess_coach/roadmap/02-phase-01-core-engine-minimal-api.md`

## Parent Issue

### Key

`P1-EPIC-CORE-API`

### Title

`[PHASE-01][EPIC] Core-engine + minimal API baseline and closure`

### Labels

- `domain:core-engine`
- `domain:api`
- `type:feature`
- `priority:p1`
- `status:in-progress`
- `cross-cutting`

### Body

```markdown
## Goal

Consolidar y cerrar Phase 1 del roadmap (`core-engine + minimal api`) con trazabilidad entre baseline existente y pendientes.

## Scope

- FEAT-1: contratos PGN y API base
- FEAT-2: pipeline estable de analisis
- FEAT-3: validacion de entradas PGN
- FEAT-4: pruebas de endpoint base

## Metadata

- alias: APIV
- domain: core-engine/api
- phase: 01
- owner: TBD
- openspec_change: phase-01-core-engine-minimal-api-baseline

## Child Issues

- [ ] P1-CH-01 · FEAT-1 contratos PGN/API
- [ ] P1-CH-02 · FEAT-2 pipeline estable
- [ ] P1-CH-03 · FEAT-3 validacion PGN
- [ ] P1-CH-04 · FEAT-4 pruebas endpoint base
```

## Child Issues

### P1-CH-01

- **Title:** `[PHASE-01][FEAT-1] Formalizar contratos PGN y API base`
- **Labels:** `domain:api`, `domain:core-engine`, `type:feature`, `priority:p1`, `status:in-progress`
- **Parent:** `P1-EPIC-CORE-API`
- **Body:**

```markdown
## Objective

Definir modelos tipados para upload/import/status de PGN y respuestas de error estables.

## Baseline

- API base y endpoints PGN ya existen.
- Falta tipado dedicado en contratos PGN.

## Acceptance Criteria

- Modelos request/response/status PGN en schemas API.
- Endpoints PGN con response_model y errores consistentes.

## Metadata

- alias: APIV
- domain: api
- phase: 01
- owner: TBD
- parent: P1-EPIC-CORE-API
- openspec_change: phase-01-core-engine-minimal-api-baseline
```

### P1-CH-02

- **Title:** `[PHASE-01][FEAT-2] Definir pipeline minimo estable de analisis`
- **Labels:** `domain:core-engine`, `domain:orchestration`, `type:feature`, `priority:p1`, `status:blocked`
- **Parent:** `P1-EPIC-CORE-API`
- **Body:**

```markdown
## Objective

Definir y estabilizar el flujo minimo de analisis para Phase 1.

## Acceptance Criteria

- Flujo trazable entrada->analisis->salida estructurada.
- Criterios minimos de estabilidad documentados.

## Metadata

- alias: ORPL
- domain: core-engine/orchestration
- phase: 01
- owner: TBD
- parent: P1-EPIC-CORE-API
- openspec_change: phase-01-core-engine-minimal-api-baseline
```

### P1-CH-03

- **Title:** `[PHASE-01][FEAT-3] Endurecer validacion de entradas PGN`
- **Labels:** `domain:api`, `domain:data`, `type:feature`, `priority:p1`, `status:blocked`
- **Parent:** `P1-EPIC-CORE-API`
- **Body:**

```markdown
## Objective

Agregar validacion de contenido PGN mas alla de extension de archivo.

## Acceptance Criteria

- Validacion de headers/movimientos minimos.
- Manejo consistente de errores invalidos.

## Metadata

- alias: APIV
- domain: api/data
- phase: 01
- owner: TBD
- parent: P1-EPIC-CORE-API
- openspec_change: phase-01-core-engine-minimal-api-baseline
```

### P1-CH-04

- **Title:** `[PHASE-01][FEAT-4] Cubrir endpoints base con pruebas automatizadas`
- **Labels:** `domain:testing`, `domain:api`, `type:test`, `priority:p1`, `status:blocked`
- **Parent:** `P1-EPIC-CORE-API`
- **Body:**

```markdown
## Objective

Cubrir endpoints base de Phase 1 con tests de happy path y casos invalidos.

## Acceptance Criteria

- Tests para upload/import/status/preview base.
- Tests para errores de validacion.

## Metadata

- alias: APIV
- domain: testing/api
- phase: 01
- owner: TBD
- parent: P1-EPIC-CORE-API
- openspec_change: phase-01-core-engine-minimal-api-baseline
```
