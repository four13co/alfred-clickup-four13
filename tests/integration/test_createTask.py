#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for createTask.py workflow script.

Tests the task creation functionality with mocked Alfred environment
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


class TestCreateTaskWorkflow:
    """Integration tests for createTask.py script."""
    
    @pytest.mark.integration
    def test_create_task_success(self):
        """Test successful task creation."""
        # Set up mock configuration
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'list': '90170402244889',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['New Test Task'], config=config) as workflow:
            # Mock the API server
            api_server = MockClickUpAPIServer()
            
            with patch('requests.post') as mock_post:
                # Set up successful API response
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_create_task_response('New Test Task')
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_post.return_value = mock_response
                
                # Import and run createTask
                import createTask
                
                # Capture the result
                result = workflow.send_feedback()
                
                # Verify API call was made correctly
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                
                # Check URL
                assert 'https://api.clickup.com/api/v2/list/90170402244889/task' in call_args[1]['url']
                
                # Check headers
                headers = call_args[1]['headers']
                assert headers['Authorization'] == 'pk_test_api_key'
                assert headers['Content-Type'] == 'application/json'
                
                # Check request data
                data = call_args[1]['json']
                assert data['name'] == 'New Test Task'
                
                # Verify workflow output contains success message
                assert 'New Test Task' in result
    
    @pytest.mark.integration
    def test_create_task_missing_api_key(self):
        """Test task creation with missing API key."""
        config = {
            'list': '90170402244889',
            'workspace': '333'
            # No API key
        }
        
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            import createTask
            
            result = workflow.send_feedback()
            
            # Should show error about missing API key
            assert any('API key' in item.title for item in workflow.items)
            assert any('config' in item.subtitle.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_create_task_missing_list_id(self):
        """Test task creation with missing list ID."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
            # No list ID
        }
        
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            import createTask
            
            result = workflow.send_feedback()
            
            # Should show error about missing list ID
            assert any('list' in item.title.lower() for item in workflow.items)
            assert any('config' in item.subtitle.lower() for item in workflow.items)
    
    @pytest.mark.integration
    @pytest.mark.security
    def test_create_task_invalid_list_id(self):
        """Test task creation with invalid list ID (security test)."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'list': '../../../etc/passwd',  # Path traversal attempt
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            import createTask
            
            result = workflow.send_feedback()
            
            # Should show error about invalid list ID
            assert any('invalid' in item.title.lower() or 'error' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_create_task_api_error(self):
        """Test task creation when API returns error."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'list': '90170402244889',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            with patch('requests.post') as mock_post:
                # Set up error API response
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_oauth_019_error()
                mock_response.status_code = 401
                mock_response.raise_for_status.side_effect = Exception("HTTP 401")
                mock_post.return_value = mock_response
                
                import createTask
                
                result = workflow.send_feedback()
                
                # Should show error message
                assert any('error' in item.title.lower() or 'failed' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_create_task_with_emoji(self):
        """Test task creation with emoji in title."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'list': '90170402244889',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['🚀 Launch new feature'], config=config) as workflow:
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_create_task_response('🚀 Launch new feature')
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_post.return_value = mock_response
                
                import createTask
                
                result = workflow.send_feedback()
                
                # Check that emoji is preserved in API call
                call_args = mock_post.call_args
                data = call_args[1]['json']
                assert data['name'] == '🚀 Launch new feature'
    
    @pytest.mark.integration
    def test_create_task_timeout_handling(self):
        """Test that API timeout is properly configured."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'list': '90170402244889',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_create_task_response('Test Task')
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_post.return_value = mock_response
                
                import createTask
                
                # Verify timeout is set in the API call
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                assert 'timeout' in call_args[1]
                assert call_args[1]['timeout'] == 30  # Should use security-recommended timeout
    
    @pytest.mark.integration
    def test_create_task_empty_title(self):
        """Test task creation with empty title."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'list': '90170402244889',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=[''], config=config) as workflow:
            import createTask
            
            result = workflow.send_feedback()
            
            # Should show error about empty title
            assert any('title' in item.title.lower() or 'name' in item.title.lower() for item in workflow.items)


class TestCreateTaskConfig:
    """Test configuration handling in createTask.py."""
    
    @pytest.mark.integration
    def test_config_validation_flow(self):
        """Test the configuration validation workflow."""
        # Test with missing all config
        with MockAlfredEnvironment(args=['Test Task'], config={}) as workflow:
            import createTask
            
            result = workflow.send_feedback()
            
            # Should prompt for configuration
            assert len(workflow.items) > 0
            assert any('config' in item.subtitle.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_masked_api_key_display(self):
        """Test that API keys are properly masked in UI."""
        config = {
            'password_clickUpAPI': 'pk_very_secret_api_key_12345',
            'list': '90170402244889',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            # Force configuration display
            with patch('createTask.getConfigValue') as mock_get_config:
                mock_get_config.return_value = None  # Force config error
                
                import createTask
                
                result = workflow.send_feedback()
                
                # Check that full API key is never displayed
                full_result = str(result)
                assert 'pk_very_secret_api_key_12345' not in full_result
                assert 'very_secret' not in full_result


if __name__ == '__main__':
    pytest.main([__file__])