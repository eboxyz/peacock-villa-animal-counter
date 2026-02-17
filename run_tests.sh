#!/bin/bash
# Test runner script for Animal Counter API

echo "Installing test dependencies..."
pip3 install pytest pytest-asyncio httpx fastapi uvicorn motor pymongo python-multipart --quiet

echo ""
echo "Running tests..."
python3 -m pytest tests/ -v --tb=short -k "test_api or test_upload"
