# 🚀 Lit-Pick Backend - Quick Start Guide

## Prerequisites

- Python 3.11+
- OpenAI API Key
- Git

## ⚡ Quick Start (5 minutes)

### Step 1: Setup Environment

```powershell
# Navigate to project
cd c:\Users\amman\Desktop\book-recommendation\Book-agent

# Create virtual environment (if needed)
python -m venv .venv
.venv\Scripts\activate

# Or if already in .venv
.venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 3: Configure API Keys

Copy `.env.example` to `.env` and add your OpenAI API key:

```powershell
copy .env.example .env
```

Edit `.env` and replace:
```
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
```

### Step 4: Initialize Data

```powershell
python load_data.py
```

This will:
- Create database tables
- Load books from CSV into vector DB
- Test emotion classifier

### Step 5: Run the Backend

```powershell
# Option A: Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 5000 --reload

# Option B: Using Python directly
python main.py
```

You should see:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:5000
```

### Step 6: Test the API

Open in browser: `http://localhost:5000/docs`

Or test with curl:

```powershell
# Health check
curl http://localhost:5000/health

# Get recommendations
curl -X POST http://localhost:5000/recommend `
  -H "Content-Type: application/json" `
  -d '{\"book\": \"1984\"}'

# Search books
curl "http://localhost:5000/search?query=dystopian"
```

## 🎨 Running the Frontend

In another terminal:

```powershell
# Navigate to frontend
cd LitPick-Ui

# Install dependencies (if needed)
npm install

# Run dev server
npm run dev
```

Frontend will be at: `http://localhost:5173`

## 📊 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/recommend` | POST | Get recommendations |
| `/classify-emotion` | POST | Classify emotions |
| `/search` | GET | Search books |
| `/book/{title}` | GET | Book analysis |
| `/stats` | GET | Engine stats |
| `/docs` | GET | API documentation |

## 🧪 Performance Testing

```powershell
# After backend is running, in another terminal
python benchmark.py
```

This will run comprehensive performance tests including:
- Health check latency
- Recommendation latency
- Search latency
- Concurrent load testing (10K+ QPS)

## 📝 Example Usage

### Python
```python
import requests

# Get recommendations
response = requests.post('http://localhost:5000/recommend', json={
    'book': '1984',
    'top_k': 10,
    'include_emotions': True
})

recommendations = response.json()['recommendations']
for book in recommendations:
    print(f"{book['title']} (similarity: {book['similarity_score']:.2%})")
    print(f"  Emotions: {book['emotions']}")
```

### JavaScript/React
```javascript
const response = await fetch('http://localhost:5000/recommend', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ book: '1984' })
});

const data = await response.json();
console.log(data.recommendations);
```

## 🐛 Common Issues

### Port Already in Use
```powershell
# Use different port
uvicorn main:app --port 5001
```

### OpenAI API Key Error
- Check `.env` file exists
- Verify API key is correct
- Test with: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

### CSV File Not Found
- Make sure you're in the correct directory
- Verify `books_with_emotions.csv` exists

### ModuleNotFoundError
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📚 Directory Structure

```
.
├── main.py                  ← Start here (FastAPI app)
├── config.py               ← Configuration
├── recommendation.py       ← Recommendation engine
├── classifier.py          ← Emotion classification
├── embeddings.py          ← RAG pipeline
├── load_data.py           ← Data initialization
├── books_with_emotions.csv ← Data file
├── chroma_db/             ← Vector database (created after first run)
└── LitPick-Ui/            ← Frontend
```

## 🔄 Workflow

```
User Query (Frontend)
    ↓
FastAPI Backend
    ├→ Find book in database
    ├→ Get query embedding (OpenAI)
    ├→ Search similar books (Chroma)
    ├→ Classify emotions (Transformers)
    ├→ Cache result (optional)
    └→ Return recommendations
```

## 🚀 Production Deployment

### Using Docker

```powershell
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop
docker-compose down
```

### Manual Server

```powershell
# Install gunicorn
pip install gunicorn

# Run with Gunicorn (4 workers)
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

## 📊 Performance Targets

- ✅ Recommendations: < 200ms p99
- ✅ Searches: < 150ms p99  
- ✅ Emotions: < 100ms p99
- ✅ 10K+ QPS capacity

## 🎯 Next Steps

1. ✅ Backend running
2. ✅ Frontend running
3. Try recommendations: `http://localhost:5173`
4. Monitor performance: `python benchmark.py`
5. Explore API docs: `http://localhost:5000/docs`

## 📞 Support

- Check `BACKEND_README.md` for detailed documentation
- Review logs for errors: `uvicorn main:app --log-level debug`
- See example requests in `/docs` endpoint

---

**Happy recommending! 📚🚀**
