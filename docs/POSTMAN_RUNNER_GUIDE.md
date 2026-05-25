# 🚀 POSTMAN RUNNER - GUÍA PASO A PASO
## Chess Trainer API - Casos de Prueba Automatizados

---

## 📋 **PASO 1: PREPARAR EL ENTORNO**

### 1.1 Crear Environment en Postman
1. Abre Postman
2. Click en "Environments" (icono de engranaje)
3. Click "Create Environment"
4. Nombre: `Chess Trainer Local`
5. Agregar estas variables:

| Variable         | Initial Value           | Current Value           |
| ---------------- | ----------------------- | ----------------------- |
| `base_url`       | `http://localhost:8000` | `http://localhost:8000` |
| `token`          | (vacío)                 | (vacío)                 |
| `admin_token`    | (vacío)                 | (vacío)                 |
| `analista_token` | (vacío)                 | (vacío)                 |
| `usuario_token`  | (vacío)                 | (vacío)                 |

6. Click "Save"
7. Seleccionar el environment desde el dropdown

---

## 📋 **PASO 2: IMPORTAR LA COLECCIÓN**

### 2.1 Crear Collection Base
1. Click "Collections" → "Create Collection"
2. Nombre: `Chess Trainer API Tests`
3. En la pestaña "Variables" agregar:
   - `base_url`: `http://localhost:8000`

### 2.2 Configurar Scripts Globales (Pre-request Script)
```javascript
// Pre-request Script a nivel de Collection
pm.test("Environment check", function () {
    pm.expect(pm.environment.get("base_url")).to.not.be.undefined;
});
```

### 2.3 Configurar Tests Globales
```javascript
// Tests Script a nivel de Collection  
pm.test("Response time is less than 5000ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(5000);
});

pm.test("Response has correct headers", function () {
    pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");
});
```

---

## 📋 **PASO 3: IMPORTAR CASOS DE PRUEBA DESDE CSV**

### 3.1 Usar CSV con Runner
1. Click en tu collection "Chess Trainer API Tests"
2. Click "Run collection" (botón play)
3. En el Runner, click "Select File" junto a "Data"
4. Seleccionar el archivo `postman_test_cases.csv`
5. Verificar que aparezcan las columnas detectadas

### 3.2 Configurar el Runner
- **Iterations**: 1 (por cada fila del CSV)
- **Delay**: 500ms (pausa entre requests)
- **Data File Type**: CSV
- **Keep variable values**: ✅ Activado
- **Run Order**: Sequential

---

## 📋 **PASO 4: CREAR REQUESTS INDIVIDUALES**

### 4.1 Login Admin (Para obtener tokens)
```
POST {{base_url}}/auth/login
Headers:
  Content-Type: application/json
Body:
{
  "username": "admin", 
  "password": "admin123"
}

Tests Script:
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("admin_token", jsonData.access_token);
    pm.environment.set("token", jsonData.access_token);
}
```

### 4.2 Login Analista
```
POST {{base_url}}/auth/login
Headers:
  Content-Type: application/json
Body:
{
  "username": "analista",
  "password": "analista123"  
}

Tests Script:
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("analista_token", jsonData.access_token);
}
```

### 4.3 Login Usuario
```
POST {{base_url}}/auth/login
Headers:
  Content-Type: application/json
Body:
{
  "username": "usuario",
  "password": "usuario123"
}

Tests Script:
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("usuario_token", jsonData.access_token);
}
```

---

## 📋 **PASO 5: EJECUTAR PRUEBAS**

### 5.1 Orden de Ejecución Recomendado
1. **Fase 1**: Endpoints básicos (health, root, favicon)
2. **Fase 2**: Autenticación (todos los logins)
3. **Fase 3**: Endpoints protegidos (games, moves, analysis)
4. **Fase 4**: Casos de error (401, 404, 403)

### 5.2 Ejecutar con Runner
1. Click "Run Chess Trainer API Tests"
2. Seleccionar archivo CSV
3. Click "Run Chess Trainer API Tests"
4. Observar resultados en tiempo real

