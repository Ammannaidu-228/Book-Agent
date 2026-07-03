# Migration Guide: New Project Structure

## Overview

The Book Recommendation project has been reorganized from a flat structure to a professional agentic AI project structure. This guide helps you understand and adapt to the new organization.

## Old vs New Structure

### Before (Flat)
```
Book-agent/
├── main.py
├── config.py
├── database.py
├── recommendation.py
├── classifier.py
├── embeddings.py
├── schemas.py
├── db_models.py
├── requirements.txt
├── *.csv (data files)
├── *.ipynb (notebooks)
└── ...
```

### After (Organized)
```
Book-agent/
├── src/
│   ├── main.py
│   ├── config/settings.py
│   ├── database/
│   ├── core/
│   │   ├── recommendation.py
│   │   ├── classifier.py
│   │   └── embeddings.py
│   └── api/schemas.py
├── data/raw/ (CSV files)
├── notebooks/ (Jupyter files)
└── ...
```

## Import Migration

### Configuration
```python
# OLD
from config import settings

# NEW
from src.config import settings
```

### Database
```python
# OLD
from database import init_db, get_db

# NEW
from src.database import init_db, get_db
```

### Core Modules
```python
# OLD
from recommendation import get_recommendation_engine
from classifier import get_classifier
from embeddings import get_rag_pipeline

# NEW
from src.core import get_recommendation_engine, get_classifier, get_rag_pipeline
# OR
from src.core.recommendation import RecommendationEngine
from src.core.classifier import EmotionClassifier
from src.core.embeddings import RAGPipeline
```

### API Schemas
```python
# OLD
from schemas import RecommendationRequest, RecommendationResponse

# NEW
from src.api import RecommendationRequest, RecommendationResponse
```

### Database Models
```python
# OLD
from db_models import create_book_document

# NEW
from src.database import create_book_document
```

## Running the Application

### Before
```bash
# Root directory
python main.py
python -m uvicorn main:app --reload
```

### After
```bash
# From project root (or in src directory)
cd src
python -m uvicorn main:app --reload

# Or from root:
python -m uvicorn src.main:app --reload
```

## Running Scripts

### Before
```bash
python init_chroma.py
python load_data.py
```

### After
```bash
# From project root
python -m scripts.init_chroma
python -m scripts.load_data

# Or navigate to scripts directory
cd scripts
python init_chroma.py
```

## Running Tests

### Before
```bash
pytest test_api.py
pytest test_client.py
```

### After
```bash
# From project root
pytest tests/
pytest tests/test_api.py
pytest -v  # Verbose output
```

## Using Notebooks

Notebooks remain in `notebooks/` directory but should import from new structure:

```python
# In Jupyter cells
import sys
sys.path.insert(0, '..')  # Go up to project root

from src.config import settings
from src.core import get_recommendation_engine
from src.database import get_db
```

## Data Files

Data files have moved to `data/` directory:

```
data/
├── raw/
│   ├── books_cleaned.csv
│   ├── books_with_categories.csv
│   └── books_with_emotions.csv
└── processed/
```

Update file paths if hardcoded:

```python
# OLD
df = pd.read_csv("books_with_emotions.csv")

# NEW
df = pd.read_csv("data/raw/books_with_emotions.csv")
```

## Environment Variables

The `.env` file remains at project root but make sure you have proper setup:

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
# Then run application
python -m uvicorn src.main:app --reload
```

## Frontend Setup

Frontend moved from `LitPick-Ui/` to `frontend/`:

```bash
cd frontend
npm install
npm run dev  # Development
npm run build  # Production
```

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'src'`

**Solution**: 
- Make sure you're running from project root
- Or add project root to PYTHONPATH: `export PYTHONPATH=$PYTHONPATH:.`

### Issue: `Cannot find 'books_with_emotions.csv'`

**Solution**:
- File moved to `data/raw/books_with_emotions.csv`
- Update hardcoded paths OR
- Run from project root where relative paths work

### Issue: Imports not working in Jupyter

**Solution**:
```python
import sys
sys.path.insert(0, '..')  # Adjust based on notebook location
from src.config import settings
```

### Issue: Tests not discovering files

**Solution**:
- Ensure you're running pytest from project root
- Check `pytest.ini` configuration

## Best Practices

1. **Always import from `src.`**: Makes code portable and clear
2. **Run from project root**: Simplifies path resolution
3. **Use relative imports within modules**: Keep internal organization flexible
4. **Document any custom paths**: If you add new modules, document import patterns
5. **Use Python modules properly**: Each directory should have `__init__.py`

## Checklist for Migration

- [ ] Update all imports to use `src.*` pattern
- [ ] Update data file paths to use `data/` directories
- [ ] Test imports with Python interpreter
- [ ] Run test suite: `pytest tests/`
- [ ] Verify API starts: `python -m uvicorn src.main:app --reload`
- [ ] Test key endpoints: `/health`, `/recommend`
- [ ] Update any CI/CD scripts with new paths
- [ ] Update Docker/Kubernetes configs if applicable

## Questions?

Refer to:
- `PROJECT_STRUCTURE.md` - Detailed directory structure
- `docs/ARCHITECTURE.md` - System design overview
- `docs/QUICKSTART.md` - Quick start guide

