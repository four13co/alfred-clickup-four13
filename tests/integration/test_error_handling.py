#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for error handling across all workflow scripts.

Tests various error scenarios and ensures proper error messages are displayed.
"""

import pytest
import sys
import os
from unittest.mock import patch, Mock
import requests

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.fixtures.mock_alfred import MockAlfredEnvironment, create_mock_workflow
from tests.fixtures.mock_clickup_api import MockClickUpAPI, MockClickUpAPIServer


class TestNetworkErrorHandling:
    """Test network and connectivity error handling."""
    
    @pytest.mark.integration
    @pytest.mark.security
    def test_timeout_errors(self):
        """Test handling of network timeout errors."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333',
            'list': '90170402244889'
        }
        
        # Test timeout in createTask
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            with patch('requests.post') as mock_post:
                mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
                
                import createTask
                
                result = workflow.send_feedback()
                
                # Should show timeout error message
                assert any('timeout' in item.title.lower() or 'network' in item.title.lower() for item in workflow.items)
        
        # Test timeout in getTasks
        with MockAlfredEnvironment(args=['search'], config=config) as workflow:
            with patch('requests.get') as mock_get:
                mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
                
                import getTasks
                
                result = workflow.send_feedback()
                
                # Should show timeout error message
                assert any('timeout' in item.title.lower() or 'network' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_connection_errors(self):
        """Test handling of connection errors."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        # Test connection error in closeTask
        with MockAlfredEnvironment(args=['8xdfdjbgd'], config=config) as workflow:
            with patch('requests.put') as mock_put:
                mock_put.side_effect = requests.exceptions.ConnectionError("Connection failed")
                
                import closeTask
                
                result = workflow.send_feedback()
                
                # Should show connection error message
                assert any('connection' in item.title.lower() or 'network' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_ssl_errors(self):
        """Test handling of SSL/TLS errors."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333',
            'list': '90170402244889'
        }
        
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            with patch('requests.post') as mock_post:
                mock_post.side_effect = requests.exceptions.SSLError("SSL certificate verification failed")
                
                import createTask
                
                result = workflow.send_feedback()
                
                # Should show SSL error message
                assert any('ssl' in item.title.lower() or 'certificate' in item.title.lower() or 'security' in item.title.lower() for item in workflow.items)