### 5.3 Ejecutar Manualmente
1. Ejecutar primero "Login Admin" para obtener token
2. Ejecutar los demás requests en secuencia
3. Verificar que las variables se actualizan correctamente

---

## 📋 **PASO 6: SCRIPTS DE AUTOMATIZACIÓN**

### 6.1 Test Script Genérico (para cada request)
```javascript
// Verificar código de estado esperado
pm.test("Status code is correct", function () {
    var expectedCode = pm.iterationData.get("expectedStatusCode") || 200;
    pm.response.to.have.status(parseInt(expectedCode));
});

// Verificar estructura de respuesta para endpoints exitosos
if (pm.response.code === 200) {
    pm.test("Response is valid JSON", function () {
        pm.response.to.be.json;
    });
}

// Guardar tokens automáticamente
if (pm.request.url.toString().includes("/auth/login") && pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("token", jsonData.access_token);
    
    var username = JSON.parse(pm.request.body.raw).username;
    pm.environment.set(username + "_token", jsonData.access_token);
}
```

### 6.2 Pre-request Script para Requests Protegidos
```javascript
// Verificar que tenemos token antes de hacer request protegido
if (pm.request.url.toString().includes("/chess/")) {
    pm.test("Token is available", function () {
        pm.expect(pm.environment.get("token")).to.not.be.undefined;
    });
}
```

---

## 📋 **PASO 7: VALIDACIONES AVANZADAS**

### 7.1 Test para Endpoint de Games
```javascript
pm.test("Game data structure is correct", function () {
    if (pm.response.code === 200) {
        var jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('game_id');
        pm.expect(jsonData).to.have.property('white');
        pm.expect(jsonData).to.have.property('black');
        pm.expect(jsonData).to.have.property('moves');
        pm.expect(jsonData.moves).to.be.an('array');
    }
});
```

### 7.2 Test para Login
```javascript
pm.test("Login response has required fields", function () {
    if (pm.response.code === 200) {
        var jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('access_token');
        pm.expect(jsonData).to.have.property('user');
        pm.expect(jsonData.user).to.have.property('username');
        pm.expect(jsonData.user).to.have.property('role');
    }
});
```

---

## 📋 **PASO 8: EJECUTAR Y ANALIZAR RESULTADOS**

### 8.1 Métricas a Monitorear
- ✅ **Passed Tests**: Número de pruebas exitosas
- ❌ **Failed Tests**: Pruebas fallidas  
- ⏱️ **Average Response Time**: Tiempo promedio
- 📊 **Status Code Distribution**: Códigos de respuesta

### 8.2 Exportar Resultados
1. Después de correr las pruebas, click "Export Results"
2. Seleccionar formato (JSON/CSV)
3. Analizar métricas de rendimiento

---

## 🔧 **TROUBLESHOOTING**

### Problemas Comunes:
1. **Server not running**: Verificar que FastAPI esté en puerto 8000
2. **Token expired**: Re-ejecutar login requests
3. **CSV format issues**: Verificar encoding UTF-8
4. **Environment not selected**: Seleccionar "Chess Trainer Local"

### Variables de Debug:
```javascript
console.log("Current token:", pm.environment.get("token"));
console.log("Base URL:", pm.environment.get("base_url"));
console.log("Response time:", pm.response.responseTime);
```

---

## ✅ **CHECKLIST FINAL**

- [ ] Backend FastAPI corriendo en puerto 8000
- [ ] Environment "Chess Trainer Local" creado y seleccionado  
- [ ] Collection "Chess Trainer API Tests" creada
- [ ] Archivo CSV `postman_test_cases.csv` importado
- [ ] Scripts de test configurados
- [ ] Orden de ejecución planificado
- [ ] Variables de token configuradas
- [ ] Runner configurado con delay apropiado

**¡Listo para ejecutar 23 casos de prueba automatizados!** 🚀