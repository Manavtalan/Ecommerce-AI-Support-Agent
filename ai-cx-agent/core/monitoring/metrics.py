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
