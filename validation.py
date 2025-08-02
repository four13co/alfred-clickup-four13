#!/usr/bin/python3
# encoding: utf-8
"""
ClickUp ID validation module for Alfred workflow.

This module provides validation functions to ensure ClickUp IDs are properly
formatted and safe to use in API calls, preventing injection attacks and
API errors.
"""

import re


def validate_clickup_id(id_value, id_type='generic'):
    """Validate ClickUp ID format based on type.
    
    Args:
        id_value (str): The ID to validate
        id_type (str): Type of ID - 'task', 'workspace', 'space', 'list', 
                      'folder', 'user', 'custom_task', 'team' (alias for workspace)
    
    Returns:
        str: Validated ID
        
    Raises:
        ValueError: If ID format is invalid
    """
    if not id_value:
        raise ValueError("ID cannot be empty")
    
    # Convert to string and strip whitespace
    id_value = str(id_value).strip()
    
    # Define patterns based on ClickUp's actual ID formats
    patterns = {
        'task': r'^[a-z0-9]{8,9}$',       # 8-9 char alphanumeric lowercase
        'workspace': r'^[0-9]+$',          # Numeric only (legacy: team)
        'team': r'^[0-9]+$',               # Alias for workspace
        'user': r'^[0-9]+$',               # Numeric only
        'space': r'^[a-zA-Z0-9]+$',       # Alphanumeric, variable length
        'list': r'^[a-zA-Z0-9]+$',        # Alphanumeric, variable length
        'folder': r'^[a-zA-Z0-9]+$',      # Alphanumeric, variable length
        'custom_task': r'^[A-Z0-9_]+$',   # Uppercase with underscores
        'generic': r'^[a-zA-Z0-9_]+$'     # Most permissive pattern
    }
    
    pattern = patterns.get(id_type, patterns['generic'])
    
    if not re.match(pattern, id_value):
        raise ValueError(f"Invalid {id_type} ID format: {id_value}")
    
    # Additional length validation for specific types
    if id_type == 'task' and len(id_value) not in [8, 9]:
        raise ValueError(f"Task ID must be 8-9 characters, got {len(id_value)}")
    
    return id_value


def validate_api_key(api_key):
    """Validate ClickUp API key format.
    
    Args:
        api_key (str): The API key to validate
        
    Returns:
        str: Validated API key
        
    Raises:
        ValueError: If API key format is invalid
    """
    if not api_key:
        raise ValueError("API key cannot be empty")
    
    # ClickUp API keys should start with 'pk_' based on documentation
    # But also allow legacy formats for backward compatibility
    api_key = str(api_key).strip()
    
    # Basic validation - must be alphanumeric with underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', api_key):
        raise ValueError("Invalid API key format")
    
    # Minimum length check
    if len(api_key) < 10:
        raise ValueError("API key too short")
    
    return api_key


def sanitize_url_parameter(param):
    """Sanitize a parameter for safe URL construction.
    
    Args:
        param (str): Parameter to sanitize
        
    Returns:
        str: Sanitized parameter
    """
    if not param:
        return ''
    
    # Convert to string and strip
    param = str(param).strip()
    
    # Remove any URL-unsafe characters
    # Allow only alphanumeric, underscore, dash
    sanitized = re.sub(r'[^a-zA-Z0-9_\-]', '', param)
    
    return sanitized


def build_safe_api_url(base_url, endpoint, **kwargs):
    """Build a safe API URL with validated parameters.
    
    Args:
        base_url (str): Base API URL (e.g., 'https://api.clickup.com/api/v2')
        endpoint (str): API endpoint (e.g., 'task')
        **kwargs: ID parameters with their types (e.g., task_id='abc123', id_type='task')
        
    Returns:
        str: Safe API URL
        
    Example:
        url = build_safe_api_url(
            'https://api.clickup.com/api/v2',
            'task',
            task_id=('8xdfdjbgd', 'task')
        )
        # Returns: 'https://api.clickup.com/api/v2/task/8xdfdjbgd'
    """
    # Ensure base URL doesn't end with slash
    base_url = base_url.rstrip('/')
    
    # Build endpoint path
    url_parts = [base_url, endpoint.strip('/')]
    
    # Add validated ID parameters
    for key, value in kwargs.items():
        if isinstance(value, tuple):
            id_value, id_type = value
            validated_id = validate_clickup_id(id_value, id_type)
            url_parts.append(validated_id)
        else:
            # If not a tuple, treat as generic ID
            validated_id = validate_clickup_id(value, 'generic')
            url_parts.append(validated_id)
    
    return '/'.join(url_parts)