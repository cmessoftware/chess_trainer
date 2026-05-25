# Chess Trainer - Deployment Files

Archivos de configuración para deployment en diferentes plataformas.

## 📁 Estructura

```
deployment/
├── render_startup.sh              # Script de inicio para Render
├── render_build.sh                # Script de build para Render
├── render_deployment_guide.md     # Guía completa de deployment en Render
└── README.md                      # Este archivo
```

## 🚀 Plataformas Soportadas

### Render (Recomendado)
- **Archivo**: `render.yaml` (en root)
- **Dockerfile**: `dockerfile.render` (en root)
- **Guía**: [render_deployment_guide.md](render_deployment_guide.md)
- **Costo**: ~$92/mes (PostgreSQL + App Pro)

### Docker Compose (Local)
- **Archivo**: `docker-compose.yml` (en root)
- **Uso**: Desarrollo local
- **Costo**: Gratis

### Kubernetes (Enterprise)
- **TBD**: Pendiente implementación
- **Uso**: Producción enterprise
- **Costo**: Variable

---

## ⚡ Quick Start - Render

```bash
# 1. Push código
git push origin main

# 2. Deploy en Render
render deploy --blueprint render.yaml

# 3. Monitorear
render logs chess-trainer-ai-coach --tail 100
```

---

## 📊 Comparación de Plataformas

| Plataforma  | Setup     | Costo/mes | GPU     | Auto-scaling |
| ----------- | --------- | --------- | ------- | ------------ |
| Render      | ⭐⭐⭐ Fácil | $92       | ❌       | ✅            |
| Railway     | ⭐⭐⭐ Fácil | $85       | ❌       | ✅            |
| Fly.io      | ⭐⭐ Medio  | $70       | ✅       | ✅            |
| AWS ECS     | ⭐ Difícil | $120+     | ✅       | ✅            |
| Self-hosted | ⭐ Difícil | $40       | Depende | ❌            |

---

## 🔧 Variables de Entorno Requeridas

### Todas las Plataformas

```bash
# Database
CHESS_TRAINER_DB_URL=postgresql://user:pass@host:5432/chess_trainer

# Ollama
OLLAMA_MODEL=llama3.1:8b
OLLAMA_HOST=0.0.0.0:11434

# API
PORT=8000
WORKERS=2
PYTHONUNBUFFERED=1

# Secrets
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
```

---

## 📚 Documentación Adicional

- **Render**: [render_deployment_guide.md](render_deployment_guide.md)
- **Docker**: `../docker-compose.yml`
- **API Docs**: `../docs/API_DOCUMENTATION.md`

---

**Última actualización:** 2026-03-13