class TestApiErrorHandling:
    """Test API-specific error handling."""
    
    @pytest.mark.integration
    def test_authentication_errors(self):
        """Test handling of authentication errors."""
        config = {
            'password_clickUpAPI': 'pk_invalid_api_key',
            'workspace': '333',
            'list': '90170402244889'
        }
        
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            with patch('requests.post') as mock_post:
                # Mock 401 Unauthorized response
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_oauth_019_error()
                mock_response.status_code = 401
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
                mock_post.return_value = mock_response
                
                import createTask
                
                result = workflow.send_feedback()
                
                # Should show authentication error
                assert any('auth' in item.title.lower() or 'api key' in item.title.lower() or 'unauthorized' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_permission_errors(self):
        """Test handling of permission/authorization errors."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['search'], config=config) as workflow:
            with patch('requests.get') as mock_get:
                # Mock 403 Forbidden response
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_oauth_023_error()
                mock_response.status_code = 403
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Forbidden")
                mock_get.return_value = mock_response
                
                import getTasks
                
                result = workflow.send_feedback()
                
                # Should show permission error
                assert any('permission' in item.title.lower() or 'access' in item.title.lower() or 'forbidden' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_not_found_errors(self):
        """Test handling of 404 Not Found errors."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
        }
        
        with MockAlfredEnvironment(args=['nonexistent123'], config=config) as workflow:
            with patch('requests.put') as mock_put:
                # Mock 404 Not Found response
                mock_response = Mock()
                mock_response.json.return_value = {"err": "Task not found", "ECODE": "TASK_NOT_FOUND"}
                mock_response.status_code = 404
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
                mock_put.return_value = mock_response
                
                import closeTask
                
                result = workflow.send_feedback()
                
                # Should show task not found error
                assert any('not found' in item.title.lower() or 'exist' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_rate_limit_errors(self):
        """Test handling of rate limit errors."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333',
            'list': '90170402244889'
        }
        
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            with patch('requests.post') as mock_post:
                # Mock 429 Rate Limited response
                mock_response = Mock()
                mock_response.json.return_value = {"err": "Rate limit exceeded", "ECODE": "RATE_LIMITED"}
                mock_response.status_code = 429
                mock_response.headers = {'Retry-After': '60'}
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")
                mock_post.return_value = mock_response
                
                import createTask
                
                result = workflow.send_feedback()
                
                # Should show rate limit error with retry info
                assert any('rate limit' in item.title.lower() or 'too many' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_server_errors(self):
        """Test handling of server errors (5xx)."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['search'], config=config) as workflow:
            with patch('requests.get') as mock_get:
                # Mock 500 Internal Server Error
                mock_response = Mock()
                mock_response.json.return_value = {"err": "Internal server error"}
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Internal Server Error")
                mock_get.return_value = mock_response
                
                import getTasks
                
                result = workflow.send_feedback()
                
                # Should show server error
                assert any('server error' in item.title.lower() or 'try again' in item.title.lower() for item in workflow.items)


class TestValidationErrorHandling:
    """Test validation error handling and user feedback."""
    
    @pytest.mark.integration
    @pytest.mark.security
    def test_input_validation_errors(self):
        """Test that validation errors provide helpful feedback."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        # Test invalid task ID in closeTask
        invalid_task_ids = [
            '',                           # Empty
            'too_short',                 # Too short
            'way_too_long_task_id_123456', # Too long
            '../../../etc/passwd',        # Path traversal
            '<script>alert("xss")</script>', # XSS attempt
        ]
        
        for invalid_id in invalid_task_ids:
            with MockAlfredEnvironment(args=[invalid_id], config=config) as workflow:
                import closeTask
                
                result = workflow.send_feedback()
                
                # Should show specific validation error
                error_items = [item for item in workflow.items if 'invalid' in item.title.lower() or 'error' in item.title.lower()]
                assert len(error_items) > 0
                
                # Error message should be helpful
                error_item = error_items[0]
                assert 'task id' in error_item.title.lower() or 'format' in error_item.subtitle.lower()
    
    @pytest.mark.integration
    def test_configuration_validation_errors(self):
        """Test configuration validation error feedback."""
        config = {}
        
        # Test setting invalid values through config
        invalid_configs = [
            ('clickUpAPI', 'invalid@key'),     # Invalid API key
            ('workspace', 'not_numeric'),      # Invalid workspace ID
            ('list', ''),                      # Empty list ID
            ('space', '<script>'),             # Invalid space ID
        ]
        
        for config_key, invalid_value in invalid_configs:
            with MockAlfredEnvironment(args=[config_key, invalid_value], config=config) as workflow:
                import config as config_module
                
                result = workflow.send_feedback()
                
                # Should show validation error
                error_items = [item for item in workflow.items if 'invalid' in item.title.lower() or 'error' in item.title.lower()]
                assert len(error_items) > 0
                
                # Error should be specific to the configuration item
                error_item = error_items[0]
                assert config_key.lower() in error_item.title.lower() or config_key.lower() in error_item.subtitle.lower()


class TestDataErrorHandling:
    """Test handling of malformed or unexpected data."""
    
    @pytest.mark.integration
    def test_malformed_json_response(self):
        """Test handling of malformed JSON responses."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['search'], config=config) as workflow:
            with patch('requests.get') as mock_get:
                # Mock response with invalid JSON
                mock_response = Mock()
                mock_response.json.side_effect = ValueError("Invalid JSON")
                mock_response.text = "Invalid JSON response"
                mock_response.status_code = 200
                mock_get.return_value = mock_response
                
                import getTasks
                
                result = workflow.send_feedback()
                
                # Should handle JSON parsing error gracefully
                assert any('error' in item.title.lower() or 'invalid' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_missing_response_fields(self):
        """Test handling of responses with missing expected fields."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['search'], config=config) as workflow:
            with patch('requests.get') as mock_get:
                # Mock response missing 'tasks' field
                mock_response = Mock()
                mock_response.json.return_value = {"something_else": "data"}
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response
                
                import getTasks
                
                result = workflow.send_feedback()
                
                # Should handle missing fields gracefully
                assert len(workflow.items) > 0
                # Should show appropriate message about no results or data format issue
                assert any('no' in item.title.lower() or 'found' in item.title.lower() or 'error' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_unexpected_data_types(self):
        """Test handling of unexpected data types in responses."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333',
            'list': '90170402244889'
        }
        
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            with patch('requests.post') as mock_post:
                # Mock response with unexpected data structure
                mock_response = Mock()
                mock_response.json.return_value = "This should be an object, not a string"
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_post.return_value = mock_response
                
                import createTask
                
                result = workflow.send_feedback()
                
                # Should handle unexpected data gracefully
                assert any('error' in item.title.lower() or 'unexpected' in item.title.lower() for item in workflow.items)


class TestRecoveryScenarios:
    """Test error recovery and user guidance scenarios."""
    
    @pytest.mark.integration
    def test_configuration_recovery_flow(self):
        """Test that users are guided to fix configuration issues."""
        # Start with missing configuration
        with MockAlfredEnvironment(args=['Test Task'], config={}) as workflow:
            import createTask
            
            result = workflow.send_feedback()
            
            # Should guide user to configuration
            config_items = [item for item in workflow.items if 'config' in item.title.lower() or 'setup' in item.title.lower()]
            assert len(config_items) > 0
            
            # Should provide actionable steps
            config_item = config_items[0]
            assert 'cu:config' in config_item.subtitle or 'configure' in config_item.subtitle.lower()
    
    @pytest.mark.integration
    def test_network_recovery_suggestions(self):
        """Test that network errors include recovery suggestions."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key',
            'workspace': '333'
        }
        
        with MockAlfredEnvironment(args=['search'], config=config) as workflow:
            with patch('requests.get') as mock_get:
                mock_get.side_effect = requests.exceptions.ConnectionError("Network unreachable")
                
                import getTasks
                
                result = workflow.send_feedback()
                
                # Should suggest recovery actions
                error_items = workflow.items
                assert len(error_items) > 0
                
                # Should mention checking network or trying again
                error_text = ' '.join([item.title + ' ' + item.subtitle for item in error_items]).lower()
                assert any(phrase in error_text for phrase in ['try again', 'check network', 'connection', 'internet'])
    
    @pytest.mark.integration
    def test_api_key_recovery_flow(self):
        """Test recovery flow for API key issues."""
        config = {
            'password_clickUpAPI': 'pk_invalid_key',
            'workspace': '333',
            'list': '90170402244889'
        }
        
        with MockAlfredEnvironment(args=['Test Task'], config=config) as workflow:
            with patch('requests.post') as mock_post:
                # Mock authentication error
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_oauth_019_error()
                mock_response.status_code = 401
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
                mock_post.return_value = mock_response
                
                import createTask
                
                result = workflow.send_feedback()
                
                # Should guide user to update API key
                error_items = workflow.items
                api_items = [item for item in error_items if 'api' in item.title.lower() or 'key' in item.title.lower()]
                assert len(api_items) > 0
                
                # Should provide path to fix the issue
                api_item = api_items[0]
                assert 'cu:config' in api_item.subtitle or 'config' in api_item.subtitle.lower()


if __name__ == '__main__':
    pytest.main([__file__])