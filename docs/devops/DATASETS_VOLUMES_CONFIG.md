# Datasets Volumes Configuration Guide

## Overview

This guide describes the volume configuration strategy for Chess Trainer datasets, ensuring efficient storage, backup, and access patterns across different environments.

## Volume Architecture

### Local Development

```yaml
# docker-compose.yml
volumes:
  chess_pgdata:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/postgres
  
  chess_datasets:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/datasets
```

### Production Setup

```yaml
# docker-compose.prod.yml
volumes:
  chess_pgdata:
    driver: local
    driver_opts:
      type: ext4
      device: /mnt/chess-data/postgres
  
  chess_datasets:
    external: true
    name: chess_datasets_prod
```

## Directory Structure

```
data/
├── datasets/           # Parquet files, exports
│   ├── export/
│   │   ├── personal/   # Personal games datasets
│   │   ├── elite/      # Elite players datasets  
│   │   ├── fide/       # FIDE games datasets
│   │   └── unified/    # Combined datasets
│   └── raw/           # Raw PGN files
├── postgres/          # PostgreSQL data directory
├── mlflow/           # MLflow artifacts
└── backups/          # Regular backups
```

## Configuration Examples

### Windows Development

```yaml
services:
  postgres:
    volumes:
      - type: bind
        source: ./data/postgres
        target: /var/lib/postgresql/data
      - type: bind
        source: ./data/backups
        target: /backups

  notebooks:
    volumes:
      - type: bind
        source: ./data/datasets
        target: /datasets
      - type: bind
        source: ./notebooks
        target: /notebooks
```

### Linux Production

```yaml
services:
  postgres:
    volumes:
      - chess_pgdata:/var/lib/postgresql/data
      - /opt/chess-trainer/backups:/backups:ro

volumes:
  chess_pgdata:
    driver: local
    driver_opts:
      type: ext4
      device: /dev/disk/by-label/chess-data
```

## Performance Optimization

### SSD Configuration

```yaml
# High-performance SSD mount
volumes:
  chess_pgdata:
    driver: local
    driver_opts:
      type: ext4
      device: /dev/nvme0n1p1
      o: noatime,nodiratime
```

### Network Storage

```yaml
# NFS mount for shared datasets
volumes:
  chess_datasets:
    driver: local
    driver_opts:
      type: nfs
      o: addr=192.168.1.100,rw,noatime
      device: ":/export/chess-datasets"
```

## Backup Strategy

### Automated Backups

```bash
#!/bin/bash
# scripts/backup_volumes.sh

BACKUP_DIR="/opt/chess-trainer/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker-compose exec postgres pg_dump -U chess chess_trainer_db > \
    "$BACKUP_DIR/chess_db_$DATE.sql"

# Volume backup
docker run --rm \
    -v chess_pgdata:/source:ro \
    -v $BACKUP_DIR:/backup \
    alpine tar czf /backup/pgdata_$DATE.tar.gz -C /source .
```

### Restore Procedures

```bash
#!/bin/bash
# scripts/restore_volumes.sh

BACKUP_FILE=$1
RESTORE_DATE=$(date +%Y%m%d_%H%M%S)

# Stop services
docker-compose down

# Restore volume
docker run --rm \
    -v chess_pgdata:/target \
    -v $BACKUP_FILE:/backup.tar.gz:ro \
    alpine sh -c "cd /target && tar xzf /backup.tar.gz"

# Start services
docker-compose up -d
```

## Security Configuration

### Access Control

```yaml
# Restricted access volumes
volumes:
  chess_secrets:
    driver: local
    driver_opts:
      type: tmpfs
      o: size=10m,uid=1000,gid=1000,mode=0600
```

### Encryption

```yaml
# Encrypted volume (Linux)
volumes:
  chess_encrypted:
    driver: local
    driver_opts:
      type: ext4
      device: /dev/mapper/chess-encrypted
      o: noatime
```

## Monitoring

### Volume Usage Monitoring

```bash
# Check volume usage
docker system df -v

# Specific volume inspection
docker volume inspect chess_pgdata

# Disk usage
du -sh /var/lib/docker/volumes/chess_trainer_chess_pgdata
```

### Health Checks

```python
import shutil
import os

def check_volume_health():
    volumes = {
        'postgres': './data/postgres',
        'datasets': './data/datasets',
        'mlflow': './data/mlflow'
    }
    
    for name, path in volumes.items():
        if os.path.exists(path):
            usage = shutil.disk_usage(path)
            free_gb = usage.free / (1024**3)
            
            if free_gb < 5:  # Less than 5GB free
                print(f"⚠️ Low disk space in {name}: {free_gb:.1f}GB free")
            else:
                print(f"✅ {name}: {free_gb:.1f}GB free")
```

## References

- [Docker Compose Volumes](https://docs.docker.com/compose/compose-file/compose-file-v3/#volumes)
- [Docker Volume Drivers](https://docs.docker.com/engine/extend/plugins_volume/)
- [Project Docker Configuration](../docker-compose.yml)