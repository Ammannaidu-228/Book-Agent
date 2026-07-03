"""API module"""
from .schemas import (
    BookBase,
    BookResponse,
    RecommendationRequest,
    RecommendationResponse,
    EmotionClassificationRequest,
    EmotionClassificationResponse,
    HealthCheckResponse,
    SearchRequest,
    SearchResponse,
    BatchRecommendationRequest
)

__all__ = [
    "BookBase",
    "BookResponse",
    "RecommendationRequest",
    "RecommendationResponse",
    "EmotionClassificationRequest",
    "EmotionClassificationResponse",
    "HealthCheckResponse",
    "SearchRequest",
    "SearchResponse",
    "BatchRecommendationRequest"
]
