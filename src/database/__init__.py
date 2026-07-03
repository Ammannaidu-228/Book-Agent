"""Database module"""
from .database import (
    get_mongo_client,
    get_db,
    init_db,
    close_db
)
from .db_models import (
    create_book_document,
    create_user_preference_document
)

__all__ = [
    "get_mongo_client",
    "get_db",
    "init_db",
    "close_db",
    "create_book_document",
    "create_user_preference_document"
]
