# 🧪 Guía de Testing - Sistema de Notificaciones y Extracción de Features (FUNCIONALIDAD 3.5)

## 📋 Resumen
Este documento proporciona un plan de testing completo para validar el **Sistema de Notificaciones + Extracción de Features** implementado pero pendiente de pruebas end-to-end.

**Funcionalidad**: 3.5  
**Estado**: 🟡 Código implementado - Requiere testing completo  
**Versión**: v0.1.128-dd808c9  
**Fecha**: 14 de Febrero, 2026  
**Dependencias**: Requiere completar 3.3 (Games Explorer) + 3.4 (Navegación)

---

## 🎯 Objetivos del Testing

Validar que:
1. ✅ Sistema de notificaciones funciona correctamente (campanita UI)
2. ✅ Botón "Extraer Features" inicia proceso background
3. ✅ Proceso de extracción se ejecuta usando `generate_features_with_tactics.py`
4. ✅ Notificaciones reflejan estado real del proceso
5. ✅ Features extraídos se almacenan correctamente en PostgreSQL
6. ✅ Sistema escala con diferentes volúmenes de datos

---

## 🔧 Prerequisitos

### **1. Servicios Requeridos**

```powershell
# Verificar servicios Docker
docker-compose ps

# Deberías ver:
# - postgres (puerto 5432) ✅ Up
# - notebooks (puerto 8888, 5000) ✅ Up (opcional)
```

### **2. Conda Environment**

```powershell
# CRÍTICO: Usar environment chess_trainer
conda activate chess_trainer

# Verificar
conda info --envs
# Debe mostrar * en chess_trainer
```

### **3. Backend y Frontend Operativos**

**Backend API (Terminal 1)**:
```powershell
cd src/api
conda activate chess_trainer
python -m uvicorn main:app --reload --port 8000

# Esperado:
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Frontend React (Terminal 2)**:
```powershell
cd src/frontend
npm run dev

# Esperado:
# VITE ready
# Local: http://localhost:5173/
```

### **4. Usuario con Permisos**

```powershell
# Login con usuario admin (tiene permisos para feature extraction)
# Usuario: admin
# Password: admin123
```

---

## 🧪 Suite de Tests - Funcionalidad 3.5

### **TEST 1: Verificar Componente NotificationBell Existe**

**Objetivo**: Confirmar que la campanita de notificaciones está visible en la UI.

**Pasos**:
1. Abrir navegador: `http://localhost:5173`
2. Login con `admin` / `admin123`
3. Buscar campanita (🔔) en el navbar/header

**Resultado Esperado**:
- ✅ Campanita visible en navigation bar
- ✅ Badge con número "0" (sin notificaciones iniciales)
- ✅ Click en campanita abre popover vacío

**Screenshot esperado**: Navbar con campanita visible, badge "0".

**Validación en DevTools**:
```javascript
// Console
document.querySelector('[data-testid="notification-bell"]') !== null
// Debe retornar: true
```

---

### **TEST 2: Verificar ImportPage con Botón "Extraer Features"**

**Objetivo**: Confirmar que ImportPage tiene el botón de extracción de features.

**Pasos**:
1. Con sesión activa, navegar a: `http://localhost:5173/import`
2. Verificar botón "🚀 Extraer Features a PostgreSQL"

**Resultado Esperado**:
- ✅ Página ImportPage carga correctamente
- ✅ Botón "Extraer Features" visible
- ✅ Botón habilitado (no disabled)

**Validación**:
```javascript
// DevTools Console
document.querySelector('button:contains("Extraer Features")') !== null
```

---

### **TEST 3: Iniciar Extracción de Features - Volumen Pequeño (1 partida)**

**Objetivo**: Probar ciclo completo con dataset mínimo.

#### **3.1. Preparar Archivo PGN de Prueba**

```powershell
# Crear archivo de prueba con 1 partida
$testPgn = @"
[Event "Test Game"]
[Site "Test"]
[Date "2026.02.14"]
[Round "1"]
[White "PlayerA"]
[Black "PlayerB"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 1-0
"@

$testPgn | Out-File -FilePath "test_single_game.pgn" -Encoding UTF8
```

#### **3.2. Subir archivo en ImportPage**

