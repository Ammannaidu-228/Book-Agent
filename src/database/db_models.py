"""
MongoDB document schemas for Lit-Pick
"""
from datetime import datetime
import uuid
from typing import Optional, List, Dict, Any

# Book document schema
def create_book_document(
    isbn13: str,
    title: str,
    authors: Optional[str] = None,
    categories: Optional[str] = None,
    description: Optional[str] = None,
    thumbnail: Optional[str] = None,
    published_year: Optional[int] = None,
    average_rating: Optional[float] = None,
    num_pages: Optional[int] = None,
    ratings_count: Optional[int] = None,
    embedding_id: Optional[str] = None,
    emotions: Optional[Dict] = None,
    isbn10: Optional[str] = None
) -> Dict[str, Any]:
    """Create a book document for MongoDB"""
    return {
        "isbn13": isbn13,
        "isbn10": isbn10,
        "title": title,
        "authors": authors,
        "categories": categories,
        "description": description,
        "thumbnail": thumbnail,
        "published_year": published_year,
        "average_rating": average_rating,
        "num_pages": num_pages,
        "ratings_count": ratings_count,
        "embedding_id": embedding_id or isbn13,
        "emotions": emotions or {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


# User preference document schema
def create_user_preference_document(
    user_id: Optional[str],
    liked_book_isbn: str,
    recommended_books: List[str],
    recommendation_score: Optional[float] = None,
    emotions_matched: Optional[Dict] = None
) -> Dict[str, Any]:
    """Create a user preference document for MongoDB"""
    return {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "liked_book_isbn": liked_book_isbn,
        "recommended_books": recommended_books,
        "recommendation_score": recommendation_score,
        "emotions_matched": emotions_matched or {},
        "created_at": datetime.utcnow()
    }


# Recommendation cache document schema
def create_cache_document(
    query_book: str,
    results: List[Dict],
) -> Dict[str, Any]:
    """Create a recommendation cache document for MongoDB"""
    return {
        "_id": str(uuid.uuid4()),
        "query_book": query_book,
        "results": results,
        "hit_count": 0,
        "created_at": datetime.utcnow(),
        "accessed_at": datetime.utcnow()
    }
