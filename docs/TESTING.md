# 🧪 Lit-Pick Backend - Testing Guide

## Test Categories

1. **Unit Tests**: Individual components
2. **Integration Tests**: Component interactions
3. **Performance Tests**: Load and latency
4. **Functional Tests**: API endpoints

## Prerequisites

```powershell
pip install pytest pytest-asyncio pytest-cov httpx
```

## Quick Test

```powershell
# Check if backend is running
curl http://localhost:5000/health

# Test recommendation
curl -X POST http://localhost:5000/recommend ^
  -H "Content-Type: application/json" ^
  -d "{\"book\": \"1984\"}"
```

## Performance Benchmarking

### Basic Benchmarks

```powershell
# Run complete benchmark suite
python benchmark.py

# Expected output:
# - Health check: ~20ms
# - Recommendations: ~145ms p99
# - Search: ~80ms
# - Emotion classification: ~50ms
# - Concurrent load: 5000+ QPS
```

### Detailed Load Testing

```python
# Create detailed_benchmark.py
import asyncio
import httpx
import time
from statistics import mean, stdev

async def load_test(concurrent_requests=100, duration=60):
    """Sustained load test"""
    async with httpx.AsyncClient() as client:
        results = []
        start_time = time.time()
        
        async def make_request():
            try:
                start = time.time()
                response = await client.post(
                    'http://localhost:5000/recommend',
                    json={'book': '1984', 'top_k': 10}
                )
                return time.time() - start
            except:
                return None
        
        while time.time() - start_time < duration:
            tasks = [make_request() for _ in range(concurrent_requests)]
            times = await asyncio.gather(*tasks)
            results.extend([t for t in times if t])
        
        print(f"Requests: {len(results)}")
        print(f"QPS: {len(results) / duration:.2f}")
        print(f"Mean: {mean(results)*1000:.2f}ms")
        print(f"Stdev: {stdev(results)*1000:.2f}ms")
        print(f"Min: {min(results)*1000:.2f}ms")
        print(f"Max: {max(results)*1000:.2f}ms")

asyncio.run(load_test())
```

## Test Scenarios

### Scenario 1: Happy Path

```python
"""
Test successful recommendation flow
"""
import requests

def test_happy_path():
    # 1. Health check
    response = requests.get('http://localhost:5000/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    
    # 2. Get recommendations
    response = requests.post('http://localhost:5000/recommend', json={
        'book': '1984',
        'top_k': 10,
        'include_emotions': True
    })
    assert response.status_code == 200
    data = response.json()
    
    # Assertions
    assert data['query_book'] == '1984'
    assert len(data['recommendations']) > 0
    assert all('title' in rec for rec in data['recommendations'])
    assert all('similarity_score' in rec for rec in data['recommendations'])
    assert all('emotions' in rec for rec in data['recommendations'])
    assert data['processing_time_ms'] < 200
    
    print("✅ Happy path test passed")

if __name__ == '__main__':
    test_happy_path()
```

### Scenario 2: Error Handling

```python
"""
Test error scenarios
"""
import requests

def test_book_not_found():
    response = requests.post('http://localhost:5000/recommend', json={
        'book': 'NonExistentBook12345XYZ'
    })
    assert response.status_code == 404
    print("✅ Book not found handled correctly")

def test_invalid_request():
    response = requests.post('http://localhost:5000/recommend', json={})
    assert response.status_code == 422  # Validation error
    print("✅ Invalid request handled correctly")

def test_long_query():
    response = requests.post('http://localhost:5000/recommend', json={
        'book': '1984',
        'top_k': 1000  # Exceeds limit
    })
    # Should be capped at 50
    assert response.status_code == 200
    data = response.json()
    assert len(data['recommendations']) <= 50
    print("✅ Query limits enforced")
```

### Scenario 3: Concurrent Requests

```python
"""
Test concurrent request handling
"""
import requests
import concurrent.futures
import time

def test_concurrent():
    def make_request(book):
        try:
            response = requests.post('http://localhost:5000/recommend', json={
                'book': book,
                'top_k': 5
            })
            return response.status_code == 200
        except:
            return False
    
    books = ['1984', 'Brave New World', 'The Great Gatsby'] * 100
    
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(make_request, books))
    
    elapsed = time.time() - start
    success_rate = sum(results) / len(results)
    
    print(f"Concurrent requests: {len(results)}")
    print(f"Success rate: {success_rate:.1%}")
    print(f"Time: {elapsed:.2f}s")
    print(f"QPS: {len(results)/elapsed:.2f}")
    
    assert success_rate > 0.95  # 95% success minimum
    print("✅ Concurrent handling test passed")

if __name__ == '__main__':
    test_concurrent()
```

