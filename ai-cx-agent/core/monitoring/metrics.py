"""
Performance Metrics Collector
Tracks: Response times, success rates, token usage, costs
Used for: Performance monitoring, cost optimization, SLA tracking
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import statistics


@dataclass
class MetricsCollector:
    """Collects and analyzes performance metrics"""
    
    # Response time tracking
    response_times: List[float] = field(default_factory=list)
    
    # Tool call tracking
    tool_calls: Dict[str, int] = field(default_factory=lambda: {'success': 0, 'failure': 0})
    
    # RAG relevance tracking
    rag_relevance_scores: List[float] = field(default_factory=list)
    
    # Token usage tracking
    token_usage: Dict[str, int] = field(default_factory=lambda: {'prompt': 0, 'completion': 0})
    
    # Error tracking
    error_counts: Dict[str, int] = field(default_factory=dict)
    
    # Quality tracking
    quality_scores: List[float] = field(default_factory=list)
    
    # Escalation tracking
    escalation_counts: Dict[str, int] = field(default_factory=lambda: {'total': 0, 'prevented': 0})
    
    # Platform tracking
    platform_events: Dict[str, int] = field(default_factory=dict)
    
    def record_response_time(self, duration_ms: float):
        """
        Record response time
        
        Args:
            duration_ms: Response time in milliseconds
        """
        self.response_times.append(duration_ms)
    
    def record_tool_call(self, success: bool, tool_name: Optional[str] = None):
        """
        Record tool call result
        
        Args:
            success: Whether tool succeeded
            tool_name: Name of tool (optional, for detailed tracking)
        """
        if success:
            self.tool_calls['success'] += 1
        else:
            self.tool_calls['failure'] += 1
    
    def record_token_usage(self, prompt_tokens: int, completion_tokens: int):
        """
        Record LLM token usage
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
        """
        self.token_usage['prompt'] += prompt_tokens
        self.token_usage['completion'] += completion_tokens
    
    def record_rag_relevance(self, relevance_score: float):
        """
        Record RAG relevance score
        
        Args:
            relevance_score: Relevance score (0-1)
        """
        self.rag_relevance_scores.append(relevance_score)
    
    def record_error(self, error_type: str):
        """
        Record error occurrence
        
        Args:
            error_type: Type of error
        """
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
    
    def record_quality_score(self, score: float):
        """
        Record quality score
        
        Args:
            score: Quality score (0-10)
        """
        self.quality_scores.append(score)
    
    def record_escalation(self, prevented: bool = False):
        """
        Record escalation
        
        Args:
            prevented: Whether escalation was prevented
        """
        self.escalation_counts['total'] += 1
        if prevented:
            self.escalation_counts['prevented'] += 1
    
    def record_platform_event(self, platform: str, event_type: str):
        """
        Record platform event
        
        Args:
            platform: Platform name (whatsapp, email, etc.)
            event_type: Event type (message_received, message_sent)
        """
        key = f"{platform}_{event_type}"
        if key not in self.platform_events:
            self.platform_events[key] = 0
        self.platform_events[key] += 1
    
    def get_percentiles(self) -> Dict:
        """
        Calculate P50, P95, P99 response times
        
        Returns:
            Dict with percentile values
        """
        if not self.response_times:
            return {'p50': 0, 'p95': 0, 'p99': 0, 'min': 0, 'max': 0, 'avg': 0}
        
        sorted_times = sorted(self.response_times)
        length = len(sorted_times)
        
        return {
            'p50': sorted_times[int(length * 0.5)] if length > 0 else 0,
            'p95': sorted_times[int(length * 0.95)] if length > 1 else sorted_times[0],
            'p99': sorted_times[int(length * 0.99)] if length > 2 else sorted_times[0],
            'min': min(sorted_times),
            'max': max(sorted_times),
            'avg': statistics.mean(sorted_times)
        }
    
    def get_tool_success_rate(self) -> float:
        """
        Calculate tool success rate
        
        Returns:
            Success rate as percentage (0-100)
        """
        total = self.tool_calls['success'] + self.tool_calls['failure']
        if total == 0:
            return 0.0
        return (self.tool_calls['success'] / total) * 100
    
    def get_average_quality(self) -> float:
        """
        Calculate average quality score
        
        Returns:
            Average quality score (0-10)
        """
        if not self.quality_scores:
            return 0.0
        return statistics.mean(self.quality_scores)
    
    def get_escalation_rate(self) -> float:
        """
        Calculate escalation rate
        
        Returns:
            Escalation rate as percentage (0-100)
        """
        total_conversations = len(self.quality_scores)  # Proxy for conversation count
        if total_conversations == 0:
            return 0.0
        return (self.escalation_counts['total'] / total_conversations) * 100
    
    def get_escalation_prevention_rate(self) -> float:
        """
        Calculate escalation prevention rate
        
        Returns:
            Prevention rate as percentage (0-100)
        """
        total_escalations = self.escalation_counts['total']
        if total_escalations == 0:
            return 0.0
        return (self.escalation_counts['prevented'] / total_escalations) * 100
    
    def calculate_token_cost(
        self,
        prompt_cost_per_1k: float = 0.00015,
        completion_cost_per_1k: float = 0.0006
    ) -> Dict:
        """
        Calculate estimated LLM costs
        
        Args:
            prompt_cost_per_1k: Cost per 1K prompt tokens (default: GPT-4o-mini)
            completion_cost_per_1k: Cost per 1K completion tokens
        
        Returns:
            Cost breakdown dict
        """
        prompt_cost = (self.token_usage['prompt'] / 1000) * prompt_cost_per_1k
        completion_cost = (self.token_usage['completion'] / 1000) * completion_cost_per_1k
        total_cost = prompt_cost + completion_cost
        
        return {
            'prompt_cost': round(prompt_cost, 4),
            'completion_cost': round(completion_cost, 4),
            'total_cost': round(total_cost, 4),
            'total_tokens': self.token_usage['prompt'] + self.token_usage['completion'],
            'cost_per_conversation': round(
                total_cost / len(self.quality_scores) if self.quality_scores else 0,
                4
            )
        }
    
    def get_summary(self) -> Dict:
        """
        Get complete metrics summary
        
        Returns:
            Comprehensive metrics dict
        """
        return {
            'response_times': self.get_percentiles(),
            'tool_performance': {
                'success_rate': round(self.get_tool_success_rate(), 2),
                'total_calls': self.tool_calls['success'] + self.tool_calls['failure'],
                'successful': self.tool_calls['success'],
                'failed': self.tool_calls['failure']
            },
            'quality': {
                'average_score': round(self.get_average_quality(), 2),
                'total_scored': len(self.quality_scores)
            },
            'escalations': {
                'total': self.escalation_counts['total'],
                'prevented': self.escalation_counts['prevented'],
                'escalation_rate': round(self.get_escalation_rate(), 2),
                'prevention_rate': round(self.get_escalation_prevention_rate(), 2)
            },
            'tokens': {
                'prompt': self.token_usage['prompt'],
                'completion': self.token_usage['completion'],
                'total': self.token_usage['prompt'] + self.token_usage['completion']
            },
            'costs': self.calculate_token_cost(),
            'errors': self.error_counts,
            'platform_events': self.platform_events
        }
    
    def get_health_status(self) -> Dict:
        """
        Get system health status based on metrics
        
        Returns:
            Health status dict with warnings
        """
        warnings = []
        status = "healthy"
        
        # Check response times
        percentiles = self.get_percentiles()
        if percentiles['p95'] > 5000:  # >5 seconds
            warnings.append("High response times (P95 > 5s)")
            status = "degraded"
        
        # Check tool success rate
        tool_success = self.get_tool_success_rate()
        if tool_success < 90 and self.tool_calls['success'] + self.tool_calls['failure'] > 10:
            warnings.append(f"Low tool success rate ({tool_success:.1f}%)")
            status = "degraded"
        
        # Check error rate
        total_errors = sum(self.error_counts.values())
        total_conversations = len(self.quality_scores)
        if total_conversations > 0:
            error_rate = (total_errors / total_conversations) * 100
            if error_rate > 5:
                warnings.append(f"High error rate ({error_rate:.1f}%)")
                status = "degraded"
        
        # Check quality scores
        avg_quality = self.get_average_quality()
        if avg_quality < 7.0 and len(self.quality_scores) > 10:
            warnings.append(f"Low average quality ({avg_quality:.1f}/10)")
            status = "degraded"
        
        # Check escalation rate
        escalation_rate = self.get_escalation_rate()
        if escalation_rate > 15 and total_conversations > 10:
            warnings.append(f"High escalation rate ({escalation_rate:.1f}%)")
            status = "warning"
        
        return {
            'status': status,
            'warnings': warnings,
            'metrics_count': len(self.response_times),
            'last_check': datetime.utcnow().isoformat() + 'Z'
        }
    
    def reset(self):
        """Reset all metrics"""
        self.response_times = []
        self.tool_calls = {'success': 0, 'failure': 0}
        self.rag_relevance_scores = []
        self.token_usage = {'prompt': 0, 'completion': 0}
        self.error_counts = {}
        self.quality_scores = []
        self.escalation_counts = {'total': 0, 'prevented': 0}
        self.platform_events = {}
    
    def __repr__(self) -> str:
        return f"MetricsCollector(conversations={len(self.quality_scores)}, avg_quality={self.get_average_quality():.1f})"


# Global metrics instance
metrics = MetricsCollector()


# Testing function
def test_metrics_collector():
    """Test metrics collector"""
    print("🧪 TESTING PERFORMANCE METRICS COLLECTOR")
    print("=" * 70)
    print()
    
    collector = MetricsCollector()
    
    # Simulate 10 conversations
    print("📊 Simulating 10 conversations...")
    print()
    
    for i in range(10):
        # Response time (varying)
        response_time = 800 + (i * 50)  # 800ms to 1250ms
        collector.record_response_time(response_time)
        
        # Tool calls (mostly successful)
        collector.record_tool_call(success=True if i < 9 else False)
        
        # Token usage
        collector.record_token_usage(prompt_tokens=150, completion_tokens=50)
        
        # Quality score (varying)
        quality = 9.0 - (i * 0.1)  # 9.0 to 8.1
        collector.record_quality_score(quality)
        
        # Some escalations
        if i in [3, 7]:
            collector.record_escalation(prevented=False)
        elif i == 5:
            collector.record_escalation(prevented=True)
        
        # Platform events
        collector.record_platform_event('whatsapp', 'message_received')
        collector.record_platform_event('whatsapp', 'message_sent')
    
    # Add some errors
    collector.record_error('ToolFailure')
    collector.record_error('LLMTimeout')
    
    print("✅ 10 conversations simulated")
    print()
    
    # Test 1: Response time percentiles
    print("TEST 1: Response Time Percentiles")
    percentiles = collector.get_percentiles()
    print(f"  P50: {percentiles['p50']:.0f}ms")
    print(f"  P95: {percentiles['p95']:.0f}ms")
    print(f"  P99: {percentiles['p99']:.0f}ms")
    print(f"  Avg: {percentiles['avg']:.0f}ms")
    print(f"  Min: {percentiles['min']:.0f}ms")
    print(f"  Max: {percentiles['max']:.0f}ms")
    assert percentiles['p50'] > 0, "P50 should be > 0"
    print("✅ Percentiles calculated")
    print()
    
    # Test 2: Tool success rate
    print("TEST 2: Tool Success Rate")
    success_rate = collector.get_tool_success_rate()
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"  Successful: {collector.tool_calls['success']}")
    print(f"  Failed: {collector.tool_calls['failure']}")
    assert success_rate == 90.0, "Success rate should be 90%"
    print("✅ Tool success rate calculated")
    print()
    
    # Test 3: Token costs
    print("TEST 3: Token Usage & Costs")
    costs = collector.calculate_token_cost()
    print(f"  Total Tokens: {costs['total_tokens']:,}")
    print(f"  Prompt Tokens: {collector.token_usage['prompt']:,}")
    print(f"  Completion Tokens: {collector.token_usage['completion']:,}")
    print(f"  Total Cost: ${costs['total_cost']:.4f}")
    print(f"  Cost per Conversation: ${costs['cost_per_conversation']:.4f}")
    assert costs['total_tokens'] == 2000, "Should have 2000 tokens"
    print("✅ Token costs calculated")
    print()
    
    # Test 4: Quality metrics
    print("TEST 4: Quality Metrics")
    avg_quality = collector.get_average_quality()
    print(f"  Average Quality: {avg_quality:.2f}/10")
    print(f"  Total Scored: {len(collector.quality_scores)}")
    assert 8.0 < avg_quality < 9.0, "Average quality should be ~8.5"
    print("✅ Quality metrics calculated")
    print()
    
    # Test 5: Escalation metrics
    print("TEST 5: Escalation Metrics")
    escalation_rate = collector.get_escalation_rate()
    prevention_rate = collector.get_escalation_prevention_rate()
    print(f"  Total Escalations: {collector.escalation_counts['total']}")
    print(f"  Prevented: {collector.escalation_counts['prevented']}")
    print(f"  Escalation Rate: {escalation_rate:.1f}%")
    print(f"  Prevention Rate: {prevention_rate:.1f}%")
    assert collector.escalation_counts['total'] == 3, "Should have 3 escalations"
    print("✅ Escalation metrics calculated")
    print()
    
    # Test 6: Complete summary
    print("TEST 6: Complete Summary")
    summary = collector.get_summary()
    print(f"  Response Time P95: {summary['response_times']['p95']:.0f}ms")
    print(f"  Tool Success: {summary['tool_performance']['success_rate']}%")
    print(f"  Avg Quality: {summary['quality']['average_score']}/10")
    print(f"  Total Cost: ${summary['costs']['total_cost']}")
    print(f"  Errors: {sum(summary['errors'].values())}")
    assert 'response_times' in summary, "Summary should have response_times"
    print("✅ Complete summary generated")
    print()
    
    # Test 7: Health status
    print("TEST 7: Health Status")
    health = collector.get_health_status()
    print(f"  Status: {health['status']}")
    print(f"  Warnings: {len(health['warnings'])}")
    if health['warnings']:
        for warning in health['warnings']:
            print(f"    - {warning}")
    print(f"  Metrics Count: {health['metrics_count']}")
    assert health['status'] in ['healthy', 'degraded', 'warning'], "Should have valid status"
    print("✅ Health status assessed")
    print()
    
    # Final summary
    print("=" * 70)
    print("📊 FINAL METRICS SUMMARY")
    print("=" * 70)
    print()
    print(f"Conversations: {len(collector.quality_scores)}")
    print(f"Avg Quality: {collector.get_average_quality():.2f}/10")
    print(f"Avg Response Time: {collector.get_percentiles()['avg']:.0f}ms")
    print(f"Tool Success: {collector.get_tool_success_rate():.1f}%")
    print(f"Total Cost: ${collector.calculate_token_cost()['total_cost']:.4f}")
    print(f"Health: {collector.get_health_status()['status'].upper()}")
    print()
    print("✅ All metrics collector tests complete!")


if __name__ == "__main__":
    test_metrics_collector()
