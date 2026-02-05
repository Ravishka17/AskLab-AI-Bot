#!/bin/bash
# Validation script for context management fix

echo "=================================="
echo "Context Management Fix Validator"
echo "=================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Test 1: Compilation
echo "Test 1: Python compilation..."
if python3 -m py_compile app.py 2>/dev/null; then
    echo -e "${GREEN}✅ app.py compiles successfully${NC}"
else
    echo -e "${RED}❌ app.py compilation failed${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 2: Unit tests
echo "Test 2: Running unit tests..."
if python3 test_context_simple.py 2>&1 | grep -q "ALL TESTS PASSED"; then
    echo -e "${GREEN}✅ All unit tests passed${NC}"
else
    echo -e "${RED}❌ Unit tests failed${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 3: Check ContextManager class exists
echo "Test 3: ContextManager class verification..."
if grep -q "class ContextManager:" app.py; then
    echo -e "${GREEN}✅ ContextManager class found${NC}"
else
    echo -e "${RED}❌ ContextManager class missing${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 4: Check key methods exist
echo "Test 4: Key methods verification..."
METHODS=("detect_stuck_loop" "build_optimized_messages" "inject_urgency" "add_thinking" "add_tool_result")
for method in "${METHODS[@]}"; do
    if grep -q "def ${method}" app.py; then
        echo -e "${GREEN}  ✓ ${method}${NC}"
    else
        echo -e "${RED}  ✗ ${method} missing${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Test 5: Check integration points exist
echo "Test 5: Integration points verification..."
if grep -q "context_mgr.detect_stuck_loop" app.py; then
    echo -e "${GREEN}  ✓ Loop detection integrated${NC}"
else
    echo -e "${RED}  ✗ Loop detection not integrated${NC}"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "context_mgr.build_optimized_messages" app.py; then
    echo -e "${GREEN}  ✓ Progressive trimming integrated${NC}"
else
    echo -e "${RED}  ✗ Progressive trimming not integrated${NC}"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "context_mgr.add_thinking" app.py; then
    echo -e "${GREEN}  ✓ Thinking tracking integrated${NC}"
else
    echo -e "${RED}  ✗ Thinking tracking not integrated${NC}"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "context_mgr.add_tool_result" app.py; then
    echo -e "${GREEN}  ✓ Tool result tracking integrated${NC}"
else
    echo -e "${RED}  ✗ Tool result tracking not integrated${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 6: Documentation files
echo "Test 6: Documentation verification..."
DOCS=("CONTEXT_ARCHITECTURE.md" "IMPLEMENTATION_SUMMARY.md" "TEST_SCENARIOS.md" "CHANGES_SUMMARY.md" "README_CONTEXT_FIX.md")
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}  ✓ ${doc}${NC}"
    else
        echo -e "${YELLOW}  ⚠ ${doc} missing${NC}"
    fi
done
echo ""

# Test 7: Test file
echo "Test 7: Test file verification..."
if [ -f "test_context_simple.py" ]; then
    echo -e "${GREEN}✅ test_context_simple.py exists${NC}"
else
    echo -e "${RED}❌ test_context_simple.py missing${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Summary
echo "=================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL VALIDATIONS PASSED!${NC}"
    echo ""
    echo "Context management fix is ready for deployment."
    echo ""
    echo "Next steps:"
    echo "  1. Review the changes: git diff"
    echo "  2. Test manually: python3 app.py"
    echo "  3. See TEST_SCENARIOS.md for test cases"
    echo "  4. Deploy when ready"
    exit 0
else
    echo -e "${RED}❌ $ERRORS ERROR(S) FOUND${NC}"
    echo ""
    echo "Please fix the errors before deployment."
    exit 1
fi
