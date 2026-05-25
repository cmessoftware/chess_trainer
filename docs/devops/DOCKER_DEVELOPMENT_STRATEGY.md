# Docker Development Strategy - Chess Trainer

## Overview

This document outlines the Docker-based development strategy for the Chess Trainer project, including container architecture, development workflows, and best practices.

## Container Architecture

### Current Stack

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_USER=chess
      - POSTGRES_PASSWORD=chess_pass
      - POSTGRES_DB=chess_trainer_db
    ports:
      - "5432:5432"
    volumes:
      - chess_pgdata:/var/lib/postgresql/data
```

### Planned Services

```mermaid
graph TB
    subgraph "🐳 Docker Environment"
        POSTGRES[("🐘 PostgreSQL<br/>Data Storage")]
        APP["🎯 Chess Trainer<br/>Main Application"]
        NOTEBOOKS["📓 Jupyter<br/>Data Science"]
        MLFLOW["🔬 MLflow<br/>ML Tracking"]
        REDIS[("🔴 Redis<br/>Caching")]
    end
    
    APP --> POSTGRES
    APP --> REDIS
    NOTEBOOKS --> POSTGRES
    NOTEBOOKS --> MLFLOW
    MLFLOW --> POSTGRES
```

## Development Workflows

### Quick Start (Windows)

```powershell
# One-command setup
.\build_up_clean_all.ps1

# Manual alternative
docker-compose build
docker-compose up -d
```

### Development Cycle

```bash
# 1. Start services
docker-compose up -d postgres

# 2. Development work (local Python environment)
python src/scripts/generate_features.py

# 3. Test with containers
docker-compose up -d notebooks

# 4. ML experiments
jupyter lab --ip=0.0.0.0 --port=8888
```

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy stack
docker-compose -f docker-compose.prod.yml up -d

# Health check
docker-compose ps
```

## Container Configurations

### PostgreSQL Container

**Purpose**: Primary data storage

```yaml
postgres:
  image: postgres:13
  environment:
    POSTGRES_USER: chess
    POSTGRES_PASSWORD: chess_pass
    POSTGRES_DB: chess_trainer_db
  ports:
    - "5432:5432"
  volumes:
    - chess_pgdata:/var/lib/postgresql/data
    - ./sql/init:/docker-entrypoint-initdb.d
```

**Features**:
- ✅ Persistent data storage
- ✅ Database initialization scripts
- ✅ Connection pooling ready
- ✅ Backup/restore support

### Application Container (Planned)

**Purpose**: Main Chess Trainer application

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    stockfish \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY src/ ./src/
COPY app.py .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Notebooks Container (Planned)

**Purpose**: Data science and ML development

```dockerfile
FROM jupyter/scipy-notebook:latest

USER root

# Install additional packages
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

USER $NB_UID

# Python ML packages
RUN pip install --no-cache-dir \
    mlflow \
    chess \
    stockfish \
    plotly \
    dash

# Copy notebooks
COPY notebooks/ work/
```

### MLflow Container (Planned)

**Purpose**: ML experiment tracking

```dockerfile
FROM python:3.11-slim

RUN pip install mlflow[extras] psycopg2-binary

# MLflow configuration
ENV MLFLOW_TRACKING_URI=postgresql://chess:chess_pass@postgres:5432/chess_trainer_db
ENV MLFLOW_DEFAULT_ARTIFACT_ROOT=/mlflow/artifacts

VOLUME ["/mlflow/artifacts"]

EXPOSE 5000

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
```

## Volume Management

### Data Persistence

```yaml
volumes:
  chess_pgdata:          # PostgreSQL data
    driver: local
  chess_mlflow:          # MLflow artifacts  
    driver: local
  chess_notebooks:       # Jupyter workspace
    driver: local
```

### Backup Strategy

```bash
# Database backup
docker-compose exec postgres pg_dump -U chess chess_trainer_db > backup.sql

# Volume backup
docker run --rm -v chess_pgdata:/data -v $(pwd):/backup alpine \
    tar czf /backup/pgdata_backup.tar.gz -C /data .

# Restore
docker run --rm -v chess_pgdata:/data -v $(pwd):/backup alpine \
    tar xzf /backup/pgdata_backup.tar.gz -C /data
```