**Pasos**:
1. En ImportPage, click "Choose File" o drag & drop
2. Seleccionar `test_single_game.pgn`
3. Click botón "Upload" (si existe)
4. Esperar confirmación de carga

**Resultado Esperado**:
- ✅ Archivo aparece en lista de archivos cargados
- ✅ Mensaje: "1 archivo(s) cargado(s) exitosamente"

#### **3.3. Iniciar Extracción**

**Pasos**:
1. Click en botón "🚀 Extraer Features a PostgreSQL"
2. Observar campanita de notificaciones

**Resultado Esperado - Inmediato**:
- ✅ Botón cambia a estado "Processing..." (opcional)
- ✅ Badge de campanita muestra "1" (nueva notificación)
- ✅ Abrir campanita: notificación "Proceso de extracción iniciado"

**Validación Backend**:
```powershell
# Verificar que el job se creó
conda activate chess_trainer
cd src/api

# Consultar endpoint (si está implementado)
curl http://localhost:8000/api/features/jobs
# Esperado: Lista con 1 job en estado "running"
```

#### **3.4. Esperar Completación**

**Tiempo esperado**: 10-30 segundos (1 partida)

**Pasos**:
1. Mantener campanita abierta (o cerrar y abrir cada 10 seg)
2. Esperar actualización de notificación

**Resultado Esperado - Después de completar**:
- ✅ Badge campanita sigue en "1"
- ✅ Notificación actualizada a "Extracción completada"
- ✅ Detalle: "1 partida procesada, X features extraídos"

#### **3.5. Validar en Base de Datos**

```powershell
conda activate chess_trainer
python

# En Python REPL:
from src.database.db_connector import DatabaseConnector

db = DatabaseConnector()

# Contar features antes y después
features_count = db.execute_query("SELECT COUNT(*) FROM features_tactics")[0][0]
print(f"Total features: {features_count}")

# Ver últimas features extraídas
recent_features = db.execute_query("""
    SELECT game_id, move_number, error_label, created_at 
    FROM features_tactics 
    ORDER BY created_at DESC 
    LIMIT 10
""")
print(f"Últimas 10 features: {recent_features}")
```

**Resultado Esperado**:
- ✅ `features_count` aumentó en ~8-16 features (1 partida * ~8-16 movimientos)
- ✅ `recent_features` muestra features con timestamp reciente

---

### **TEST 4: Extracción - Volumen Medio (10 partidas)**

**Objetivo**: Validar sistema con carga media.

#### **4.1. Preparar Dataset de 10 Partidas**

```powershell
# Usar script para generar 10 partidas de prueba
# O copiar 10 partidas de un archivo PGN existente

# Ejemplo: extraer 10 primeras partidas de un PGN grande
Get-Content "data/games/personal/*.pgn" -TotalCount 200 | Out-File "test_10_games.pgn"
```

#### **4.2. Proceso de Testing**

**Pasos**:
1. Upload `test_10_games.pgn` en ImportPage
2. Click "🚀 Extraer Features"
3. Observar notificación "Proceso iniciado"
4. **Tiempo esperado**: 1-3 minutos
5. Esperar notificación "Completado"

**Resultado Esperado**:
- ✅ Notificación muestra "10 partidas procesadas"
- ✅ Features en DB aumentan en ~80-160 (10 * ~8-16 movs)

**Validación adicional**:
```python
# Verificar que NO hay errores en el proceso
errors = db.execute_query("""
    SELECT * FROM feature_extraction_logs 
    WHERE status = 'error' 
    ORDER BY created_at DESC 
    LIMIT 5
""")
print(f"Errores recientes: {len(errors)}")
# Esperado: 0 errores
```

---

### **TEST 5: Extracción - Volumen Alto (100+ partidas) - STRESS TEST**

**Objetivo**: Validar escalabilidad y performance.

**⚠️ Nota**: Este test es **opcional** y solo debe ejecutarse si:
- Tests 3 y 4 pasaron exitosamente
- Sistema está estable
- Hay tiempo para esperar ~10-30 minutos de procesamiento

#### **5.1. Preparar Dataset Grande**

