#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for closeTask.py workflow script.

Tests the task closing functionality with mocked Alfred environment
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


class TestCloseTaskWorkflow:
    """Integration tests for closeTask.py script."""
    
    @pytest.mark.integration
    def test_close_task_success(self):
        """Test successful task closing."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
        }
        
        task_id = '8xdfdjbgd'
        with MockAlfredEnvironment(args=[task_id], config=config) as workflow:
            with patch('requests.put') as mock_put:
                # Set up successful API response
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_update_task_response(task_id)
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_put.return_value = mock_response
                
                import closeTask
                
                result = workflow.send_feedback()
                
                # Verify API call was made correctly
                mock_put.assert_called_once()
                call_args = mock_put.call_args
                
                # Check URL construction is safe
                expected_url = f'https://api.clickup.com/api/v2/task/{task_id}'
                assert call_args[0][0] == expected_url
                
                # Check headers
                headers = call_args[1]['headers']
                assert headers['Authorization'] == 'pk_test_api_key'
                assert headers['Content-Type'] == 'application/json'
                
                # Check request data
                data = call_args[1]['json']
                assert data['status'] == 'Closed'
                
                # Verify workflow output shows success
                assert any('closed' in item.title.lower() or 'complete' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    @pytest.mark.security
    def test_close_task_injection_protection(self):
        """Test that closeTask.py is protected against injection attacks."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
        }
        
        # Test various injection attempts
        malicious_task_ids = [
            "../../../etc/passwd",           # Path traversal
            "task'; DROP TABLE tasks; --",   # SQL injection style
            "task$(rm -rf /)",               # Command injection
            "task&api_key=stolen",           # URL manipulation
            "<script>alert('xss')</script>", # XSS
        ]
        
        for malicious_id in malicious_task_ids:
            with MockAlfredEnvironment(args=[malicious_id], config=config) as workflow:
                import closeTask
                
                result = workflow.send_feedback()
                
                # Should show error about invalid task ID
                assert any('invalid' in item.title.lower() or 'error' in item.title.lower() for item in workflow.items)
                
                # Should never make an API call with malicious data
                with patch('requests.put') as mock_put:
                    # If any API calls are made, they should be safe
                    if mock_put.called:
                        call_args = mock_put.call_args
                        url = call_args[0][0]
                        # URL should not contain the malicious input directly
                        assert malicious_id not in url
    
    @pytest.mark.integration
    def test_close_task_missing_api_key(self):
        """Test task closing with missing API key."""
        config = {}  # No API key
        
        with MockAlfredEnvironment(args=['8xdfdjbgd'], config=config) as workflow:
            import closeTask
            
            result = workflow.send_feedback()
            
            # Should show error about missing API key
            assert any('API key' in item.title or 'config' in item.subtitle.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_close_task_invalid_task_id(self):
        """Test task closing with invalid task ID format."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
        }
        
        invalid_task_ids = [
            '',              # Empty
            'short',         # Too short
            'TOOLONG1234567', # Too long  
            'task@invalid',  # Special characters
            'task with spaces', # Spaces
        ]
        
        for invalid_id in invalid_task_ids:
            with MockAlfredEnvironment(args=[invalid_id], config=config) as workflow:
                import closeTask
                
                result = workflow.send_feedback()
                
                # Should show error about invalid task ID
                assert any('invalid' in item.title.lower() or 'error' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_close_task_api_error(self):
        """Test task closing when API returns error."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
        }
        
        with MockAlfredEnvironment(args=['8xdfdjbgd'], config=config) as workflow:
            with patch('requests.put') as mock_put:
                # Set up error API response
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_oauth_019_error()
                mock_response.status_code = 401
                mock_response.raise_for_status.side_effect = Exception("HTTP 401")
                mock_put.return_value = mock_response
                
                import closeTask
                
                result = workflow.send_feedback()
                
                # Should show error message
                assert any('error' in item.title.lower() or 'failed' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_close_task_timeout_handling(self):
        """Test that API timeout is properly configured."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
        }
        
        with MockAlfredEnvironment(args=['8xdfdjbgd'], config=config) as workflow:
            with patch('requests.put') as mock_put:
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_update_task_response('8xdfdjbgd')
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_put.return_value = mock_response
                
                import closeTask
                
                # Verify timeout is set in the API call
                mock_put.assert_called_once()
                call_args = mock_put.call_args
                assert 'timeout' in call_args[1]
                assert call_args[1]['timeout'] == 30  # Should use security-recommended timeout
    
    @pytest.mark.integration
    def test_close_task_missing_task_id(self):
        """Test task closing with missing task ID."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
        }
        
        with MockAlfredEnvironment(args=[], config=config) as workflow:
            import closeTask
            
            result = workflow.send_feedback()
            
            # Should show error about missing task ID
            assert any('task' in item.title.lower() and 'id' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_close_task_network_error(self):
        """Test task closing with network connectivity issues."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
        }
        
        with MockAlfredEnvironment(args=['8xdfdjbgd'], config=config) as workflow:
            with patch('requests.put') as mock_put:
                # Simulate network error
                mock_put.side_effect = Exception("Network error")
                
                import closeTask
                
                result = workflow.send_feedback()
                
                # Should show network error message
                assert any('error' in item.title.lower() or 'network' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_close_task_url_construction(self):
        """Test that task URLs are constructed safely."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
        }
        
        valid_task_id = '8xdfdjbgd'
        with MockAlfredEnvironment(args=[valid_task_id], config=config) as workflow:
            with patch('requests.put') as mock_put:
                mock_response = Mock()
                mock_response.json.return_value = MockClickUpAPI.get_update_task_response(valid_task_id)
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_put.return_value = mock_response
                
                import closeTask
                
                # Check that URL is constructed properly
                mock_put.assert_called_once()
                call_args = mock_put.call_args
                url = call_args[0][0]
                
                # URL should be properly formed
                assert url.startswith('https://api.clickup.com/api/v2/task/')
                assert url.endswith(valid_task_id)
                assert '//' not in url[8:]  # No double slashes after https://
                assert '?' not in url       # No query parameters in URL path
                assert '&' not in url       # No additional parameters
    
    @pytest.mark.integration
    def test_close_task_api_key_validation(self):
        """Test that API key is properly validated."""
        config = {
            'password_clickUpAPI': 'invalid@key!with$special'  # Invalid API key format
        }
        
        with MockAlfredEnvironment(args=['8xdfdjbgd'], config=config) as workflow:
            import closeTask
            
            result = workflow.send_feedback()
            
            # Should show error about invalid API key
            assert any('API key' in item.title or 'invalid' in item.title.lower() for item in workflow.items)