## Environment Configuration

### Environment Variables

```bash
# .env file
POSTGRES_USER=chess
POSTGRES_PASSWORD=chess_pass
POSTGRES_DB=chess_trainer_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

MLFLOW_TRACKING_URI=postgresql://chess:chess_pass@postgres:5432/chess_trainer_db
MLFLOW_DEFAULT_ARTIFACT_ROOT=/mlflow/artifacts

STOCKFISH_PATH=/usr/games/stockfish
CHESS_TRAINER_LOG_LEVEL=INFO
```

### Network Configuration

```yaml
networks:
  chess_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Development Best Practices

### Local Development

1. **Use host networking for development**
   ```yaml
   network_mode: host  # For local development only
   ```

2. **Mount source code as volumes**
   ```yaml
   volumes:
     - ./src:/app/src
     - ./notebooks:/notebooks
   ```

3. **Hot reload configuration**
   ```yaml
   environment:
     - FLASK_ENV=development
     - JUPYTER_ENABLE_LAB=yes
   ```

### Production Guidelines

1. **Multi-stage builds for smaller images**
2. **Non-root user execution**
3. **Health checks for all services**
4. **Resource limits**
5. **Secrets management**

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

## Monitoring and Logging

### Log Aggregation

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Health Monitoring

```bash
# Container health status
docker-compose ps

# Service logs
docker-compose logs -f postgres
docker-compose logs -f app

# Resource usage
docker stats
```

### Monitoring Stack (Future)

```yaml
# Planned monitoring services
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

## Performance Optimization

### Build Optimization

```dockerfile
# Use .dockerignore
echo "__pycache__/" >> .dockerignore
echo "*.pyc" >> .dockerignore
echo ".git/" >> .dockerignore

# Multi-stage builds
FROM python:3.11 as builder
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
```

### Runtime Optimization

```yaml
# Resource limits
services:
  postgres:
    shm_size: 256m
    command: |
      postgres
      -c shared_preload_libraries=pg_stat_statements
      -c max_connections=200
      -c shared_buffers=256MB
```

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check port usage
   netstat -tulpn | grep :5432
   
   # Use different port
   ports:
     - "5433:5432"
   ```

2. **Permission issues**
   ```bash
   # Fix volume permissions
   docker-compose exec postgres chown -R postgres:postgres /var/lib/postgresql/data
   ```

3. **Database connection issues**
   ```bash
   # Test connection
   docker-compose exec postgres psql -U chess -d chess_trainer_db -c "SELECT 1;"
   ```

### Debugging Commands

```bash
# Container inspection
docker-compose exec app bash
docker-compose logs --tail=50 app

# Network debugging
docker network ls
docker network inspect chess_trainer_default

# Volume debugging
docker volume ls
docker volume inspect chess_trainer_chess_pgdata
```

## Migration Strategy

### From Local to Docker

1. **Phase 1**: Containerize database only
2. **Phase 2**: Add application container
3. **Phase 3**: Add supporting services (MLflow, Redis)
4. **Phase 4**: Full orchestration with Kubernetes (future)

### Rollback Plan

```bash
# Emergency rollback to local development
docker-compose down
pg_dump -h localhost -U chess chess_trainer_db > emergency_backup.sql

# Restore to local PostgreSQL
psql -U local_user -d local_db < emergency_backup.sql
```

## Future Roadmap

### Short Term (1-3 months)
- [ ] Complete application containerization
- [ ] Add MLflow service
- [ ] Implement proper networking
- [ ] Add monitoring stack

### Medium Term (3-6 months)
- [ ] Kubernetes deployment
- [ ] CI/CD integration
- [ ] Advanced monitoring
- [ ] Auto-scaling configuration

### Long Term (6+ months)
- [ ] Multi-region deployment
- [ ] Service mesh integration
- [ ] Advanced observability
- [ ] Cost optimization

## References

- [Docker Compose File](../docker-compose.yml)
- [PowerShell Automation](../build_up_clean_all.ps1)
- [Environment Configuration](../.env.example)
- [Database Schema](../alembic/)

---

**Document Version**: 1.0  
**Last Updated**: December 29, 2025  
**Maintained by**: Chess Trainer Development Team
