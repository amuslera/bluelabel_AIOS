#!/bin/bash
# Test script for AIOS API

echo "Testing the test endpoint..."
curl -X POST -H "Content-Type: application/json" -d '{"content_type": "url", "content": "https://example.com"}' http://localhost:8000/test/process

echo -e "\n\nTesting the Streamlit UI is up..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501

echo -e "\n\nTesting the local LLM connection..."
curl -s http://localhost:8000/test-local

echo -e "\n\nDone testing!"