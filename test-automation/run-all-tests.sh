#!/bin/bash
# Test Execution Script
# Run this script to execute all verification tests

echo "=================================="
echo "Hotel Booking Platform - Phase 7: Verification"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Installing Backend Test Dependencies${NC}"
cd dev
pip install -r tests/requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install backend dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend dependencies installed${NC}"
echo ""

echo -e "${YELLOW}Step 2: Running Backend API Tests${NC}"
pytest tests/ -v --tb=short --color=yes
BACKEND_EXIT_CODE=$?
echo ""

echo -e "${YELLOW}Step 3: Installing Frontend Test Dependencies${NC}"
cd ../test-automation
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
echo ""

echo -e "${YELLOW}Step 4: Installing Playwright Browsers${NC}"
npx playwright install --with-deps
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install Playwright browsers${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Playwright browsers installed${NC}"
echo ""

echo -e "${YELLOW}Step 5: Starting Backend Services (in background)${NC}"
echo "Note: This assumes services are already running or using in-memory database"
echo ""

echo -e "${YELLOW}Step 6: Running Frontend E2E Tests${NC}"
npm test
FRONTEND_EXIT_CODE=$?
echo ""

echo "=================================="
echo "Test Execution Summary"
echo "=================================="
if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Backend Tests: PASSED${NC}"
else
    echo -e "${RED}❌ Backend Tests: FAILED${NC}"
fi

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend Tests: PASSED${NC}"
else
    echo -e "${RED}❌ Frontend Tests: FAILED${NC}"
fi
echo ""

echo "View detailed reports:"
echo "  - Backend: Check console output above"
echo "  - Frontend: npx playwright show-report"
echo ""

# Exit with error if any tests failed
if [ $BACKEND_EXIT_CODE -ne 0 ] || [ $FRONTEND_EXIT_CODE -ne 0 ]; then
    exit 1
fi

exit 0
