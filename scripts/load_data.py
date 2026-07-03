"""
Data loader script to initialize database and load book embeddings
"""
import pandas as pd
import logging
import asyncio
import os
import time
from database import init_db, get_db
from config import settings
from db_models import create_book_document
from embeddings import get_rag_pipeline
from classifier import get_classifier
from tqdm import tqdm


def _cleanup_stale_lock(lock_path: str, max_age_seconds: int = 300):
    if os.path.exists(lock_path):
        try:
            lock_age = time.time() - os.path.getmtime(lock_path)
            if lock_age > max_age_seconds:
                logging.warning(
                    "Detected stale ingest lock older than %s seconds. Removing stale lock at %s",
                    max_age_seconds,
                    lock_path
                )
                os.remove(lock_path)
        except Exception as e:
            logging.warning(f"Failed to cleanup stale ingest lock '{lock_path}': {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def load_books_to_db(csv_file: str = "books_with_emotions.csv"):
    """Load books from CSV into MongoDB"""
    try:
        logger.info(f"Loading books from {csv_file}...")
        
        # Initialize database
        await init_db()
        
        # Load CSV
        df = pd.read_csv(csv_file)
        logger.info(f"Loaded {len(df)} books from CSV")
        
        # Get MongoDB database
        db = get_db()
        books_collection = db["books"]
        
        # Check if books already exist
        existing_count = books_collection.count_documents({})
        if existing_count > 0:
            logger.info(f"Database already has {existing_count} books. Skipping...")
            return
        
        # Add books to database
        logger.info("Adding books to database...")
        books_to_insert = []
        
        for idx, row in tqdm(df.iterrows(), total=len(df)):
            book_doc = create_book_document(
                isbn13=str(row['isbn13']),
                isbn10=row.get('isbn10'),
                title=row['title'],
                authors=row.get('authors'),
                categories=row.get('categories'),
                description=row.get('description'),
                thumbnail=row.get('thumbnail'),
                published_year=row.get('published_year'),
                average_rating=row.get('average_rating'),
                num_pages=row.get('num_pages'),
                ratings_count=row.get('ratings_count'),
                embedding_id=str(row['isbn13']),  # Use ISBN as embedding ID
                emotions=row.get('emotions') or {}
            )
            books_to_insert.append(book_doc)
            
            # Insert in batches
            if (idx + 1) % 100 == 0:
                books_collection.insert_many(books_to_insert)
                books_to_insert = []
        
        # Insert remaining books
        if books_to_insert:
            books_collection.insert_many(books_to_insert)
        
        logger.info("Successfully added books to database")
    
    except Exception as e:
        logger.error(f"Error loading books: {e}")
        raise


async def initialize_vector_db(csv_file: str = "books_with_emotions.csv"):
    """Initialize vector database with book embeddings"""
    try:
        logger.info("Initializing vector database...")
        
        # Load CSV
        df = pd.read_csv(csv_file)
        
        # Initialize RAG pipeline
        rag = get_rag_pipeline()
        
        # Check if already populated
        stats = rag.get_collection_stats()
        if stats.get('total_books', 0) > 0:
            logger.info(f"Vector DB already has {stats['total_books']} books. Skipping...")
            return
        
        # Ingest books using configured batch size. Use a simple file lock
        # in the Chroma persist directory to avoid concurrent ingestion
        logger.info(f"Ingesting {len(df)} books into vector database...")
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        lock_path = os.path.join(settings.CHROMA_PERSIST_DIR, "ingest.lock")
        _cleanup_stale_lock(lock_path)
        lock_acquired = False
        lock_fd = None
        try:
            try:
                # Try to create lock file atomically
                lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(lock_fd, str(os.getpid()).encode())
                lock_acquired = True
                logger.info("Acquired ingest lock; proceeding with ingestion")

                success_count, errors = rag.ingest_books(df, batch_size=settings.BATCH_SIZE)

            except FileExistsError:
                # Another process is ingesting; wait until collection is populated
                logger.info("Ingest lock present — another process is ingesting. Waiting for completion...")
                wait_seconds = 0
                max_wait = 120
                success_count, errors = 0, []
                while wait_seconds < max_wait:
                    stats = rag.get_collection_stats()
                    if stats.get('total_books', 0) > 0:
                        logger.info(f"Detected collection populated ({stats.get('total_books')}). Skipping ingestion")
                        break
                    time.sleep(2)
                    wait_seconds += 2
                else:
                    # Timeout: attempt ingestion anyway (last resort)
                    logger.warning("Timeout waiting for ingest lock to clear — attempting ingestion")
                    success_count, errors = rag.ingest_books(df, batch_size=settings.BATCH_SIZE)
        finally:
            if lock_acquired and lock_fd:
                try:
                    os.close(lock_fd)
                except Exception:
                    pass
                try:
                    os.remove(lock_path)
                except Exception:
                    pass
        
        logger.info(f"Vector DB initialized: {success_count} books indexed, {len(errors)} errors")
        
        if errors:
            logger.warning(f"Failed ISBNs: {errors[:10]}")  # Log first 10 errors
    
    except Exception as e:
        logger.error(f"Error initializing vector database: {e}")
        raise


async def test_classifier():
    """Test emotion classifier"""
    try:
        logger.info("Testing emotion classifier...")
        
        classifier = get_classifier()
        
        test_text = "An exciting adventure full of mystery and wonder"
        emotions = classifier.classify_text(test_text)
        
        logger.info(f"Emotions: {emotions}")
        logger.info("Classifier test passed!")
    
    except Exception as e:
        logger.error(f"Error testing classifier: {e}")
        raise


async def main():
    """Main data loading function"""
    try:
        logger.info("Starting data initialization...")
        
        # Initialize MongoDB (optional — skip if unavailable)
        try:
            logger.info("Attempting to initialize MongoDB...")
            await load_books_to_db()
        except Exception as e:
            logger.warning(f"MongoDB initialization skipped (non-critical): {e}")
        
        # Initialize vector database (critical for RAG)
        logger.info("Proceeding with vector database initialization...")
        await initialize_vector_db()
        
        # Test classifier
        await test_classifier()
        
        logger.info("Data initialization complete!")
    
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
