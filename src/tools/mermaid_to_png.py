#!/usr/bin/env python3
"""
🎨 Mermaid to PNG Converter - Frontend Roadmap Edition
Convierte diagramas Mermaid a imágenes PNG, con soporte específico para el roadmap frontend.

Usage:
    python mermaid_to_png.py --from-roadmap-frontend --output diagram.png
    python mermaid_to_png.py --text "graph TD; A-->B" --output simple.png
    python mermaid_to_png.py --file diagram.mmd --output diagram.png

Requirements:
    pip install requests pillow

Author: ChessTrainer Project
Date: 15 enero 2026
"""

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

import requests
from PIL import Image
from io import BytesIO


class MermaidToPNGConverter:
    """Convierte código Mermaid a imágenes PNG"""

    def __init__(self):
        self.api_base = "https://mermaid.ink"
        self.temp_dir = Path("temp_mermaid")
        self.temp_dir.mkdir(exist_ok=True)

    def convert_via_api(
        self, mermaid_code: str, output_path: str, theme: str = "default"
    ) -> bool:
        """
        Convierte Mermaid a PNG usando la API de mermaid.ink

        Args:
            mermaid_code: Código Mermaid
            output_path: Ruta de salida para la imagen PNG
            theme: Tema (default, dark, forest, neutral)

        Returns:
            bool: True si la conversión fue exitosa
        """
        try:
            print(f"🌐 Convirtiendo via API de mermaid.ink...")
            print(f"📊 Código Mermaid ({len(mermaid_code)} caracteres)")

            # Codificar el diagrama Mermaid
            encoded = base64.b64encode(mermaid_code.encode("utf-8")).decode("ascii")

            # Construir URL para PNG
            url = f"{self.api_base}/img/{encoded}?theme={theme}"

            print(f"📡 URL generada: {url[:100]}...")

            # Hacer request
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Verificar que es una imagen
            if not response.headers.get("content-type", "").startswith("image/"):
                print(
                    f"❌ Respuesta no es una imagen: {response.headers.get('content-type')}"
                )
                return False

            # Guardar imagen directamente como PNG
            with open(output_path, "wb") as f:
                f.write(response.content)

            print(f"✅ Imagen PNG guardada: {output_path}")

            # Verificar tamaño del archivo
            if os.path.exists(output_path):
                size = os.path.getsize(output_path)
                print(f"📏 Tamaño: {size:,} bytes")

                # Verificar que la imagen se puede abrir
                try:
                    with Image.open(output_path) as img:
                        print(f"🖼️ Dimensiones: {img.size[0]}x{img.size[1]} pixels")
                        print(f"🎨 Formato: {img.format}, Modo: {img.mode}")
                except Exception as e:
                    print(f"⚠️ Advertencia: No se puede verificar la imagen: {e}")

            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ Error de red: {e}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def extract_mermaid_from_roadmap(self, roadmap_path: str) -> Optional[str]:
        """
        Extrae código Mermaid del archivo roadmap

        Args:
            roadmap_path: Ruta al archivo roadmap.md

        Returns:
            str: Código Mermaid extraído o None si no se encuentra
        """
        try:
            with open(roadmap_path, "r", encoding="utf-8") as f:
                content = f.read()

            print(f"📄 Leyendo roadmap: {roadmap_path}")

            # Buscar bloque mermaid (con diferentes patrones)
            patterns = [
                r"```mermaid\n(.*?)\n```",  # Patrón estándar
                r"```mermaid(.*?)```",  # Sin saltos de línea
                r"```\nmermaid(.*?)\n```",  # Variante con salto
            ]

            mermaid_code = None
            for pattern in patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    mermaid_code = matches[0].strip()
                    break

            if mermaid_code:
                print(f"📊 Código Mermaid extraído ({len(mermaid_code)} caracteres)")
                print(f"🔍 Primeras líneas:")
                for line in mermaid_code.split("\n")[:5]:
                    print(f"    {line}")
                if len(mermaid_code.split("\n")) > 5:
                    print("    ...")
                return mermaid_code
            else:
                print("❌ No se encontró código Mermaid en el roadmap")
                print("🔍 Buscando en el contenido...")

                # Mostrar fragmentos que podrían contener mermaid
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "mermaid" in line.lower() or "graph" in line or "```" in line:
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        print(f"    Líneas {start+1}-{end}:")
                        for j in range(start, end):
                            marker = ">>>" if j == i else "   "
                            print(f"    {marker} {j+1:3d}: {lines[j]}")
                        print()

                return None

        except Exception as e:
            print(f"❌ Error leyendo roadmap: {e}")
            return None

    def get_frontend_roadmap_mermaid(self) -> str:
        """
        Retorna el código Mermaid específico del roadmap frontend
        """
        return """graph TB
    subgraph "Frontend (Streamlit)"
        A[app.py - Main Navigation]
        B[games_browser.py - Database Viewer]
        C[upload_pgn_advanced.py - PGN Upload]
        D[analysis_dashboard.py - ML Analysis]
    end
    
    subgraph "Backend APIs"
        E[FastAPI - Error Classifier]
        F[Flask - Survivorship Analysis]
        G[New FastAPI - Game Management]
    end
    
    subgraph "Database"
        H[(PostgreSQL)]
        I[(games table)]
        J[(features table)]
        K[(analyzed_tacticals)]
    end
    
    A --> B
    A --> C
    A --> D
    B --> G
    C --> G
    D --> E
    D --> F
    G --> H
    E --> H
    F --> H"""


