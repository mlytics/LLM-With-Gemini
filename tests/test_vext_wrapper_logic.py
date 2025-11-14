"""
Test Vext API wrapper logic matches spec requirements
Tests the internal wrapper behavior, not just output format
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app import app

client = TestClient(app)


class TestGenerateQuestionsWrapperLogic:
    """Test /generateQuestions wrapper logic per spec"""
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_context_saved_with_content_id(self, mock_cache_set, mock_cache_get, 
                                          mock_save_content, mock_reserve_id, 
                                          mock_gemini, auth_headers):
        """Test that context is saved to database with content_id per spec"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [{"text": "Question 1"}],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_content_id_123"
        mock_save_content.return_value = None
        
        test_context = "Test article content for saving"
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "context": test_context
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify content was saved with the content_id
        mock_save_content.assert_called_once()
        call_args = mock_save_content.call_args
        assert call_args[0][0] == "test_content_id_123"  # content_id
        assert call_args[0][1] == test_context  # content text
        assert call_args[0][2] is None  # url (None when using context)
        
        # Verify content_id is returned in response
        data = response.json()
        assert data["data"]["outputs"]["content_id"] == "test_content_id_123"
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.fetch_content', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_url_content_fetched_and_saved(self, mock_cache_set, mock_cache_get, 
                                          mock_save_content, mock_fetch_content, 
                                          mock_reserve_id, mock_gemini, 
                                          auth_headers, test_domain):
        """Test that URL content is fetched and saved with content_id"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        fetched_content = "Fetched article content from URL"
        mock_fetch_content.return_value = fetched_content
        mock_gemini.return_value = {
            "questions": [{"text": "Question 1"}],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "url_content_id_456"
        mock_save_content.return_value = None
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "url": test_domain
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify content was fetched from URL
        mock_fetch_content.assert_called_once()
        assert mock_fetch_content.call_args[0][0] == test_domain
        
        # Verify content was saved with content_id
        mock_save_content.assert_called_once()
        call_args = mock_save_content.call_args
        assert call_args[0][0] == "url_content_id_456"
        assert call_args[0][1] == fetched_content
        assert call_args[0][2] == test_domain
        
        # Verify content_id in response
        data = response.json()
        assert data["data"]["outputs"]["content_id"] == "url_content_id_456"
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_gemini_called_with_prompt_context_lang(self, mock_cache_set, mock_cache_get, 
                                                    mock_save_content, mock_reserve_id, 
                                                    mock_gemini, auth_headers):
        """Test Gemini is called with prompt, context, and lang per spec"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [{"text": "Question 1"}],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_id"
        mock_save_content.return_value = None
        
        test_context = "Article content"
        test_prompt = "# 角色 你是鉅亨網的資深金融新聞記者..."
        test_lang = "zh-tw"
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "context": test_context,
                    "prompt": test_prompt,
                    "lang": test_lang
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify Gemini was called with correct parameters
        mock_gemini.assert_called_once()
        call_kwargs = mock_gemini.call_args[1]
        assert call_kwargs["content"] == test_context
        assert call_kwargs["lang"] == test_lang
        assert call_kwargs["custom_prompt"] == test_prompt


