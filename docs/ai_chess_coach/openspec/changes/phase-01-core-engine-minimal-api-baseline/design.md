# Design: phase-01-core-engine-minimal-api-baseline

## Intent

Formalizar la separacion entre:

- **estado existente** (implementacion actual verificable), y
- **estado objetivo** (pendientes necesarios para cerrar Phase 1).

## Feature Mapping

### 01-FEAT-1 · Diseñar contratos PGN y API base

Estado actual:

- API base montada y operativa.
- Endpoints PGN upload/import presentes.
- Falta contrato tipado explicito para respuestas de upload/import/status.

Estado objetivo:

- Modelos tipados para request/response de PGN.
- Convenciones de errores y campos estables para clientes API/UI.

### 01-FEAT-2 · Crear pipeline estable de analisis

Estado actual:

- Existen endpoints y servicios de analisis.
- Falta criterio minimo de estabilidad definido para Phase 1.

Estado objetivo:

- Workflow minimo trazable: entrada valida -> analisis base -> salida estructurada.
- Definicion de criterios de estabilidad y observabilidad minima.

### 01-FEAT-3 · Agregar validacion de entradas PGN

Estado actual:

- Validacion basica por extension de archivo.
- Preview PGN disponible.

Estado objetivo:

- Validacion de contenido PGN (headers/movimientos minimos/casos invalidos comunes).
- Respuestas de error consistentes para el consumidor.

### 01-FEAT-4 · Cubrir endpoint base con pruebas

Estado actual:

- Existen tests y app de prueba, sin cobertura objetivo de los flujos base de Phase 1.

Estado objetivo:

- Pruebas automatizadas para endpoints base de PGN/API.
- Casos felices y casos invalidos minimos.

## Architectural Notes

- Mantener enfoque Core + Extensions: contratos de dominio estables y adaptadores API/UI.
- Evitar contratos ad-hoc en responses de rutas criticas.
- Preparar el terreno para persistir jobs PGN fuera de memoria en una fase posterior.
