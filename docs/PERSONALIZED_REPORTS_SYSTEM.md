# Sistema de Reportes Personalizados Asíncronos

## Resumen

Este documento describe la implementación completa del sistema de generación de reportes personalizados asíncronos para el Chess Trainer. El sistema permite a los usuarios generar reportes de análisis de jugadores de forma asíncrona, con notificaciones de progreso y descarga de resultados.

## Arquitectura del Sistema

### Componentes Backend

#### 1. Router de Reportes (`src/api/routers/reports.py`)

**Endpoints principales:**
- `POST /api/reports/generate` - Generar reporte para jugador existente
- `POST /api/reports/generate-from-upload` - Generar reporte desde PGNs subidos
- `GET /api/reports/status/{job_id}` - Obtener estado de un job
- `GET /api/reports/download/{job_id}` - Descargar reporte generado
- `GET /api/reports/list` - Listar reportes recientes

**Funcionalidades clave:**
- Procesamiento asíncrono con jobs en background
- Sistema de polling para tracking de progreso
- Integración con scripts genéricos existentes
- Soporte para multiple formatos (Markdown, PDF)

#### 2. Servicio de Notificaciones (`src/api/services/notification_service.py`)

**Funcionalidades principales:**
- Crear, leer, marcar y eliminar notificaciones
- Notificaciones específicas para reportes completados/fallidos
- Sistema de metadata para contexto adicional
- Limpieza automática de notificaciones antiguas

#### 3. Servicio de Reportes (`src/api/services/report_service.py`)

**Responsabilidades:**
- Validar existencia de jugadores en BD
- Importar archivos PGN
- Ejecutar análisis usando scripts genéricos
- Generar análisis de Survivorship Bias
- Convertir reportes a PDF
- Manejo de archivos y directorios

#### 4. Router de Notificaciones (`src/api/routers/notifications.py`)

**Endpoints:**
- `GET /api/notifications/` - Obtener notificaciones
- `GET /api/notifications/unread/count` - Conteo no leídas
- `POST /api/notifications/` - Crear notificación
- `PATCH /api/notifications/{id}/read` - Marcar como leída
- `DELETE /api/notifications/{id}` - Eliminar notificación

### Componentes Frontend

#### 1. Página de Reportes (`src/frontend/src/pages/PersonalizedReportsPage.jsx`)

**Funcionalidades principales:**
- Formulario para generar reportes (jugador existente vs PGN upload)
- Seguimiento de progreso en tiempo real
- Lista de reportes recientes
- Descarga directa de reportes
- Integración con sistema de notificaciones

#### 2. Servicio de Reportes (`src/frontend/src/services/reportsService.js`)

**Capacidades:**
- Validación de datos de entrada
- Generación de reportes asíncronos
- Polling automático de estados
- Descarga de archivos
- Estimación de tiempos de procesamiento

#### 3. Servicio de Notificaciones Actualizado (`src/frontend/src/services/notificationService.js`)

**Mejoras implementadas:**
- Integración con nueva API de notificaciones
- Notificaciones del navegador
- Sistema de eventos personalizados
- Polling configurable
- Formateo y utilidades de tiempo

## Flujo de Trabajo del Sistema

### 1. Generar Reporte para Jugador Existente

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant API as API Reports
    participant S as Scripts
    participant N as Notifications
    
    U->>F: Ingresa nombre jugador + opciones
    F->>API: POST /api/reports/generate
    API->>S: Verificar jugador existe
    S-->>API: Datos del jugador
    API->>API: Crear job asíncrono
    API-->>F: Job ID + estado inicial
    F->>F: Iniciar polling estado
    
    Note over API, S: Background processing
    API->>S: analyze_player.py
    API->>S: analyze_survivorship.py
    API->>S: convert_md_to_pdf.py
    
    API->>N: Notificar completado
    N-->>F: Evento notificación
    F->>U: Mostrar reporte listo
    U->>F: Descargar reporte
    F->>API: GET /api/reports/download/{job_id}
```

### 2. Generar Reporte desde Upload

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant API as API Reports
    participant S as Scripts
    
    U->>F: Selecciona archivos PGN
    F->>F: Validar archivos
    F->>API: Subir PGNs
    F->>API: POST /api/reports/generate-from-upload
    API->>S: import_player_pgns.py
    API->>S: Verificar importación
    API->>S: analyze_player.py
    API-->>F: Reporte completado
```

## Integración con Scripts Genéricos

El sistema reutiliza completamente los scripts genéricos existentes:

### Scripts Utilizados

1. **`check_player_data.py`** - Verificar existencia y obtener estadísticas
2. **`import_player_pgns.py`** - Importar archivos PGN
3. **`analyze_player.py`** - Análisis principal del jugador
4. **`analyze_survivorship.py`** - Análisis de Survivorship Bias
5. **`convert_md_to_pdf.py`** - Conversión a PDF

### Ejemplo de Integración

```python
# Verificar jugador
result = subprocess.run(
    ["python", "src/scripts/check_player_data.py", player_name, "--json"],
    capture_output=True, text=True
)

# Análisis completo
result = subprocess.run([
    "python", "src/scripts/analyze_player.py", 
    player_name,
    "--min-games", str(min_games),
    "--output-dir", "reports/api_generated"
], capture_output=True, text=True)
```

## Sistema de Notificaciones Asíncronas

### Tipos de Notificaciones

1. **`report_ready`** - Reporte completado y listo para descarga
2. **`error`** - Error durante procesamiento
3. **`info`** - Información general del sistema
4. **`success`** - Operación exitosa

### Metadata de Reportes

```json
{
  "job_id": "uuid-job-id",
  "player_name": "nombre_jugador",
  "report_type": "análisis completo",
  "action_url": "/api/reports/download/uuid-job-id",
  "action_text": "Descargar reporte"
}
```

