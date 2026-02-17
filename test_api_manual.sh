#!/bin/bash
# Manual API testing script
# This script helps you manually test the API endpoints

API_URL="${API_URL:-http://localhost:8000}"

echo "Animal Counter API - Manual Test Script"
echo "========================================"
echo ""
echo "API URL: $API_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Health Check${NC}"
echo "curl $API_URL/health"
echo ""
curl -s "$API_URL/health" | python3 -m json.tool || echo "❌ API not running"
echo ""

echo -e "${BLUE}2. Get All Results (should be empty initially)${NC}"
echo "curl $API_URL/all"
echo ""
curl -s "$API_URL/all" | python3 -m json.tool || echo "❌ Failed"
echo ""

echo -e "${BLUE}3. Upload and Process Video${NC}"
echo "To upload a video, use:"
echo ""
echo -e "${YELLOW}curl -X POST \"$API_URL/process\" \\"
echo "  -F \"video=@/path/to/your/video.mp4\" \\"
echo "  -F \"detection_type=birds\"${NC}"
echo ""
echo "Or for livestock:"
echo -e "${YELLOW}curl -X POST \"$API_URL/process\" \\"
echo "  -F \"video=@/path/to/your/video.mp4\" \\"
echo "  -F \"detection_type=livestock\"${NC}"
echo ""

echo -e "${BLUE}4. Get Specific Result${NC}"
echo "After uploading, you'll get a result_id. Use it like:"
echo -e "${YELLOW}curl \"$API_URL/results/YOUR_RESULT_ID\"${NC}"
echo ""

echo -e "${GREEN}To start the API server:${NC}"
echo "python3 -m uvicorn animal_counter.api.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "Or with Docker Compose:"
echo "docker-compose up api"
