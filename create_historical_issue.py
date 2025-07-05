#!/usr/bin/env python3
import subprocess
import json

def create_historical_issue():
    title = "Get features and training data in datasets"
    body = """✅ **COMPLETADO** - Issue histórico para referencia en tabla README.md

## 🎯 Implementación Exitosa

### Feature Generation
- ✅ `generate_features.py` en `src/pipeline/`
- ✅ Extracción automática de características de partidas
- ✅ Features tácticas, posicionales y temporales
- ✅ Tests en `tests/test_generate_features_pipeline.py`

### Dataset Export
- ✅ `export_dataset.py` en `src/pipeline/`
- ✅ Generación de datasets en formato Parquet
- ✅ Datasets compartidos entre containers Docker
- ✅ Pipeline automatizado completo

### Training Data Preparation
- ✅ Normalización y escalado de features
- ✅ División train/validation/test
- ✅ Almacenamiento en `datasets/` compartido
- ✅ Integración con MLflow para tracking

## 📁 Archivos Clave
- `src/pipeline/generate_features.py`
- `src/pipeline/export_dataset.py`
- `tests/test_generate_features_pipeline.py`
- `datasets/` - Datasets generados

## 📊 Features Implementadas
- Material advantage
- Piece activity
- King safety
- Pawn structure
- Tactical patterns
- Move accuracy
- Time pressure analysis

**Estado**: COMPLETADO ✅"""
    
    try:
        # Crear el issue
        result = subprocess.run([
            "gh", "issue", "create", 
            "--title", title,
            "--body", body
        ], capture_output=True, text=True, check=True)
        
        print("✅ Issue creado exitosamente")
        print(result.stdout)
        
        # Extraer número del issue
        if "/issues/" in result.stdout:
            issue_url = result.stdout.strip()
            issue_number = issue_url.split("/issues/")[-1]
            print(f"📊 Issue #{issue_number} creado")
            
            # Cerrar inmediatamente como completado
            close_result = subprocess.run([
                "gh", "issue", "close", issue_number,
                "--reason", "completed",
                "--comment", "🏆 Cerrando como completado - Tarea implementada exitosamente. Issue histórico para referencia en README.md"
            ], capture_output=True, text=True, check=True)
            
            print(f"✅ Issue #{issue_number} cerrado como completado")
            return issue_number, issue_url
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return None, None

if __name__ == "__main__":
    issue_number, issue_url = create_historical_issue()
    if issue_number:
        print(f"\n📋 Para actualizar README.md:")
        print(f"Issue #{issue_number}: {issue_url}")
    else:
        print("❌ No se pudo crear el issue")
