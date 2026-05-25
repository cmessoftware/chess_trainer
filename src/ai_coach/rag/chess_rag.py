"""
Sistema RAG (Retrieval Augmented Generation) para conocimiento de ajedrez
Usa ChromaDB + SentenceTransformers para recuperación de información
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Deshabilitar telemetría de ChromaDB completamente
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Silenciar logs de telemetría de ChromaDB
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)


class ChessRAG:
    """
    Sistema RAG para conocimiento de ajedrez
    Almacena y recupera información de libros, aperturas, tácticas, etc.
    """

    def __init__(
        self,
        collection_name: str = "chess_knowledge",
        persist_directory: str = "data/chess_books/chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Inicializa el sistema RAG

        Args:
            collection_name: Nombre de la colección en ChromaDB
            persist_directory: Directorio para persistir la DB
            embedding_model: Modelo de embeddings (SentenceTransformers)
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"Inicializando ChessRAG con modelo {embedding_model}")

        # Inicializar ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False, allow_reset=True  # Deshabilitar telemetría
            ),
        )

        # Cargar modelo de embeddings
        logger.info("Cargando modelo de embeddings...")
        self.embedding_model = SentenceTransformer(embedding_model)
        logger.info(f"Modelo {embedding_model} cargado")

        # Obtener o crear colección
        try:
            self.collection = self.client.get_collection(name=collection_name)
            count = self.collection.count()
            logger.info(f"Colección '{collection_name}' cargada con {count} documentos")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Chess knowledge from books and databases"},
            )
            logger.info(f"Colección '{collection_name}' creada")

    def add_documents(self, chunks: List[Dict[str, str]], batch_size: int = 100):
        """
        Agrega documentos (chunks) a la base de conocimiento

        Args:
            chunks: Lista de dicts con 'text' y metadata
            batch_size: Tamaño del batch para inserción
        """
        if not chunks:
            logger.warning("No hay chunks para agregar")
            return

        logger.info(f"Agregando {len(chunks)} chunks a ChromaDB...")

        # Procesar en batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]

            # Extraer textos para embeddings
            texts = [chunk["text"] for chunk in batch]

            # Generar embeddings
            embeddings = self.embedding_model.encode(texts).tolist()

            # Preparar IDs y metadata
            ids = [f"doc_{self.collection.count() + j}" for j in range(len(batch))]
            metadatas = [
                {
                    "source": chunk.get("source", "unknown"),
                    "source_type": chunk.get("source_type", "book"),
                    "notation_type": chunk.get("notation_type", "algebraic"),
                }
                for chunk in batch
            ]

            # Insertar en ChromaDB
            self.collection.add(
                documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids
            )

            logger.info(f"Batch {i//batch_size + 1}: {len(batch)} chunks agregados")

        total = self.collection.count()
        logger.info(f"✅ Total de documentos en colección: {total}")

    def retrieve_knowledge(
        self, query: str, n_results: int = 5, filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Recupera conocimiento relevante para una consulta

        Args:
            query: Pregunta o tema a buscar
            n_results: Número de resultados a devolver
            filter_metadata: Filtros opcionales (ej: {"source": "kasparov_book"})

        Returns:
            Lista de documentos relevantes con metadata
        """
        logger.info(f"Buscando: '{query}' (top {n_results})")

        # Generar embedding de la query
        query_embedding = self.embedding_model.encode(query).tolist()

        # Buscar en ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
        )

        # Formatear resultados
        retrieved_docs = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                retrieved_docs.append(
                    {
                        "text": doc,
                        "metadata": results["metadatas"][0][i],
                        "distance": (
                            results["distances"][0][i]
                            if "distances" in results
                            else None
                        ),
                    }
                )

        logger.info(f"Recuperados {len(retrieved_docs)} documentos")
        return retrieved_docs

    def get_context_for_prompt(
        self, query: str, n_results: int = 3, max_context_length: int = 2000
    ) -> str:
        """
        Obtiene contexto formateado para inyectar en un prompt de LLM

        Args:
            query: Consulta del usuario
            n_results: Número de documentos a recuperar
            max_context_length: Longitud máxima del contexto (caracteres)

        Returns:
            Contexto formateado para el prompt
        """
        docs = self.retrieve_knowledge(query, n_results=n_results)

        if not docs:
            return "No se encontró información relevante en la base de conocimiento."

        # Construir contexto
        context_parts = ["CONOCIMIENTO RELEVANTE:\n"]
        current_length = len(context_parts[0])

        for i, doc in enumerate(docs, 1):
            source = doc["metadata"].get("source", "unknown")
            text = doc["text"]

            doc_part = f"\n[Fuente {i}: {source}]\n{text}\n"

            if current_length + len(doc_part) > max_context_length:
                break

            context_parts.append(doc_part)
            current_length += len(doc_part)

        context = "".join(context_parts)
        context += f"\n---\nFuentes consultadas: {len(docs)}\n"

        return context

    def reset_collection(self):
        """Elimina todos los documentos de la colección (uso con precaución)"""
        logger.warning(f"Reseteando colección '{self.collection_name}'")
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Chess knowledge from books and databases"},
        )
        logger.info("Colección reseteada")

    def get_stats(self) -> Dict:
        """Obtiene estadísticas de la base de conocimiento"""
        count = self.collection.count()

        # Obtener muestra de metadata
        sample = self.collection.get(limit=min(100, count))
        sources = set()
        notation_types = {"algebraic": 0, "descriptive": 0}

        if sample["metadatas"]:
            for meta in sample["metadatas"]:
                sources.add(meta.get("source", "unknown"))
                notation = meta.get("notation_type", "algebraic")
                notation_types[notation] = notation_types.get(notation, 0) + 1

        return {
            "total_documents": count,
            "unique_sources": len(sources),
            "sources": list(sources),
            "notation_types": notation_types,
            "collection_name": self.collection_name,
            "persist_directory": str(self.persist_directory),
        }


# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