### Integración Frontend-Backend

```javascript
// Polling automático
reportService.startJobPolling(
    jobId,
    (status) => console.log('Progreso:', status.progress_percentage),
    (final) => notificationService.showNotification('Completado', `Reporte de ${final.player_name} listo`),
    (error) => notificationService.showNotification('Error', error, 'error')
);
```

## Configuración y Deployment

### Requisitos del Sistema

1. **Backend**:
   - FastAPI con Python 3.8+
   - Scripts genéricos en `src/scripts/`
   - PostgreSQL database
   - Directorio `reports/api_generated/`

2. **Frontend**:
   - React 18+ con TypeScript
   - Axios para HTTP requests
   - UI components (Shadcn/ui recomendado)

### Variables de Entorno

```bash
# Frontend (.env)
VITE_API_URL=http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000

# Backend
DATABASE_URL=postgresql://user:pass@localhost/chess_trainer
REPORTS_BASE_DIR=reports
API_REPORTS_DIR=reports/api_generated
```

### Estructura de Directorios

```
reports/
├── api_generated/          # Reportes generados por API
│   ├── player_analysis_*.md
│   └── player_survivorship_*.md
├── individual/             # Reportes individuales existentes
└── technical/             # Reportes técnicos existentes
```

## API Reference

### Generar Reporte (Existente)

```http
POST /api/reports/generate
Content-Type: application/json

{
  "player_name": "Magnus_Carlsen",
  "min_games": 50,
  "include_survivorship": true,
  "output_format": "markdown"
}
```

**Respuesta:**
```json
{
  "job_id": "uuid-4",
  "status": "pending",
  "message": "Generación de reporte para 'Magnus_Carlsen' iniciada",
  "estimated_time_minutes": 3
}
```

### Estado del Job

```http
GET /api/reports/status/{job_id}
```

**Respuesta:**
```json
{
  "job_id": "uuid-4",
  "status": "completed",
  "player_name": "Magnus_Carlsen",
  "progress_percentage": 100,
  "created_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:03:00Z",
  "report_path": "/reports/api_generated/magnus_carlsen_analysis.md"
}
```

## Casos de Uso

### 1. Usuario Avanzado - Análisis Rápido

Usuario con jugador ya en BD que necesita reporte actualizado:

1. Navega a "Reportes Personalizados"
2. Selecciona "Jugador Existente"
3. Ingresa nombre: "hikaru"
4. Configura: 100 partidas mín, incluir survivorship, formato PDF
5. Presiona "Generar Reporte"
6. Recibe notificación cuando está listo (2-3 min)
7. Descarga PDF con análisis completo

### 2. Usuario Novato - Primer Análisis

Usuario nuevo que sube sus PGNs por primera vez:

1. Selecciona "Subir PGNs"
2. Arrastra 5 archivos .pgn
3. Ingresa su nombre de usuario
4. Sistema importa partidas (1-2 min)
5. Genera análisis automáticamente (3-5 min)
6. Recibe reporte personalizado con recomendaciones

### 3. Entrenador - Análisis Masivo

Entrenador que analiza múltiples estudiantes:

1. Usa API directamente o interfaz batch
2. Lista de jugadores: ["student1", "student2", "student3"]
3. Sistema procesa en paralelo
4. Recibe notificaciones por cada completado
5. Descarga pack con todos los reportes

## Troubleshooting

### Problemas Comunes

#### 1. Job Queda en "pending"

**Causa**: Scripts no se encuentran o faltan dependencias
**Solución**: 
```bash
# Verificar scripts existen
ls -la src/scripts/analyze_player.py
ls -la src/scripts/import_player_pgns.py

# Verificar permisos
chmod +x src/scripts/*.py

# Verificar dependencias Python
pip install -r requirements.txt
```

#### 2. Notificaciones no llegan

**Causa**: Polling desactivado o error en servicio
**Solución**:
```javascript
// Verificar polling activo
const stopPolling = notificationService.startPolling(callback);

// Verificar permisos del navegador
notificationService.requestNotificationPermission();
```

#### 3. Descarga de reporte falla

**Causa**: Archivo no existe o permisos
**Solución**:
```bash
# Verificar directorio reportes
ls -la reports/api_generated/

# Verificar permisos
chmod 755 reports/
chmod 644 reports/api_generated/*.md
```

### Logs de Debug

```python
# Backend - habilitar logs detallados
import logging
logging.basicConfig(level=logging.DEBUG)

# Frontend - consola del navegador
localStorage.setItem('debug', 'chess-trainer:*');
```

## Roadmap y Mejoras Futuras

### Versión 2.0 (Próximo Release)

- [ ] WebSockets para notificaciones en tiempo real
- [ ] Sistema de colas Redis para jobs
- [ ] Batch processing para múltiples jugadores
- [ ] Templates personalizables de reportes
- [ ] Exportación a múltiples formatos (Word, Excel)

### Versión 2.1 (Futuro)

- [ ] Análisis comparativo entre jugadores
- [ ] Reportes de progreso temporal
- [ ] Integración con calendarios para seguimiento
- [ ] API webhooks para integraciones externas
- [ ] Dashboard de métricas de uso del sistema

## Conclusión

El sistema de reportes personalizados asíncronos integra perfectamente con la arquitectura existente del Chess Trainer, reutilizando todos los scripts genéricos y proporcionando una experiencia de usuario fluida para la generación de análisis profundos de jugadores de ajedrez.

La implementación es robusta, escalable y mantiene la compatibilidad total con el sistema existente, mientras añade capacidades avanzadas de procesamiento asíncrono y notificaciones en tiempo real.