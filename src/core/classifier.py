"""
Emotion classification using Hugging Face Transformers
"""
from ..config import settings
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class EmotionClassifier:
    """Zero-shot emotion classifier using BART"""
    
    def __init__(self):
        """Initialize the emotion classifier"""
        # Lazy import heavy ML libraries to avoid large memory use at module import
        try:
            import torch
            from transformers import pipeline

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading emotion classifier on device: {self.device}")

            # Show user what model is being loaded
            logger.info(f"Downloading and loading model: {settings.EMOTION_MODEL} (this may take a minute on first run)")

            self.classifier = pipeline(
                "zero-shot-classification",
                model=settings.EMOTION_MODEL,
                device=0 if self.device == "cuda" else -1
            )
            self.emotions = settings.EMOTIONS
            logger.info(f"Emotion classifier loaded successfully. Emotions: {self.emotions}")

        except Exception as e:
            logger.error(f"Error loading emotion classifier: {e}")
            logger.error(
                "The classifier model requires internet access to download from Hugging Face. "
                "Please check your internet connection and try again."
            )
            raise
    
    def classify_text(self, text: str) -> Dict[str, float]:
        """
        Classify emotions in a given text
        
        Args:
            text: Text to classify
            
        Returns:
            Dictionary with emotion scores
        """
        try:
            # Truncate text if too long (BART has max length)
            max_length = 1024
            if len(text) > max_length:
                text = text[:max_length]
            
            result = self.classifier(text, self.emotions, multi_class=True)
            
            # Convert to dictionary
            emotions_dict = {
                label: score for label, score in zip(result["labels"], result["scores"])
            }
            
            return emotions_dict
        
        except Exception as e:
            logger.error(f"Error classifying emotions: {e}")
            # Return neutral emotions on error
            return {emotion: 0.1 for emotion in self.emotions}
    
    def classify_book(self, title: str, description: str, authors: str = "") -> Tuple[Dict[str, float], str]:
        """
        Classify emotions for a book based on its metadata
        
        Args:
            title: Book title
            description: Book description
            authors: Book authors
            
        Returns:
            Tuple of (emotions_dict, top_emotion)
        """
        try:
            # Combine metadata with weights
            combined_text = f"{title} {description} by {authors}".strip()
            
            emotions = self.classify_text(combined_text)
            top_emotion = max(emotions, key=emotions.get)
            
            return emotions, top_emotion
        
        except Exception as e:
            logger.error(f"Error classifying book emotions: {e}")
            return {emotion: 0.1 for emotion in self.emotions}, "unknown"
    
    def batch_classify(self, texts: list) -> list:
        """
        Classify emotions for multiple texts
        
        Args:
            texts: List of texts to classify
            
        Returns:
            List of emotion dictionaries
        """
        return [self.classify_text(text) for text in texts]


# Global classifier instance
_classifier = None


def get_classifier() -> EmotionClassifier:
    """Get or create the global classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = EmotionClassifier()
    return _classifier
