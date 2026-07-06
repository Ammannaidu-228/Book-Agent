"""
RAG pipeline using LangChain, OpenAI embeddings, and Chroma vector database
This loads the pre-built Chroma index created by init_chroma.py
"""
from ..config import settings
import logging
import os
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG pipeline for semantic book recommendations"""
    
    def __init__(self):
        """Initialize the RAG pipeline"""
        logger.info("Initializing RAG pipeline...")

        try:
            # Validate required API key
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-proj-YOUR"):
                raise ValueError(
                    "OPENAI_API_KEY not configured. Please set a valid OpenAI API key in .env file. "
                    "Get one from: https://platform.openai.com/api-keys"
                )

            # Lazy import heavy libraries only when needed
            from langchain_openai import OpenAIEmbeddings
            from langchain_chroma import Chroma

            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                model=settings.EMBEDDING_MODEL
            )

            # Load pre-built Chroma database
            if not os.path.exists(settings.CHROMA_PERSIST_DIR):
                raise ValueError(
                    f"Chroma database not found at {settings.CHROMA_PERSIST_DIR}\n"
                    "Please run: python -m src.scripts.init_chroma"
                )

            logger.info("Loading Chroma database from %s", os.path.abspath(settings.CHROMA_PERSIST_DIR))
            self.db = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIR,
                embedding_function=self.embeddings,
                collection_name=settings.CHROMA_COLLECTION_NAME,
            )

            self._bootstrap_collection_if_empty()

            logger.info("RAG pipeline initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing RAG pipeline: {e}")
            raise

    def _bootstrap_collection_if_empty(self):
        """Build Chroma from packaged descriptions when deploys lack persisted vectors."""
        try:
            existing_count = self.db._collection.count()
            if existing_count > 0:
                return

            if not settings.AUTO_BOOTSTRAP_CHROMA:
                logger.warning("Chroma collection is empty and AUTO_BOOTSTRAP_CHROMA is disabled")
                return

            descriptions_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "tagged_description.txt"
            if not descriptions_path.exists():
                logger.warning("Chroma collection is empty and %s was not found", descriptions_path)
                return

            logger.warning(
                "Chroma collection is empty; bootstrapping vectors from %s. "
                "This can take a few minutes on first deploy.",
                descriptions_path,
            )

            texts = [
                line.strip()
                for line in descriptions_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            batch_size = max(1, settings.CHROMA_BOOTSTRAP_BATCH_SIZE)
            for start in range(0, len(texts), batch_size):
                batch = texts[start:start + batch_size]
                ids = [
                    text.split(maxsplit=1)[0] if text.split(maxsplit=1) else str(start + offset)
                    for offset, text in enumerate(batch)
                ]
                self.db.add_texts(texts=batch, ids=ids)
                logger.info(
                    "Bootstrapped Chroma vectors: %s/%s",
                    min(start + len(batch), len(texts)),
                    len(texts),
                )

            logger.info("Chroma bootstrap complete: %s vectors", self.db._collection.count())

        except Exception as e:
            logger.error("Failed to bootstrap empty Chroma collection: %s", e)
            raise
    
    def search_similar_books(
        self, 
        query: str, 
        top_k: int = 10,
        similarity_threshold: float = 0.0
    ) -> List[Dict]:
        """
        Search for similar books using semantic similarity
        
        Args:
            query: Search query (book title or description)
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (compatibility param, not used)
            
        Returns:
            List of similar books with metadata and scores
        """
        try:
            # Chroma similarity_search_with_score returns (Document, score) tuples
            results = self.db.similarity_search_with_score(query, k=top_k)
            
            similar_books = []
            for doc, score in results:
                # Extract ISBN from page content (format: "ISBN description")
                parts = doc.page_content.split(maxsplit=1)
                isbn = parts[0] if parts else ""
                
                # Chroma returns distances, convert to similarity (lower distance = higher similarity)
                similarity = 1 / (1 + score) if score else 0.5
                
                book = {
                    'isbn13': isbn,
                    'similarity_score': float(similarity),
                    'document_preview': doc.page_content[:300]
                }
                similar_books.append(book)
            
            return similar_books
        
        except Exception as e:
            logger.error(f"Error searching similar books: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics"""
        try:
            # Get count from Chroma collection
            count = self.db._collection.count()
            return {
                'collection_name': settings.CHROMA_COLLECTION_NAME,
                'total_books': count,
                'embedding_model': settings.EMBEDDING_MODEL
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                'collection_name': settings.CHROMA_COLLECTION_NAME,
                'total_books': 0,
                'embedding_model': settings.EMBEDDING_MODEL,
            }


# Global RAG pipeline instance
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create the global RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