def main():
    parser = argparse.ArgumentParser(
        description="🎨 Convierte diagramas Mermaid a imágenes PNG"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", help="Archivo .mmd con código Mermaid")
    group.add_argument("--text", "-t", help="Código Mermaid como string")
    group.add_argument(
        "--from-roadmap", action="store_true", help="Extraer del roadmap especificado"
    )
    group.add_argument(
        "--from-roadmap-frontend",
        action="store_true",
        help="Usar el diagrama del roadmap frontend",
    )

    parser.add_argument(
        "--output", "-o", required=True, help="Archivo de salida (.png)"
    )
    parser.add_argument(
        "--theme",
        choices=["default", "dark", "forest", "neutral"],
        default="default",
        help="Tema del diagrama (default: default)",
    )
    parser.add_argument(
        "--roadmap-path",
        default="../../docs/ROADMAP_FRONT_CHESS_TRAINER.md",
        help="Ruta al archivo roadmap (para --from-roadmap)",
    )

    args = parser.parse_args()

    converter = MermaidToPNGConverter()

    # Obtener código Mermaid
    mermaid_code = None

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                mermaid_code = f.read()
        except Exception as e:
            print(f"❌ Error leyendo archivo {args.file}: {e}")
            sys.exit(1)

    elif args.text:
        mermaid_code = args.text

    elif args.from_roadmap_frontend:
        print("📊 Usando diagrama del roadmap frontend...")
        mermaid_code = converter.get_frontend_roadmap_mermaid()

    elif args.from_roadmap:
        roadmap_path = Path(__file__).parent / args.roadmap_path
        mermaid_code = converter.extract_mermaid_from_roadmap(str(roadmap_path))
        if not mermaid_code:
            sys.exit(1)

    # Asegurarse de que el directorio de salida existe
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convertir
    print(f"🎨 Iniciando conversión a PNG...")
    print(f"   🎨 Tema: {args.theme}")
    print(f"   📁 Salida: {args.output}")

    success = converter.convert_via_api(mermaid_code, args.output, args.theme)

    if success:
        print(f"🎉 Conversión a PNG completada exitosamente!")
        print(f"📁 Archivo generado: {os.path.abspath(args.output)}")
        sys.exit(0)
    else:
        print(f"❌ La conversión falló")
        sys.exit(1)


if __name__ == "__main__":
    main()


"""
📖 Ejemplos de uso:

# Convertir el diagrama del roadmap frontend
python mermaid_to_png.py --from-roadmap-frontend --output roadmap_architecture.png

# Convertir con tema oscuro
python mermaid_to_png.py --from-roadmap-frontend --output roadmap_dark.png --theme dark

# Convertir del roadmap actual (intentar extraer)
python mermaid_to_png.py --from-roadmap --output architecture.png

# Convertir archivo específico
python mermaid_to_png.py --file diagrama.mmd --output diagrama.png

# Convertir texto directo
python mermaid_to_png.py --text "graph TD; A-->B; B-->C" --output simple.png

📦 Dependencias:
pip install requests pillow
"""
