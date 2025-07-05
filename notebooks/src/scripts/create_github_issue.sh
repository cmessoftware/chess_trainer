#!/bin/bash

# Detectar repo desde git
REPO=$(git config --get remote.origin.url | sed -E 's/.*github.com[/:](.*)\.git/\1/')
if [[ -z "$REPO" ]]; then
    echo "❌ No se detectó un repositorio válido. Asegurate de estar en una carpeta con git."
    exit 1
fi

# Detectar rama actual
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
BRANCH_LABEL=""
if [[ -n "$BRANCH" ]]; then
    read -p "¿Querés usar la rama '$BRANCH' como etiqueta del issue? (s/n): " use_label
    if [[ "$use_label" == "s" || "$use_label" == "S" ]]; then
        if gh label list --repo "$REPO" | grep -q "^$BRANCH\b"; then
            BRANCH_LABEL="--label $BRANCH"
        else
            echo "⚠️  El label '$BRANCH' no existe en el repo. Podés crearlo con:"
            echo "    gh label create \"$BRANCH\" --repo \"$REPO\" --color \"ededed\""
        fi
    fi
fi

echo "📦 Repositorio detectado: $REPO"

# Preguntar si quiere usar vim
read -p "¿Querés usar vim para editar el issue? (s/n): " use_vim

if [[ "$use_vim" == "s" || "$use_vim" == "S" ]]; then
    if ! command -v vim &> /dev/null; then
        echo "❌ vim no está instalado. Instalalo con: apt update && apt install -y vim"
        exit 1
    fi

    TMPFILE=$(mktemp)
    echo "# Línea 1 = Título del issue (sin '#')" > "$TMPFILE"
    echo "# Las demás líneas = Cuerpo del issue" >> "$TMPFILE"
    echo "" >> "$TMPFILE"
    echo "Título del issue..." >> "$TMPFILE"
    echo "" >> "$TMPFILE"
    echo "Descripción del problema o mejora..." >> "$TMPFILE"

    vim "$TMPFILE"

    TITLE=$(head -n 1 "$TMPFILE" | sed 's/^# *//')
    BODY=$(tail -n +2 "$TMPFILE" | sed '/^#/d')

    gh issue create --repo "$REPO" --title "$TITLE" --body "$BODY" $BRANCH_LABEL
    rm "$TMPFILE"

else
    # Modo por consola
    read -p "Título del issue: " title
    echo "Escribí la descripción (Ctrl+D para terminar):"
    body=$(</dev/stdin)

    gh issue create --repo "$REPO" --title "$title" --body "$body" $BRANCH_LABEL
fi
