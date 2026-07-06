"""
FastAPI application for Lit-Pick recommendation engine
Organized in modular agentic AI project structure
"""
import logging
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import time
import asyncio

# Add parent directory to path to support running from src directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.database import init_db, close_db, get_db
from src.api import (
    RecommendationRequest, RecommendationResponse, BookResponse,
    EmotionClassificationRequest, EmotionClassificationResponse,
    HealthCheckResponse, SearchRequest, SearchResponse
)
from src.core import get_recommendation_engine, get_classifier, get_rag_pipeline

# Lock to prevent concurrent engine initialization
engine_init_lock = asyncio.Lock()
engine_init_task = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global engine instance
engine = None
_initialization_error = None

REPO_ROOT = Path(__file__).resolve().parents[1]


def resolve_data_file_path(filename: str):
    """Resolve a data file from the repository root or common data locations."""
    candidates = [
        Path(filename),
        Path.cwd() / filename,
        REPO_ROOT / filename,
        REPO_ROOT / "data" / "raw" / filename,
        REPO_ROOT / "data" / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def describe_data_search_paths(filename: str):
    """Return the data paths checked for diagnostics."""
    return [
        str(Path(filename)),
        str(Path.cwd() / filename),
        str(REPO_ROOT / filename),
        str(REPO_ROOT / "data" / "raw" / filename),
        str(REPO_ROOT / "data" / filename),
    ]


def json_safe(value, default=None):
    """Convert pandas/numpy missing values into JSON-safe defaults."""
    if value is None:
        return default
    try:
        import pandas as pd
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    return value


BOOK_FIELDS = {
    "_id": 0,
    "isbn13": 1,
    "isbn10": 1,
    "title": 1,
    "authors": 1,
    "categories": 1,
    "description": 1,
    "thumbnail": 1,
    "published_year": 1,
    "average_rating": 1,
    "num_pages": 1,
    "ratings_count": 1,
    "embedding_id": 1,
    "emotions": 1,
}


def normalize_book_document(book: dict) -> dict:
    """Return a JSON-safe book document from MongoDB."""
    rating = json_safe(book.get("average_rating"), None)
    description = json_safe(book.get("description"), None)

    return {
        "isbn13": str(json_safe(book.get("isbn13"), "")),
        "isbn10": json_safe(book.get("isbn10"), None),
        "title": str(json_safe(book.get("title"), "")),
        "authors": json_safe(book.get("authors"), None),
        "categories": json_safe(book.get("categories"), None),
        "category": json_safe(book.get("categories"), None),
        "description": description,
        "thumbnail": json_safe(book.get("thumbnail"), None),
        "published_year": json_safe(book.get("published_year"), None),
        "average_rating": float(rating) if rating is not None else None,
        "rating": float(rating) if rating is not None else None,
        "num_pages": json_safe(book.get("num_pages"), None),
        "ratings_count": json_safe(book.get("ratings_count"), None),
        "embedding_id": json_safe(book.get("embedding_id"), None),
        "emotions": json_safe(book.get("emotions"), {}),
    }


def load_books_from_mongodb():
    """Load all books from MongoDB into a dataframe-compatible list."""
    db = get_db()
    books = list(db["books"].find({}, BOOK_FIELDS))
    return [normalize_book_document(book) for book in books]


def load_books_dataframe():
    """Load book metadata from MongoDB, falling back to the CSV if Mongo is empty."""
    import pandas as pd

    try:
        mongo_books = load_books_from_mongodb()
        if mongo_books:
            logger.info("Loaded %s books from MongoDB", len(mongo_books))
            return pd.DataFrame(mongo_books), "mongodb"
        logger.warning("MongoDB books collection is empty; falling back to CSV if available")
    except Exception as e:
        logger.warning("Could not load books from MongoDB; falling back to CSV if available: %s", e)

    csv_path = resolve_data_file_path("books_with_emotions.csv")
    if csv_path:
        logger.info("Loaded books from CSV fallback at %s", csv_path)
        return pd.read_csv(csv_path), "csv"

    logger.warning(
        "No MongoDB books and books_with_emotions.csv not found; checked: %s",
        describe_data_search_paths("books_with_emotions.csv"),
    )
    return pd.DataFrame(), "empty"


async def ensure_engine_ready():
    """Ensure the recommendation engine is created and initialized (lazy)."""
    global engine
    if engine and getattr(engine, 'initialized', False):
        return

    async with engine_init_lock:
        if engine and getattr(engine, 'initialized', False):
            return

        try:
            # Create engine instance if missing
            if engine is None:
                engine = get_recommendation_engine()

            # Load dataset and initialize in a thread to avoid blocking event loop.
            books_df, source = await asyncio.to_thread(load_books_dataframe)
            if not books_df.empty:
                logger.info("Initializing recommendation engine with %s book data", source)
                await asyncio.to_thread(engine.initialize, books_df)
            else:
                logger.warning("No books available to initialize recommendation engine")

        except Exception as e:
            logger.error(f"Failed to initialize engine lazily: {e}")
            raise


async def _background_engine_initialization():
    """Background task to warm up the engine on startup."""
    global engine_init_task
    try:
        await ensure_engine_ready()
    except Exception as e:
        logger.warning(f"Background engine initialization failed: {e}")
    finally:
        engine_init_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global engine, _initialization_error
    
    # Startup
    try:
        logger.info("Starting up Lit-Pick backend...")
        
        # Initialize database
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization failed (non-critical): {e}")
        
        # Warm up the engine if MongoDB already has books. Heavy components still
        # initialize in the background so startup stays fast.
        try:
            logger.info("Loading books data...")
            books_count = await asyncio.to_thread(lambda: get_db()["books"].count_documents({}))
            if books_count > 0:
                logger.info("MongoDB books collection has %s books; engine will initialize lazily on first use", books_count)
                engine = None
                global engine_init_task
                engine_init_task = asyncio.create_task(_background_engine_initialization())
            else:
                logger.warning("MongoDB books collection is empty - run `python -m scripts.load_data` to load books")
                engine = None
        except Exception as e:
            logger.warning(f"Engine initialization deferred: {e}")
            engine = None
        
        logger.info("Lit-Pick backend started (models will load on first use)")
    
    except Exception as e:
        _initialization_error = str(e)
        logger.error(f"Error during startup: {e}")
    
    # Yield control to the application
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down Lit-Pick backend...")
        await close_db()
        logger.info("Backend shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AI-powered book recommendation engine using RAG, LLMs, and emotion classification",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    try:
        if _initialization_error:
            logger.warning(f"Health check: Initialization error present: {_initialization_error}")
        
        # Check whether heavy components are loaded without instantiating them
        classifier_loaded = False
        rag_loaded = False
        
        try:
            from src.core import classifier as classifier_module
            from src.core import embeddings as embeddings_module

            classifier_loaded = getattr(classifier_module, "_classifier", None) is not None
            rag_loaded = getattr(embeddings_module, "_rag_pipeline", None) is not None

        except Exception as e:
            logger.warning(f"Could not inspect model modules: {e}")
        
        # Check database
        db_connected = True
        try:
            db = get_db()
            db["books"].find_one({}, {"_id": 1})
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            db_connected = False
        
        return HealthCheckResponse(
            status="healthy",
            version=settings.API_VERSION,
            database_connected=db_connected,
            vector_db_connected=rag_loaded,
            model_loaded=classifier_loaded,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):
    """
    Get book recommendations
    
    Endpoint: POST /recommend
    Returns recommendations based on a query book using semantic similarity
    """
    try:
        try:
            await ensure_engine_ready()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Engine initialization failed: {e}")
        
        start_time = time.time()
        
        # Run heavy recommendation work in thread pool to avoid blocking event loop
        def get_recs():
            return engine.get_recommendations(
                book_title=request.book,
                top_k=request.top_k,
                include_emotions=request.include_emotions,
                min_similarity=settings.SIMILARITY_THRESHOLD
            )
        
        recommendations, query_info = await asyncio.wait_for(
            asyncio.to_thread(get_recs),
            timeout=settings.RECOMMENDATION_TIMEOUT
        )
        recommendation_responses = [
            BookResponse(
                isbn13=book.get('isbn13', ''),
                title=book.get('title', ''),
                authors=book.get('authors'),
                categories=book.get('category'),
                description=book.get('document_preview'),
                thumbnail=book.get('thumbnail'),
                average_rating=book.get('rating'),
                emotions=book.get('emotions'),
                similarity_score=book.get('similarity_score'),
                match_reason=book.get('match_reason')
            )
            for book in recommendations
        ]
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"Recommendation request for '{request.book}' completed in {processing_time:.2f}ms")
        
        return RecommendationResponse(
            query_book=request.book,
            recommendations=recommendation_responses,
            total_results=len(recommendations),
            processing_time_ms=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in recommendation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/classify-emotion", response_model=EmotionClassificationResponse)
async def classify_emotion(request: EmotionClassificationRequest):
    """
    Classify emotions in text
    
    Endpoint: POST /classify-emotion
    Performs zero-shot emotion classification on provided text
    """
    try:
        classifier = get_classifier()
        
        emotions = await asyncio.to_thread(classifier.classify_text, request.text)
        top_emotion = max(emotions, key=emotions.get)
        confidence = emotions[top_emotion]
        
        return EmotionClassificationResponse(
            text=request.text[:100],  # Return first 100 chars
            emotions=emotions,
            top_emotion=top_emotion,
            confidence=confidence
        )
    
    except Exception as e:
        logger.error(f"Error classifying emotions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search", response_model=SearchResponse)
async def search_books(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search books by title or description
    
    Endpoint: GET /search
    Performs semantic search across book titles and descriptions
    """
    try:
        try:
            await ensure_engine_ready()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Engine initialization failed: {e}")

        results = await asyncio.to_thread(engine.search_books, query, limit)
        
        response_books = [
            BookResponse(
                isbn13=book.get('isbn13', ''),
                title=book.get('title', ''),
                authors=book.get('authors'),
                categories=book.get('category'),
                description=book.get('document_preview') or book.get('description'),
                thumbnail=book.get('thumbnail'),
                average_rating=book.get('rating') or book.get('average_rating'),
                similarity_score=book.get('similarity_score')
            )
            for book in results
        ]
        
        return SearchResponse(
            query=query,
            results=response_books,
            total_found=len(response_books)
        )
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error searching books: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/book/{book_title}")
async def get_book_analysis(book_title: str):
    """
    Get detailed book analysis including emotions
    
    Endpoint: GET /book/{book_title}
    Returns book metadata and emotion analysis
    """
    try:
        try:
            await ensure_engine_ready()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Engine initialization failed: {e}")

        analysis = await asyncio.to_thread(engine.get_emotion_analysis, book_title)
        
        if not analysis.get('found'):
            raise HTTPException(status_code=404, detail=f"Book '{book_title}' not found")
        
        return analysis
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting book analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/books")
async def get_top_books(limit: int = 50):
    """
    Get top books by rating
    
    Endpoint: GET /books
    Returns top books sorted by rating (default: 50)
    """
    try:
        try:
            db = get_db()
            cursor = (
                db["books"]
                .find({}, BOOK_FIELDS)
                .sort("average_rating", -1)
                .limit(limit)
            )
            top_books = await asyncio.to_thread(lambda: list(cursor))
        except Exception as e:
            logger.warning("MongoDB books query failed, falling back to recommendation engine: %s", e)
            try:
                await ensure_engine_ready()
            except Exception as init_error:
                raise HTTPException(status_code=503, detail=f"Books unavailable: {init_error}")
            top_books = engine.get_top_books(limit=limit)
        
        books_response = []
        for book in top_books:
            book = normalize_book_document(book)
            thumbnail = json_safe(book.get('thumbnail'), None)
            rating = json_safe(book.get('rating') or book.get('average_rating'), None)
            description = json_safe(book.get('document_preview') or book.get('description'), None)

            books_response.append({
                "isbn13": str(json_safe(book.get('isbn13'), '')),
                "title": str(json_safe(book.get('title'), '')),
                "authors": json_safe(book.get('authors'), None),
                "thumbnail": thumbnail,
                "average_rating": float(rating) if rating is not None else None,
                "description": description[:100] if description else None
            })
        
        return {
            "books": books_response,
            "total": len(books_response)
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error getting top books: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_engine_stats():
    """
    Get engine statistics
    
    Endpoint: GET /stats
    Returns information about the recommendation engine state
    """
    try:
        try:
            await ensure_engine_ready()
        except Exception:
            # If engine can't be initialized, return empty stats with timestamp
            return {"initialized": False, "timestamp": datetime.utcnow().isoformat()}

        stats = engine.get_stats() if engine else {}
        stats['timestamp'] = datetime.utcnow().isoformat()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "recommend": "POST /recommend",
            "search": "GET /search",
            "classify_emotion": "POST /classify-emotion",
            "book_analysis": "GET /book/{book_title}",
            "stats": "/stats",
            "docs": "/docs"
        }
    }


@app.get("/docs", include_in_schema=False)
async def docs():
    """Redirect to OpenAPI docs"""
    return {"detail": "OpenAPI docs available at /docs"}


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
