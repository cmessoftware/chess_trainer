#!/usr/bin/env python
"""Script para eliminar referencias a test_auth de main.py"""

filepath = "src/api/main.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Eliminar test_auth del import
content = content.replace("    test_auth,\n", "")

# Eliminar include_router de test_auth
content = content.replace('app.include_router(test_auth.router, prefix="/test", tags=["testing"])\n', '')

#  Agregar include de analysis router si no está
if 'app.include_router(analysis.router' not in content:
    # Buscar la línea de notifications y agregar analysis después
    content = content.replace(
        'app.include_router(notifications.router, tags=["notifications"])',
        'app.include_router(notifications.router, tags=["notifications"])\napp.include_router(analysis.router, tags=["analysis", "ml", "shap"])'
    )

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ main.py corregido:")
print("   - test_auth import eliminado")
print("   - test_auth router eliminado")
print("   - analysis router agregado")
