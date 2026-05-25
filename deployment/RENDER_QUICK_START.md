# 🚀 Deployment en Render - Quick Start

Guía rápida para desplegar chess_trainer + AI Coach + Ollama en Render.

---

## 📋 **LO QUE NECESITAS SABER**

### Costos Mensuales

| Configuración                | Plan              | Costo       |
| ---------------------------- | ----------------- | ----------- |
| **Producción (Recomendado)** | Pro (8GB RAM)     | **$92/mes** |
| **Development/Testing**      | Starter (4GB RAM) | **$32/mes** |
| **Budget Mínimo**            | Sin Ollama        | **$14/mes** |

### Por Qué Estos Costos?

- **Modelo LLM** `llama3.1:8b` requiere **8GB RAM mínimo**
- **PostgreSQL** necesita storage persistente
- **Ollama** + **FastAPI** + **Base de datos** en un solo servicio

---

## ⚡ **DEPLOYMENT EN 5 PASOS**

### **Paso 1: Commit Archivos de Deployment**

```bash
# Verifica que estos archivos existan:
ls dockerfile.render
ls render.yaml
ls deployment/render_startup.sh

# Commit y push
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### **Paso 2: Crear Cuenta en Render**

1. Ir a [render.com](https://render.com)
2. Sign up con GitHub
3. Conectar repositorio `chess_trainer`

### **Paso 3: Deploy con Blueprint**

```bash
# Opción A: Desde Dashboard
1. Click "New +" → "Blueprint"
2. Select repository: chess_trainer
3. Select branch: main
4. Review render.yaml
5. Click "Apply"

# Opción B: Desde CLI
render deploy --blueprint render.yaml
```

### **Paso 4: Esperar Primera Descarga (15-30 min)**

```bash
# Monitorear logs
render logs chess-trainer-ai-coach --tail 100

# Verás:
📥 Downloading model: llama3.1:8b (this may take a while)...
✅ Model downloaded successfully
🌐 Starting Chess Trainer API...
```

### **Paso 5: Verificar Deployment**

```bash
# Check health
curl https://chess-trainer-ai-coach.onrender.com/health

# Respuesta esperada:
{
  "status": "healthy",
  "checks": {
    "api": "ok",
    "database": "ok",
    "ollama": "ok"
  }
}
```

---

## 🎛️ **CONFIGURACIONES ALTERNATIVAS**

### Opción 1: Modelo Más Pequeño (Menor Costo)

```yaml
# En render.yaml, cambiar:
services:
  - name: chess-trainer-ai-coach
    plan: starter  # 4GB RAM ($25/mo)
    envVars:
      - key: OLLAMA_MODEL
        value: llama3.2:3b  # Modelo más pequeño
```

**Total**: $32/mo (vs $92/mo)  
**Trade-off**: Menor calidad en reportes

### Opción 2: Sin Ollama en Render (Mínimo Costo)

```bash
# Deploy solo API + Database
# Ollama corre en tu máquina local
# Conectas via ngrok/tunneling

Total: $14/mo
```

---

## 📊 **COMPARACIÓN DE PLANES**

| Plan         | RAM   | CPU | Disco | Costo/mes | Modelo Soportado |
| ------------ | ----- | --- | ----- | --------- | ---------------- |
| Starter      | 512MB | 0.5 | -     | $7        | ❌ No LLM         |
| Standard     | 2GB   | 1   | -     | $25       | ❌ Muy pequeño    |
| Starter Plus | 4GB   | 1   | -     | $25       | ✅ llama3.2:3b    |
| Pro          | 8GB   | 2   | -     | $85       | ✅ llama3.1:8b ⭐  |
| Pro Plus     | 16GB  | 4   | -     | $150      | ✅ llama3.1:70b   |

---

## 🔍 **MONITOREO Y LOGS**

### Ver Logs en Tiempo Real

```bash
# CLI
render logs chess-trainer-ai-coach --tail 100 --follow

# O en Dashboard
https://dashboard.render.com → Service → Logs
```

### Métricas

```bash
Dashboard → Service → Metrics

- CPU Usage
- Memory Usage
- Request Rate
- Response Time
```

---

## 🚨 **TROUBLESHOOTING COMÚN**

### ❌ Error: "Out of Memory"

```bash
# Síntoma: Service crashes durante inference
# Solución: Upgrade a plan superior

render services:scale chess-trainer-ai-coach --plan pro-plus
```

### ❌ Error: "Model download timeout"

```bash
# Síntoma: Build excede 15 minutos
# Solución: Pre-build imagen con modelo

# Crear imagen con modelo pre-instalado
docker build -f dockerfile.render -t chess-trainer-ai .
docker push your-registry/chess-trainer-ai

# Luego usar en render.yaml:
image:
  url: your-registry/chess-trainer-ai:latest
```

### ❌ Error: "Database connection failed"

```bash
# Verificar CHESS_TRAINER_DB_URL
render env:get chess-trainer-ai-coach CHESS_TRAINER_DB_URL

# Debe ser: postgresql://user:pass@host:5432/chess_trainer
```

---

## 📚 **ARCHIVOS CREADOS**

```
chess_trainer/
├── dockerfile.render                      # Dockerfile para Render
├── render.yaml                            # Blueprint de configuración
└── deployment/
    ├── render_startup.sh                  # Script de inicio
    ├── render_build.sh                    # Script de build
    ├── render_deployment_guide.md         # Guía completa
    ├── RENDER_QUICK_START.md             # Este archivo
    └── README.md                          # Overview
```

---

## 🎯 **RECOMENDACIONES**

### Para Empezar

1. **Usa Plan Starter Plus** ($32/mo) con `llama3.2:3b`
2. **Prueba la funcionalidad** durante 1 semana
3. **Upgrade a Pro** cuando necesites mejor calidad

### Para Producción

1. **Usa Plan Pro** ($92/mo) con `llama3.1:8b`
2. **Configura custom domain**
3. **Activa auto-scaling** si esperas tráfico variable
4. **Configura alertas** de uptime

### Para Reducir Costos

1. **Opción A**: Self-host Ollama en servidor dedicado (~$40/mo)
2. **Opción B**: Usa API externa (OpenAI, Anthropic) en lugar de Ollama
3. **Opción C**: Deploy en Railway/Fly.io (ligeramente más barato)

---

## 🔗 **LINKS ÚTILES**

- **Render Dashboard**: https://dashboard.render.com
- **Guía Completa**: [deployment/render_deployment_guide.md](deployment/render_deployment_guide.md)
- **Render Docs**: https://render.com/docs
- **Pricing**: https://render.com/pricing

---

## ✅ **CHECKLIST DE DEPLOYMENT**

```
Antes del Deploy:
[ ] Cuenta en Render creada
[ ] Tarjeta de crédito agregada
[ ] Repositorio en GitHub
[ ] Archivos de deployment commiteados

Durante el Deploy:
[ ] Blueprint aplicado correctamente
[ ] PostgreSQL database creada
[ ] Environment variables configuradas
[ ] Persistent disk configurado (10GB)

Después del Deploy:
[ ] Health check pasa: /health
[ ] Modelo LLM descargado
[ ] API responde: /docs
[ ] Database conectada
[ ] Logs sin errores
```

---

## 🎉 **¡TODO LISTO!**

Ahora puedes ejecutar:

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main

# Luego en Render Dashboard:
New + → Blueprint → chess_trainer → Apply
```

**Tiempo estimado total**: 30-45 minutos (mayoría es descarga del modelo)

---

**Última actualización**: 2026-03-13  
**Siguiente paso**: [render_deployment_guide.md](deployment/render_deployment_guide.md) para guía completa
