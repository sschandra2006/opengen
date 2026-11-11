"""
Tests for OpenGen REST API Layer.
Verifies FastAPI endpoints using TestClient.
"""
import pytest
from fastapi.testclient import TestClient
from opengen.api import app

client = TestClient(app)


def test_api_health_endpoint():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert "document" in data["engines"]
    assert "presentation" in data["engines"]
    assert "image" in data["engines"]
    assert "handwriting" in data["engines"]


def test_api_presentation_generate():
    payload = {
        "topic": "API Microservices Architecture",
        "slide_count": 4,
        "theme": "modern_corporate"
    }
    resp = client.post("/api/v1/presentations/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "pptx_path" in data
    assert data["slide_count"] == 4
    assert "download_url" in data


def test_api_image_generate():
    payload = {
        "prompt": "Vector diagram of distributed caching",
        "style": "vector",
        "output_format": "svg"
    }
    resp = client.post("/api/v1/images/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["is_vector"] is True
    assert "download_url" in data


def test_api_handwriting_generate():
    payload = {
        "text": "Assignment 1: Algorithms and Data Structures.",
        "paper_mode": "direct_print_transparent",
        "ruled_type": "college_ruled"
    }
    resp = client.post("/api/v1/handwriting/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["transparent_mode"] is True
    assert "download_url" in data


def test_api_job_status():
    resp = client.get("/api/v1/jobs/job_abc123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "job_abc123"
    assert data["status"] == "completed"
