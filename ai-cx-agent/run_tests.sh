#!/bin/bash

echo "🧪 AI CX AGENT - TEST SUITE RUNNER"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse arguments
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    "e2e"|"end-to-end")
        echo "Running End-to-End Tests..."
        python3 tests/test_end_to_end.py
        ;;
    
    "multi-brand"|"brands")
        echo "Running Multi-Brand Tests..."
        python3 tests/test_multi_brand.py
        ;;
    
    "integration"|"integrations")
        echo "Running Integration Tests..."
        python3 tests/test_integration_readiness.py
        ;;
    
    "edge"|"edge-cases")
        echo "Running Edge Case Tests..."
        python3 tests/test_edge_cases.py
        ;;
    
    "load"|"performance")
        echo "Running Load & Performance Tests..."
        python3 tests/test_load_performance.py
        ;;
    
    "validate"|"production")
        echo "Running Full Production Validation..."
        python3 scripts/validate_production_ready.py
        ;;
    
    "all")
        echo "Running ALL Test Suites..."
        python3 scripts/validate_production_ready.py
        ;;
    
    "help"|"--help"|"-h")
        echo "Usage: ./run_tests.sh [TEST_TYPE]"
        echo ""
        echo "Available test types:"
        echo "  e2e, end-to-end       - End-to-end conversation tests"
        echo "  multi-brand, brands   - Multi-brand isolation tests"
        echo "  integration           - Integration adapter tests"
        echo "  edge, edge-cases      - Edge case tests"
        echo "  load, performance     - Load & performance tests"
        echo "  validate, production  - Full production validation"
        echo "  all                   - Run all tests (default)"
        echo ""
        exit 0
        ;;
    
    *)
        echo "Unknown test type: $TEST_TYPE"
        echo "Run './run_tests.sh help' for usage"
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Tests PASSED${NC}"
    exit 0
else
    echo -e "${RED}❌ Tests FAILED${NC}"
    exit 1
fi
