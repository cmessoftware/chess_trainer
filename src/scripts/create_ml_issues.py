#!/usr/bin/env python3
"""
Script para crear issues específicos para los items de la tabla ML del README
Utiliza el archivo ml_issues.json como fuente de datos
"""
import json
import sys
import os

# Agregar el directorio de herramientas al path para importar create_issues
sys.path.append('src/tools')

from create_issues import create_issue, add_issue_to_project, get_GITHUB_REPO, gh_login

def create_ml_issues():
    """Crea los issues específicos para ML usando el archivo JSON"""
    
    # Verificar autenticación
    gh_login()
    
    # Obtener repositorio
    repo = get_GITHUB_REPO()
    print(f"🎯 Creando issues para repositorio: {repo}")
    
    # Cargar issues del archivo JSON
    try:
        with open('ml_issues.json', 'r', encoding='utf-8') as f:
            issues_data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo ml_issues.json")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear JSON: {e}")
        return []
    
    created_issues = []
    
    for i, issue_data in enumerate(issues_data, 1):
        title = issue_data['title']
        body = issue_data['body']
        
        print(f"\n🔥 Creando issue {i}/4: {title}")
        
        try:
            # Crear el issue con prioridad alta
            issue_number, issue_id = create_issue(
                repo,
                title,
                body,
                labels=["high-priority", "ml-workflow"],
                priority="high-priority"
            )
            
            print(f"✅ Issue #{issue_number} creado exitosamente")
            
            # Intentar agregar al proyecto (opcional)
            try:
                print(f"📋 Agregando issue #{issue_number} al proyecto...")
                add_issue_to_project(issue_number, labels=["high-priority"])
                print(f"✅ Issue #{issue_number} agregado al proyecto")
            except Exception as project_error:
                print(f"⚠️ No se pudo agregar al proyecto (el issue existe): {project_error}")
            
            # Construir URL del issue
            issue_url = f"https://github.com/{repo}/issues/{issue_number}"
            created_issues.append({
                'number': issue_number,
                'title': title,
                'url': issue_url
            })
            
            print(f"🔗 Issue disponible en: {issue_url}")
            
        except Exception as e:
            print(f"❌ Error al crear issue '{title}': {e}")
            continue
    
    return created_issues

def print_summary(created_issues):
    """Imprime un resumen de los issues creados"""
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN: Se crearon {len(created_issues)} issues")
    print(f"{'='*60}")
    
    for issue in created_issues:
        print(f"#{issue['number']}: {issue['title']}")
        print(f"   🔗 {issue['url']}")
        print()
    
    print("📋 Links para actualizar la tabla del README:")
    print("| Item | Status | Issues # |")
    print("|------|--------|----------|")
    
    items = [
        "Preprocess the data (cleaning, transforming moves into numeric values)",
        "Train a Machine Learning model to predict patterns or errors in games", 
        "Evaluate the model and make adjustments if necessary",
        "Implement the model in your Fast API API and generate recommendations"
    ]
    
    statuses = ["In Progress", "Pending", "Pending", "Pending"]
    
    for i, (item, status) in enumerate(zip(items, statuses)):
        if i < len(created_issues):
            issue_link = f"[#{created_issues[i]['number']}]({created_issues[i]['url']})"
        else:
            issue_link = "#"
        print(f"| {item} | {status} | {issue_link} |")

if __name__ == "__main__":
    print("🚀 Iniciando creación de issues ML para Chess Trainer")
    
    # Crear los issues
    created_issues = create_ml_issues()
    
    if created_issues:
        print_summary(created_issues)
        print("\n✅ ¡Issues creados exitosamente!")
        print("💡 Ahora puedes actualizar la tabla en README.md con los links generados")
    else:
        print("\n❌ No se pudieron crear los issues")
        sys.exit(1)
