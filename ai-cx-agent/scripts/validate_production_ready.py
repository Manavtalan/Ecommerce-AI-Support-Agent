#!/usr/bin/env python3
"""
Production Readiness Validation
Master script that runs ALL validation checks
Must pass 100% before deployment
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
import time


class ProductionValidator:
    """Master validation runner"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def run_test_suite(self, name: str, script_path: str):
        """Run a test suite"""
        print(f"\n{'='*70}")
        print(f"RUNNING: {name}")
        print(f"{'='*70}")
        
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Print output
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            passed = result.returncode == 0
            
            self.results.append({
                'name': name,
                'passed': passed,
                'returncode': result.returncode
            })
            
            return passed
            
        except subprocess.TimeoutExpired:
            print(f"❌ TIMEOUT: {name} took >5 minutes")
            self.results.append({
                'name': name,
                'passed': False,
                'returncode': -1
            })
            return False
        
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.results.append({
                'name': name,
                'passed': False,
                'returncode': -1
            })
            return False
    
    def validate_all(self):
        """Run all validation checks"""
        
        print("🔍 PRODUCTION READINESS VALIDATION")
        print("=" * 70)
        print("This will run ALL tests to verify production readiness")
        print("=" * 70)
        print()
        
        # Define all test suites
        test_suites = [
            ("End-to-End Tests", "tests/test_end_to_end.py"),
            ("Multi-Brand Tests", "tests/test_multi_brand.py"),
            ("Integration Tests", "tests/test_integration_readiness.py"),
            ("Edge Case Tests", "tests/test_edge_cases.py"),
            ("Performance Tests", "tests/test_load_performance.py")
        ]
        
        # Run each suite
        for name, script in test_suites:
            script_path = Path(__file__).parent.parent / script
            
            if not script_path.exists():
                print(f"⚠️  SKIPPING: {name} (file not found: {script})")
                continue
            
            self.run_test_suite(name, str(script_path))
            
            # Brief pause between suites
            time.sleep(2)
        
        # Final report
        self.generate_report()
    
    def generate_report(self):
        """Generate final validation report"""
        
        total_time = time.time() - self.start_time
        
        print("\n" + "="*70)
        print("PRODUCTION READINESS REPORT")
        print("="*70)
        print()
        
        # Test results
        print("TEST RESULTS:")
        print("-" * 70)
        
        for result in self.results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"{status} - {result['name']}")
        
        print()
        
        # Statistics
        passed_count = sum(1 for r in self.results if r['passed'])
        total_count = len(self.results)
        pass_rate = (passed_count / total_count * 100) if total_count > 0 else 0
        
        print("STATISTICS:")
        print("-" * 70)
        print(f"Total Test Suites: {total_count}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {total_count - passed_count}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print(f"Total Time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        print()
        
        # Production checklist
        print("PRODUCTION READINESS CHECKLIST:")
        print("-" * 70)
        
        checklist = [
            ("End-to-End Conversations", any(r['name'] == "End-to-End Tests" and r['passed'] for r in self.results)),
            ("Multi-Brand Isolation", any(r['name'] == "Multi-Brand Tests" and r['passed'] for r in self.results)),
            ("Integration Adapters", any(r['name'] == "Integration Tests" and r['passed'] for r in self.results)),
            ("Edge Case Handling", any(r['name'] == "Edge Case Tests" and r['passed'] for r in self.results)),
            ("Performance Under Load", any(r['name'] == "Performance Tests" and r['passed'] for r in self.results))
        ]
        
        for item, status in checklist:
            check = "✅" if status else "❌"
            print(f"{check} {item}")
        
        print()
        
        # Final verdict
        all_passed = all(r['passed'] for r in self.results)
        
        if all_passed:
            print("="*70)
            print("🎉🎉🎉 SYSTEM IS PRODUCTION READY! 🎉🎉🎉")
            print("="*70)
            print()
            print("✅ All validation checks passed")
            print("✅ Ready for client deployment")
            print("✅ Ready to generate revenue")
            print()
            print("NEXT STEPS:")
            print("1. Deploy to staging environment")
            print("2. Test with real client (Aaveg)")
            print("3. Monitor metrics and logs")
            print("4. Deploy to production")
            print()
            print("🚀 GO LAUNCH!")
            return True
        else:
            failed_tests = [r['name'] for r in self.results if not r['passed']]
            print("="*70)
            print("⚠️  SYSTEM NOT READY FOR PRODUCTION")
            print("="*70)
            print()
            print(f"❌ {len(failed_tests)} test suite(s) failed:")
            for test in failed_tests:
                print(f"   - {test}")
            print()
            print("Fix the failing tests before deploying to production")
            return False


def main():
    """Main validation entry point"""
    validator = ProductionValidator()
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
