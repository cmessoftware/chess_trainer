#!/usr/bin/env python3
"""
Script para consolidar carpetas artifacts duplicadas en chess_trainer.

Este script resuelve el problema de tener:
- /artifacts/ (raíz)
- /ml/artifacts/ (dentro de ml/)

Consolida todo en /artifacts/ con estructura organizada.

Autor: Chess Trainer ML Pipeline  
Versión: 1.0.0
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import List, Dict
import datetime

def setup_logging():
    """Configurar logging básico."""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_project_root() -> Path:
    """Obtener el directorio raíz del proyecto."""
    current_dir = Path(__file__).resolve()
    
    # Buscar hacia arriba hasta encontrar docker-compose.yml o README.md
    for parent in current_dir.parents:
        if (parent / 'docker-compose.yml').exists() or (parent / 'README.md').exists():
            return parent
    
    raise FileNotFoundError("No se pudo encontrar el directorio raíz del proyecto")

def analyze_artifacts_structure(project_root: Path) -> Dict:
    """Analizar la estructura actual de carpetas artifacts."""
    logger = setup_logging()
    
    analysis = {
        'root_artifacts': project_root / 'artifacts',
        'ml_artifacts': project_root / 'ml' / 'artifacts',
        'root_exists': False,
        'ml_exists': False,
        'root_contents': [],
        'ml_contents': [],
        'conflicts': []
    }
    
    # Verificar artifacts en raíz
    if analysis['root_artifacts'].exists():
        analysis['root_exists'] = True
        analysis['root_contents'] = list(analysis['root_artifacts'].iterdir())
        logger.info(f"📁 /artifacts/ existe con {len(analysis['root_contents'])} elementos")
    
    # Verificar artifacts en ml/
    if analysis['ml_artifacts'].exists():
        analysis['ml_exists'] = True
        analysis['ml_contents'] = list(analysis['ml_artifacts'].iterdir())
        logger.info(f"📁 /ml/artifacts/ existe con {len(analysis['ml_contents'])} elementos")
    
    # Detectar conflictos de nombres
    if analysis['root_exists'] and analysis['ml_exists']:
        root_names = {item.name for item in analysis['root_contents'] if item.is_file()}
        ml_names = {item.name for item in analysis['ml_contents'] if item.is_file()}
        analysis['conflicts'] = list(root_names.intersection(ml_names))
        
        if analysis['conflicts']:
            logger.warning(f"⚠️ Conflictos detectados: {analysis['conflicts']}")
    
    return analysis

def create_consolidated_structure(target_dir: Path) -> None:
    """Crear estructura consolidada recomendada."""
    logger = setup_logging()
    
    # Estructura de directorios recomendada
    subdirs = [
        'ml_experiments',
        'phase1_baseline_mvp', 
        'ml_legacy_experiments',
        'survivorship_analysis',
        'consolidated_reports'
    ]
    
    for subdir in subdirs:
        subdir_path = target_dir / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Creado: {subdir_path}")

def move_files_safely(source_files: List[Path], target_dir: Path, 
                     source_name: str) -> None:
    """Mover archivos de manera segura evitando conflictos."""
    logger = setup_logging()
    
    moved_count = 0
    for file_path in source_files:
        if file_path.is_file():
            target_path = target_dir / file_path.name
            
            # Evitar sobrescribir
            if target_path.exists():
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                target_path = target_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
                logger.warning(f"⚠️ Renombrado para evitar conflicto: {target_path.name}")
            
            shutil.move(str(file_path), str(target_path))
            logger.info(f"📦 Movido: {file_path.name} → {target_path}")
            moved_count += 1
        
        elif file_path.is_dir():
            # Para directorios, mover todo el contenido
            target_subdir = target_dir / file_path.name
            if target_subdir.exists():
                # Si existe, mover contenido individualmente
                for item in file_path.iterdir():
                    if item.is_file():
                        target_file = target_subdir / item.name
                        if target_file.exists():
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            target_file = target_subdir / f"{item.stem}_{timestamp}{item.suffix}"
                        shutil.move(str(item), str(target_file))
                        moved_count += 1
                # Eliminar directorio vacío
                if not any(file_path.iterdir()):
                    file_path.rmdir()
            else:
                shutil.move(str(file_path), str(target_subdir))
                moved_count += 1
                logger.info(f"📁 Movido directorio: {file_path.name} → {target_subdir}")
    
    logger.info(f"📊 {source_name}: {moved_count} elementos movidos")

def consolidate_artifacts(project_root: Path, dry_run: bool = False) -> None:
    """Consolidar todas las carpetas artifacts en una sola ubicación."""
    logger = setup_logging()
    
    logger.info("🚀 Iniciando consolidación de carpetas artifacts...")
    
    # Analizar estructura actual
    analysis = analyze_artifacts_structure(project_root)
    
    if not analysis['root_exists'] and not analysis['ml_exists']:
        logger.info("ℹ️ No se encontraron carpetas artifacts para consolidar")
        return
    
    # Decidir directorio target (preferir raíz)
    target_artifacts = analysis['root_artifacts']
    
    if dry_run:
        logger.info("🔍 MODO DRY-RUN - No se realizarán cambios reales")
        logger.info(f"Target: {target_artifacts}")
        if analysis['ml_exists']:
            logger.info(f"Se moverían {len(analysis['ml_contents'])} elementos desde /ml/artifacts/")
        return
    
    # Crear estructura consolidada
    target_artifacts.mkdir(exist_ok=True)
    create_consolidated_structure(target_artifacts)
    
    # Consolidar desde ml/artifacts/ si existe
    if analysis['ml_exists'] and analysis['ml_contents']:
        legacy_dir = target_artifacts / 'ml_legacy_experiments'
        legacy_dir.mkdir(exist_ok=True)
        
        logger.info("📦 Consolidando desde /ml/artifacts/...")
        move_files_safely(analysis['ml_contents'], legacy_dir, "ML Legacy")
        
        # Eliminar directorio vacío
        if not any(analysis['ml_artifacts'].iterdir()):
            analysis['ml_artifacts'].rmdir()
            logger.info("🗑️ Eliminado /ml/artifacts/ (vacío)")
    
    # Crear archivo de documentación
    create_consolidation_documentation(target_artifacts)
    
    logger.info("✅ Consolidación completada exitosamente!")
    logger.info(f"📍 Artifacts consolidados en: {target_artifacts}")

def create_consolidation_documentation(artifacts_dir: Path) -> None:
    """Crear documentación de la consolidación."""
    doc_file = artifacts_dir / 'CONSOLIDATION_LOG.md'
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"""# Consolidación de Carpetas Artifacts

**Fecha**: {timestamp}
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
"""

    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Consolidar carpetas artifacts duplicadas"
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help="Solo mostrar lo que se haría sin realizar cambios"
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        help="Directorio raíz del proyecto (auto-detectado por defecto)"
    )
    
    args = parser.parse_args()
    
    try:
        project_root = args.project_root or get_project_root()
        consolidate_artifacts(project_root, dry_run=args.dry_run)
        
    except Exception as e:
        logger = setup_logging()
        logger.error(f"❌ Error durante la consolidación: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())