# Git Workflow Playbook (Branch + PR)

Este documento define el flujo recomendado cuando `main` tiene push directo deshabilitado.

## Objetivo

- Evitar cambios directos en `main`.
- Trabajar siempre con ramas cortas.
- Integrar via Pull Request (PR) con revisión.

## Flujo estandar

1. Sincronizar `main` local con `origin/main`.
2. Crear rama de trabajo desde `main`.
3. Hacer cambios y commits pequenos.
4. Ejecutar post-commit de versionado (si aplica en este repo).
5. Restaurar `README.md` y `VERSION` si el hook los vuelve a dejar modificados.
6. Push de la rama.
7. Abrir PR hacia `main`.
8. Merge del PR.
9. Borrar rama remota y local.

## Comandos base

```bash
git checkout main
git pull origin main

git checkout -b chore/mi-cambio
# editar archivos...

git add .
git commit -m "chore: descripcion corta"

# ciclo habitual de este repo
git add README.md VERSION
git commit -m "chore: post-commit version sync" || true
git restore README.md VERSION

git push -u origin chore/mi-cambio
```

## Merge y limpieza

Despues de mergear el PR:

```bash
git checkout main
git pull origin main
git branch -d chore/mi-cambio
git push origin --delete chore/mi-cambio
```

## Politica recomendada de proteccion de `main`

- Require pull request before merging.
- Require at least 1 approval.
- Require status checks to pass (si hay CI).
- Disable direct pushes to `main`.
- (Opcional) Restrict who can bypass rules.

## Notas para este repo

- `origin` se considera fuente de verdad.
- `gitea` puede mantenerse sincronizado desde `origin` cuando haga falta.
- Si un `git pull` falla por LFS, usar `fetch` + resolucion controlada, evitando mezclar estados sucios en `main`.
