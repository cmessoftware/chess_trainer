# 🧪 Frontend Tests - Chess Trainer

## Archivos de Testing Interactivo

### 📋 `test_api_interactive.http`
**Propósito:** Testing de API usando REST Client extension
- ✅ Pruebas directas de endpoints
- ✅ Configuración de variables base URL
- ✅ Tests de búsqueda y filtrado
- ✅ Validación de respuestas JSON

**Uso:** Abrir en VS Code con REST Client extension instalada y hacer clic en "Send Request"

### 🌐 `frontend_test_interactive.html`
**Propósito:** Testing completo frontend-backend con interfaz web
- ✅ Pruebas de conectividad API
- ✅ Análisis de red y CORS
- ✅ Debug interactivo de servicios frontend
- ✅ Simulación de llamadas axios
- ✅ Performance testing

**Uso:** 
1. Abrir con Live Server o servidor HTTP
2. Usar botones interactivos para diagnosticar problemas
3. Ver logs en tiempo real en la interfaz

## 🚀 Uso Recomendado

1. **Para pruebas rápidas de API:** Usar `test_api_interactive.http`
2. **Para debug completo frontend-backend:** Usar `frontend_test_interactive.html`
3. **Para análisis de conectividad:** Usar ambos en conjunto

## 📊 Configuración

- **API Base URL:** `http://127.0.0.1:8000`
- **Frontend URL:** `http://localhost:5173`
- **Tests incluidos:** Sources, Games, Search, Network Analysis

---
_Creado para debuggear FUNCIONALIDAD 3.1 - Chess Board Interactivo + Log System Base_