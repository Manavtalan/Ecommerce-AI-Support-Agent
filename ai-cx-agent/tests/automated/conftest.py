"""
Pytest Configuration and Fixtures
"""

import pytest
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def agent():
    """Create fresh agent instance for each test"""
    try:
        from core.orchestrator import ConversationOrchestrator
        return ConversationOrchestrator(brand_id='fashionhub')
    except ImportError as e:
        pytest.skip(f"Could not import ConversationOrchestrator: {e}")


@pytest.fixture
def send_message(agent):
    """Helper to send message to agent"""
    def _send(message: str):
        start_time = time.time()
        
        try:
            # Call without context parameter
            response, metadata = agent.process_message(user_message=message)
            
            response_time = time.time() - start_time
            
            return {
                'response': response,
                'metadata': metadata,
                'response_time': response_time
            }
        except Exception as e:
            return {
                'response': f"Error: {str(e)}",
                'metadata': {'error': str(e)},
                'response_time': time.time() - start_time
            }
    
    return _send


@pytest.fixture
def multi_turn_conversation(agent):
    """Helper for multi-turn conversations"""
    def _conversation(turns: list):
        results = []
        
        for i, user_message in enumerate(turns):
            start_time = time.time()
            
            try:
                # Call without context parameter
                response, metadata = agent.process_message(user_message=user_message)
                
                response_time = time.time() - start_time
                
                results.append({
                    'turn': i + 1,
                    'user_message': user_message,
                    'response': response,
                    'metadata': metadata,
                    'response_time': response_time
                })
            except Exception as e:
                results.append({
                    'turn': i + 1,
                    'user_message': user_message,
                    'response': f"Error: {str(e)}",
                    'metadata': {'error': str(e)},
                    'response_time': time.time() - start_time
                })
        
        return results
    
    return _conversation
