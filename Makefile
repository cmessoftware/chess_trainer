.PHONY: extract push clean

extract:
	@echo "🔍 Extrayendo #TODOs del código..."
	python3 /app/src/tools/extract_todos.py /app/src

push:
	@echo "📤 Subiendo issues a GitHub..."
	python3 /app/src/tools/create_issues_from_json.py

clean:
	@echo "🧹 Borrando archivo de issues..."
	rm -f issues_todo.json
