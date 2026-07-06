"""
Book recommendation engine combining RAG and emotion classification
"""
import pandas as pd
from typing import List, Dict, Tuple, Optional
from .embeddings import get_rag_pipeline
from .classifier import get_classifier
from ..config import settings
import logging
import time

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Main recommendation engine"""
    
    def __init__(self, books_df: Optional[pd.DataFrame] = None):
        """
        Initialize recommendation engine instance lazily.
        
        Args:
            books_df: Optional DataFrame with book data
        """
        # Delay heavy model loading until initialize() is called
        self.rag_pipeline = None
        self.classifier = None
        self.books_df = books_df
        self.books_by_isbn = {}
        self.emotion_cache = {}
        self.initialized = False

    @staticmethod
    def _safe_value(value, default=None):
        """Return JSON-safe values instead of pandas NaN/NA."""
        if value is None:
            return default
        try:
            if pd.isna(value):
                return default
        except (TypeError, ValueError):
            pass
        return value

    def _book_record_from_row(self, row: pd.Series) -> Dict:
        """Normalize a dataframe row into the API's book shape."""
        title = self._safe_value(row.get("title"), "")
        authors = self._safe_value(row.get("authors"), None)
        category = self._safe_value(row.get("simple_categories"), row.get("categories"))
        thumbnail = self._safe_value(row.get("thumbnail"), None)
        description = self._safe_value(row.get("description"), "")
        average_rating = self._safe_value(row.get("average_rating"), None)

        return {
            "isbn13": str(self._safe_value(row.get("isbn13"), "")),
            "title": str(title) if title is not None else "",
            "authors": str(authors) if authors is not None else None,
            "category": str(category) if category is not None else None,
            "categories": str(category) if category is not None else None,
            "description": str(description) if description is not None else "",
            "thumbnail": str(thumbnail) if thumbnail is not None else None,
            "rating": float(average_rating) if average_rating is not None else None,
            "average_rating": float(average_rating) if average_rating is not None else None,
            "published_year": self._safe_value(row.get("published_year"), None),
            "num_pages": self._safe_value(row.get("num_pages"), None),
            "ratings_count": self._safe_value(row.get("ratings_count"), None),
        }

    def _enrich_search_result(self, search_result: Dict) -> Dict:
        """Merge Chroma search metadata with full CSV metadata by ISBN."""
        isbn = str(search_result.get("isbn13", ""))
        book = dict(self.books_by_isbn.get(isbn, {}))
        book.update({
            "isbn13": isbn,
            "similarity_score": search_result.get("similarity_score"),
            "document_preview": search_result.get("document_preview") or book.get("description"),
        })
        return book
    
    def initialize(self, books_df: pd.DataFrame):
        """Initialize engine with book data"""
        try:
            logger.info("Initializing recommendation engine with book data...")
            
            # Load heavy components lazily in background thread
            if self.rag_pipeline is None:
                self.rag_pipeline = get_rag_pipeline()
            
            # Store books dataframe for quick lookups. Keep title as a column so
            # response formatting can still return it.
            self.books_df = books_df.copy()
            self.books_by_isbn = {
                str(record.get("isbn13")): record
                for record in (
                    self._book_record_from_row(row)
                    for _, row in self.books_df.iterrows()
                )
                if record.get("isbn13")
            }
            
            # Check that vector DB is ready (pre-built by init_chroma.py)
            stats = self.rag_pipeline.get_collection_stats()
            
            logger.info(f"Engine initialized: {stats['total_books']} books in vector DB")
            self.initialized = True
            
            return stats['total_books'], []
        
        except Exception as e:
            logger.error(f"Error initializing recommendation engine: {e}")
            raise
    
    def _find_book_in_dataset(self, query: str) -> Optional[Dict]:
        """
        Find book in dataset by fuzzy matching
        
        Args:
            query: Book title query
            
        Returns:
            Book metadata if found
        """
        try:
            if self.books_df is None:
                return None
            
            # Try exact match first
            title_series = self.books_df["title"].fillna("").astype(str)
            exact_matches = self.books_df[title_series == query]
            if not exact_matches.empty:
                return self._book_record_from_row(exact_matches.iloc[0])
            
            # Try case-insensitive match
            query_lower = query.lower()
            lower_matches = self.books_df[title_series.str.lower() == query_lower]
            if not lower_matches.empty:
                return self._book_record_from_row(lower_matches.iloc[0])
            
            # Try substring match (if title contains query)
            contains_matches = self.books_df[title_series.str.lower().str.contains(query_lower, regex=False)]
            if not contains_matches.empty:
                return self._book_record_from_row(contains_matches.iloc[0])
            
            return None
        
        except Exception as e:
            logger.error(f"Error finding book in dataset: {e}")
            return None
    
    def get_recommendations(
        self,
        book_title: str,
        top_k: int = settings.TOP_K_RESULTS,
        include_emotions: bool = True,
        min_similarity: float = settings.SIMILARITY_THRESHOLD
    ) -> Tuple[List[Dict], Dict]:
        """
        Get book recommendations for a given book
        
        Args:
            book_title: Query book title
            top_k: Number of recommendations
            include_emotions: Include emotion scores
            min_similarity: Minimum similarity threshold
            
        Returns:
            Tuple of (recommendations_list, query_book_info)
        """
        try:
            start_time = time.time()
            
            # Find the query book
            query_book = self._find_book_in_dataset(book_title)
            if not query_book:
                logger.warning(f"Book not found: {book_title}")
                return [], {"title": book_title, "found": False}
            
            # Get similar books from vector DB
            search_text = f"{query_book.get('title', '')} {query_book.get('description', '')}"
            similar_books = self.rag_pipeline.search_similar_books(
                query=search_text,
                top_k=top_k * 2,  # Get more to filter by similarity
                similarity_threshold=min_similarity
            )
            
            # Filter duplicates and the query book itself
            query_isbn = query_book.get('isbn13', '')
            seen_isbns = {query_isbn}
            filtered_books = []
            
            for book in similar_books:
                isbn = book.get('isbn13', '')
                if isbn and isbn not in seen_isbns:
                    seen_isbns.add(isbn)
                    filtered_books.append(self._enrich_search_result(book))
                    if len(filtered_books) >= top_k:
                        break
            
            # Add emotions if requested and enabled
            if include_emotions:
                if not settings.ENABLE_EMOTION_CLASSIFICATION:
                    logger.info("Emotion classification disabled by configuration; skipping emotion metadata.")
                else:
                    if self.classifier is None:
                        self.classifier = get_classifier()
                    for book in filtered_books:
                        try:
                            cache_key = book.get("isbn13") or book.get("title")
                            if cache_key and cache_key in self.emotion_cache:
                                emotions, top_emotion = self.emotion_cache[cache_key]
                            else:
                                emotions, top_emotion = self.classifier.classify_book(
                                    title=book.get('title', ''),
                                    description=book.get('document_preview', ''),
                                    authors=book.get('authors', '')
                                )
                                if cache_key:
                                    self.emotion_cache[cache_key] = (emotions, top_emotion)
                            book['emotions'] = emotions
                            book['top_emotion'] = top_emotion
                            book['match_reason'] = f"Similar to {book_title}. Emotional themes: {', '.join(list(emotions.keys())[:3])}"
                        except Exception as e:
                            logger.error(f"Error classifying emotions for {book.get('title')}: {e}")
                            book['emotions'] = None
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            logger.info(f"Generated {len(filtered_books)} recommendations for '{book_title}' in {processing_time:.2f}ms")
            
            return filtered_books, {
                "title": query_book.get('title', ''),
                "isbn": query_isbn,
                "authors": query_book.get('authors', ''),
                "rating": query_book.get('average_rating') or query_book.get('rating') or 0,
                "found": True,
                "processing_time_ms": processing_time
            }
        
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return [], {"title": book_title, "found": False, "error": str(e)}
    
    def get_emotion_analysis(self, book_title: str) -> Dict:
        """
        Get detailed emotion analysis for a book
        
        Args:
            book_title: Book title
            
        Returns:
            Emotion analysis data
        """
        try:
            book = self._find_book_in_dataset(book_title)
            if not book:
                return {"found": False, "title": book_title}

            if self.classifier is None:
                self.classifier = get_classifier()

            cache_key = book.get("isbn13") or book.get("title")
            if cache_key and cache_key in self.emotion_cache:
                emotions, top_emotion = self.emotion_cache[cache_key]
            else:
                emotions, top_emotion = self.classifier.classify_book(
                    title=book.get('title', ''),
                    description=book.get('description', ''),
                    authors=book.get('authors', '')
                )
                if cache_key:
                    self.emotion_cache[cache_key] = (emotions, top_emotion)
            
            return {
                "found": True,
                "title": book.get('title', ''),
                "authors": book.get('authors', ''),
                "emotions": emotions,
                "top_emotion": top_emotion,
                "emotion_scores_sorted": dict(sorted(emotions.items(), key=lambda x: x[1], reverse=True))
            }
        
        except Exception as e:
            logger.error(f"Error analyzing emotions: {e}")
            return {"found": False, "error": str(e)}
    
    def search_books(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search books by title or description
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching books
        """
        try:
            results = self.rag_pipeline.search_similar_books(query, top_k=limit)
            return [self._enrich_search_result(result) for result in results[:limit]]
        
        except Exception as e:
            logger.error(f"Error searching books: {e}")
            return []
    
    def get_top_books(self, limit: int = 50) -> List[Dict]:
        """
        Get top books by rating
        
        Args:
            limit: Maximum books to return
            
        Returns:
            List of top-rated books
        """
        try:
            if self.books_df is None or self.books_df.empty:
                return []
            
            # Sort by average_rating (descending) and get top books
            top_books_df = self.books_df.nlargest(limit, 'average_rating')
            
            return [
                self._book_record_from_row(row)
                for _, row in top_books_df.iterrows()
            ]
        
        except Exception as e:
            logger.error(f"Error getting top books: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """
        Get engine statistics
        
        Returns:
            Dictionary with engine stats
        """
        try:
            stats = {
                "initialized": self.initialized,
                "total_books": len(self.books_by_isbn) if self.books_by_isbn else 0,
                "cached_emotions": len(self.emotion_cache),
                "rag_pipeline_loaded": self.rag_pipeline is not None,
                "classifier_loaded": self.classifier is not None,
            }
            
            if self.rag_pipeline:
                try:
                    rag_stats = self.rag_pipeline.get_collection_stats()
                    stats["vector_db_stats"] = rag_stats
                except Exception as e:
                    logger.warning(f"Could not get vector DB stats: {e}")
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e), "initialized": False}


# Global recommendation engine instance
_engine = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get or create the global recommendation engine instance"""
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
    return _engine
