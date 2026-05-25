# 📋 Chess Trainer API - Tests Directory

Este directorio contiene los casos de prueba y documentación para testing de la Chess Trainer API.

## 📁 **Estructura de Archivos**

### `postman_test_cases.csv`
- **Propósito**: Dataset con 23 casos de prueba para Postman Runner
- **Formato**: CSV con columnas para método, URL, headers, body, etc.
- **Uso**: Importar en Postman Runner para ejecutar pruebas automatizadas

### `POSTMAN_RUNNER_GUIDE.md`
- **Propósito**: Guía completa paso a paso para configurar y ejecutar pruebas
- **Contenido**: Instrucciones detalladas, scripts JavaScript, configuración de environments
- **Uso**: Seguir la guía para configurar testing automatizado completo

## 🚀 **Inicio Rápido**

1. **Importar casos**: Usar `postman_test_cases.csv` en Postman Runner
2. **Seguir guía**: Leer `POSTMAN_RUNNER_GUIDE.md` paso a paso
3. **Configurar environment**: Variables baseUrl, tokens, etc.
4. **Ejecutar**: 23 tests automatizados en secuencia

## ✅ **Casos de Prueba Incluidos**

- **3 endpoints básicos**: health, root, favicon
- **5 casos de autenticación**: login válido/inválido, verify token  
- **12 endpoints de ajedrez**: games, moves, analysis, validation
- **3 casos de error**: 401, 404, 403

## 🎯 **URLs de Testing**

- **Base URL**: `http://localhost:8000`
- **Game IDs válidos**: 1, 2
- **Usuarios**: admin/admin123, analista/analista123, usuario/usuario123

## 📊 **Features del Testing Suite**

- ✅ Auto-captura de tokens JWT
- ✅ Validaciones automáticas de estructura  
- ✅ Métricas de rendimiento
- ✅ Tests con diferentes roles de usuario
- ✅ Casos de error y permisos

---

**Ubicación anterior**: Archivos movidos desde la raíz del proyecto para mejor organización.