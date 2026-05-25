# Configuración de Variables de Entorno

## Frontend

El frontend utiliza Vite, que requiere que las variables de entorno comiencen con `VITE_`.

### Archivo de configuración

Crear un archivo `.env.local` en `src/frontend/` basado en `.env.example`:

```bash
# Desarrollo local
VITE_API_URL=http://127.0.0.1:8000

# Producción
# VITE_API_URL=https://api.chess-trainer.com
```

### Variables disponibles

| Variable       | Descripción                | Valor por defecto       |
| -------------- | -------------------------- | ----------------------- |
| `VITE_API_URL` | URL base de la API backend | `http://127.0.0.1:8000` |

### Uso en el código

Las URLs están centralizadas en `src/frontend/src/config/api.js`:

```javascript
import { API_ENDPOINTS } from '../config/api.js'

// Usar endpoints predefinidos
fetch(API_ENDPOINTS.AUTH_LOGIN, { ... })

// O usar la URL base directamente
import API_BASE_URL from '../config/api.js'
const url = `${API_BASE_URL}/custom/endpoint`
```

## Backend

El backend utiliza variables de entorno estándar de Python.

### Archivo de configuración

Crear un archivo `.env` en la raíz del proyecto:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chess_trainer
DB_USER=postgres
DB_PASSWORD=your_password

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### Variables disponibles

| Variable                          | Descripción                     | Valor por defecto               |
| --------------------------------- | ------------------------------- | ------------------------------- |
| `DB_HOST`                         | Host de PostgreSQL              | `localhost`                     |
| `DB_PORT`                         | Puerto de PostgreSQL            | `5432`                          |
| `DB_NAME`                         | Nombre de la base de datos      | `chess_trainer`                 |
| `DB_USER`                         | Usuario de PostgreSQL           | `postgres`                      |
| `DB_PASSWORD`                     | Contraseña de PostgreSQL        | -                               |
| `JWT_SECRET_KEY`                  | Clave secreta para JWT          | `chess-trainer-secret-key-2024` |
| `JWT_ALGORITHM`                   | Algoritmo de JWT                | `HS256`                         |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Minutos de expiración del token | `1440` (24 horas)               |

## Despliegue en Producción

### Frontend (Vite)

Al compilar para producción:

```bash
cd src/frontend
VITE_API_URL=https://api.chess-trainer.com npm run build
```

O configurar en el archivo `.env.production`:

```bash
VITE_API_URL=https://api.chess-trainer.com
```

### Backend (FastAPI)

Configurar las variables de entorno en el servidor de producción (ejemplo con systemd):

```ini
[Service]
Environment="DB_HOST=prod-db-server"
Environment="DB_PASSWORD=strong-password"
Environment="JWT_SECRET_KEY=production-secret-key"
```

O usar un archivo `.env` y cargarlo con `python-dotenv`.

## Notas de Seguridad

- **NUNCA** commitear archivos `.env` o `.env.local` al repositorio
- Usar secretos diferentes para cada entorno (desarrollo, staging, producción)
- Rotar el `JWT_SECRET_KEY` regularmente en producción
- Usar HTTPS en producción para todas las comunicaciones
