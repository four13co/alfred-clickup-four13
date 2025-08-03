#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for config.py workflow script.

Tests the configuration management functionality with mocked Alfred environment.
"""

import pytest
import sys
import os
from unittest.mock import patch, Mock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.fixtures.mock_alfred import MockAlfredEnvironment, create_mock_workflow
from tests.fixtures.mock_clickup_api import MockClickUpAPI, MockClickUpAPIServer


class TestConfigWorkflow:
    """Integration tests for config.py script."""
    
    @pytest.mark.integration
    def test_config_display_masked_values(self):
        """Test that configuration displays with masked sensitive values."""
        config = {
            'password_clickUpAPI': 'pk_very_secret_api_key_1234567890',
            'workspace': '333',
            'list': '90170402244889',
            'space': '90170402244889'
        }
        
        with MockAlfredEnvironment(args=[], config=config) as workflow:
            import config as config_module
            
            result = workflow.send_feedback()
            
            # Should show configuration items
            assert len(workflow.items) > 0
            
            # Find API key item
            api_items = [item for item in workflow.items if 'API' in item.title]
            assert len(api_items) > 0
            
            api_item = api_items[0]
            # Should show masked API key, not full key
            assert 'pk_very_secret_api_key_1234567890' not in api_item.subtitle
            assert 'very_secret' not in api_item.subtitle
            assert '***' in api_item.subtitle or 'pk_***' in api_item.subtitle
    
    @pytest.mark.integration
    def test_config_set_api_key(self):
        """Test setting API key through config interface."""
        config = {}  # Start with empty config
        
        # Test setting API key
        with MockAlfredEnvironment(args=['clickUpAPI', 'pk_new_api_key_12345'], config=config) as workflow:
            import config as config_module
            
            result = workflow.send_feedback()
            
            # Should confirm API key was set
            assert any('API' in item.title and 'set' in item.title.lower() for item in workflow.items)
            
            # Check that API key was stored (should be in mock password store)
            assert workflow.get_password('clickUpAPI') == 'pk_new_api_key_12345'
    
    @pytest.mark.integration
    @pytest.mark.security
    def test_config_validate_api_key_format(self):
        """Test that config validates API key format."""
        config = {}
        
        # Test with invalid API key
        invalid_api_keys = [
            'invalid@key',           # Special characters
            'short',                 # Too short
            'key with spaces',       # Spaces
            'key-with-dashes',       # Dashes not allowed
        ]
        
        for invalid_key in invalid_api_keys:
            with MockAlfredEnvironment(args=['clickUpAPI', invalid_key], config=config) as workflow:
                import config as config_module
                
                result = workflow.send_feedback()
                
                # Should show error about invalid format
                assert any('invalid' in item.title.lower() or 'error' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    @pytest.mark.security  
    def test_config_validate_workspace_id(self):
        """Test that config validates workspace ID format."""
        config = {}
        
        # Test with invalid workspace IDs
        invalid_workspace_ids = [
            '../../../etc/passwd',   # Path traversal
            'workspace@invalid',     # Special characters
            'workspace with spaces', # Spaces
            '',                      # Empty
        ]
        
        for invalid_id in invalid_workspace_ids:
            with MockAlfredEnvironment(args=['workspace', invalid_id], config=config) as workflow:
                import config as config_module
                
                result = workflow.send_feedback()
                
                # Should show error about invalid format
                assert any('invalid' in item.title.lower() or 'error' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_config_set_workspace_id(self):
        """Test setting workspace ID through config interface."""
        config = {}
        
        with MockAlfredEnvironment(args=['workspace', '333'], config=config) as workflow:
            import config as config_module
            
            result = workflow.send_feedback()
            
            # Should confirm workspace was set
            assert any('workspace' in item.title.lower() and 'set' in item.title.lower() for item in workflow.items)
            
            # Check that workspace was stored
            assert workflow.settings.get('workspace') == '333'
    
    @pytest.mark.integration
    def test_config_set_list_id(self):
        """Test setting list ID through config interface."""
        config = {}
        
        with MockAlfredEnvironment(args=['list', '90170402244889'], config=config) as workflow:
            import config as config_module
            
            result = workflow.send_feedback()
            
            # Should confirm list was set
            assert any('list' in item.title.lower() and 'set' in item.title.lower() for item in workflow.items)
            
            # Check that list was stored
            assert workflow.settings.get('list') == '90170402244889'
    
    @pytest.mark.integration
    def test_config_set_space_id(self):
        """Test setting space ID through config interface."""
        config = {}
        
        with MockAlfredEnvironment(args=['space', '90170402244889'], config=config) as workflow:
            import config as config_module
            
            result = workflow.send_feedback()
            
            # Should confirm space was set
            assert any('space' in item.title.lower() and 'set' in item.title.lower() for item in workflow.items)
            
            # Check that space was stored
            assert workflow.settings.get('space') == '90170402244889'
    
    @pytest.mark.integration
    def test_config_help_display(self):
        """Test that config shows help when no arguments provided."""
        with MockAlfredEnvironment(args=[], config={}) as workflow:
            import config as config_module
            
            result = workflow.send_feedback()
            
            # Should show configuration options
            config_items = workflow.items
            assert len(config_items) >= 4  # API, workspace, list, space
            
            # Should have items for all main config options
            config_titles = [item.title.lower() for item in config_items]
            assert any('api' in title for title in config_titles)
            assert any('workspace' in title or 'team' in title for title in config_titles)
            assert any('list' in title for title in config_titles)
            assert any('space' in title for title in config_titles)
    
    @pytest.mark.integration
    def test_config_invalid_option(self):
        """Test config with invalid configuration option."""
        with MockAlfredEnvironment(args=['invalid_option', 'value'], config={}) as workflow:
            import config as config_module
            
            result = workflow.send_feedback()
            
            # Should show error about invalid option
            assert any('invalid' in item.title.lower() or 'unknown' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_config_missing_value(self):
        """Test config with missing value for setting."""
        with MockAlfredEnvironment(args=['clickUpAPI'], config={}) as workflow:
            import config as config_module
            
            result = workflow.send_feedback()
            
            # Should show current value or prompt for value
            assert len(workflow.items) > 0
            # Should either show current value or ask for input
            assert any('enter' in item.subtitle.lower() or 'current' in item.subtitle.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_config_current_values_display(self):
        """Test that config shows current values correctly."""
        config = {
            'password_clickUpAPI': 'pk_current_api_key',
            'workspace': '333',
            'list': '90170402244889',
            'space': '90170402244889'
        }
        
        with MockAlfredEnvironment(args=[], config=config) as workflow:
            import config as config_module
            
            result = workflow.send_feedback()
            
            # Find items and check they show current values
            config_items = workflow.items
            
            # API key should be masked
            api_items = [item for item in config_items if 'api' in item.title.lower()]
            assert len(api_items) > 0
            api_item = api_items[0]
            assert 'pk_***' in api_item.subtitle or '***' in api_item.subtitle
            
            # Other values should be shown
            workspace_items = [item for item in config_items if 'workspace' in item.title.lower() or 'team' in item.title.lower()]
            if workspace_items:
                assert '333' in workspace_items[0].subtitle
            
            list_items = [item for item in config_items if 'list' in item.title.lower()]
            if list_items:
                assert '90170402244889' in list_items[0].subtitle


class TestConfigValidation:
    """Test validation in config.py."""
    
    @pytest.mark.integration
    @pytest.mark.security
    def test_config_injection_protection(self):
        """Test that config is protected against injection attacks."""
        config = {}
        
        # Test various injection attempts
        injection_attempts = [
            ('clickUpAPI', "../../../etc/passwd"),
            ('workspace', "'; DROP TABLE config; --"),
            ('list', "<script>alert('xss')</script>"),
            ('space', "$(rm -rf /)"),
        ]
        
        for config_key, malicious_value in injection_attempts:
            with MockAlfredEnvironment(args=[config_key, malicious_value], config=config) as workflow:
                import config as config_module
                
                result = workflow.send_feedback()
                
                # Should reject malicious input
                assert any('invalid' in item.title.lower() or 'error' in item.title.lower() for item in workflow.items)
    
    @pytest.mark.integration
    def test_config_whitespace_handling(self):
        """Test that config properly handles whitespace in values."""
        config = {}
        
        # Test with values that have leading/trailing whitespace
        test_cases = [
            ('workspace', '  333  ', '333'),
            ('list', '  90170402244889  ', '90170402244889'),
            ('clickUpAPI', '  pk_api_key_123  ', 'pk_api_key_123'),
        ]
        
        for config_key, input_value, expected_value in test_cases:
            with MockAlfredEnvironment(args=[config_key, input_value], config=config) as workflow:
                import config as config_module
                
                result = workflow.send_feedback()
                
                # Should succeed (strip whitespace)
                success_items = [item for item in workflow.items if 'set' in item.title.lower()]
                assert len(success_items) > 0
                
                # Check stored value is trimmed
                if config_key == 'clickUpAPI':
                    assert workflow.get_password('clickUpAPI') == expected_value
                else:
                    assert workflow.settings.get(config_key) == expected_value


if __name__ == '__main__':
    pytest.main([__file__])