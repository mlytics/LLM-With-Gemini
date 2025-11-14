"""
Test input JSON keys and validation logic
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app import app

client = TestClient(app)

class TestInputValidation:
    """Test input validation logic"""
    
    def test_empty_url_and_context(self, auth_headers):
        """Test that empty url and context raises 400"""
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "url": "",
                    "context": ""
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Either url or context must be provided" in response.json()["detail"]
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_empty_url_with_context(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers):
        """Test that empty url with valid context works"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [{"text": "Test question"}],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_content_id"
        mock_save_content.return_value = None
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "url": "",
                    "context": "Valid context here"
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.fetch_content', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_url_without_context(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_fetch_content, mock_gemini, auth_headers, test_domain):
        """Test URL without context works"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_fetch_content.return_value = "Fetched from URL"
        mock_gemini.return_value = {
            "questions": [{"text": "Test question"}],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_content_id"
        mock_save_content.return_value = None
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "url": test_domain,
                    "context": None
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        mock_fetch_content.assert_called_once_with(test_domain)
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_previous_questions_empty_string(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers):
        """Test that empty string previous_questions is converted to empty list"""
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
                    "context": "Test",
                    "previous_questions": ""
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        # Should not error on empty string
        assert response.status_code != 422
