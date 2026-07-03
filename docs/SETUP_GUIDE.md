# Lit-Pick Backend - Setup Guide

## Issues Fixed ✅

1. **Deprecation Warnings**: Converted from deprecated `@app.on_event()` to modern `lifespan` event handlers
2. **Worker Crashes**: Fixed child process crashes by:
   - Making startup non-blocking 
   - Deferring heavy model loading to first use
   - Adding graceful error handling for missing API keys
3. **Better Error Messages**: Added clear guidance when services are unavailable

## Quick Setup

### 1. Configure Environment Variables (.env)

Edit your `.env` file with:

```bash
# Get OpenAI API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-your_actual_key_here

# MongoDB connection (optional - needed only for storing recommendations)
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=litpick

# Other optional settings
HF_TOKEN=hf_your_token_here  # For private Hugging Face models
```

### 2. Start the Server

```bash
python main.py
```

The server will now start successfully and show:
- ✅ Database initialization (or graceful skip if MongoDB unavailable)
- ✅ Models will load on first API request
- ✅ Server ready at http://0.0.0.0:5000

### 3. Verify It's Working

```bash
# Health check
curl http://localhost:5000/health

# Test emotion classification
curl -X POST http://localhost:5000/classify-emotion \
  -H "Content-Type: application/json" \
  -d '{"text": "I loved this thrilling adventure!"}'
```

## How It Works Now

### Lazy Model Loading
- Heavy models (BART, OpenAI embeddings) only load when first needed
- Faster startup, better resource management
- On first API call requiring the model, there's a slight delay for loading

### Graceful Degradation
- Missing OpenAI API key? You can still use emotion classification
- MongoDB down? Other endpoints still work
- Model download fails? Clear error message pointing to solution

### Health Check Endpoint
Returns service status:
```
{
  "status": "healthy" | "degraded",
  "database_connected": boolean,
  "vector_db_connected": boolean,
  "model_loaded": boolean,
  "timestamp": "ISO-8601 timestamp"
}
```

## Troubleshooting

### "OPENAI_API_KEY not configured"
✅ Solution: Get a key from https://platform.openai.com/api-keys and add to .env

### Models downloading on first run
✅ Expected: BART model (~1.6GB) will download once from Hugging Face
- Internet connection required
- First request takes 1-2 minutes

### "Could not connect to MongoDB"
✅ Optional - the API works without it. Only needed for storing recommendations.
- Either start MongoDB locally or remove those API endpoints

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Service health check |
| POST | `/classify-emotion` | Classify emotions in text |
| POST | `/recommend` | Get book recommendations |
| GET | `/search` | Search books by query |
| GET | `/book/{title}` | Get book analysis with emotions |

## Performance Notes

- **First request takes longer** due to model initialization
- **Subsequent requests** are fast (models stay in memory)
- **CUDA available?** Emotion classification automatically uses GPU
- **Memory usage**: ~4-6GB when all models loaded (BART + embeddings)

## Next Steps

1. Get your [OpenAI API key](https://platform.openai.com/api-keys)
2. Add it to `.env`
3. Run `python main.py`
4. Try the endpoints!

---

For more details, see [BACKEND_README.md](BACKEND_README.md)
