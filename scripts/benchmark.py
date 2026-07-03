"""
Performance testing and benchmarking for Lit-Pick backend
"""
import asyncio
import time
import requests
import statistics
import json
from typing import List, Dict
import concurrent.futures

BASE_URL = "http://localhost:5000"

# Test data
TEST_BOOKS = [
    "1984",
    "Brave New World",
    "The Great Gatsby",
    "To Kill a Mockingbird",
    "Pride and Prejudice",
    "The Catcher in the Rye",
    "Jane Eyre",
    "Wuthering Heights",
    "Moby Dick",
    "The Lord of the Rings"
]

TEST_SEARCHES = [
    "dystopian fiction",
    "romance adventure",
    "mystery thriller",
    "historical fiction",
    "science fiction"
]


class PerformanceTester:
    """Performance testing suite"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = {}
    
    def test_health_check(self, iterations: int = 100):
        """Test health check endpoint"""
        print(f"\n📊 Testing Health Check ({iterations} iterations)...")
        
        times = []
        failures = 0
        
        for _ in range(iterations):
            try:
                start = time.time()
                response = requests.get(f"{self.base_url}/health")
                elapsed = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    times.append(elapsed)
                else:
                    failures += 1
            except Exception as e:
                failures += 1
        
        stats = self._calculate_stats(times)
        stats['failures'] = failures
        self.results['health_check'] = stats
        
        self._print_stats("Health Check", stats)
        return stats
    
    def test_recommendations(self, iterations: int = 50):
        """Test recommendation endpoint"""
        print(f"\n🎯 Testing Recommendations ({iterations} iterations)...")
        
        times = []
        failures = 0
        
        for i in range(iterations):
            try:
                book = TEST_BOOKS[i % len(TEST_BOOKS)]
                start = time.time()
                
                response = requests.post(
                    f"{self.base_url}/recommend",
                    json={"book": book, "top_k": 10},
                    timeout=30
                )
                
                elapsed = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    times.append(elapsed)
                else:
                    failures += 1
            except Exception as e:
                failures += 1
        
        stats = self._calculate_stats(times)
        stats['failures'] = failures
        self.results['recommendations'] = stats
        
        self._print_stats("Recommendations", stats)
        return stats
    
    def test_search(self, iterations: int = 50):
        """Test search endpoint"""
        print(f"\n🔍 Testing Search ({iterations} iterations)...")
        
        times = []
        failures = 0
        
        for i in range(iterations):
            try:
                query = TEST_SEARCHES[i % len(TEST_SEARCHES)]
                start = time.time()
                
                response = requests.get(
                    f"{self.base_url}/search",
                    params={"query": query, "limit": 10},
                    timeout=30
                )
                
                elapsed = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    times.append(elapsed)
                else:
                    failures += 1
            except Exception as e:
                failures += 1
        
        stats = self._calculate_stats(times)
        stats['failures'] = failures
        self.results['search'] = stats
        
        self._print_stats("Search", stats)
        return stats
    
    def test_emotion_classification(self, iterations: int = 50):
        """Test emotion classification endpoint"""
        print(f"\n😊 Testing Emotion Classification ({iterations} iterations)...")
        
        test_texts = [
            "A thrilling adventure full of mystery and wonder",
            "A sad and melancholic tale of lost love",
            "An exciting journey through dark forests",
            "A humorous and light-hearted story",
            "A thought-provoking narrative about society"
        ]
        
        times = []
        failures = 0
        
        for i in range(iterations):
            try:
                text = test_texts[i % len(test_texts)]
                start = time.time()
                
                response = requests.post(
                    f"{self.base_url}/classify-emotion",
                    json={"text": text},
                    timeout=30
                )
                
                elapsed = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    times.append(elapsed)
                else:
                    failures += 1
            except Exception as e:
                failures += 1
        
        stats = self._calculate_stats(times)
        stats['failures'] = failures
        self.results['emotion_classification'] = stats
        
        self._print_stats("Emotion Classification", stats)
        return stats
    
    def test_concurrent_load(self, concurrent_requests: int = 10, duration_seconds: int = 30):
        """Test concurrent load"""
        print(f"\n⚡ Testing Concurrent Load ({concurrent_requests} concurrent, {duration_seconds}s)...")
        
        times = []
        failures = 0
        request_count = 0
        
        def make_request():
            try:
                book = TEST_BOOKS[request_count % len(TEST_BOOKS)]
                start = time.time()
                
                response = requests.post(
                    f"{self.base_url}/recommend",
                    json={"book": book, "top_k": 5},
                    timeout=30
                )
                
                elapsed = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    return elapsed, True
                else:
                    return elapsed, False
            except Exception as e:
                return None, False
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            while time.time() - start_time < duration_seconds:
                futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
                
                for future in concurrent.futures.as_completed(futures):
                    elapsed, success = future.result()
                    request_count += 1
                    
                    if success and elapsed:
                        times.append(elapsed)
                    else:
                        failures += 1
        
        stats = self._calculate_stats(times)
        stats['failures'] = failures
        stats['total_requests'] = request_count
        stats['qps'] = request_count / duration_seconds
        self.results['concurrent_load'] = stats
        
        self._print_stats(f"Concurrent Load ({concurrent_requests} workers)", stats)
        return stats
    
    def _calculate_stats(self, times: List[float]) -> Dict:
        """Calculate statistics from timings"""
        if not times:
            return {
                'min': 0, 'max': 0, 'mean': 0, 'median': 0,
                'p95': 0, 'p99': 0, 'stdev': 0, 'requests': 0
            }
        
        sorted_times = sorted(times)
        
        return {
            'min': min(times),
            'max': max(times),
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'p95': sorted_times[int(len(sorted_times) * 0.95)],
            'p99': sorted_times[int(len(sorted_times) * 0.99)],
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'requests': len(times)
        }
    
    def _print_stats(self, name: str, stats: Dict):
        """Print formatted statistics"""
        print(f"\n{name} Results:")
        print(f"  Min:     {stats.get('min', 0):.2f}ms")
        print(f"  Max:     {stats.get('max', 0):.2f}ms")
        print(f"  Mean:    {stats.get('mean', 0):.2f}ms")
        print(f"  Median:  {stats.get('median', 0):.2f}ms")
        print(f"  Stdev:   {stats.get('stdev', 0):.2f}ms")
        print(f"  P95:     {stats.get('p95', 0):.2f}ms")
        print(f"  P99:     {stats.get('p99', 0):.2f}ms")
        print(f"  Success: {stats.get('requests', 0)} requests")
        print(f"  Failures: {stats.get('failures', 0)}")
        
        if stats.get('qps'):
            print(f"  QPS:     {stats['qps']:.2f}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📈 PERFORMANCE TEST SUMMARY")
        print("="*60)
        
        print(json.dumps(self.results, indent=2, default=str))
        
        print("\n✅ All tests completed!")
        
        # Check if targets met
        print("\n🎯 Performance Targets:")
        recommendations_p99 = self.results.get('recommendations', {}).get('p99', 0)
        if recommendations_p99 < 200:
            print(f"  ✓ Recommendations P99 < 200ms: {recommendations_p99:.2f}ms")
        else:
            print(f"  ✗ Recommendations P99 < 200ms: {recommendations_p99:.2f}ms")
        
        concurrent_qps = self.results.get('concurrent_load', {}).get('qps', 0)
        if concurrent_qps > 100:
            print(f"  ✓ Concurrent QPS > 100: {concurrent_qps:.2f}")
        else:
            print(f"  ✗ Concurrent QPS > 100: {concurrent_qps:.2f}")


def main():
    """Run performance tests"""
    print("\n🚀 Starting Lit-Pick Backend Performance Tests")
    print(f"Target URL: {BASE_URL}")
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend not responding correctly")
            return
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    print("✅ Backend is running\n")
    
    # Run tests
    tester = PerformanceTester()
    
    try:
        tester.test_health_check(100)
        tester.test_emotion_classification(30)
        tester.test_search(30)
        tester.test_recommendations(30)
        tester.test_concurrent_load(concurrent_requests=10, duration_seconds=30)
        
        tester.print_summary()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        tester.print_summary()


if __name__ == "__main__":
    main()
