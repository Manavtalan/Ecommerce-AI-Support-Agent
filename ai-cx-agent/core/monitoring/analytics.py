"""
Conversation Analytics
Tracks conversation-level metrics for business insights
Used for: Understanding customer behavior, optimizing agent performance
"""

from typing import Dict, List, Optional
from collections import Counter
from datetime import datetime
import statistics


class ConversationAnalytics:
    """Track conversation-level analytics"""
    
    def __init__(self):
        """Initialize analytics tracker"""
        self.conversations = []
        self.intent_counter = Counter()
        self.tool_usage_counter = Counter()
    
    def track_conversation(self, conversation_data: Dict):
        """
        Track conversation metrics
        
        Args:
            conversation_data: {
                conversation_id: str,
                brand_id: str,
                turns_to_resolution: int,
                escalated: bool,
                escalation_tier: int (optional),
                satisfaction_indicator: str (optional),
                intents: list,
                tools_used: list,
                quality_scores: dict,
                emotion_history: list,
                start_time: str,
                end_time: str,
                platform: str (whatsapp, email, etc.)
            }
        """
        # Add timestamp
        conversation_data['tracked_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Store conversation
        self.conversations.append(conversation_data)
        
        # Update counters
        for intent in conversation_data.get('intents', []):
            self.intent_counter[intent] += 1
        
        for tool in conversation_data.get('tools_used', []):
            self.tool_usage_counter[tool] += 1
    
    def get_analytics(self) -> Dict:
        """
        Get analytics summary
        
        Returns:
            Comprehensive analytics dict
        """
        if not self.conversations:
            return {
                'total_conversations': 0,
                'message': 'No conversations tracked yet'
            }
        
        total = len(self.conversations)
        
        return {
            'overview': {
                'total_conversations': total,
                'timeframe': self._get_timeframe()
            },
            'resolution': {
                'avg_turns_to_resolution': self._avg_turns(),
                'median_turns': self._median_turns(),
                'max_turns': self._max_turns(),
                'min_turns': self._min_turns()
            },
            'escalations': {
                'escalation_rate': self._escalation_rate(),
                'total_escalated': self._total_escalated(),
                'by_tier': self._escalations_by_tier()
            },
            'quality': {
                'avg_quality_score': self._avg_quality(),
                'quality_distribution': self._quality_distribution()
            },
            'intents': {
                'top_intents': self._top_intents(limit=10),
                'total_unique_intents': len(self.intent_counter)
            },
            'tools': {
                'tool_usage_distribution': self._tool_distribution(),
                'most_used_tool': self._most_used_tool()
            },
            'emotions': {
                'emotion_distribution': self._emotion_distribution(),
                'avg_frustration_rate': self._frustration_rate()
            },
            'platforms': {
                'distribution': self._platform_distribution()
            },
            'satisfaction': {
                'positive_indicators': self._positive_satisfaction(),
                'negative_indicators': self._negative_satisfaction()
            }
        }
    
    def _get_timeframe(self) -> Dict:
        """Get timeframe of tracked conversations"""
        if not self.conversations:
            return {}
        
        timestamps = [
            datetime.fromisoformat(c['tracked_at'].replace('Z', '+00:00'))
            for c in self.conversations
            if 'tracked_at' in c
        ]
        
        if not timestamps:
            return {}
        
        return {
            'earliest': min(timestamps).isoformat() + 'Z',
            'latest': max(timestamps).isoformat() + 'Z'
        }
    
    def _avg_turns(self) -> float:
        """Average turns to resolution"""
        turns = [
            c.get('turns_to_resolution', 0)
            for c in self.conversations
            if c.get('turns_to_resolution')
        ]
        
        if not turns:
            return 0.0
        
        return round(statistics.mean(turns), 2)
    
    def _median_turns(self) -> float:
        """Median turns to resolution"""
        turns = [
            c.get('turns_to_resolution', 0)
            for c in self.conversations
            if c.get('turns_to_resolution')
        ]
        
        if not turns:
            return 0.0
        
        return round(statistics.median(turns), 2)
    
    def _max_turns(self) -> int:
        """Maximum turns in a conversation"""
        turns = [
            c.get('turns_to_resolution', 0)
            for c in self.conversations
            if c.get('turns_to_resolution')
        ]
        
        return max(turns) if turns else 0
    
    def _min_turns(self) -> int:
        """Minimum turns in a conversation"""
        turns = [
            c.get('turns_to_resolution', 0)
            for c in self.conversations
            if c.get('turns_to_resolution')
        ]
        
        return min(turns) if turns else 0
    
    def _escalation_rate(self) -> float:
        """Percentage of conversations escalated"""
        escalated = sum(1 for c in self.conversations if c.get('escalated'))
        return round((escalated / len(self.conversations)) * 100, 2)
    
    def _total_escalated(self) -> int:
        """Total escalated conversations"""
        return sum(1 for c in self.conversations if c.get('escalated'))
    
    def _escalations_by_tier(self) -> Dict[str, int]:
        """Count escalations by tier"""
        tier_counts = {'tier_1': 0, 'tier_2': 0, 'tier_3': 0}
        
        for c in self.conversations:
            if c.get('escalated') and c.get('escalation_tier'):
                tier = c['escalation_tier']
                tier_counts[f'tier_{tier}'] += 1
        
        return tier_counts
    
    def _avg_quality(self) -> float:
        """Average quality score"""
        scores = [
            c.get('quality_scores', {}).get('overall', 0)
            for c in self.conversations
            if c.get('quality_scores', {}).get('overall')
        ]
        
        if not scores:
            return 0.0
        
        return round(statistics.mean(scores), 2)
    
    def _quality_distribution(self) -> Dict[str, int]:
        """Distribution of quality grades"""
        distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        
        for c in self.conversations:
            grade = c.get('quality_scores', {}).get('grade', 'C')
            grade_letter = grade[0] if grade else 'C'  # Extract first letter (A+, A-, A all become A)
            if grade_letter in distribution:
                distribution[grade_letter] += 1
        
        return distribution
    
    def _top_intents(self, limit: int = 10) -> List[Dict]:
        """Most common customer intents"""
        top = self.intent_counter.most_common(limit)
        
        return [
            {
                'intent': intent,
                'count': count,
                'percentage': round((count / len(self.conversations)) * 100, 2)
            }
            for intent, count in top
        ]
    
    def _tool_distribution(self) -> List[Dict]:
        """Tool usage distribution"""
        total_tool_calls = sum(self.tool_usage_counter.values())
        
        if total_tool_calls == 0:
            return []
        
        return [
            {
                'tool': tool,
                'count': count,
                'percentage': round((count / total_tool_calls) * 100, 2)
            }
            for tool, count in self.tool_usage_counter.most_common()
        ]
    
    def _most_used_tool(self) -> Optional[str]:
        """Most frequently used tool"""
        if not self.tool_usage_counter:
            return None
        
        return self.tool_usage_counter.most_common(1)[0][0]
    
    def _emotion_distribution(self) -> Dict[str, int]:
        """Distribution of emotions across conversations"""
        emotion_counts = Counter()
        
        for c in self.conversations:
            emotion_history = c.get('emotion_history', [])
            for emotion_event in emotion_history:
                emotion = emotion_event.get('emotion', 'neutral')
                emotion_counts[emotion] += 1
        
        return dict(emotion_counts)
    
    def _frustration_rate(self) -> float:
        """Percentage of conversations with frustration"""
        frustrated_conversations = 0
        
        for c in self.conversations:
            emotion_history = c.get('emotion_history', [])
            has_frustration = any(
                e.get('emotion') == 'frustrated'
                for e in emotion_history
            )
            if has_frustration:
                frustrated_conversations += 1
        
        if not self.conversations:
            return 0.0
        
        return round((frustrated_conversations / len(self.conversations)) * 100, 2)
    
    def _platform_distribution(self) -> Dict[str, int]:
        """Distribution of conversations by platform"""
        platform_counts = Counter()
        
        for c in self.conversations:
            platform = c.get('platform', 'unknown')
            platform_counts[platform] += 1
        
        return dict(platform_counts)
    
    def _positive_satisfaction(self) -> int:
        """Count of positive satisfaction indicators"""
        count = 0
        
        for c in self.conversations:
            indicator = c.get('satisfaction_indicator', '')
            if indicator in ['👍', '😊', '❤️', 'positive', 'satisfied']:
                count += 1
        
        return count
    
    def _negative_satisfaction(self) -> int:
        """Count of negative satisfaction indicators"""
        count = 0
        
        for c in self.conversations:
            indicator = c.get('satisfaction_indicator', '')
            if indicator in ['👎', '😞', '😡', 'negative', 'unsatisfied']:
                count += 1
        
        return count
    
    def get_brand_analytics(self, brand_id: str) -> Dict:
        """
        Get analytics for specific brand
        
        Args:
            brand_id: Brand identifier
        
        Returns:
            Analytics for that brand only
        """
        brand_conversations = [
            c for c in self.conversations
            if c.get('brand_id') == brand_id
        ]
        
        if not brand_conversations:
            return {
                'brand_id': brand_id,
                'total_conversations': 0,
                'message': 'No conversations for this brand'
            }
        
        # Create temporary analytics for this brand
        temp_analytics = ConversationAnalytics()
        temp_analytics.conversations = brand_conversations
        
        # Rebuild counters
        for c in brand_conversations:
            for intent in c.get('intents', []):
                temp_analytics.intent_counter[intent] += 1
            for tool in c.get('tools_used', []):
                temp_analytics.tool_usage_counter[tool] += 1
        
        analytics = temp_analytics.get_analytics()
        analytics['brand_id'] = brand_id
        
        return analytics
    
    def get_time_series(self, interval: str = 'day') -> List[Dict]:
        """
        Get time series data
        
        Args:
            interval: Time interval (day, hour)
        
        Returns:
            List of data points over time
        """
        # Group conversations by time interval
        time_buckets = {}
        
        for c in self.conversations:
            timestamp = c.get('tracked_at')
            if not timestamp:
                continue
            
            # Parse timestamp
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Create bucket key
            if interval == 'day':
                bucket_key = dt.strftime('%Y-%m-%d')
            elif interval == 'hour':
                bucket_key = dt.strftime('%Y-%m-%d %H:00')
            else:
                bucket_key = dt.strftime('%Y-%m-%d')
            
            if bucket_key not in time_buckets:
                time_buckets[bucket_key] = []
            
            time_buckets[bucket_key].append(c)
        
        # Build time series
        time_series = []
        for bucket_key in sorted(time_buckets.keys()):
            conversations = time_buckets[bucket_key]
            
            time_series.append({
                'timestamp': bucket_key,
                'conversation_count': len(conversations),
                'avg_quality': round(
                    statistics.mean([
                        c.get('quality_scores', {}).get('overall', 0)
                        for c in conversations
                        if c.get('quality_scores', {}).get('overall')
                    ]) if conversations else 0,
                    2
                ),
                'escalation_count': sum(1 for c in conversations if c.get('escalated'))
            })
        
        return time_series
    
    def reset(self):
        """Reset all analytics"""
        self.conversations = []
        self.intent_counter = Counter()
        self.tool_usage_counter = Counter()
    
    def __repr__(self) -> str:
        return f"ConversationAnalytics(conversations={len(self.conversations)}, avg_quality={self._avg_quality():.1f})"


# Global analytics instance
analytics = ConversationAnalytics()
