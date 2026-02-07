#!/bin/bash

echo "==========================================="
echo "Browser Tool Display Fix Validation"
echo "==========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to check for a pattern in app.py
check_pattern() {
    pattern=$1
    description=$2
    
    if grep -q "$pattern" app.py; then
        echo -e "${GREEN}✅${NC} $description"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $description"
        ((FAILED++))
    fi
}

echo "Checking app.py modifications..."
echo ""

# Check for immediate searching indicator
check_pattern "# IMMEDIATELY show \"Searching...\" indicator" "Searching indicator comment"
check_pattern "display_sections.append(f\"🔍 \*\*Searching...\*\*" "Searching display code"

# Check for immediate reading indicator
check_pattern "# IMMEDIATELY show \"Reading...\" indicator" "Reading indicator comment"
check_pattern "display_sections.append(f\"📖 \*\*Reading...\*\*" "Reading display code"

# Check for display updates with results
check_pattern "display_sections\[-1\] = f\"🔍 \*\*Searched\*\*" "Search results update"
check_pattern "display_sections\[-1\] = f\"📖 \*\*Read Article\*\*" "Read article update"

# Check for past tense conversion
check_pattern "\*\*Searching...\*\*.*\*\*Searched\*\*" "Searching past tense conversion"
check_pattern "\*\*Reading...\*\*.*\*\*Read Article\*\*" "Reading past tense conversion"

echo ""
echo "-------------------------------------------"
echo "Checking Python syntax..."
echo ""

# Check Python syntax
if python3 -m py_compile app.py 2>/dev/null; then
    echo -e "${GREEN}✅${NC} app.py syntax is valid"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} app.py syntax errors found"
    ((FAILED++))
fi

echo ""
echo "-------------------------------------------"
echo "Running automated tests..."
echo ""

# Run test script
if python3 test_searching_display.py 2>&1 | grep -q "✅ All tests completed!"; then
    echo -e "${GREEN}✅${NC} Automated tests passed"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} Automated tests failed"
    ((FAILED++))
fi

echo ""
echo "==========================================="
echo "Validation Summary"
echo "==========================================="
echo ""
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All validations passed!${NC}"
    echo ""
    echo "The browser tool display fix is ready to deploy."
    exit 0
else
    echo -e "${RED}❌ Some validations failed.${NC}"
    echo ""
    echo "Please review the errors above."
    exit 1
fi
