# ClickUp ID Validation Guide

**Date**: August 2, 2025  
**Purpose**: Define proper validation for ClickUp IDs based on API documentation and observed patterns

## ClickUp ID Formats

Based on analysis of ClickUp API documentation and the alfred-clickup-four13 codebase, here are the ID formats used by ClickUp:

### ID Types and Patterns

| ID Type | Format | Examples | Pattern | Notes |
|---------|--------|----------|---------|-------|
| **Task ID** | 8-9 char alphanumeric | `8xdfdjbgd`, `8xdfm9vmz`, `8xdfe67cz` | `^[a-z0-9]{8,9}$` | Lowercase letters and numbers |
| **Workspace ID** | Numeric | `333`, `90170402244889` | `^[0-9]+$` | Previously called "Team ID" in API |
| **User ID** | Numeric | `395492` | `^[0-9]+$` | User identifiers |
| **Space ID** | Alphanumeric | `90170402244889` | `^[a-zA-Z0-9]+$` | Can be 14+ characters |
| **List ID** | Alphanumeric | Variable length | `^[a-zA-Z0-9]+$` | Can be 14+ characters |
| **Folder ID** | Alphanumeric | Variable length | `^[a-zA-Z0-9]+$` | Can be 14+ characters |
| **Custom Task ID** | Alphanumeric + underscore | `PROJ_123` | `^[A-Z0-9_]+$` | All caps prefix, user-defined |

### Key Observations

1. **Length Variations**: Modern ClickUp IDs can be 14+ characters (contrary to old 7-character limit)
2. **Case Sensitivity**: Task IDs appear to use lowercase, while custom task IDs use uppercase
3. **Character Set**: Generally alphanumeric, with underscores allowed only in custom task IDs
4. **Legacy Terms**: API still uses "team_id" to refer to workspace IDs

## Validation Implementation

### Recommended Validation Function

```python
import re

def validate_clickup_id(id_value, id_type='generic'):
    """Validate ClickUp ID format based on type
    
    Args:
        id_value (str): The ID to validate
        id_type (str): Type of ID - 'task', 'workspace', 'space', 'list', 'folder', 'user', 'custom_task'
    
    Returns:
        str: Validated ID
        
    Raises:
        ValueError: If ID format is invalid
    """
    if not id_value:
        raise ValueError("ID cannot be empty")
    
    # Remove any whitespace
    id_value = id_value.strip()
    
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
```

### Usage Examples

```python
# Validate different ID types
try:
    # Task validation
    task_id = validate_clickup_id("8xdfdjbgd", "task")  # Valid
    
    # Workspace validation
    workspace_id = validate_clickup_id("333", "workspace")  # Valid
    
    # Space validation (long ID)
    space_id = validate_clickup_id("90170402244889", "space")  # Valid
    
    # Invalid task ID (wrong length)
    bad_task = validate_clickup_id("abc", "task")  # Raises ValueError
    
except ValueError as e:
    print(f"Validation error: {e}")
```

### Integration Points

The validation should be applied at these critical points in the workflow:

1. **API URL Construction**
   ```python
   # Before:
   url = 'https://api.clickup.com/api/v2/task/' + strTaskId
   
   # After:
   url = f'https://api.clickup.com/api/v2/task/{validate_clickup_id(strTaskId, "task")}'
   ```

2. **Configuration Validation**
   ```python
   # Validate configured IDs
   workspace_id = validate_clickup_id(getConfigValue('workspace'), 'workspace')
   space_id = validate_clickup_id(getConfigValue('space'), 'space')
   list_id = validate_clickup_id(getConfigValue('list'), 'list')
   ```

3. **User Input Processing**
   ```python
   # When parsing user commands
   if task_id_from_user:
       task_id = validate_clickup_id(task_id_from_user, 'task')
   ```

## Security Considerations

### Why Validation is Critical

1. **API Injection Prevention**: Unvalidated IDs could be manipulated to access unauthorized endpoints
2. **Path Traversal**: Without validation, IDs like `../../admin` could be attempted
3. **Error Information Leakage**: Invalid IDs might trigger verbose error messages exposing system details
4. **Rate Limiting Bypass**: Malformed IDs could potentially bypass rate limiting

### What Validation Prevents

```python
# Attack examples that validation prevents:

# SQL Injection attempt
malicious_id = "'; DROP TABLE tasks; --"
# ValueError: Invalid task ID format

# Path traversal attempt  
malicious_id = "../../../etc/passwd"
# ValueError: Invalid task ID format

# Script injection
malicious_id = "<script>alert('xss')</script>"
# ValueError: Invalid task ID format

# API manipulation
malicious_id = "task_id&api_key=stolen"
# ValueError: Invalid task ID format
```

## Implementation Checklist

- [ ] Add `validate_clickup_id()` function to a shared module
- [ ] Replace all direct string concatenations with validated versions
- [ ] Add validation to configuration storage/retrieval
- [ ] Implement proper error handling for validation failures
- [ ] Add unit tests for all ID type validations
- [ ] Document validation in user-facing error messages

## Testing Requirements

```python
# Test cases that must pass
def test_clickup_id_validation():
    # Valid IDs
    assert validate_clickup_id("8xdfdjbgd", "task") == "8xdfdjbgd"
    assert validate_clickup_id("333", "workspace") == "333"
    assert validate_clickup_id("90170402244889", "space") == "90170402244889"
    
    # Invalid IDs
    with pytest.raises(ValueError):
        validate_clickup_id("", "task")  # Empty
        validate_clickup_id("abc", "task")  # Too short
        validate_clickup_id("UPPERCASE", "task")  # Wrong case
        validate_clickup_id("test@123", "workspace")  # Special chars
        validate_clickup_id("../../etc", "space")  # Path traversal
```

## Migration Notes

When implementing validation in the existing codebase:

1. **Backward Compatibility**: Ensure existing valid IDs continue to work
2. **Error Messages**: Provide clear guidance on valid ID formats
3. **Gradual Rollout**: Consider warning mode before strict enforcement
4. **Documentation**: Update all user documentation with ID format requirements