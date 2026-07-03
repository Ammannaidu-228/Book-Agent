# Book Recommendation AI - Project Structure

```
📚 book-agent/
├── 📁 src/                              # Main source code (agentic AI modules)
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry point
│   │
│   ├── 📁 agents/                       # Agentic AI implementations
│   │   └── __init__.py
│   │
│   ├── 📁 api/                          # API routes and schemas
│   │   ├── __init__.py
│   │   ├── schemas.py                   # Pydantic request/response models
│   │   └── routes.py                    # (Optional) Separate route definitions
│   │
│   ├── 📁 core/                         # Core business logic
│   │   ├── __init__.py
│   │   ├── recommendation.py            # Recommendation engine
│   │   ├── classifier.py                # Emotion classifier
│   │   ├── embeddings.py                # RAG pipeline & vector search
│   │   └── orchestrator.py              # (Optional) Agent orchestration
│   │
│   ├── 📁 database/                     # Data persistence layer
│   │   ├── __init__.py
│   │   ├── database.py                  # MongoDB connection & initialization
│   │   └── db_models.py                 # Document schema creators
│   │
│   └── 📁 config/                       # Configuration management
│       ├── __init__.py
│       └── settings.py                  # Pydantic settings
│
├── 📁 data/                             # Data files (raw & processed)
│   ├── raw/                             # Original data files
│   │   ├── books_cleaned.csv
│   │   ├── books_with_categories.csv
│   │   └── books_with_emotions.csv
│   ├── processed/                       # Generated/processed data
│   └── embeddings/                      # Stored embeddings (if needed)
│
├── 📁 notebooks/                        # Jupyter notebooks (exploration/analysis)
│   ├── data-explorer.ipynb
│   ├── sentiment-analysis.ipynb
│   ├── text-classification.ipynb
│   └── vector-search.ipynb
│
├── 📁 frontend/                         # React UI (LitPick-Ui moved here)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── README.md
│
├── 📁 tests/                            # Test suite
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_client.py
│   ├── conftest.py
│   └── test_recommendation.py            # (Optional) Additional tests
│
├── 📁 scripts/                          # Utility & setup scripts
│   ├── __init__.py
│   ├── init_chroma.py                   # Vector DB initialization
│   ├── load_data.py                     # Data loading
│   ├── verify.py                        # Verification utility
│   ├── setup.sh                         # Linux/Mac setup
│   └── setup.bat                        # Windows setup
│
├── 📁 docs/                             # Documentation
│   ├── ARCHITECTURE.md                  # System design & diagrams
│   ├── SETUP_GUIDE.md                   # Installation & configuration
│   ├── QUICKSTART.md                    # Quick start guide
│   ├── DEPLOYMENT.md                    # Deployment instructions
│   ├── TESTING.md                       # Testing documentation
│   └── API_REFERENCE.md                 # (Optional) API documentation
│
├── 📁 logs/                             # Application logs (runtime generated)
│   └── .gitkeep
│
├── 📁 chroma_db/                        # Vector database storage
│   └── (runtime generated)
│
├── .env.example                         # Environment variables template
├── .env                                 # Environment variables (GITIGNORED)
├── requirements.txt                     # Python dependencies
├── Dockerfile                           # Docker image definition
├── docker-compose.yml                   # Docker Compose orchestration
├── pyproject.toml                       # Project metadata & build config
├── pytest.ini                           # Pytest configuration
├── .gitignore                           # Git ignore rules
├── README.md                            # Project overview
├── INDEX.md                             # Document index
├── MANIFEST.md                          # Delivery manifest
└── PROJECT_STRUCTURE.md                 # This file
```

## Directory Descriptions

### `src/` - Source Code
All application source code organized into logical modules following agentic AI principles:

- **agents/** - Agentic AI components (tools, agents, workflows)
- **api/** - HTTP API layer (schemas, routes, middleware)
- **core/** - Business logic (recommendation engine, ML models, RAG pipeline)
- **database/** - Data persistence (MongoDB, schema definitions)
- **config/** - Configuration management (environment variables, settings)

### `data/` - Data Management
Organized data directory:

- **raw/** - Original CSV data files
- **processed/** - Derived/transformed data
- **embeddings/** - Cached embeddings (optional)

### `notebooks/` - Jupyter Notebooks
Exploratory and analytical notebooks kept separate from production code.

### `frontend/` - React Application
React + Vite frontend moved from `LitPick-Ui/` for consistency.

### `tests/` - Test Suite
Centralized test directory with unit, integration, and API tests.

### `scripts/` - Utility Scripts
Build, setup, and maintenance scripts:
- Data loading
- Vector database initialization
- Verification utilities

### `docs/` - Documentation
Comprehensive documentation:
- Architecture overview
- Setup and deployment guides
- API reference
- Testing documentation

## Module Dependencies

```
main.py (FastAPI app)
  ├── src.config.settings              # Configuration
  ├── src.database                     # MongoDB operations
  ├── src.api.schemas                  # Request/Response models
  └── src.core                         # Business logic
      ├── recommendation.py            # Engine core
      ├── classifier.py                # ML models
      └── embeddings.py                # RAG pipeline
```

## Running the Application

### Development
```bash
# From project root
cd src
python -m uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

### Production
```bash
# Using Docker
docker-compose up

# Or using Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app
```

## Environment Setup

1. Copy `.env.example` to `.env`
2. Configure required environment variables
3. Run setup scripts from `scripts/` directory
4. Initialize vector database: `python -m scripts.init_chroma`

## Import Patterns

All imports follow the new structure:

```python
# ✅ Correct
from src.config import settings
from src.core import get_recommendation_engine
from src.database import get_db
from src.api import RecommendationRequest

# ❌ Incorrect (old style)
from config import settings
from recommendation import get_recommendation_engine
```

## Key Features

- **Modular Architecture**: Clean separation of concerns
- **Type Safety**: Pydantic models for all I/O
- **Async Support**: Full async/await implementation
- **Lazy Loading**: Models load on first request
- **Comprehensive Logging**: Detailed operation tracking
- **Production Ready**: Docker, error handling, monitoring

---

**Last Updated**: 2026-07-03
