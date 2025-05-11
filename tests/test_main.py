import pytest
import httpx
import asyncio

import os

import pytest_asyncio

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")

@pytest.mark.asyncio
async def test_root():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json().get("message") == "Welcome to Bluelabel AIOS API"

@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "ok" in data
        assert isinstance(data["ok"], bool)

@pytest.mark.asyncio
async def test_test_local():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/test-local")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["status"] in ["success", "error"]

@pytest.mark.asyncio
async def test_list_local_models():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/list-local-models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert isinstance(data["models"], list) 