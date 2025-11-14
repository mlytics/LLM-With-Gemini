"""
Test URL/context selection precedence logic
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app import app

client = TestClient(app)

class TestURLContextPrecedence:
    """Test URL and context precedence logic"""
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_context_takes_precedence_over_url(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers, test_domain):
        """Test that when both context and URL are provided, context is used"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [{"text": "Test"}],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_content_id"
        mock_save_content.return_value = None
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "url": test_domain,
                    "context": "Direct context provided"
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # Should pass context to generate_questions
        call_args = mock_gemini.call_args
        assert call_args[1]["content"] == "Direct context provided"
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.fetch_content', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_url_fetched_when_no_context(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_fetch_content, mock_gemini, auth_headers, test_domain):
        """Test that URL is fetched when context is not provided"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_fetch_content.return_value = "Fetched from URL"
        mock_gemini.return_value = {
            "questions": [{"text": "Test"}],
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
        call_args = mock_gemini.call_args
        assert call_args[1]["content"] == "Fetched from URL"
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_empty_string_url_with_context(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers):
        """Test that empty string URL is treated as None when context is provided"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [{"text": "Test"}],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_content_id"
        mock_save_content.return_value = None
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "url": "",
                    "context": "Context provided"
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
