#!/usr/bin/env python3
"""
Manual Testing Tracker
Track test results as you chat with the agent
"""

import json
import csv
from datetime import datetime
from pathlib import Path


class TestingTracker:
    """Track manual testing results"""
    
    def __init__(self):
        self.results = []
        self.current_test = None
        
    def start_test(self, test_id, test_name):
        """Start a new test"""
        self.current_test = {
            'id': test_id,
            'name': test_name,
            'started_at': datetime.now().isoformat(),
            'turns': [],
            'issues': [],
            'status': 'in_progress'
        }
        
    def add_turn(self, user_message, agent_response, quality_score, 
                 tool_used=None, emotion=None, escalated=False):
        """Add a conversation turn"""
        if not self.current_test:
            return
            
        self.current_test['turns'].append({
            'user': user_message,
            'agent': agent_response[:200],  # Truncate
            'quality': quality_score,
            'tool': tool_used,
            'emotion': emotion,
            'escalated': escalated
        })
    
    def add_issue(self, issue_description):
        """Report an issue"""
        if not self.current_test:
            return
            
        self.current_test['issues'].append(issue_description)
    
    def complete_test(self, passed=True, notes=""):
        """Complete current test"""
        if not self.current_test:
            return
            
        self.current_test['status'] = 'passed' if passed else 'failed'
        self.current_test['completed_at'] = datetime.now().isoformat()
        self.current_test['notes'] = notes
        
        # Calculate stats
        turns = self.current_test['turns']
        if turns:
            qualities = [t['quality'] for t in turns if t['quality']]
            self.current_test['avg_quality'] = sum(qualities) / len(qualities) if qualities else 0
            self.current_test['turn_count'] = len(turns)
        
        self.results.append(self.current_test)
        self.current_test = None
    
    def save_results(self, filename="test_results.json"):
        """Save results to file"""
        output_dir = Path("test_results")
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                'tested_at': datetime.now().isoformat(),
                'total_tests': len(self.results),
                'passed': sum(1 for r in self.results if r['status'] == 'passed'),
                'failed': sum(1 for r in self.results if r['status'] == 'failed'),
                'results': self.results
            }, f, indent=2)
        
        print(f"✅ Results saved to {filepath}")
        
    def generate_report(self):
        """Generate summary report"""
        if not self.results:
            print("No test results yet")
            return
            
        passed = sum(1 for r in self.results if r['status'] == 'passed')
        failed = sum(1 for r in self.results if r['status'] == 'failed')
        
        print("\n" + "="*70)
        print("TESTING SUMMARY")
        print("="*70)
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {passed} ({passed/len(self.results)*100:.1f}%)")
        print(f"Failed: {failed} ({failed/len(self.results)*100:.1f}%)")
        print()
        
        # Quality stats
        all_qualities = []
        for result in self.results:
            if result.get('avg_quality'):
                all_qualities.append(result['avg_quality'])
        
        if all_qualities:
            print(f"Average Quality: {sum(all_qualities)/len(all_qualities):.1f}/10")
        
        # Issues
        all_issues = []
        for result in self.results:
            all_issues.extend(result.get('issues', []))
        
        if all_issues:
            print(f"\nTotal Issues: {len(all_issues)}")
            print("Top Issues:")
            for issue in all_issues[:5]:
                print(f"  - {issue}")
        
        print()


# Simple usage example
def demo():
    tracker = TestingTracker()
    
    # Test 1
    tracker.start_test("OM-001", "Basic Order Lookup")
    tracker.add_turn("Where is order 12345?", "Your order has been shipped...", 8.5, "get_order_status")
    tracker.add_turn("When will it arrive?", "Expected Jan 29...", 9.0)
    tracker.complete_test(passed=True, notes="Works great!")
    
    # Test 2
    tracker.start_test("OM-002", "Order Contents")
    tracker.add_turn("What's in my order?", "Summer Floral Dress...", 9.2, "get_order_status")
    tracker.add_issue("Didn't mention size")
    tracker.complete_test(passed=False, notes="Missing size info")
    
    tracker.generate_report()
    tracker.save_results()


if __name__ == "__main__":
    demo()
