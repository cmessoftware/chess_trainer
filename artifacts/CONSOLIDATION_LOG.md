# Consolidación de Carpetas Artifacts

**Fecha**: 2026-02-09 13:07:35
**Script**: consolidate_artifacts.py

## Problema Original
- Carpetas duplicadas: `/artifacts/` y `/ml/artifacts/`
- Conflictos de organización y mantenimiento

## Solución Implementada
- Consolidación en `/artifacts/` (raíz)
- Estructura organizada por categorías
- Preservación de contenido existente

## Estructura Final
```
artifacts/
├── ml_experiments/          # Experimentos ML organizados
├── phase1_baseline_mvp/     # Baseline del proyecto  
├── ml_legacy_experiments/   # Contenido movido desde /ml/artifacts/
├── survivorship_analysis/   # Reportes de survivorship bias
└── consolidated_reports/    # Reportes generales
```

## Comandos de Verificación
```bash
# Verificar estructura
ls -la artifacts/

# Verificar que /ml/artifacts/ ya no existe
ls -la ml/artifacts/  # Debería dar error o estar vacío
```

## Mantenimiento Futuro
- Usar solo `/artifacts/` para nuevos experimentos
- Categorizar por tipo: ml_experiments, survival_analysis, etc.
- Evitar creación de /ml/artifacts/ nuevamente
