"""Core module - recommendation engine, classifiers, and RAG pipeline"""
from .recommendation import RecommendationEngine, get_recommendation_engine
from .classifier import EmotionClassifier, get_classifier
from .embeddings import RAGPipeline, get_rag_pipeline

__all__ = [
    "RecommendationEngine",
    "get_recommendation_engine",
    "EmotionClassifier",
    "get_classifier",
    "RAGPipeline",
    "get_rag_pipeline"
]
