## 🛠️ Script de gestión de entorno DS + JupyterLab + MLflow

Este proyecto incluye un script **`ds_tool.ps1`** que permite configurar y lanzar un entorno de Data Science de forma automática.

### Características
- Instala **Mamba** si no está disponible.
- Crea (o usa) el entorno `ds` con Python, JupyterLab, MLflow y librerías básicas de DS.
- Opción **InfraSplit** para correr MLflow en un entorno separado (`infra-mlflow`).
- Lanza **JupyterLab** y **MLflow server** en puertos configurables.
- Modos opcionales para solo preparación, solo Jupyter o solo MLflow.

### Uso básico
```powershell
# Lanzar JupyterLab y MLflow en el mismo entorno
.\ds_tool.ps1

## Uso de parámetros opcionales.

# Solo preparar (no lanza servicios)
.\ds_tool.ps1 -SetupOnly

# Usar InfraSplit: MLflow en entorno separado
.\ds_tool.ps1 -InfraSplit

# Solo JupyterLab
.\ds_tool.ps1 -OnlyLab

# Solo MLflow
.\ds_tool.ps1 -OnlyMLflow

# Entorno minimal (ds con solo python+jlab+ipykernel)
.\ds_tool.ps1 -Minimal

# Puertos personalizados y abrir navegador
.\ds_tool.ps1 -JLabPort 8890 -MLflowPort 5050 -NoBrowser:$false
