"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class BookBase(BaseModel):
    """Base book model"""
    isbn13: str
    title: str
    authors: Optional[str] = None
    categories: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    average_rating: Optional[float] = None
    ratings_count: Optional[int] = None


class BookResponse(BookBase):
    """Book response model"""
    emotions: Optional[Dict[str, float]] = None
    similarity_score: Optional[float] = Field(None, ge=0, le=1)
    match_reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class RecommendationRequest(BaseModel):
    """Request model for book recommendations"""
    book: str = Field(..., min_length=1, description="Book title to get recommendations for")
    top_k: int = Field(10, ge=1, le=50, description="Number of recommendations to return")
    include_emotions: bool = Field(
        False,
        description="Include emotion scores in response. Set true for slower results with emotional metadata."
    )


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    query_book: str
    recommendations: List[BookResponse]
    total_results: int
    processing_time_ms: float


class EmotionClassificationRequest(BaseModel):
    """Request model for emotion classification"""
    text: str = Field(..., min_length=10, description="Text to classify")


class EmotionClassificationResponse(BaseModel):
    """Response model for emotion classification"""
    text: str
    emotions: Dict[str, float] = Field(..., description="Emotion scores")
    top_emotion: str
    confidence: float = Field(..., ge=0, le=1)


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    database_connected: bool
    vector_db_connected: bool
    model_loaded: bool
    timestamp: datetime


class SearchRequest(BaseModel):
    """Request model for book search"""
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")


class SearchResponse(BaseModel):
    """Response model for book search"""
    query: str
    results: List[BookResponse]
    total_found: int


class BatchRecommendationRequest(BaseModel):
    """Request model for batch recommendations"""
    books: List[str] = Field(..., min_items=1, max_items=10, description="List of book titles")
    top_k: int = Field(5, ge=1, le=20, description="Recommendations per book")
