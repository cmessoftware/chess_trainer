# Guía de OCR para PDFs Escaneados

## ¿Cuándo necesitas OCR?

Si tus libros de ajedrez son:
- Escaneos de libros físicos
- PDFs sin texto seleccionable
- Imágenes convertidas a PDF

## Solución: Tesseract + pytesseract

### Instalación

#### Windows
```powershell
# 1. Instalar Tesseract OCR
# Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
# O con chocolatey:
choco install tesseract

# 2. Agregar al PATH (si no está)
# C:\Program Files\Tesseract-OCR\

# 3. Instalar librerías Python
pip install pytesseract pillow pdf2image poppler-utils
```

#### Dependencias Adicionales
```powershell
# Instalar Poppler para pdf2image
# Descargar desde: https://github.com/oschwartz10612/poppler-windows/releases/
# Extraer y agregar bin\ al PATH
```

### Actualizar requirements_ai_coach.txt

Agregar:
```
pytesseract==0.3.10     # OCR engine wrapper
pdf2image==1.17.0       # Convert PDF pages to images
pillow==10.4.0          # Image processing
```

### Código de Ejemplo

```python
import pytesseract
from pdf2image import convert_from_path
from pathlib import Path

def extract_text_with_ocr(pdf_path: Path) -> str:
    """Extrae texto de PDF escaneado usando OCR"""
    
    # Convertir PDF a imágenes
    images = convert_from_path(pdf_path, dpi=300)
    
    # OCR en cada página
    text_parts = []
    for i, image in enumerate(images):
        print(f"Procesando página {i+1}/{len(images)}...")
        text = pytesseract.image_to_string(image, lang='spa')  # 'spa' para español
        text_parts.append(text)
    
    return "\n\n".join(text_parts)
```

### Integración en pdf_processor.py

```python
def extract_text_from_pdf(self, pdf_path: Path, method: str = "pdfplumber") -> str:
    """Intenta extracción normal, si falla usa OCR"""
    
    try:
        # Intentar método normal
        text = self._extract_with_pdfplumber(pdf_path)
        
        # Verificar si extrajo suficiente texto
        if len(text.strip()) < 100:
            logger.warning(f"Poco texto extraído, intentando OCR...")
            text = self._extract_with_ocr(pdf_path)
        
        return text
    except Exception as e:
        logger.error(f"Error: {e}, intentando OCR como último recurso")
        return self._extract_with_ocr(pdf_path)
```

## ⚠️ Consideraciones

### Rendimiento
- **OCR es LENTO**: 1-5 segundos por página
- 100 páginas = 2-10 minutos por libro
- 44 libros con OCR = varias horas

### Calidad
- **Depende de la calidad del escaneo**
- Resolución baja → errores de OCR
- PDFs con notación descriptiva antigua → más difícil

### Idiomas
```python
# Para libros en español
pytesseract.image_to_string(image, lang='spa')

# Para libros en inglés
pytesseract.image_to_string(image, lang='eng')

# Para ambos
pytesseract.image_to_string(image, lang='spa+eng')
```

## 🎯 Recomendación

1. **Primero intenta sin OCR** con los PDFs actuales
2. **Si algunos PDFs no funcionan**, identifícalos
3. **Instala OCR solo si es necesario**
4. **Procesa PDFs digitales y escaneados por separado**

## Verificación Rápida

```python
# Script para verificar qué PDFs necesitan OCR
import PyPDF2
from pathlib import Path

def check_pdf_type(pdf_path):
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = reader.pages[0].extract_text()
        
        if len(text.strip()) < 50:
            print(f"❌ ESCANEADO (necesita OCR): {pdf_path.name}")
        else:
            print(f"✅ DIGITAL (funciona): {pdf_path.name}")

# Verificar todos
for pdf in Path("data/chess_books/raw").glob("**/*.pdf"):
    check_pdf_type(pdf)
```