class TestCloseTaskStatusHandling:
    """Test status handling and response parsing in closeTask.py."""
    
    @pytest.mark.integration
    def test_close_task_custom_status(self):
        """Test closing task with custom closed status."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
        }
        
        with MockAlfredEnvironment(args=['8xdfdjbgd'], config=config) as workflow:
            with patch('requests.put') as mock_put:
                # Mock response with custom status
                response_data = MockClickUpAPI.get_update_task_response('8xdfdjbgd')
                response_data['status']['status'] = 'Done'  # Custom closed status
                
                mock_response = Mock()
                mock_response.json.return_value = response_data
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_put.return_value = mock_response
                
                import closeTask
                
                result = workflow.send_feedback()
                
                # Should handle custom status names
                assert any('Done' in item.title or 'closed' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_close_task_response_parsing(self):
        """Test that task response is properly parsed."""
        config = {
            'password_clickUpAPI': 'pk_test_api_key'
        }
        
        with MockAlfredEnvironment(args=['8xdfdjbgd'], config=config) as workflow:
            with patch('requests.put') as mock_put:
                # Mock full task response
                response_data = MockClickUpAPI.get_update_task_response('8xdfdjbgd')
                response_data['name'] = 'Test Task Name'
                response_data['url'] = 'https://app.clickup.com/t/8xdfdjbgd'
                
                mock_response = Mock()
                mock_response.json.return_value = response_data
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_put.return_value = mock_response
                
                import closeTask
                
                result = workflow.send_feedback()
                
                # Should include task name and URL in response
                feedback_items = workflow.items
                task_item = next((item for item in feedback_items if 'Test Task Name' in item.title), None)
                assert task_item is not None
                
                # Should provide way to open task
                assert any(item.arg for item in feedback_items if item.arg)


if __name__ == '__main__':
    pytest.main([__file__])