### Scenario 4: Search and Classification

```python
"""
Test search and classification features
"""
import requests

def test_search():
    response = requests.get('http://localhost:5000/search', params={
        'query': 'dystopian fiction',
        'limit': 10
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data['results']) > 0
    print("✅ Search test passed")

def test_emotion_classification():
    response = requests.post('http://localhost:5000/classify-emotion', json={
        'text': 'A thrilling adventure through dark forests'
    })
    assert response.status_code == 200
    data = response.json()
    assert 'emotions' in data
    assert 'top_emotion' in data
    assert 'confidence' in data
    print("✅ Emotion classification test passed")

if __name__ == '__main__':
    test_search()
    test_emotion_classification()
```

## API Endpoint Testing

### Using curl

```bash
# Health check
curl http://localhost:5000/health

# Recommendation
curl -X POST http://localhost:5000/recommend \
  -H "Content-Type: application/json" \
  -d '{"book": "1984", "top_k": 10}'

# Search
curl "http://localhost:5000/search?query=mystery&limit=5"

# Emotion classification
curl -X POST http://localhost:5000/classify-emotion \
  -H "Content-Type: application/json" \
  -d '{"text": "An exciting mystery novel"}'

# Book analysis
curl "http://localhost:5000/book/1984"

# Stats
curl http://localhost:5000/stats
```

### Using Python Client

```python
from client import LitPickClient

client = LitPickClient()

# Test all endpoints
print(client.health_check())
print(client.get_recommendations("1984", top_k=5))
print(client.classify_emotion("A dark novel"))
print(client.search_books("dystopian"))
print(client.get_book_analysis("1984"))
```

## Monitoring & Debugging

### Enable Debug Logging

```python
# In config.py
SQLALCHEMY_ECHO = True  # Log SQL
DEBUG = True            # Log verbose output
```

### Monitor Database

```sql
-- Check query performance
SELECT * FROM pg_stat_statements ORDER BY mean_time DESC;

-- Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) 
FROM pg_stat_user_tables 
ORDER BY pg_total_relation_size(relid) DESC;

-- Check active connections
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;
```

### Monitor Vectors

```python
# Check Chroma collection stats
from embeddings import get_rag_pipeline
rag = get_rag_pipeline()
print(rag.get_collection_stats())
```

## Profiling

### Profile Recommendation Endpoint

```python
import cProfile
import pstats
from io import StringIO

pr = cProfile.Profile()
pr.enable()

# Make request
import requests
requests.post('http://localhost:5000/recommend', json={'book': '1984'})

pr.disable()
s = StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(10)
print(s.getvalue())
```

## Continuous Testing

### GitHub Actions Example

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
      redis:
        image: redis:7
    
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/
      - run: python benchmark.py
```

## Performance Regression Testing

```python
"""
Track performance over time
"""
import json
from datetime import datetime

BASELINE = {
    'health_check': 50,
    'recommendation': 200,
    'search': 150,
    'emotion': 100
}

def compare_performance(current_metrics):
    """Compare current metrics with baseline"""
    results = {}
    
    for key, baseline_value in BASELINE.items():
        current_value = current_metrics.get(key, 0)
        variance = ((current_value - baseline_value) / baseline_value) * 100
        
        status = "✅" if variance < 10 else "⚠️" if variance < 20 else "❌"
        results[key] = {
            'baseline': baseline_value,
            'current': current_value,
            'variance': variance,
            'status': status
        }
    
    return results

if __name__ == '__main__':
    # After running benchmarks
    metrics = {
        'health_check': 22,
        'recommendation': 148,
        'search': 82,
        'emotion': 52
    }
    
    results = compare_performance(metrics)
    for key, value in results.items():
        print(f"{value['status']} {key}: {value['variance']:.1f}%")
```

## Deployment Testing

### Pre-deployment Checklist

- [ ] All unit tests pass
- [ ] Performance benchmarks within targets
- [ ] Load test successful (100+ concurrent)
- [ ] Database migrations applied
- [ ] Vector DB populated
- [ ] Models loaded successfully
- [ ] API documentation generated
- [ ] Security checks passed
- [ ] Logging configured
- [ ] Monitoring setup

### Smoke Test

```bash
# After deployment
curl https://your-domain.com/health
curl -X POST https://your-domain.com/recommend \
  -H "Content-Type: application/json" \
  -d '{"book": "1984"}'
```

---

See `benchmark.py` for automated performance testing suite.
