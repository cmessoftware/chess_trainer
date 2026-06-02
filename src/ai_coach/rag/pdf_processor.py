"""
PDF Processor para extraer y procesar libros de ajedrez
Soporta tanto notación algebraica como descriptiva
Incluye soporte OCR para PDFs escaneados
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
import logging
import time

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image

    # Configurar ruta de Tesseract (Windows)
    import platform

    if platform.system() == "Windows":
        import os

        tesseract_path = (
            r"C:\Users\sergiosal\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
        )
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    OCR_AVAILABLE = True
except ImportError:
    pytesseract = None
    convert_from_path = None
    Image = None
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Procesa PDFs de libros de ajedrez y extrae contenido relevante"""

    def __init__(
        self,
        raw_books_dir: str = "data/chess_books/raw",
        processed_dir: str = "data/chess_books/processed",
        checkpoint_file: str = "data/chess_books/processing_checkpoint.json",
        enable_ocr: bool = True,
        ocr_languages: str = "spa+eng",
    ):
        self.raw_books_dir = Path(raw_books_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoint_file = Path(checkpoint_file)
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        self.processed_books = self._load_checkpoint()

        # Configuración OCR
        self.enable_ocr = enable_ocr and OCR_AVAILABLE
        self.ocr_languages = ocr_languages

        if self.enable_ocr:
            logger.info("📸 OCR habilitado para procesar PDFs escaneados")
        elif not OCR_AVAILABLE:
            logger.warning("⚠️ OCR no disponible (falta pytesseract/pdf2image)")

    def extract_text_from_pdf(
        self, pdf_path: Path, method: str = "pdfplumber", max_pages: int = None
    ) -> str:
        """
        Extrae texto de un PDF usando diferentes métodos
        Intenta OCR automáticamente si el texto extraído es muy corto

        Args:
            pdf_path: Ruta al archivo PDF
            method: 'pdfplumber', 'pypdf2', o 'ocr'
            max_pages: Número máximo de páginas para OCR (None = todas)

        Returns:
            Texto extraído del PDF
        """
        logger.info(f"Extrayendo texto de {pdf_path.name} usando {method}")

        try:
            if method == "ocr":
                # Forzar OCR
                return self._extract_with_ocr(pdf_path, max_pages=max_pages)
            elif method == "pdfplumber" and pdfplumber:
                text = self._extract_with_pdfplumber(pdf_path)
            elif method == "pypdf2" and PyPDF2:
                text = self._extract_with_pypdf2(pdf_path)
            else:
                raise ValueError(
                    f"Método {method} no disponible o librería no instalada"
                )

            # Detección automática de PDF escaneado (poco texto extraído)
            if len(text.strip()) < 100 and self.enable_ocr:
                logger.warning(
                    f"Texto extraído muy corto (<100 chars), intentando OCR..."
                )
                return self._extract_with_ocr(pdf_path, max_pages=max_pages)

            return text

        except Exception as e:
            logger.error(f"Error extrayendo texto de {pdf_path}: {e}")
            # Intentar método alternativo
            if method == "pdfplumber" and PyPDF2:
                logger.info("Intentando con PyPDF2 como fallback...")
                text = self._extract_with_pypdf2(pdf_path)
                if len(text.strip()) < 100 and self.enable_ocr:
                    logger.warning("Poco texto, intentando OCR...")
                    return self._extract_with_ocr(pdf_path, max_pages=max_pages)
                return text
            elif method == "pypdf2" and pdfplumber:
                logger.info("Intentando con pdfplumber como fallback...")
                text = self._extract_with_pdfplumber(pdf_path)
                if len(text.strip()) < 100 and self.enable_ocr:
                    logger.warning("Poco texto, intentando OCR...")
                    return self._extract_with_ocr(pdf_path, max_pages=max_pages)
                return text
            elif self.enable_ocr:
                logger.warning(
                    "Todos los métodos fallaron, intentando OCR como último recurso..."
                )
                return self._extract_with_ocr(pdf_path, max_pages=max_pages)
            else:
                raise

    def _extract_with_pdfplumber(self, pdf_path: Path) -> str:
        """Extrae texto usando pdfplumber (mejor calidad)"""
        with pdfplumber.open(pdf_path) as pdf:
            text_parts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n\n".join(text_parts)

    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """Extrae texto usando PyPDF2 (fallback)"""
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n\n".join(text_parts)

    def _extract_with_ocr(self, pdf_path: Path, max_pages: int = None) -> str:
        """
        Extrae texto de PDF escaneado usando OCR (Tesseract)
        Procesa en lotes pequeños para evitar MemoryError

        Args:
            pdf_path: Ruta al PDF escaneado
            max_pages: Número máximo de páginas a procesar (None = todas)

        Returns:
            Texto extraído via OCR
        """
        if not OCR_AVAILABLE:
            logger.error(
                "OCR no disponible. Instala: pip install pytesseract pdf2image pillow"
            )
            return ""

        logger.info(f"📸 Iniciando OCR para {pdf_path.name}...")
        start_time = time.time()

        try:
            # Detectar total de páginas sin cargar todo el PDF
            from pdf2image.pdf2image import pdfinfo_from_path

            info = pdfinfo_from_path(pdf_path)
            total_pages = info.get("Pages", 0)
            pages_to_process = min(total_pages, max_pages) if max_pages else total_pages

            logger.info(
                f"   Total de páginas: {total_pages} (procesando {pages_to_process})"
            )

            # Procesar en lotes de 5 páginas para evitar MemoryError
            batch_size = 5
            text_parts = []

            for batch_start in range(1, pages_to_process + 1, batch_size):
                batch_end = min(batch_start + batch_size - 1, pages_to_process)

                logger.info(
                    f"   📄 Procesando lote: páginas {batch_start}-{batch_end}/{pages_to_process}"
                )

                # Convertir solo este lote (DPI 200 = buen balance calidad/memoria)
                images = convert_from_path(
                    pdf_path,
                    dpi=200,
                    first_page=batch_start,
                    last_page=batch_end,
                )

                # OCR en cada página del lote
                for i, image in enumerate(images, batch_start):
                    page_start = time.time()

                    try:
                        # Ejecutar OCR con configuración optimizada
                        text = pytesseract.image_to_string(
                            image,
                            lang=self.ocr_languages,
                            config="--psm 1",  # PSM 1 = Automatic page segmentation with OSD
                        )
                        text_parts.append(text)

                        page_time = time.time() - page_start
                        chars = len(text)
                        logger.info(
                            f"   ✅ Página {i}/{pages_to_process} procesada en {page_time:.1f}s ({chars} chars)"
                        )

                    except Exception as e:
                        logger.warning(f"   ⚠️ Error en página {i}: {e}")
                        continue

                # Liberar memoria del lote
                del images

            full_text = "\n\n".join(text_parts)
            total_time = time.time() - start_time

            logger.info(
                f"📸 OCR completado en {total_time:.1f}s - {len(full_text)} caracteres extraídos"
            )

            return full_text

        except Exception as e:
            logger.error(f"Error en OCR de {pdf_path.name}: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return ""

    def detect_notation_type(self, text: str) -> str:
        """
        Detecta el tipo de notación predominante en el texto

        Returns:
            'algebraic' o 'descriptive'
        """
        # Patrones de notación algebraica: e4, Nf3, Qxd5, O-O
        algebraic_pattern = r"\b[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8][+#]?\b"

        # Patrones de notación descriptiva: P-K4, N-KB3, PxP
        descriptive_pattern = r"\b[KQRBN]?-?[KQ]?[RBN]?[1-8]?\b"

        algebraic_matches = len(re.findall(algebraic_pattern, text))
        # Descriptiva es más difícil de detectar sin falsos positivos
        descriptive_keywords = ["P-K4", "N-KB3", "B-B4", "P-Q4", "Kt-KB3"]
        descriptive_matches = sum(1 for kw in descriptive_keywords if kw in text)

        if algebraic_matches > descriptive_matches * 3:
            return "algebraic"
        elif descriptive_matches > 5:
            return "descriptive"
        else:
            return "algebraic"  # Default moderno

    def chunk_text(
        self, text: str, chunk_size: int = 1000, overlap: int = 200
    ) -> List[Dict[str, str]]:
        """
        Divide el texto en chunks con overlap para RAG

        Args:
            text: Texto a dividir
            chunk_size: Tamaño máximo del chunk (caracteres)
            overlap: Overlap entre chunks

        Returns:
            Lista de dicts con {text, metadata}
        """
        # Limpiar texto
        text = self._clean_text(text)

        # Dividir en párrafos primero
        paragraphs = text.split("\n\n")

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(
                        {
                            "text": current_chunk.strip(),
                            "notation_type": self.detect_notation_type(current_chunk),
                        }
                    )
                # Empezar nuevo chunk con overlap
                if overlap > 0 and chunks:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + para + "\n\n"
                else:
                    current_chunk = para + "\n\n"

        # Agregar último chunk
        if current_chunk:
            chunks.append(
                {
                    "text": current_chunk.strip(),
                    "notation_type": self.detect_notation_type(current_chunk),
                }
            )

        return chunks

    def _clean_text(self, text: str) -> str:
        """Limpia el texto extraído del PDF"""
        # Eliminar headers/footers repetitivos (números de página, etc.)
        text = re.sub(r"\n\d+\n", "\n", text)

        # Eliminar espacios múltiples
        text = re.sub(r" +", " ", text)

        # Eliminar líneas vacías múltiples
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _load_checkpoint(self) -> Dict[str, Dict]:
        """Carga el archivo de checkpoint con libros procesados"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(
                    f"Checkpoint cargado: {len(data.get('processed_books', {}))} libros ya procesados"
                )
                return data.get("processed_books", {})
            except Exception as e:
                logger.warning(f"Error cargando checkpoint: {e}")
                return {}
        return {}

    def _save_checkpoint(self, book_name: str, chunks_count: int, success: bool = True):
        """Guarda el progreso de un libro procesado"""
        self.processed_books[book_name] = {
            "processed_at": datetime.now().isoformat(),
            "chunks_count": chunks_count,
            "success": success,
        }

        checkpoint_data = {
            "last_updated": datetime.now().isoformat(),
            "processed_books": self.processed_books,
        }

        try:
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Checkpoint actualizado para: {book_name}")
        except Exception as e:
            logger.warning(f"Error guardando checkpoint: {e}")

    def reset_checkpoint(self):
        """Elimina el checkpoint para forzar reprocesamiento completo"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        self.processed_books = {}
        logger.info("Checkpoint reseteado")

    def is_book_processed(self, pdf_path: Path) -> bool:
        """Verifica si un libro ya fue procesado exitosamente"""
        book_name = pdf_path.stem
        return book_name in self.processed_books and self.processed_books[
            book_name
        ].get("success", False)

    def process_book(
        self,
        pdf_path: Path,
        save_processed: bool = True,
        force_reprocess: bool = False,
        max_pages: int = None,
    ) -> List[Dict[str, str]]:
        """
        Procesa un libro completo: extrae texto, detecta notación, hace chunking

        Args:
            pdf_path: Ruta al PDF
            save_processed: Si guardar el texto procesado
            force_reprocess: Forzar reprocesamiento aunque esté en checkpoint
            max_pages: Número máximo de páginas para OCR (None = todas)

        Returns:
            Lista de chunks listos para ChromaDB
        """
        book_name = pdf_path.stem

        # Verificar checkpoint
        if not force_reprocess and self.is_book_processed(pdf_path):
            logger.info(f"⏭️  Saltando {pdf_path.name} (ya procesado)")
            # Retornar chunks vacíos, se recuperarán de ChromaDB si es necesario
            return []

        logger.info(f"📖 Procesando libro: {pdf_path.name}")

        # Extraer texto
        try:
            text = self.extract_text_from_pdf(pdf_path, max_pages=max_pages)
        except Exception as e:
            logger.error(f"Error extrayendo texto de {pdf_path.name}: {e}")
            self._save_checkpoint(book_name, 0, success=False)
            return []

        if not text or len(text) < 100:
            logger.warning(f"Texto extraído muy corto o vacío para {pdf_path.name}")
            self._save_checkpoint(book_name, 0, success=False)
            return []

        # Detectar notación
        notation_type = self.detect_notation_type(text)
        logger.info(f"Notación detectada: {notation_type}")

        # Hacer chunking
        chunks = self.chunk_text(text)

        # Agregar metadata del libro
        for chunk in chunks:
            chunk["source"] = book_name
            chunk["source_type"] = "book"

        # Guardar texto procesado
        if save_processed:
            processed_path = self.processed_dir / f"{book_name}.txt"
            try:
                with open(processed_path, "w", encoding="utf-8") as f:
                    f.write(text)
                logger.info(f"Texto procesado guardado en {processed_path}")
            except Exception as e:
                logger.warning(f"Error guardando texto procesado: {e}")

        # Guardar checkpoint exitoso
        self._save_checkpoint(book_name, len(chunks), success=True)

        logger.info(f"✅ Generados {len(chunks)} chunks de {pdf_path.name}")
        return chunks

    def process_all_books(
        self, force_reprocess: bool = False, max_pages: int = None
    ) -> List[Dict[str, str]]:
        """
        Procesa todos los PDFs en el directorio raw (recursivamente en subcarpetas)

        Args:
            force_reprocess: Forzar reprocesamiento de todos los libros
            max_pages: Número máximo de páginas por libro para OCR (None = todas)

        Returns:
            Lista de todos los chunks de todos los libros
        """
        all_chunks = []
        # Búsqueda recursiva en todas las subcarpetas
        pdf_files = list(self.raw_books_dir.glob("**/*.pdf"))

        if not pdf_files:
            logger.warning(f"No se encontraron PDFs en {self.raw_books_dir}")
            return []

        # Estadísticas
        total_books = len(pdf_files)
        already_processed = sum(1 for pdf in pdf_files if self.is_book_processed(pdf))
        to_process = (
            total_books - already_processed if not force_reprocess else total_books
        )

        logger.info(f"📚 Total de libros: {total_books}")
        if not force_reprocess and already_processed > 0:
            logger.info(f"✅ Ya procesados: {already_processed}")
            logger.info(f"🔄 Por procesar: {to_process}")

        if force_reprocess:
            logger.info("🔄 Forzando reprocesamiento de todos los libros")

        for i, pdf_path in enumerate(pdf_files, 1):
            try:
                logger.info(f"\n[{i}/{total_books}] {pdf_path.name}")
                chunks = self.process_book(
                    pdf_path, force_reprocess=force_reprocess, max_pages=max_pages
                )
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"❌ Error procesando {pdf_path.name}: {e}")
                continue

        logger.info(
            f"\n📊 Total de chunks generados en esta ejecución: {len(all_chunks)}"
        )
        return all_chunks


# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
