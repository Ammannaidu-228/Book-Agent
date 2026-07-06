"""
Initialize Chroma vector DB from CSV (same approach as Gradio)
Run this once to build the semantic search index
"""
import os
import sys
import logging
import shutil
from pathlib import Path

import pandas as pd
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from src.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
BOOKS_CSV = REPO_ROOT / "data" / "raw" / "books_with_emotions.csv"
TAGGED_DESCRIPTIONS = REPO_ROOT / "data" / "raw" / "tagged_description.txt"


def backup_existing_chroma():
    """Backup existing chroma_db if it exists"""
    if os.path.exists(settings.CHROMA_PERSIST_DIR):
        backup_dir = settings.CHROMA_PERSIST_DIR + "_backup"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.move(settings.CHROMA_PERSIST_DIR, backup_dir)
        logger.info(f"Backed up existing Chroma DB to {backup_dir}")


def create_tagged_descriptions():
    """Create tagged_description.txt from CSV"""
    logger.info("Loading books from CSV...")
    books = pd.read_csv(BOOKS_CSV)
    
    logger.info(f"Creating tagged descriptions for {len(books)} books...")
    
    # Create tagged descriptions: ISBN13 + description
    with open(TAGGED_DESCRIPTIONS, "w", encoding="utf-8") as f:
        for _, row in books.iterrows():
            isbn = str(row['isbn13'])
            description = str(row.get('description', ''))
            # Write: ISBN description
            f.write(f"{isbn} {description}\n")
    
    logger.info("Created tagged_description.txt")
    return books


def build_chroma_index():
    """Build Chroma index from tagged descriptions"""
    logger.info("Loading documents...")
    raw_documents = TextLoader(str(TAGGED_DESCRIPTIONS), encoding="utf-8").load()
    
    logger.info("Splitting documents...")
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1, chunk_overlap=0)
    documents = text_splitter.split_documents(raw_documents)
    
    logger.info(f"Creating Chroma index with {len(documents)} documents...")
    logger.info("(This may take a few minutes on first run - downloading OpenAI embeddings model...)")
    
    # Create index with OpenAI embeddings (same as Gradio)
    db = Chroma.from_documents(
        documents,
        embedding=OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL
        ),
        persist_directory=settings.CHROMA_PERSIST_DIR,
        collection_name=settings.CHROMA_COLLECTION_NAME,
    )
    
    logger.info(f"✓ Chroma index built successfully with {len(documents)} documents")
    return db


def verify_index(books_df):
    """Verify the index works"""
    logger.info("Verifying index...")
    
    db = Chroma(
        persist_directory=settings.CHROMA_PERSIST_DIR,
        embedding_function=OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL
        ),
        collection_name=settings.CHROMA_COLLECTION_NAME,
    )
    
    # Test search
    test_query = "A story about forgiveness and redemption"
    results = db.similarity_search(test_query, k=5)
    
    logger.info(f"✓ Test search for '{test_query}':")
    for i, doc in enumerate(results, 1):
        # Extract ISBN from page content
        isbn = doc.page_content.split()[0]
        book = books_df[books_df['isbn13'] == int(isbn)].iloc[0] if len(books_df[books_df['isbn13'] == int(isbn)]) > 0 else None
        if book is not None:
            logger.info(f"  {i}. {book['title']} by {book['authors']}")
    
    logger.info("✓ Index verification complete")


def main():
    """Main initialization"""
    try:
        # Check API key
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-proj-YOUR"):
            logger.error("❌ OPENAI_API_KEY not configured in .env")
            logger.error("Get one from: https://platform.openai.com/api-keys")
            sys.exit(1)
        
        # Backup existing corrupted index
        backup_existing_chroma()
        
        # Create tagged descriptions
        books_df = create_tagged_descriptions()
        
        # Build Chroma index
        build_chroma_index()
        
        # Verify it works
        verify_index(books_df)
        
        logger.info("\n" + "="*60)
        logger.info("✅ Chroma initialization complete!")
        logger.info("="*60)
        logger.info("\nYou can now start the FastAPI server:")
        logger.info("  python main.py")
        logger.info("\nOr test the API:")
        logger.info('  curl -X POST http://localhost:5000/recommend -H "Content-Type: application/json" -d \'{"book":"1984","top_k":5}\'')
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
