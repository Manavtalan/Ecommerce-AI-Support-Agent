#!/usr/bin/env python3
"""
Day 1 Phase 1: Environment Setup Verification
Tests that all dependencies and configurations are correct.
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """Comprehensive environment test"""
    
    print("=" * 60)
    print("DAY 1 PHASE 1: ENVIRONMENT SETUP VERIFICATION")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # Test 1: Python version
    print("1. Python Version:")
    py_version = sys.version_info
    if py_version.major == 3 and py_version.minor >= 11:
        print(f"   ✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print(f"   ⚠️  Python {py_version.major}.{py_version.minor} (3.11+ recommended)")
    print()
    
    # Test 2: Dependencies
    print("2. Core Dependencies:")
    deps = [
        ("openai", "OpenAI API"),
        ("yaml", "PyYAML"),
        ("dotenv", "python-dotenv"),
        ("pandas", "Pandas")
    ]
    
    for module, name in deps:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - NOT INSTALLED")
            all_passed = False
    print()
    
    # Test 3: Environment variables
    print("3. Environment Configuration:")
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "your_openai_api_key_here":
        print(f"   ✅ OpenAI API Key (starts with: {api_key[:7]}...)")
    else:
        print("   ❌ OpenAI API Key - NOT SET")
        all_passed = False
    
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    print(f"   ✅ Model: {model}")
    print()
    
    # Test 4: Project structure
    print("4. Project Structure:")
    required_dirs = [
        "core/conversation",
        "core/llm",
        "core/emotion",
        "test_data/brands/fashionhub"
    ]
    
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"   ✅ {dir_path}/")
        else:
            print(f"   ❌ {dir_path}/ - MISSING")
            all_passed = False
    print()
    
    # Test 5: Key files
    print("5. Key Files:")
    key_files = [
        "core/emotion/detector.py",
        "core/llm/composer.py",
        "test_data/orders/fashionhub_orders.json",
        ".env"
    ]
    
    for file_path in key_files:
        if os.path.isfile(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
            all_passed = False
    print()
    
    # Test 6: Imports
    print("6. Module Imports:")
    try:
        from core.emotion.detector import EmotionDetector
        print("   ✅ EmotionDetector")
    except:
        print("   ❌ EmotionDetector")
        all_passed = False
    
    try:
        from core.llm.composer import LLMResponseComposer
        print("   ✅ LLMResponseComposer")
    except:
        print("   ❌ LLMResponseComposer")
        all_passed = False
    print()
    
    # Final verdict
    print("=" * 60)
    if all_passed:
        print("✅ PHASE 1 COMPLETE - ENVIRONMENT READY!")
        print("🚀 Ready to proceed to Phase 2: Memory System")
        return 0
    else:
        print("❌ PHASE 1 INCOMPLETE - Fix issues above")
        return 1
    print("=" * 60)

if __name__ == "__main__":
    exit(test_environment())
