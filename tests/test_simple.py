#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple smoke tests to verify basic functionality.
These tests verify that the code can be imported and basic functions work.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest


def test_validation_imports():
    """Test that validation module can be imported."""
    from validation import validate_clickup_id, validate_api_key
    assert validate_clickup_id is not None
    assert validate_api_key is not None


def test_validate_task_id():
    """Test basic task ID validation."""
    from validation import validate_clickup_id
    
    # Valid task IDs
    assert validate_clickup_id("8xdfdjbgd", "task") == "8xdfdjbgd"
    assert validate_clickup_id("abc12345", "task") == "abc12345"
    
    # Invalid task IDs
    with pytest.raises(ValueError):
        validate_clickup_id("", "task")
    
    with pytest.raises(ValueError):
        validate_clickup_id("../etc/passwd", "task")


def test_validate_api_key():
    """Test API key validation."""
    from validation import validate_api_key
    
    # Valid API key
    assert validate_api_key("pk_1234567890abcdef") == "pk_1234567890abcdef"
    
    # Invalid API keys
    with pytest.raises(ValueError):
        validate_api_key("")
    
    with pytest.raises(ValueError):
        validate_api_key("invalid@key")


def test_configStore_imports():
    """Test that configStore module can be imported."""
    import configStore
    assert configStore is not None


def test_fuzzy_imports():
    """Test that fuzzy module can be imported."""
    import fuzzy
    assert fuzzy is not None


if __name__ == '__main__':
    pytest.main([__file__])