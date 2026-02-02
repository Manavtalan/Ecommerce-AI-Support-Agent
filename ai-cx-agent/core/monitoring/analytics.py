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


# Testing function
def test_conversation_analytics():
    """Test conversation analytics"""
    print("🧪 TESTING CONVERSATION ANALYTICS")
    print("=" * 70)
    print()
    
    tracker = ConversationAnalytics()
    
    # Simulate 20 conversations
    print("📊 Simulating 20 conversations...")
    print()
    
    for i in range(20):
        conversation = {
            'conversation_id': f'conv_{i}',
            'brand_id': 'fashionhub' if i % 2 == 0 else 'techgear',
            'turns_to_resolution': 3 + (i % 5),  # 3-7 turns
            'escalated': i in [3, 7, 15],  # 3 escalations
            'escalation_tier': 2 if i in [3, 7, 15] else None,
            'intents': ['order_status'] if i < 10 else ['return_policy'],
            'tools_used': ['get_order_status'] if i < 10 else ['search_knowledge'],
            'quality_scores': {
                'overall': 9.0 - (i % 3) * 0.5,  # 9.0, 8.5, 8.0
                'grade': 'A' if i % 3 == 0 else 'B'
            },
            'emotion_history': [
                {'emotion': 'frustrated' if i in [3, 7, 15] else 'neutral'}
            ],
            'platform': 'whatsapp' if i < 15 else 'email',
            'satisfaction_indicator': '👍' if i % 4 == 0 else None
        }
        
        tracker.track_conversation(conversation)
    
    print("✅ 20 conversations tracked")
    print()
    
    # Test 1: Overview analytics
    print("TEST 1: Overview Analytics")
    analytics_data = tracker.get_analytics()
    
    overview = analytics_data['overview']
    print(f"  Total Conversations: {overview['total_conversations']}")
    assert overview['total_conversations'] == 20
    print("✅ Overview correct")
    print()
    
    # Test 2: Resolution metrics
    print("TEST 2: Resolution Metrics")
    resolution = analytics_data['resolution']
    print(f"  Avg Turns: {resolution['avg_turns_to_resolution']}")
    print(f"  Median Turns: {resolution['median_turns']}")
    print(f"  Min Turns: {resolution['min_turns']}")
    print(f"  Max Turns: {resolution['max_turns']}")
    assert resolution['avg_turns_to_resolution'] > 0
    print("✅ Resolution metrics calculated")
    print()
    
    # Test 3: Escalation analytics
    print("TEST 3: Escalation Analytics")
    escalations = analytics_data['escalations']
    print(f"  Escalation Rate: {escalations['escalation_rate']}%")
    print(f"  Total Escalated: {escalations['total_escalated']}")
    print(f"  By Tier: {escalations['by_tier']}")
    assert escalations['total_escalated'] == 3
    print("✅ Escalation analytics correct")
    print()
    
    # Test 4: Quality analytics
    print("TEST 4: Quality Analytics")
    quality = analytics_data['quality']
    print(f"  Avg Quality: {quality['avg_quality_score']}/10")
    print(f"  Distribution: {quality['quality_distribution']}")
    assert quality['avg_quality_score'] > 8.0
    print("✅ Quality analytics calculated")
    print()
    
    # Test 5: Intent analytics
    print("TEST 5: Intent Analytics")
    intents = analytics_data['intents']
    print(f"  Top Intents:")
    for intent in intents['top_intents']:
        print(f"    - {intent['intent']}: {intent['count']} ({intent['percentage']}%)")
    assert len(intents['top_intents']) > 0
    print("✅ Intent analytics working")
    print()
    
    # Test 6: Tool analytics
    print("TEST 6: Tool Analytics")
    tools = analytics_data['tools']
    print(f"  Most Used Tool: {tools['most_used_tool']}")
    print(f"  Distribution:")
    for tool in tools['tool_usage_distribution']:
        print(f"    - {tool['tool']}: {tool['count']} ({tool['percentage']}%)")
    assert tools['most_used_tool'] in ['get_order_status', 'search_knowledge']
    print("✅ Tool analytics working")
    print()
    
    # Test 7: Emotion analytics
    print("TEST 7: Emotion Analytics")
    emotions = analytics_data['emotions']
    print(f"  Emotion Distribution: {emotions['emotion_distribution']}")
    print(f"  Frustration Rate: {emotions['avg_frustration_rate']}%")
    assert 'frustrated' in emotions['emotion_distribution'] or 'neutral' in emotions['emotion_distribution']
    print("✅ Emotion analytics working")
    print()
    
    # Test 8: Platform analytics
    print("TEST 8: Platform Analytics")
    platforms = analytics_data['platforms']
    print(f"  Platform Distribution: {platforms['distribution']}")
    assert 'whatsapp' in platforms['distribution']
    print("✅ Platform analytics working")
    print()
    
    # Test 9: Brand-specific analytics
    print("TEST 9: Brand-Specific Analytics")
    brand_analytics = tracker.get_brand_analytics('fashionhub')
    print(f"  FashionHub Conversations: {brand_analytics['overview']['total_conversations']}")
    print(f"  FashionHub Avg Quality: {brand_analytics['quality']['avg_quality_score']}")
    assert brand_analytics['overview']['total_conversations'] == 10
    print("✅ Brand-specific analytics working")
    print()
    
    # Test 10: Time series
    print("TEST 10: Time Series Data")
    time_series = tracker.get_time_series(interval='day')
    print(f"  Time Series Points: {len(time_series)}")
    if time_series:
        print(f"  Latest: {time_series[-1]}")
    print("✅ Time series generated")
    print()
    
    # Final summary
    print("=" * 70)
    print("📊 ANALYTICS SUMMARY")
    print("=" * 70)
    print()
    print(f"Total Conversations: {overview['total_conversations']}")
    print(f"Avg Quality: {quality['avg_quality_score']}/10")
    print(f"Escalation Rate: {escalations['escalation_rate']}%")
    print(f"Most Common Intent: {intents['top_intents'][0]['intent'] if intents['top_intents'] else 'N/A'}")
    print(f"Most Used Tool: {tools['most_used_tool']}")
    print()
    print("✅ All conversation analytics tests complete!")


if __name__ == "__main__":
    test_conversation_analytics()
