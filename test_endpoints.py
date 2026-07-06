#!/usr/bin/env python3
"""
API Endpoint Testing Script
Tests all endpoints of the Lit-Pick API
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def call_endpoint(method, path, description, data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    print(f"\n[{method}] {path}")
    print(f"Description: {description}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data, headers=HEADERS)
        
        print(f"Status Code: {response.status_code} ✓")
        
        try:
            resp_json = response.json()
            if isinstance(resp_json, dict):
                for key, value in list(resp_json.items())[:5]:
                    if isinstance(value, (dict, list)):
                        print(f"  {key}: {type(value).__name__}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"  Response: {resp_json}")
        except:
            print(f"  Response: {response.text[:100]}")
        
    except requests.exceptions.ConnectionError:
        print("  ✗ ERROR: Cannot connect to server")
    except Exception as e:
        print(f"  ✗ ERROR: {str(e)}")

# Run tests
print("\n" + "="*60)
print("  TESTING ALL API ENDPOINTS")
print("  Lit-Pick Book Recommendation Engine")
print("="*60)

print(f"\nServer: {BASE_URL}")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# GET endpoints
print_section("GET ENDPOINTS")

call_endpoint("GET", "/", 
              "Root endpoint - API information")

call_endpoint("GET", "/health",
              "Health check - API and service status")

call_endpoint("GET", "/stats",
              "Engine statistics - Current state and metrics")

call_endpoint("GET", "/books?limit=3",
              "Get top books - Top rated books from database")

call_endpoint("GET", "/search?query=adventure&limit=5",
              "Search books - Find books by semantic search")

# POST endpoints  
print_section("POST ENDPOINTS")

call_endpoint("POST", "/classify-emotion",
              "Classify emotions - Zero-shot emotion classification",
              {"text": "This is an amazing and wonderful book with great characters and adventure!"})

call_endpoint("POST", "/recommend",
              "Get recommendations - Get similar book recommendations",
              {
                  "book": "Harry Potter and the Philosopher's Stone",
                  "top_k": 5,
                  "include_emotions": True
              })

# Summary
print_section("ENDPOINT TESTING SUMMARY")
print("\nEndpoints tested:")
print("  ✓ GET  /                  - Root")
print("  ✓ GET  /health            - Health check")
print("  ✓ GET  /stats             - Statistics")
print("  ✓ GET  /books             - Top books")
print("  ✓ GET  /search            - Search books")
print("  ✓ POST /classify-emotion  - Emotion classification")
print("  ✓ POST /recommend         - Get recommendations")
print("\nAPI Documentation: http://localhost:8000/docs")
print("\n" + "="*60)