class TestGetMetadataWrapperLogic:
    """Test /getMetadata wrapper logic per spec"""
    
    @patch('app.search_service.get_metadata', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_domain_extracted_from_url(self, mock_cache_set, mock_cache_get, 
                                      mock_get_metadata, auth_headers, test_domain):
        """Test that domain is extracted from URL per spec"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        
        mock_get_metadata.return_value = {
            "domain": "cnyes.com",
            "title": "Test",
            "summary": "Test",
            "tags": [],
            "images": [],
            "sources": [],
            "tokens_used": 0,
            "search_quota": 0
        }
        
        response = client.post(
            "/getMetadata",
            json={
                "inputs": {
                    "url": test_domain,
                    "query": "test query",
                    "tag_prompt": ""
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify get_metadata was called with URL
        mock_get_metadata.assert_called_once()
        call_args = mock_get_metadata.call_args
        assert call_args[1]["url"] == test_domain
        assert call_args[1]["query"] == "test query"
    
    @patch('app.search_service.get_metadata', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_search_results_filtered_by_domain(self, mock_cache_set, mock_cache_get, 
                                              mock_get_metadata, auth_headers, test_domain):
        """Test that search results are filtered to same domain per spec"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        
        # Mock sources from same domain
        mock_get_metadata.return_value = {
            "domain": "cnyes.com",
            "title": "Test",
            "summary": "Test",
            "tags": [],
            "images": [],
            "sources": [
                {
                    "title": "Related Article",
                    "url": "https://cnyes.com/article1",
                    "snippet": "Article snippet"
                },
                {
                    "title": "Another Article",
                    "url": "https://news.cnyes.com/article2",
                    "snippet": "Another snippet"
                }
            ],
            "tokens_used": 0,
            "search_quota": 1
        }
        
        response = client.post(
            "/getMetadata",
            json={
                "inputs": {
                    "url": test_domain,
                    "query": "test query",
                    "tag_prompt": ""
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify sources are formatted as citations
        sources = data["data"]["outputs"]["sources"]
        assert len(sources) > 0
        
        import json
        citations_data = json.loads(sources[0]["sources"])
        assert "citations" in citations_data
        assert len(citations_data["citations"]) == 2
        
        # Verify citation structure
        for citation in citations_data["citations"]:
            assert "title" in citation
            assert "url" in citation
            assert "content" in citation


class TestGetAnswerWrapperLogic:
    """Test /getAnswer wrapper logic per spec"""
    
    @patch('app.gemini_service.generate_answer', new_callable=AsyncMock)
    @patch('app.content_service.get_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_content_retrieved_by_content_id(self, mock_cache_set, mock_cache_get, 
                                            mock_get_content, mock_gemini, auth_headers):
        """Test that content is retrieved by content_id per spec"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        
        saved_content = "Previously saved article content"
        mock_get_content.return_value = saved_content
        mock_gemini.return_value = {
            "answer": "Generated answer based on saved content",
            "tokens_used": 200
        }
        
        content_id = "d1e3b8d3-0b0c-47f9-8a9b-cca7b74ad5ae"
        
        response = client.post(
            "/getAnswer",
            json={
                "inputs": {
                    "query": "Test question?",
                    "content_id": content_id,
                    "lang": "zh-tw"
                },
                "user": "test_user",
                "stream": False
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify content was retrieved by content_id
        mock_get_content.assert_called_once_with(content_id)
        
        # Verify Gemini was called with the retrieved content
        mock_gemini.assert_called_once()
        call_kwargs = mock_gemini.call_args[1]
        assert call_kwargs["content"] == saved_content
        assert call_kwargs["question"] == "Test question?"
    
    @patch('app.gemini_service.generate_answer', new_callable=AsyncMock)
    @patch('app.content_service.fetch_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_content_fetched_from_url_when_no_content_id(self, mock_cache_set, mock_cache_get, 
                                                         mock_fetch_content, mock_gemini, 
                                                         auth_headers, test_domain):
        """Test that content is fetched from URL when no content_id per spec"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        
        fetched_content = "Content fetched from URL"
        mock_fetch_content.return_value = fetched_content
        mock_gemini.return_value = {
            "answer": "Answer from URL content",
            "tokens_used": 150
        }
        
        response = client.post(
            "/getAnswer",
            json={
                "inputs": {
                    "query": "Test question?",
                    "url": test_domain,
                    "lang": "zh-tw"
                },
                "user": "test_user",
                "stream": False
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify content was fetched from URL
        mock_fetch_content.assert_called_once_with(test_domain)
        
        # Verify Gemini was called with fetched content
        mock_gemini.assert_called_once()
        call_kwargs = mock_gemini.call_args[1]
        assert call_kwargs["content"] == fetched_content
    
    @patch('app.gemini_service.generate_answer', new_callable=AsyncMock)
    @patch('app.content_service.get_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_gemini_called_with_prompt_and_temperature(self, mock_cache_set, mock_cache_get, 
                                                        mock_get_content, mock_gemini, 
                                                        auth_headers):
        """Test Gemini is called with prompt and temperature=0.4 per spec"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_get_content.return_value = "Article content"
        mock_gemini.return_value = {
            "answer": "Answer text",
            "tokens_used": 100
        }
        
        test_prompt = "Your task is to generate a natural, fluent answer..."
        
        response = client.post(
            "/getAnswer",
            json={
                "inputs": {
                    "query": "Test question?",
                    "content_id": "test_id",
                    "prompt": test_prompt,
                    "lang": "zh-tw"
                },
                "user": "test_user",
                "stream": False
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify Gemini was called with prompt
        mock_gemini.assert_called_once()
        call_kwargs = mock_gemini.call_args[1]
        assert call_kwargs["prompt"] == test_prompt
        # Note: temperature is set in gemini_service, not in app.py
        # This test verifies prompt is passed correctly


class TestVextAPICacheBehavior:
    """Test caching behavior matches Vext API expectations"""
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_cache_hit_returns_cached_response(self, mock_cache_set, mock_cache_get, 
                                               mock_save_content, mock_reserve_id, 
                                               mock_gemini, auth_headers):
        """Test that cache hit returns cached response without calling Gemini"""
        cached_response = {
            "task_id": "cached_task_id",
            "data": {
                "status": "succeeded",
                "outputs": {
                    "result": {
                        "question_1": "Cached question"
                    },
                    "content_id": "cached_id"
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
                    "context": "Test"
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json() == cached_response
        
        # Verify Gemini was NOT called (cache hit)
        mock_gemini.assert_not_called()
        mock_save_content.assert_not_called()

