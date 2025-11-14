"""
Test output JSON keys and format
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app import app
import json

client = TestClient(app)

class TestOutputFormat:
    """Test output format matches expected schema"""
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_generate_questions_output_keys(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers):
        """Test output contains all required keys"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [
                {"text": "Question 1"},
                {"text": "Question 2"},
                {"text": "Question 3"}
            ],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_content_id"
        mock_save_content.return_value = None
        
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
        data = response.json()
        
        # Check top-level keys
        assert "task_id" in data
        assert "data" in data
        
        # Check data keys
        assert "status" in data["data"]
        assert "outputs" in data["data"]
        assert "elapsed_time" in data["data"]
        assert "created_at" in data["data"]
        assert "finished_at" in data["data"]
        
        # Check outputs keys
        assert "result" in data["data"]["outputs"]
        assert "content_id" in data["data"]["outputs"]
        
        # Check result format (question_1, question_2, etc.)
        result = data["data"]["outputs"]["result"]
        assert isinstance(result, dict)
        assert "question_1" in result
        assert "question_2" in result
        assert "question_3" in result
        
        # Check status
        assert data["data"]["status"] == "succeeded"
        
        # Check timestamps are integers
        assert isinstance(data["data"]["created_at"], int)
        assert isinstance(data["data"]["finished_at"], int)
        assert isinstance(data["data"]["elapsed_time"], (int, float))
        
        # Check elapsed_time is positive
        assert data["data"]["elapsed_time"] > 0
        
        # Check finished_at >= created_at
        assert data["data"]["finished_at"] >= data["data"]["created_at"]
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_question_format(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers):
        """Test questions are formatted as question_1, question_2, etc."""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [
                {"text": "First question"},
                {"text": "Second question"},
                {"text": "Third question"},
                {"text": "Fourth question"},
                {"text": "Fifth question"}
            ],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_content_id"
        mock_save_content.return_value = None
        
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
        result = response.json()["data"]["outputs"]["result"]
        
        # Check all questions are present
        for i in range(1, 6):
            assert f"question_{i}" in result
            assert isinstance(result[f"question_{i}"], str)
            assert len(result[f"question_{i}"]) > 0
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_question_dict_format_extraction(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers):
        """Test that question dict format is properly extracted"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [
                {"id": "q1", "text": "Question from dict", "type": "fact"},
                "Question as string"
            ],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_content_id"
        mock_save_content.return_value = None
        
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
        result = response.json()["data"]["outputs"]["result"]
        
        assert result["question_1"] == "Question from dict"
        assert result["question_2"] == "Question as string"
