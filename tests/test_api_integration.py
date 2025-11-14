"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app import app

client = TestClient(app)

class TestAPIIntegration:
    """Integration tests"""
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_full_generate_questions_flow(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers, test_domain):
        """Test complete generateQuestions flow"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [
                {"text": "Question 1"},
                {"text": "Question 2"},
                {"text": "Question 3"}
            ],
            "tokens_used": 150
        }
        mock_reserve_id.return_value = "test_content_id_123"
        mock_save_content.return_value = None
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "context": "Test article content here",
                    "lang": "zh-tw",
                    "prompt": "Generate questions"
                },
                "user": "test_user_123",
                "type": "widget_page",
                "source_url": test_domain
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "task_id" in data
        assert data["data"]["status"] == "succeeded"
        assert len(data["data"]["outputs"]["result"]) == 3
        
        # Verify content was saved
        mock_save_content.assert_called_once()
    
    @patch('app.cache_service.get', new_callable=AsyncMock)
    def test_cache_hit_returns_cached_response(self, mock_cache_get, auth_headers):
        """Test that cache hit returns cached response"""
        cached_response = {
            "task_id": "cached_task_id",
            "data": {
                "status": "succeeded",
                "outputs": {
                    "result": {"question_1": "Cached question"},
                    "content_id": "cached_content_id"
                },
                "elapsed_time": 0.5,
                "created_at": 1234567890,
                "finished_at": 1234567891
            }
        }
        mock_cache_get.return_value = cached_response
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "context": "Test content"
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json() == cached_response
    
    def test_unauthorized_request(self):
        """Test that requests without auth token are rejected"""
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "context": "Test"
                },
                "user": "test_user"
            }
        )
        assert response.status_code == 401
    
    def test_invalid_bearer_token(self):
        """Test that invalid bearer token is rejected"""
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "context": "Test"
                },
                "user": "test_user"
            },
            headers={"Authorization": "Bearer wrong_token"}
        )
        assert response.status_code == 403
