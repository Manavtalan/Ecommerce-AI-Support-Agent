# analytics.py
"""
Analytics and Reporting System
Tracks metrics to prove ROI to clients.
"""

import json
from datetime import datetime
from typing import Dict, Any
import os


class AgentAnalytics:
    """Track agent performance metrics"""
    
    def __init__(self, client_id: str = "default"):
        self.client_id = client_id
        self.log_file = f"analytics_{client_id}.jsonl"
    
    def track_interaction(
        self,
        intent: str,
        used_context: bool,
        escalated: bool,
        response_time_ms: float = 0
    ):
        """Log a single interaction"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "client_id": self.client_id,
            "intent": intent,
            "used_context": used_context,
            "escalated": escalated,
            "response_time_ms": response_time_ms
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """Generate summary report"""
        if not os.path.exists(self.log_file):
            return {"error": "No data available"}
        
        # Read all events
        events = []
        with open(self.log_file, 'r') as f:
            for line in f:
                events.append(json.loads(line))
        
        # Calculate metrics
        total = len(events)
        escalated = sum(1 for e in events if e.get('escalated'))
        context_used = sum(1 for e in events if e.get('used_context'))
        
        return {
            "total_queries": total,
            "handled_by_ai": total - escalated,
            "escalated": escalated,
            "escalation_rate": f"{(escalated/total*100):.1f}%" if total > 0 else "0%",
            "context_usage_rate": f"{(context_used/total*100):.1f}%" if total > 0 else "0%"
        }
    
    def generate_report(self) -> str:
        """Generate text report"""
        summary = self.get_summary()
        
        report = f"""
📊 AI Agent Performance Report
Client: {self.client_id}
Period: Last 7 days

Total Queries: {summary.get('total_queries', 0)}
Handled by AI: {summary.get('handled_by_ai', 0)}
Escalated: {summary.get('escalated', 0)} ({summary.get('escalation_rate', '0%')})
Context Usage: {summary.get('context_usage_rate', '0%')}
        """
        
        return report


# Example usage in main.py:
# analytics = AgentAnalytics("fashionhub")
# analytics.track_interaction("order_status", used_context=True, escalated=False)