```powershell
# Seleccionar 100 partidas de un archivo PGN
# Ejemplo usando data existente
Get-Content "data/games/elite/elite_games.pgn" -TotalCount 2000 | Out-File "test_100_games.pgn"
```

#### **5.2. Proceso de Testing**

**Pasos**:
1. Upload `test_100_games.pgn`
2. Click "🚀 Extraer Features"
3. **NO esperar en la UI** - el proceso corre en background
4. Verificar notificación "Procesando..."
5. **Tiempo esperado**: 10-30 minutos

**Monitoreo durante proceso**:
```powershell
# Terminal separada para monitorear logs backend
cd src/api
conda activate chess_trainer

# Ver logs en tiempo real (si hay logging configurado)
tail -f logs/feature_extraction.log
```

**Resultado Esperado**:
- ✅ Sistema no se cuelga
- ✅ Frontend sigue funcional durante extracción
- ✅ Después de 10-30 min: notificación "Completado"
- ✅ Features aumentan en ~800-1600

**Métricas de Performance**:
```python
# Calcular tiempo promedio por partida
total_time_minutes = 15  # ejemplo
games_processed = 100
avg_time_per_game = (total_time_minutes * 60) / games_processed
print(f"Tiempo promedio por partida: {avg_time_per_game:.2f} segundos")
# Aceptable: < 15 segundos por partida
```

---

### **TEST 6: Notificaciones - Marcar como Leída**

**Objetivo**: Validar gestión de notificaciones.

**Pasos**:
1. Con notificaciones en la campanita
2. Click en una notificación individual
3. Debe marcarse como leída (cambia estilo visual)
4. Badge disminuye en 1

**Resultado Esperado**:
- ✅ Notificación cambia a "leída" (ej: texto gris, sin negrita)
- ✅ Badge actualiza a N-1 notificaciones

**Validación API**:
```powershell
# Verificar endpoint de marcar como leída
curl -X PUT http://localhost:8000/api/features/notifications/1/read `
    -H "Authorization: Bearer $token"
