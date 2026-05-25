#!/usr/bin/env python3
"""
Convertidor automático de reportes MD a PDF
Convierte todos los reportes de ajedrez a PDF con formato mejorado
"""

import os
import subprocess
import sys
from pathlib import Path

def check_pandoc():
    """Verificar si pandoc está instalado."""
    try:
        subprocess.run(['pandoc', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def convert_md_to_pdf(md_file, output_dir="reports/pdf"):
    """Convertir archivo MD a PDF con formato mejorado."""
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Nombres de archivos
    input_path = Path(md_file)
    output_filename = input_path.stem + ".pdf"
    output_path = Path(output_dir) / output_filename
    
    # Comando pandoc con formato mejorado
    cmd = [
        'pandoc',
        str(input_path),
        '-o', str(output_path),
        '--pdf-engine=wkhtmltopdf',
        '--margin-top=20mm',
        '--margin-bottom=20mm', 
        '--margin-left=20mm',
        '--margin-right=20mm',
        '--enable-local-file-access'
    ]
    
    try:
        print(f"🔄 Convirtiendo: {input_path.name}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ PDF creado: {output_path}")
        return str(output_path)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error convirtiendo {input_path.name}: {e}")
        print(f"   Salida de error: {e.stderr}")
        return None

def convert_reports_to_pdf():
    """Convertir todos los reportes de ajedrez a PDF."""
    
    print("🎯 CHESS TRAINER - CONVERTIDOR MD → PDF")
    print("=" * 50)
    
    # Verificar pandoc
    if not check_pandoc():
        print("❌ Pandoc no encontrado!")
        print("💡 Instalación:")
        print("   - Windows: choco install pandoc")  
        print("   - O descargar: https://pandoc.org/installing.html")
        return
    
    print("✅ Pandoc encontrado")
    
    # Archivos a convertir
    reports_to_convert = [
        "reports/cmess1315_reporte_personal.md",
        "reports/Th3Hound_reporte_personal.md", 
        "reports/REPORTE_INTEGRADO_cmess1315_vs_Th3Hound.md"
    ]
    
    converted_files = []
    
    for report_file in reports_to_convert:
        if os.path.exists(report_file):
            pdf_file = convert_md_to_pdf(report_file)
            if pdf_file:
                converted_files.append(pdf_file)
        else:
            print(f"⚠️  Archivo no encontrado: {report_file}")
    
    # Resumen
    print("\n📊 CONVERSIÓN COMPLETADA")
    print(f"✅ {len(converted_files)} archivos convertidos:")
    for pdf_file in converted_files:
        file_size = os.path.getsize(pdf_file) / 1024  # KB
        print(f"   📄 {Path(pdf_file).name} ({file_size:.1f} KB)")
    
    print(f"\n📁 PDFs guardados en: reports/pdf/")
    
    # Abrir directorio (Windows)
    if sys.platform == "win32" and converted_files:
        try:
            os.startfile("reports/pdf/")
            print("🚀 Directorio de PDFs abierto automáticamente")
        except:
            pass

def convert_single_file(md_file):
    """Convertir un solo archivo MD a PDF."""
    if not check_pandoc():
        print("❌ Pandoc no encontrado! Instalar: choco install pandoc")
        return
        
    if not os.path.exists(md_file):
        print(f"❌ Archivo no encontrado: {md_file}")
        return
        
    pdf_file = convert_md_to_pdf(md_file)
    if pdf_file:
        print(f"🎉 ¡Conversión exitosa! PDF: {pdf_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Convertir archivo específico
        convert_single_file(sys.argv[1])
    else:
        # Convertir todos los reportes
        convert_reports_to_pdf()