#!/usr/bin/env python3
"""
Load & Performance Tests
Tests system under concurrent load
Measures: Response times, memory usage, throughput
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import ConversationOrchestrator
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics


class LoadTester:
    """Load testing utility"""
    
    def __init__(self):
        self.results = []
        self.errors = []
        self.lock = threading.Lock()
    
    def single_conversation(self, session_id: int, brand_id: str = "fashionhub"):
        """Run a single conversation"""
        messages = [
            "Hello!",
            "Where is my order?",
            "Thank you"
        ]
        
        start_time = time.time()
        
        try:
            orch = ConversationOrchestrator(brand_id=brand_id)
            
            response_times = []
            
            for msg in messages:
                msg_start = time.time()
                response, metadata = orch.process_message(msg)
                msg_duration = (time.time() - msg_start) * 1000
                response_times.append(msg_duration)
            
            total_duration = (time.time() - start_time) * 1000
            
            with self.lock:
                self.results.append({
                    'session_id': session_id,
                    'total_duration': total_duration,
                    'avg_response_time': statistics.mean(response_times),
                    'max_response_time': max(response_times),
                    'success': True
                })
            
            return True
            
        except Exception as e:
            with self.lock:
                self.errors.append({
                    'session_id': session_id,
                    'error': str(e)
                })
            return False
    
    def run_concurrent_test(self, num_conversations: int = 50, max_workers: int = 10):
        """Run concurrent conversations"""
        print(f"\n{'='*70}")
        print(f"RUNNING {num_conversations} CONCURRENT CONVERSATIONS")
        print(f"Max Workers: {max_workers}")
        print(f"{'='*70}")
        print()
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.single_conversation, i)
                for i in range(num_conversations)
            ]
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 10 == 0:
                    print(f"Completed: {completed}/{num_conversations}")
        
        total_time = time.time() - start_time
        
        return total_time
    
    def analyze_results(self):
        """Analyze load test results"""
        if not self.results:
            return {
                'success_rate': 0,
                'total_tests': 0
            }
        
        durations = [r['total_duration'] for r in self.results]
        avg_times = [r['avg_response_time'] for r in self.results]
        max_times = [r['max_response_time'] for r in self.results]
        
        return {
            'total_tests': len(self.results) + len(self.errors),
            'successful': len(self.results),
            'failed': len(self.errors),
            'success_rate': (len(self.results) / (len(self.results) + len(self.errors))) * 100,
            'total_duration': {
                'min': min(durations),
                'max': max(durations),
                'avg': statistics.mean(durations),
                'p50': statistics.median(durations),
                'p95': sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0]
            },
            'response_time': {
                'avg': statistics.mean(avg_times),
                'max': max(max_times),
                'p95': sorted(avg_times)[int(len(avg_times) * 0.95)] if len(avg_times) > 1 else avg_times[0]
            }
        }


def test_performance_single():
    """Test single conversation performance"""
    print("\n" + "="*70)
    print("TEST: Single Conversation Performance")
    print("="*70)
    print()
    
    orch = ConversationOrchestrator(brand_id="fashionhub")
    
    messages = [
        "Where is my order 12345?",
        "When will it arrive?",
        "Can I track it?",
        "What's your return policy?",
        "Thank you!"
    ]
    
    response_times = []
    
    for i, msg in enumerate(messages, 1):
        start = time.time()
        response, metadata = orch.process_message(msg)
        duration = (time.time() - start) * 1000
        
        response_times.append(duration)
        print(f"Turn {i}: {duration:.0f}ms")
    
    avg_time = statistics.mean(response_times)
    max_time = max(response_times)
    
    print()
    print(f"Average Response Time: {avg_time:.0f}ms")
    print(f"Max Response Time: {max_time:.0f}ms")
    
    # Check performance thresholds
    if avg_time < 3000:
        print("✅ Performance: EXCELLENT (<3s avg)")
    elif avg_time < 5000:
        print("✅ Performance: GOOD (<5s avg)")
    else:
        print("⚠️  Performance: SLOW (>5s avg)")
    
    return avg_time < 5000


def test_concurrent_load():
    """Test concurrent load (50 conversations)"""
    print("\n" + "="*70)
    print("TEST: Concurrent Load (50 Conversations)")
    print("="*70)
    print()
    
    tester = LoadTester()
    
    # Run 50 concurrent conversations
    total_time = tester.run_concurrent_test(num_conversations=50, max_workers=10)
    
    # Analyze results
    analysis = tester.analyze_results()
    
    print()
    print("="*70)
    print("LOAD TEST RESULTS")
    print("="*70)
    print()
    print(f"Total Tests: {analysis['total_tests']}")
    print(f"Successful: {analysis['successful']}")
    print(f"Failed: {analysis['failed']}")
    print(f"Success Rate: {analysis['success_rate']:.1f}%")
    print()
    print(f"Total Execution Time: {total_time:.2f}s")
    print(f"Throughput: {analysis['total_tests']/total_time:.2f} conversations/sec")
    print()
    print("Conversation Duration:")
    print(f"  Avg: {analysis['total_duration']['avg']:.0f}ms")
    print(f"  P50: {analysis['total_duration']['p50']:.0f}ms")
    print(f"  P95: {analysis['total_duration']['p95']:.0f}ms")
    print(f"  Max: {analysis['total_duration']['max']:.0f}ms")
    print()
    print("Response Time per Message:")
    print(f"  Avg: {analysis['response_time']['avg']:.0f}ms")
    print(f"  P95: {analysis['response_time']['p95']:.0f}ms")
    print(f"  Max: {analysis['response_time']['max']:.0f}ms")
    print()
    
    # Check thresholds
    checks = {
        'success_rate': analysis['success_rate'] >= 95,
        'avg_response_time': analysis['response_time']['avg'] < 3000,
        'p95_response_time': analysis['response_time']['p95'] < 5000
    }
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("✅ ALL LOAD TEST THRESHOLDS PASSED!")
        print("✅ Success Rate: >95%")
        print("✅ Avg Response: <3s")
        print("✅ P95 Response: <5s")
    else:
        print("⚠️  SOME THRESHOLDS NOT MET:")
        if not checks['success_rate']:
            print(f"   ❌ Success Rate: {analysis['success_rate']:.1f}% (target: >95%)")
        if not checks['avg_response_time']:
            print(f"   ❌ Avg Response: {analysis['response_time']['avg']:.0f}ms (target: <3000ms)")
        if not checks['p95_response_time']:
            print(f"   ❌ P95 Response: {analysis['response_time']['p95']:.0f}ms (target: <5000ms)")
    
    return all_passed


def run_all_performance_tests():
    """Run all performance tests"""
    
    print("🧪 LOAD & PERFORMANCE TEST SUITE")
    print("=" * 70)
    print()
    
    tests = [
        ("Single Conversation", test_performance_single),
        ("Concurrent Load", test_concurrent_load)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("PERFORMANCE TEST SUMMARY")
    print("="*70)
    print()
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"Tests Passed: {passed_count}/{total_count}")
    print()
    
    if passed_count == total_count:
        print("🎉 ALL PERFORMANCE TESTS PASSED!")
        print("✅ System performs well under load")
        return True
    else:
        print(f"⚠️  {total_count - passed_count} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_performance_tests()
    sys.exit(0 if success else 1)