# Esperado: { "status": "success", "id": 1 }
```

---

### **TEST 7: Notificaciones - Eliminar Individual**

**Objetivo**: Validar eliminación de notificaciones.

**Pasos**:
1. Click en botón "Eliminar" (X) de una notificación
2. Notificación debe desaparecer
3. Badge disminuye en 1

**Resultado Esperado**:
- ✅ Notificación eliminada de la lista
- ✅ Badge actualiza correctamente

---

### **TEST 8: Notificaciones - Limpiar Todas**

**Objetivo**: Validar limpiar todas las notificaciones.

**Pasos**:
1. Click en botón "Limpiar todas" (si existe)
2. Todas las notificaciones desaparecen
3. Badge = 0

**Resultado Esperado**:
- ✅ Lista de notificaciones vacía
- ✅ Badge muestra "0" o desaparece
- ✅ Mensaje: "No hay notificaciones"

---

### **TEST 9: Polling de Notificaciones**

**Objetivo**: Verificar que notificaciones se actualizan automáticamente.

**Configuración actual**: Polling cada 10 segundos.

**Pasos**:
1. Iniciar extracción de features
2. **NO abrir** la campanita
3. Esperar 10-20 segundos
4. Observar badge de campanita

**Resultado Esperado**:
- ✅ Badge se actualiza automáticamente sin refrescar página
- ✅ Después de completar: badge muestra nueva notificación

**Validación en DevTools (Network Tab)**:
- ✅ Cada 10 segundos: request a `/api/features/notifications`
- ✅ Response con lista actualizada de notificaciones

---

### **TEST 10: Errores y Edge Cases**

#### **10.1. Intentar Extraer Sin Archivos**

**Pasos**:
1. En ImportPage sin archivos cargados
2. Click "Extraer Features"

**Resultado Esperado**:
- ✅ Error: "No hay archivos para procesar"
- ✅ Notificación NO se crea

#### **10.2. Archivo PGN Inválido**

**Pasos**:
1. Crear archivo `invalid.pgn` con contenido corrupto:
   ```
   This is not a valid PGN file!
   Random text here.
   ```
2. Upload y extraer features

**Resultado Esperado**:
- ✅ Notificación: "Error al procesar archivos"
- ✅ Detalle del error (si disponible)
- ✅ No se agregan features corruptos a DB

#### **10.3. Usuario Sin Permisos (rol: user)**

**Pasos**:
1. Logout de admin
2. Login con `user` / `user123`
3. Navegar a ImportPage

**Resultado Esperado**:
- ✅ Botón "Extraer Features" **no visible** o **disabled**
- ✅ Mensaje: "No tiene permisos para esta operación"

---

## 📊 Checklist de Validación Final

### **Componentes UI**
- [ ] Campanita de notificaciones visible en navbar
- [ ] Badge muestra cantidad correcta de notificaciones
- [ ] Popover de notificaciones funcional
- [ ] Botón "Extraer Features" visible en ImportPage
- [ ] Notificaciones se marcan como leídas
- [ ] Notificaciones se eliminan correctamente

### **Funcionalidad Backend**
- [ ] Endpoint `/api/features/extract` funciona
- [ ] Endpoint `/api/features/jobs` lista jobs
- [ ] Endpoint `/api/features/notifications` retorna notificaciones
- [ ] Proceso background ejecuta `generate_features_with_tactics.py`
- [ ] Features se almacenan en PostgreSQL correctamente

### **Performance**
- [ ] 1 partida: < 30 segundos
- [ ] 10 partidas: < 3 minutos
- [ ] 100 partidas: < 30 minutos
- [ ] Sistema estable (no crashes)
- [ ] Frontend funcional durante procesamiento

### **Seguridad**
- [ ] Solo usuarios con rol `admin` o `pgn_uploader` pueden extraer
- [ ] Usuario `user` no ve botón de extracción
- [ ] Tokens JWT válidos requeridos

---

## 🐛 Issues Conocidos / A Investigar

### **Issues a documentar durante testing**:
1. **Performance**: ¿Cuánto tarda realmente 1 partida, 10, 100?
2. **Errores comunes**: ¿Qué tipos de errores aparecen con PGNs inválidos?
3. **Límites**: ¿Hay un máximo de partidas que se pueden procesar en un job?
4. **Notificaciones**: ¿Se pierden notificaciones al refrescar página?
5. **Polling**: ¿10 segundos es adecuado o muy frecuente?

**Formato de reporte de issues**:
```markdown
## Issue: [Descripción breve]

**Prioridad**: Alta / Media / Baja  
**Reproducible**: Sí / No

**Pasos para reproducir**:
1. ...
2. ...

**Resultado esperado**: ...
**Resultado actual**: ...

**Logs/Screenshots**: [adjuntar]
```

---

## 📚 Referencias

- **Script de extracción**: [src/scripts/generate_features_with_tactics.py](../src/scripts/generate_features_with_tactics.py)
- **Backend API**: [src/api/routers/features.py](../src/api/routers/features.py) (si existe)
- **Frontend ImportPage**: [src/frontend/src/pages/ImportPage.jsx](../src/frontend/src/pages/ImportPage.jsx)
- **NotificationBell**: [src/frontend/src/components/shared/NotificationBell.jsx](../src/frontend/src/components/shared/NotificationBell.jsx)
- **Roadmap Funcional**: [ROADMAP_FUNCTIONAL_CHESS_TRAINER.md](ROADMAP_FUNCTIONAL_CHESS_TRAINER.md)

---

## ✅ Criterio de Éxito

La **FUNCIONALIDAD 3.5** se considerará **100% validada** cuando:

1. ✅ Todos los tests 1-9 pasan exitosamente
2. ✅ Test 10 (edge cases) muestra errores manejados correctamente
3. ✅ Performance es aceptable (< 15 seg/partida)
4. ✅ No hay crashes ni errores críticos
5. ✅ Issues conocidos están documentados con soluciones propuestas
6. ✅ Documentación actualizada con hallazgos del testing

**Al completar este testing**, actualizar roadmap:
- Cambiar estado de 🟡 a ✅ en ROADMAP_FUNCTIONAL_CHESS_TRAINER.md
- Agregar sección "Testing Completado" con fecha y resultados

---

_Documento creado: 14 de Febrero, 2026_  
_Versión: v1.0_  
_Autor: Chess Trainer Development Team_
