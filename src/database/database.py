"""
Database connection and initialization (MongoDB)
"""
from pymongo import MongoClient, errors
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB client
_client = None
_db = None


def get_mongo_client():
    """Get MongoDB client"""
    global _client
    if _client is None:
        try:
            _client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
            # Verify connection
            _client.admin.command('ping')
            logger.info("MongoDB connection established")
        except errors.ServerSelectionTimeoutError:
            logger.error(f"Could not connect to MongoDB at {settings.MONGODB_URL}")
            raise
    return _client


def get_db():
    """Get MongoDB database"""
    global _db
    if _db is None:
        client = get_mongo_client()
        _db = client[settings.DATABASE_NAME]
    return _db


async def init_db():
    """Initialize MongoDB collections with indexes"""
    try:
        db = get_db()
        
        # Create collections if they don't exist
        books_collection = db["books"]
        books_collection.create_index("title")
        books_collection.create_index("embedding_id", unique=True, sparse=True)
        books_collection.create_index("isbn13", unique=True)
        logger.info("Books collection initialized")
        
        preferences_collection = db["user_preferences"]
        preferences_collection.create_index("user_id")
        preferences_collection.create_index("liked_book_isbn")
        logger.info("User preferences collection initialized")
        
        cache_collection = db["recommendation_cache"]
        cache_collection.create_index("query_book")
        cache_collection.create_index("accessed_at")
        logger.info("Recommendation cache collection initialized")
        
        logger.info("MongoDB database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def close_db():
    """Close database connection"""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed")
