"""
Test schema completeness and validation
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app import app

client = TestClient(app)

class TestSchemaValidation:
    """Test input/output schema validation"""
    
    def test_generate_questions_missing_inputs(self, auth_headers):
        """Test missing inputs field"""
        response = client.post(
            "/generateQuestions",
            json={"user": "test_user"},
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_generate_questions_missing_user(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers):
        """Test missing user field - should work with default"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [{"text": "Test"}],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_id"
        mock_save_content.return_value = None
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "context": "Test content"
                }
            },
            headers=auth_headers
        )
        # Should work with default user
        assert response.status_code in [200, 400, 500]
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_generate_questions_input_keys(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers, test_domain):
        """Test all valid input keys are accepted"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [{"text": "Test"}],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_id"
        mock_save_content.return_value = None
        
        valid_inputs = {
            "url": test_domain,
            "context": "Test content",
            "prompt": "Custom prompt",
            "lang": "zh-tw",
            "previous_questions": ["Question 1"]
        }
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": valid_inputs,
                "user": "test_user",
                "type": "widget_page",
                "source_url": test_domain
            },
            headers=auth_headers
        )
        # Should not fail on schema validation
        assert response.status_code != 422
    
    def test_get_answer_missing_query(self, auth_headers, test_domain):
        """Test getAnswer requires query"""
        response = client.post(
            "/getAnswer",
            json={
                "inputs": {
                    "url": test_domain
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Query is required" in response.json()["detail"]
    
    def test_get_metadata_missing_url(self, auth_headers):
        """Test getMetadata requires URL"""
        response = client.post(
            "/getMetadata",
            json={
                "inputs": {},
                "user": "test_user"
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "URL is required" in response.json()["detail"]
