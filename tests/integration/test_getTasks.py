#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for getTasks.py workflow script.

Tests the task search functionality with mocked Alfred environment
and ClickUp API responses.
"""

import pytest
import sys
import os
from unittest.mock import patch, Mock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.fixtures.mock_alfred import MockAlfredEnvironment, create_mock_workflow
from tests.fixtures.mock_clickup_api import MockClickUpAPI, MockClickUpAPIServer


class TestGetTasksWorkflow:
    """Integration tests for getTasks.py script."""
    
    @pytest.mark.integration
    def test_search_tasks_success(self):
        """Test successful task search."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['test'], config=config) as workflow:
            api_server = MockClickUpAPIServer()
            
            with patch('requests.get') as mock_get:
                # Set up successful API response with multiple tasks
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_tasks_response(3)
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response
                
                import getTasks
                
                result = workflow.send_feedback()
                
                # Verify API call was made correctly
                mock_get.assert_called_once()
                call_args = mock_get.call_args
                
                # Check URL contains team ID
                assert 'https://api.clickup.com/api/v2/team/333/task' in call_args[0][0]
                
                # Check headers
                headers = call_args[1]['headers']
                assert headers['Authorization'] == 'pk_test_api_key'
                
                # Check search parameters
                params = call_args[1]['params']
                assert params['query'] == 'test'
                
                # Verify workflow shows task results
                assert len(workflow.items) >= 3
                assert any('Test Task' in item.title for item in workflow.items)
    
    @pytest.mark.integration
    def test_search_tasks_no_results(self):
        """Test task search with no results."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['nonexistent'], config=config) as workflow:
            with patch('requests.get') as mock_get:
                # Set up empty API response
                mock_response = Mock()
                mock_response.json.return_value = {'tasks': []}
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response
                
                import getTasks
                
                result = workflow.send_feedback()
                
                # Should show "no results" message
                assert len(workflow.items) >= 1
                assert any('no' in item.title.lower() and 'found' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_search_tasks_missing_api_key(self):
        """Test task search with missing API key."""
        config = {
            'workspace': '333'
            # No API key
        }
        
        with MockAlfredEnvironment(args=['test'], config=config) as workflow:
            import getTasks
            
            result = workflow.send_feedback()
            
            # Should show error about missing API key
            assert any('API key' in item.title or 'config' in item.subtitle.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_search_tasks_missing_workspace(self):
        """Test task search with missing workspace ID."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
            # No workspace
        }
        
        with MockAlfredEnvironment(args=['test'], config=config) as workflow:
            import getTasks
            
            result = workflow.send_feedback()
            
            # Should show error about missing workspace
            assert any('workspace' in item.title.lower() or 'team' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    @pytest.mark.security
    def test_search_tasks_invalid_workspace_id(self):
        """Test task search with invalid workspace ID (security test)."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '../../etc/passwd'  # Path traversal attempt
        }
        
        with MockAlfredEnvironment(args=['test'], config=config) as workflow:
            import getTasks
            
            result = workflow.send_feedback()
            
            # Should show error about invalid workspace ID
            assert any('invalid' in item.title.lower() or 'error' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_search_tasks_api_error(self):
        """Test task search when API returns error."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['test'], config=config) as workflow:
            with patch('requests.get') as mock_get:
                # Set up error API response
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_oauth_023_error()
                mock_response.status_code = 403
                mock_response.raise_for_status.side_effect = Exception("HTTP 403")
                mock_get.return_value = mock_response
                
                import getTasks
                
                result = workflow.send_feedback()
                
                # Should show error message
                assert any('error' in item.title.lower() or 'failed' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_search_with_special_characters(self):
        """Test task search with special characters in query."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        # Test with various special characters that should be safely handled
        test_queries = [
            'test & development',
            'test@example.com',
            'test #123',
            'test "quotes"',
            "test 'single quotes'"
        ]
        
        for query in test_queries:
            with MockAlfredEnvironment(args=[query], config=config) as workflow:
                with patch('requests.get') as mock_get:
                    mock_response = Mock()
                    mock_response.json.return_value = MockClickUpAPI.get_tasks_response(1)
                    mock_response.status_code = 200
                    mock_response.raise_for_status = Mock()
                    mock_get.return_value = mock_response
                    
                    import getTasks
                    
                    result = workflow.send_feedback()
                    
                    # Check that query is properly passed to API
                    call_args = mock_get.call_args
                    params = call_args[1]['params']
                    assert params['query'] == query
    
    @pytest.mark.integration
    def test_search_timeout_handling(self):
        """Test that API timeout is properly configured."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['test'], config=config) as workflow:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_tasks_response(1)
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response
                
                import getTasks
                
                # Verify timeout is set in the API call
                mock_get.assert_called_once()
                call_args = mock_get.call_args
                assert 'timeout' in call_args[1]
                assert call_args[1]['timeout'] == 30  # Should use security-recommended timeout
    
    @pytest.mark.integration
    def test_task_display_format(self):
        """Test that tasks are displayed in correct format."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['test'], config=config) as workflow:
            with patch('requests.get') as mock_get:
                # Create custom task data for testing display
                task_data = MockClickUpAPI.get_tasks_response(1)
                task = task_data['tasks'][0]
                task['name'] = 'Test Task for Display'
                task['status']['status'] = 'In Progress'
                task['id'] = 'display123'
                
                mock_response = Mock()
                mock_response.json.return_value = task_data
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response
                
                import getTasks
                
                result = workflow.send_feedback()
                
                # Find the task item in results
                task_items = [item for item in workflow.items if 'Test Task for Display' in item.title]
                assert len(task_items) > 0
                
                task_item = task_items[0]
                # Should contain task ID for opening
                assert task_item.arg == 'display123'
                # Should show status in subtitle
                assert 'Progress' in task_item.subtitle
    
    @pytest.mark.integration
    def test_empty_search_query(self):
        """Test behavior with empty search query."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=[''], config=config) as workflow:
            import getTasks
            
            result = workflow.send_feedback()
            
            # Should show help text or prompt for input
            assert len(workflow.items) >= 1
            assert any('search' in item.title.lower() or 'enter' in item.title.lower() for item in workflow.items)


class TestGetTasksFuzzySearch:
    """Test fuzzy search functionality in getTasks.py."""
    
    @pytest.mark.integration
    def test_fuzzy_matching(self):
        """Test that fuzzy matching works for task search."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['tsk'], config=config) as workflow:  # Typo: 'tsk' instead of 'task'
            with patch('requests.get') as mock_get:
                # Return tasks with 'task' in the name
                task_data = MockClickUpAPI.get_tasks_response(2)
                task_data['tasks'][0]['name'] = 'Important Task 1'
                task_data['tasks'][1]['name'] = 'Another Task 2'
                
                mock_response = Mock()
                mock_response.json.return_value = task_data
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response
                
                import getTasks
                
                result = workflow.send_feedback()
                
                # Should still find tasks with fuzzy matching
                assert len(workflow.items) >= 2
                assert any('Task' in item.title for item in workflow.items)


if __name__ == '__main__':
    pytest.main([__file__])