# Chess Trainer AI Coach - Render Deployment Guide

Guía completa para desplegar chess_trainer con AI Coach (Ollama + LLM) en Render.

---

## 📋 Requisitos Previos

### 1. Cuenta en Render
- Crear cuenta en [render.com](https://render.com)
- Tarjeta de crédito (para planes pagos)

### 2. Recursos Necesarios

| Componente        | Plan Render | RAM   | Disco | Costo/mes      |
| ----------------- | ----------- | ----- | ----- | -------------- |
| PostgreSQL        | Standard    | -     | 10GB  | $7             |
| App + AI Coach    | Pro         | 8GB   | 10GB  | $85            |
| MLflow (opcional) | Starter     | 512MB | 5GB   | $7             |
| **TOTAL**         | -           | -     | -     | **$92-99/mes** |

⚠️ **IMPORTANTE**: El modelo LLM requiere mínimo **8GB RAM** (Plan Pro)

---

## 🚀 Opción 1: Deployment con Blueprint (Recomendado)

### Paso 1: Preparar Repositorio

```bash
# Commit todos los archivos de deployment
git add dockerfile.render render.yaml deployment/
git commit -m "Add Render deployment configuration"
git push origin main
```

### Paso 2: Deploy desde Render Dashboard

1. **Login** en [dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. **Connect repository**: `chess_trainer`
4. **Select branch**: `main`
5. **Review** configuración en `render.yaml`
6. Click **"Apply"**

Render creará automáticamente:
- ✅ PostgreSQL database
- ✅ Web service (App + Ollama)
- ✅ MLflow service (opcional)

### Paso 3: Configurar Variables de Entorno

En el Dashboard de cada service:

**chess-trainer-ai-coach:**
```
OLLAMA_MODEL=llama3.1:8b
WORKERS=2
PORT=8000
PYTHONUNBUFFERED=1
```

**chess-trainer-db:**
```
POSTGRES_DB=chess_trainer
POSTGRES_USER=admin
POSTGRES_PASSWORD=[auto-generated]
```

### Paso 4: Primera Descarga del Modelo

⚠️ **Primera vez toma 15-30 minutos** descargando el modelo LLM.

Monitorear logs:
```
Dashboard → chess-trainer-ai-coach → Logs
```

Verás:
```
📥 Downloading model: llama3.1:8b (this may take a while on first deploy)...
✅ Model downloaded successfully
🌐 Starting Chess Trainer API...
```

---

## 🚀 Opción 2: Deployment Manual

### Paso 1: Crear PostgreSQL Database

```bash
# En Render Dashboard
New + → PostgreSQL
- Name: chess-trainer-db
- Database: chess_trainer
- Plan: Standard ($7/mo)
```

Guardar el `Internal Database URL`.

### Paso 2: Crear Web Service

```bash
# En Render Dashboard
New + → Web Service
- Repository: chess_trainer
- Branch: main
- Build Command: (empty)
- Start Command: /app/startup.sh
- Docker: dockerfile.render
- Plan: Pro (8GB RAM)
```

### Paso 3: Configurar Environment Variables

```bash
CHESS_TRAINER_DB_URL=[Internal Database URL from Step 1]
OLLAMA_MODEL=llama3.1:8b
WORKERS=2
PORT=8000
```

### Paso 4: Configurar Persistent Disk

```bash
# En Service Settings
Disks → Add Disk
- Name: ollama-models
- Mount Path: /app/models
- Size: 10GB
```

---

## 📊 Monitoring y Health Checks

### Health Check Endpoint

Render verificará automáticamente: `https://your-app.onrender.com/health`

Crear endpoint en `src/api/main.py`:

```python
@app.get("/health")
async def health_check():
    """Health check for Render"""
    try:
        # Check Ollama
        response = httpx.get("http://localhost:11434")
        ollama_ok = response.status_code == 200
        
        # Check Database
        db = next(get_db())
        db.execute("SELECT 1")
        db_ok = True
    except:
        db_ok = False
    
    return {
        "status": "healthy" if (ollama_ok and db_ok) else "degraded",
        "ollama": "ok" if ollama_ok else "error",
        "database": "ok" if db_ok else "error",
        "timestamp": datetime.now().isoformat()
    }
```

### Logs

```bash
# Ver logs en tiempo real
render logs chess-trainer-ai-coach --tail 100
```

---

## 💰 Optimización de Costos

### Opción: Usar Modelo Más Pequeño

Para reducir costos, usar `llama3.2:3b` requiere solo **4GB RAM** (Plan Starter - $25/mes):

```bash
# En Environment Variables
OLLAMA_MODEL=llama3.2:3b

# Total cost con plan Starter:
# - PostgreSQL Standard: $7/mo
# - App Starter (4GB): $25/mo
# TOTAL: $32/mo (vs $92/mo)
```

**Trade-off**: Menor calidad en reportes de coaching.

### Opción: Deploy Ollama en Servicio Separado

```yaml
# render.yaml - Split services
services:
  - name: chess-trainer-api
    plan: starter  # $7/mo
    
  - name: chess-trainer-ollama
    plan: pro  # $85/mo (solo este necesita 8GB)
    env:
      - OLLAMA_HOST=0.0.0.0:11434
```

---

## 🔧 Troubleshooting

### Error: "Out of Memory"

```bash
# Síntoma: Service crashes durante inference
# Solución: Upgrade a plan con más RAM

Plan Pro Plus (16GB): $150/mo
```

### Error: "Model download timeout"

```bash
# Síntoma: Deployment falla al descargar modelo
# Solución 1: Pre-build Docker image con modelo incluido
docker build -f dockerfile.render -t chess-trainer-ai .
docker push your-registry/chess-trainer-ai

# Solución 2: Aumentar timeout en render.yaml
services:
  - type: web
    healthCheckPath: /health
    healthCheckInterval: 300000  # 5 minutes
```

### Modelo No Se Descarga

```bash
# Verificar en logs
render logs chess-trainer-ai-coach

# Si falla, descargar manualmente via Render Shell
render shell chess-trainer-ai-coach
ollama pull llama3.1:8b
```

---

## 🔐 Seguridad

### Variables Sensibles

```bash
# NO commitear en .env o código
# Usar Render Secret Files o Environment Variables

# En Render Dashboard → Environment
SECRET_KEY=[generate secure key]
POSTGRES_PASSWORD=[auto-generated]
JWT_SECRET=[generate secure key]
```

### Firewall

```yaml
# render.yaml
databases:
  - name: chess-trainer-db
    ipAllowList:
      - 192.168.1.0/24  # Solo tu red
```

---

## 📈 Escalabilidad

### Horizontal Scaling

```bash
# Aumentar workers FastAPI
WORKERS=4  # Para más requests concurrentes
```

### Vertical Scaling

```bash
# Upgrade plan para modelo más grande
Plan: Pro Plus (16GB RAM)
Model: llama3.1:70b  # Mejor calidad
```

---

## 🧪 Testing Deployment

### Comandos de Verificación

```bash
# 1. Check API
curl https://your-app.onrender.com/health

# 2. Check Ollama
curl https://your-app.onrender.com/api/ollama/version

# 3. Test AI Coach
curl -X POST https://your-app.onrender.com/ai-coach/analyze-game/123

# 4. Check logs
render logs chess-trainer-ai-coach --tail 50
```

---

## 📚 URLs de Acceso

Después del deployment:

```
API: https://chess-trainer-ai-coach.onrender.com
MLflow UI: https://chess-trainer-mlflow.onrender.com
PostgreSQL: [Internal URL only]
```

---

## 🔄 CI/CD Automático

Render auto-deploya en cada push a `main`:

```bash
# Push código
git push origin main

# Render automáticamente:
# 1. Build Docker image
# 2. Deploy nuevo container
# 3. Run health checks
# 4. Switch traffic
```

---

## 📝 Checklist de Deployment

- [ ] Crear cuenta en Render
- [ ] Preparar tarjeta de crédito
- [ ] Push código a GitHub
- [ ] Crear PostgreSQL database
- [ ] Crear Web Service (Plan Pro mínimo)
- [ ] Configurar Environment Variables
- [ ] Configurar Persistent Disk (10GB)
- [ ] Esperar descarga de modelo (~15-30min primera vez)
- [ ] Verificar health check: `/health`
- [ ] Probar API: `/ai-coach/analyze-game/{id}`
- [ ] Monitorear logs y métricas
- [ ] Configurar custom domain (opcional)

---

## 💡 Alternativas a Render

Si el costo es muy alto:

### Railway.app
- Pros: Similar a Render, pricing por uso
- Cons: Sin GPU, similar costo para 8GB RAM

### Fly.io
- Pros: GPU disponible, mejor para LLMs
- Cons: Más complejo de configurar

### AWS EC2 + ECS
- Pros: Más control, GPU opciones
- Cons: Requiere más setup manual

### Self-hosted (Linode/DigitalOcean)
- Pros: Menor costo (~$40/mo para 8GB)
- Cons: Mantenimiento manual

---

## 🎯 Recomendación Final

**Para Producción:**
```
Modelo: llama3.1:8b
Plan: Pro (8GB RAM)
Costo: ~$92/mo
```

**Para Desarrollo/Testing:**
```
Modelo: llama3.2:3b
Plan: Starter (4GB RAM)
Costo: ~$32/mo
```

**Para Budget Mínimo:**
```
Deploy sin Ollama en Render
Usar Ollama en máquina local
API calls via ngrok/tunneling
Costo: ~$14/mo (solo DB + API)
```

---

**Última actualización:** 2026-03-13  
**Soporte:** Ver logs en Render Dashboard
