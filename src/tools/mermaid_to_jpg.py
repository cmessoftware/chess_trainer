#!/usr/bin/env python3
"""
🎨 Mermaid to JPG Converter
Convierte diagramas Mermaid a imágenes JPG usando múltiples métodos.

Usage:
    python mermaid_to_jpg.py --file diagram.mmd --output diagram.jpg
    python mermaid_to_jpg.py --text "graph TD; A-->B" --output simple.jpg
    python mermaid_to_jpg.py --from-roadmap  # Extrae del roadmap y convierte

Requirements:
    pip install requests pillow
    # Para método CLI (opcional):
    npm install -g @mermaid-js/mermaid-cli

Author: ChessTrainer Project
Date: 29 diciembre 2025
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path
from typing import Optional

import requests
from PIL import Image
from io import BytesIO


class MermaidConverter:
    """Convierte código Mermaid a imágenes JPG"""

    def __init__(self):
        self.api_base = "https://mermaid.ink"
        self.temp_dir = Path("temp_mermaid")
        self.temp_dir.mkdir(exist_ok=True)

    def convert_via_api(
        self,
        mermaid_code: str,
        output_path: str,
        theme: str = "default",
        format: str = "jpg",
    ) -> bool:
        """
        Convierte Mermaid a imagen usando la API de mermaid.ink

        Args:
            mermaid_code: Código Mermaid
            output_path: Ruta de salida para la imagen
            theme: Tema (default, dark, forest, neutral)
            format: Formato de salida (jpg, png, svg)

        Returns:
            bool: True si la conversión fue exitosa
        """
        try:
            print(f"🌐 Convirtiendo via API de mermaid.ink...")

            # Codificar el diagrama Mermaid
            encoded = base64.b64encode(mermaid_code.encode("utf-8")).decode("ascii")

            # Construir URL
            if format.lower() == "jpg":
                url = f"{self.api_base}/img/{encoded}?theme={theme}&format=jpeg"
            else:
                url = f"{self.api_base}/img/{encoded}?theme={theme}"

            print(f"📡 URL: {url[:100]}...")

            # Hacer request
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Guardar imagen
            if format.lower() == "jpg" and response.headers.get(
                "content-type", ""
            ).startswith("image/"):
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Imagen guardada: {output_path}")
                return True
            else:
                # Convertir a JPG si no es JPG
                image = Image.open(BytesIO(response.content))
                if image.mode in ("RGBA", "LA", "P"):
                    # Convertir transparencia a blanco para JPG
                    rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    rgb_image.paste(
                        image, mask=image.split()[-1] if image.mode == "RGBA" else None
                    )
                    image = rgb_image

                image.save(output_path, "JPEG", quality=90)
                print(f"✅ Imagen convertida y guardada: {output_path}")
                return True

        except requests.exceptions.RequestException as e:
            print(f"❌ Error de red: {e}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def convert_via_cli(self, mermaid_code: str, output_path: str) -> bool:
        """
        Convierte Mermaid usando mermaid-cli (mmdc)
        Requiere: npm install -g @mermaid-js/mermaid-cli

        Args:
            mermaid_code: Código Mermaid
            output_path: Ruta de salida

        Returns:
            bool: True si la conversión fue exitosa
        """
        try:
            print("🔧 Convirtiendo via mermaid-cli...")

            # Verificar si mmdc está instalado
            result = subprocess.run(
                ["mmdc", "--version"], capture_output=True, text=True
            )
            if result.returncode != 0:
                print("❌ mermaid-cli no está instalado.")
                print("💡 Instala con: npm install -g @mermaid-js/mermaid-cli")
                return False

            # Crear archivo temporal
            temp_mmd = self.temp_dir / "temp.mmd"
            with open(temp_mmd, "w", encoding="utf-8") as f:
                f.write(mermaid_code)

            # Convertir
            cmd = [
                "mmdc",
                "-i",
                str(temp_mmd),
                "-o",
                output_path,
                "-f",
                "jpeg",
                "-b",
                "white",  # Background blanco
                "--scale",
                "2",  # Mejor resolución
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ Imagen generada: {output_path}")
                # Limpiar archivo temporal
                temp_mmd.unlink()
                return True
            else:
                print(f"❌ Error en mmdc: {result.stderr}")
                return False

        except FileNotFoundError:
            print("❌ mermaid-cli (mmdc) no encontrado.")
            print("💡 Instala con: npm install -g @mermaid-js/mermaid-cli")
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

            # Buscar bloque mermaid
            pattern = r"```mermaid\n(.*?)\n```"
            matches = re.findall(pattern, content, re.DOTALL)

            if matches:
                mermaid_code = matches[0].strip()
                print(f"📊 Código Mermaid extraído ({len(mermaid_code)} caracteres)")
                return mermaid_code
            else:
                print("❌ No se encontró código Mermaid en el roadmap")
                return None

        except Exception as e:
            print(f"❌ Error leyendo roadmap: {e}")
            return None

    def extract_all_mermaid_from_markdown(self, markdown_path: str) -> list:
        """
        Extrae todos los diagramas Mermaid de un archivo markdown

        Args:
            markdown_path: Ruta al archivo markdown

        Returns:
            list: Lista de tuplas (codigo_mermaid, tipo_diagrama)
        """
        try:
            with open(markdown_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Buscar bloques mermaid
            pattern = r"```mermaid\n(.*?)\n```"
            matches = re.findall(pattern, content, re.DOTALL)

            diagrams = []
            for i, match in enumerate(matches):
                mermaid_code = match.strip()
                # Determinar tipo de diagrama
                diagram_type = "diagram"
                if "flowchart" in mermaid_code.lower():
                    diagram_type = "flowchart"
                elif "sequenceDiagram" in mermaid_code:
                    diagram_type = "sequence"
                elif "graph" in mermaid_code.lower():
                    diagram_type = "graph"
                elif "classDiagram" in mermaid_code:
                    diagram_type = "class"

                diagrams.append((mermaid_code, diagram_type, i + 1))
                print(
                    f"📊 Diagrama {i+1} encontrado: {diagram_type} ({len(mermaid_code)} caracteres)"
                )

            print(f"✅ Se encontraron {len(diagrams)} diagramas Mermaid")
            return diagrams

        except Exception as e:
            print(f"❌ Error leyendo markdown: {e}")
            return []

    def generate_all_diagrams_from_markdown(
        self,
        markdown_path: str,
        output_dir: str = "diagrams",
        method: str = "api",
        theme: str = "default",
    ) -> bool:
        """
        Genera imágenes para todos los diagramas Mermaid en un archivo markdown

        Args:
            markdown_path: Ruta al archivo markdown
            output_dir: Directorio de salida para las imágenes
            method: Método de conversión ("api" o "cli")
            theme: Tema para la conversión

        Returns:
            bool: True si todas las conversiones fueron exitosas
        """
        # Crear directorio de salida si no existe
        Path(output_dir).mkdir(exist_ok=True)

        # Extraer todos los diagramas
        diagrams = self.extract_all_mermaid_from_markdown(markdown_path)

        if not diagrams:
            print("❌ No se encontraron diagramas Mermaid")
            return False

        success_count = 0
        total_count = len(diagrams)

        for mermaid_code, diagram_type, index in diagrams:
            # Generar nombre de archivo
            base_name = Path(markdown_path).stem
            output_file = Path(output_dir) / f"{base_name}_{diagram_type}_{index}.jpg"

            print(f"\n🎨 Convirtiendo diagrama {index}/{total_count}: {diagram_type}")

            # Convertir
            if self.convert(mermaid_code, str(output_file), method, theme):
                success_count += 1
                print(f"✅ Guardado: {output_file}")
            else:
                print(f"❌ Error convirtiendo diagrama {index}")

        print(
            f"\n📊 Resumen: {success_count}/{total_count} diagramas convertidos exitosamente"
        )
        return success_count == total_count

    def convert(
        self,
        mermaid_code: str,
        output_path: str,
        method: str = "api",
        theme: str = "default",
    ) -> bool:
        """
        Convierte Mermaid a JPG usando el método especificado

        Args:
            mermaid_code: Código Mermaid
            output_path: Ruta de salida
            method: Método de conversión ("api" o "cli")
            theme: Tema para la conversión

        Returns:
            bool: True si la conversión fue exitosa
        """
        if method == "cli":
            return self.convert_via_cli(mermaid_code, output_path)
        else:
            return self.convert_via_api(mermaid_code, output_path, theme, "jpg")


def main():
    parser = argparse.ArgumentParser(
        description="🎨 Convierte diagramas Mermaid a imágenes JPG"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", help="Archivo .mmd con código Mermaid")
    group.add_argument("--text", "-t", help="Código Mermaid como string")
    group.add_argument(
        "--from-roadmap", action="store_true", help="Extraer del roadmap del proyecto"
    )
    group.add_argument(
        "--from-markdown",
        "-md",
        help="Extraer todos los diagramas de un archivo markdown",
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Archivo de salida (.jpg) - requerido excepto para --from-markdown",
    )
    parser.add_argument(
        "--output-dir",
        "-d",
        default="diagrams",
        help="Directorio de salida para --from-markdown (default: diagrams)",
    )
    parser.add_argument(
        "--method",
        "-m",
        choices=["api", "cli"],
        default="api",
        help="Método de conversión (default: api)",
    )
    parser.add_argument(
        "--theme",
        choices=["default", "dark", "forest", "neutral"],
        default="default",
        help="Tema del diagrama (default: default)",
    )
    parser.add_argument(
        "--roadmap-path",
        default="../../docs/ROADMAP_TECHNICAL.md",
        help="Ruta al archivo roadmap (para --from-roadmap)",
    )

    args = parser.parse_args()

    # Validar argumentos
    if not args.from_markdown and not args.output:
        print("❌ --output es requerido excepto cuando se usa --from-markdown")
        sys.exit(1)

    converter = MermaidConverter()

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

    elif args.from_roadmap:
        roadmap_path = Path(__file__).parent / args.roadmap_path
        mermaid_code = converter.extract_mermaid_from_roadmap(str(roadmap_path))
        if not mermaid_code:
            sys.exit(1)

    elif args.from_markdown:
        # Generar todos los diagramas del archivo markdown
        print(f"🎨 Procesando archivo markdown: {args.from_markdown}")
        success = converter.generate_all_diagrams_from_markdown(
            args.from_markdown, args.output_dir, args.method, args.theme
        )
        sys.exit(0 if success else 1)

    # Convertir diagrama individual
    print(f"🎨 Iniciando conversión...")
    print(f"   📊 Método: {args.method}")
    print(f"   🎨 Tema: {args.theme}")
    print(f"   📁 Salida: {args.output}")

    success = converter.convert(mermaid_code, args.output, args.method, args.theme)

    if success:
        # Verificar tamaño del archivo
        if os.path.exists(args.output):
            size = os.path.getsize(args.output)
            print(f"📏 Tamaño: {size:,} bytes")

        print(f"🎉 Conversión completada exitosamente!")
        sys.exit(0)
    else:
        print(f"❌ La conversión falló")

        # Intentar método alternativo
        alt_method = "cli" if args.method == "api" else "api"
        print(f"🔄 Intentando con método alternativo: {alt_method}")

        success_alt = converter.convert(
            mermaid_code, args.output, alt_method, args.theme
        )
        if success_alt:
            print(f"✅ Conversión exitosa con método alternativo!")
            sys.exit(0)
        else:
            print(f"❌ Ambos métodos fallaron")
            sys.exit(1)


if __name__ == "__main__":
    main()


"""
📖 Ejemplos de uso:

# Convertir del roadmap actual
python mermaid_to_jpg.py --from-roadmap --output architecture.jpg

# Convertir archivo específico
python mermaid_to_jpg.py --file diagrama.mmd --output diagrama.jpg

# Convertir texto directo
python mermaid_to_jpg.py --text "graph TD; A-->B; B-->C" --output simple.jpg

# Extraer todos los diagramas de un markdown (NUEVO)
python mermaid_to_jpg.py --from-markdown readme.md --output-dir img

# Extraer del readme.md del proyecto
python mermaid_to_jpg.py --from-markdown ../tools/readme.md --output-dir diagrams

# Usar tema oscuro
python mermaid_to_jpg.py --from-roadmap --output arch_dark.jpg --theme dark

# Usar CLI en lugar de API
python mermaid_to_jpg.py --from-roadmap --output arch_cli.jpg --method cli

📦 Dependencias:
pip install requests pillow

🛠️ Para método CLI (opcional):
npm install -g @mermaid-js/mermaid-cli
"""
