# Spec: phase-01-core-engine-minimal-api

## Requirement: API base must be available for Phase 1

La aplicacion debe exponer una API base operativa para los dominios minimos de Phase 1.

### Scenario: API base initialized

- **Given** el servicio FastAPI esta levantado
- **When** el cliente consulta endpoints base de salud/documentacion
- **Then** la API responde de forma consistente y enruta modulos principales

## Requirement: PGN import flow must expose stable contracts

El flujo de PGN upload/import debe tener contratos estables para clientes.

### Scenario: Upload and batch import contract

- **Given** un cliente sube un archivo PGN valido
- **When** invoca upload e import batch
- **Then** recibe respuestas con campos estables para `jobId`, estado y metadatos

### Scenario: Invalid file contract

- **Given** un archivo con extension o contenido invalido
- **When** se invoca upload/import
- **Then** la API responde error estructurado y accionable

## Requirement: Minimal analysis pipeline must be defined and stable

Phase 1 debe definir un pipeline de analisis minimo con entrada/salida trazables.

### Scenario: Valid input executes minimal analysis

- **Given** una entrada valida para analisis
- **When** se ejecuta el flujo minimo
- **Then** se obtiene una salida estructurada consistente

## Requirement: Base endpoints must be covered by automated tests

Los endpoints base de Phase 1 deben contar con pruebas de humo y validacion.

### Scenario: Happy path and invalid path covered

- **Given** la suite de pruebas de API
- **When** se ejecuta sobre endpoints base de PGN/API
- **Then** valida casos exitosos e invalidos minimos para Phase 1
