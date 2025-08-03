#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mock Alfred environment for testing workflow scripts.

Provides mock implementations of the Alfred workflow library components
to enable testing without the actual Alfred application.
"""

import json
import tempfile
import os
from typing import Dict, List, Any, Optional
from unittest.mock import Mock


class MockWorkflowItem:
    """Mock implementation of Alfred workflow item."""
    
    def __init__(self, title: str, subtitle: str = "", arg: str = None, 
                 autocomplete: str = None, valid: bool = True, icon: str = None, **kwargs):
        self.title = title
        self.subtitle = subtitle
        self.arg = arg
        self.autocomplete = autocomplete
        self.valid = valid
        self.icon = icon
        self.variables = {}
        self.modifiers = {}
        self.kwargs = kwargs
    
    def setvar(self, name: str, value: str):
        """Set a workflow variable."""
        self.variables[name] = value
    
    def getvar(self, name: str, default: str = None) -> str:
        """Get a workflow variable."""
        return self.variables.get(name, default)
    
    def add_modifier(self, key: str, subtitle: str = None, arg: str = None, valid: bool = None):
        """Add a modifier to the item."""
        modifier = {
            'subtitle': subtitle,
            'arg': arg,
            'valid': valid
        }
        self.modifiers[key] = {k: v for k, v in modifier.items() if v is not None}
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary for Alfred JSON format."""
        item_dict = {
            'title': self.title,
            'subtitle': self.subtitle,
            'valid': self.valid
        }
        
        if self.arg is not None:
            item_dict['arg'] = self.arg
        if self.autocomplete is not None:
            item_dict['autocomplete'] = self.autocomplete
        if self.icon is not None:
            item_dict['icon'] = self.icon
        if self.variables:
            item_dict['variables'] = self.variables
        if self.modifiers:
            item_dict['mods'] = self.modifiers
            
        return item_dict


class MockWorkflowLogger:
    """Mock implementation of workflow logger."""
    
    def __init__(self):
        self.logs = []
    
    def debug(self, message: str):
        self.logs.append(('DEBUG', message))
    
    def info(self, message: str):
        self.logs.append(('INFO', message))
    
    def warning(self, message: str):
        self.logs.append(('WARNING', message))
    
    def error(self, message: str):
        self.logs.append(('ERROR', message))
    
    def get_logs(self, level: str = None) -> List[tuple]:
        """Get logs, optionally filtered by level."""
        if level:
            return [log for log in self.logs if log[0] == level]
        return self.logs


class MockWorkflowWeb:
    """Mock implementation of workflow web requests."""
    
    def __init__(self):
        self.requests = []
        self.responses = {}
        self.default_response = None
    
    def set_response(self, url: str, response_data: Dict[str, Any], 
                    status_code: int = 200, headers: Dict[str, str] = None):
        """Set a mock response for a specific URL."""
        mock_response = Mock()
        mock_response.json.return_value = response_data
        mock_response.status_code = status_code
        mock_response.headers = headers or {}
        mock_response.text = json.dumps(response_data)
        mock_response.raise_for_status = Mock()
        
        if status_code >= 400:
            from requests.exceptions import HTTPError
            mock_response.raise_for_status.side_effect = HTTPError(f"HTTP {status_code}")
        
        self.responses[url] = mock_response
    
    def set_default_response(self, response_data: Dict[str, Any], 
                           status_code: int = 200):
        """Set a default response for any unmocked URL."""
        self.set_response('__default__', response_data, status_code)
        self.default_response = self.responses['__default__']
    
    def get(self, url: str, params: Dict = None, headers: Dict = None, 
           timeout: int = None):
        """Mock GET request."""
        self.requests.append({
            'method': 'GET',
            'url': url,
            'params': params,
            'headers': headers,
            'timeout': timeout
        })
        
        return self.responses.get(url, self.default_response)
    
    def post(self, url: str, data: Dict = None, json: Dict = None, 
            headers: Dict = None, timeout: int = None):
        """Mock POST request."""
        self.requests.append({
            'method': 'POST',
            'url': url,
            'data': data,
            'json': json,
            'headers': headers,
            'timeout': timeout
        })
        
        return self.responses.get(url, self.default_response)
    
    def put(self, url: str, data: Dict = None, json: Dict = None,
           headers: Dict = None, timeout: int = None):
        """Mock PUT request."""
        self.requests.append({
            'method': 'PUT',
            'url': url,
            'data': data,
            'json': json,
            'headers': headers,
            'timeout': timeout
        })
        
        return self.responses.get(url, self.default_response)


class MockWorkflow:
    """Mock implementation of Alfred Workflow class."""
    
    def __init__(self, args: List[str] = None):
        self.args = args or []
        self.items = []
        self.settings = {}
        self._passwords = {}
        self._cache = {}
        self.logger = MockWorkflowLogger()
        self.web = MockWorkflowWeb()
        self._temp_dir = tempfile.mkdtemp()
        self._feedback_sent = False
        
        # Mock workflow constants
        self.ICON_WARNING = 'icon_warning.png'
        self.ICON_ERROR = 'icon_error.png'
        self.ICON_INFO = 'icon_info.png'
    
    def add_item(self, title: str, subtitle: str = "", arg: str = None,
                autocomplete: str = None, valid: bool = True, 
                icon: str = None, **kwargs) -> MockWorkflowItem:
        """Add an item to the workflow results."""
        item = MockWorkflowItem(
            title=title,
            subtitle=subtitle,
            arg=arg,
            autocomplete=autocomplete,
            valid=valid,
            icon=icon,
            **kwargs
        )
        self.items.append(item)
        return item
    
    def send_feedback(self) -> str:
        """Send feedback to Alfred (return JSON for testing)."""
        self._feedback_sent = True
        feedback = {
            'items': [item.to_dict() for item in self.items]
        }
        return json.dumps(feedback, indent=2)
    
    def get_password(self, account: str) -> Optional[str]:
        """Get password from keychain (mock)."""
        return self._passwords.get(account)
    
    def save_password(self, account: str, password: str):
        """Save password to keychain (mock)."""
        self._passwords[account] = password
    
    def delete_password(self, account: str):
        """Delete password from keychain (mock)."""
        self._passwords.pop(account, None)
    
    def cached_data(self, name: str, data_func=None, max_age: int = 60) -> Any:
        """Get cached data (mock)."""
        if name in self._cache:
            return self._cache[name]
        
        if data_func and callable(data_func):
            data = data_func()
            self._cache[name] = data
            return data
        
        return None
    
    def cache_data(self, name: str, data: Any):
        """Cache data (mock)."""
        self._cache[name] = data
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
    
    def run(self, func):
        """Run the workflow function (mock)."""
        try:
            return func(self)
        except SystemExit as e:
            return e.code
        except Exception as e:
            self.logger.error(f"Workflow error: {e}")
            raise
    
    def run_trigger(self, name: str, arg: str = None):
        """Run a workflow trigger (mock)."""
        self.logger.debug(f"Trigger '{name}' called with arg: {arg}")
        return f"trigger_{name}_{arg}"
    
    def notify(self, title: str, text: str = ""):
        """Send a notification (mock)."""
        self.logger.info(f"Notification: {title} - {text}")
    
    @property
    def datadir(self) -> str:
        """Get workflow data directory."""
        return self._temp_dir
    
    @property
    def cachedir(self) -> str:
        """Get workflow cache directory."""
        return self._temp_dir
    
    def cleanup(self):
        """Clean up temporary resources."""
        import shutil
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)


class MockAlfredEnvironment:
    """Context manager for mocking Alfred environment."""
    
    def __init__(self, args: List[str] = None, config: Dict[str, Any] = None):
        self.args = args or []
        self.config = config or {}
        self.workflow = None
        self.original_modules = {}
    
    def __enter__(self) -> MockWorkflow:
        """Set up mock environment."""
        import sys
        
        # Mock the workflow module
        self.workflow = MockWorkflow(self.args)
        
        # Set up mock configuration
        for key, value in self.config.items():
            if key.startswith('password_'):
                account = key.replace('password_', '')
                self.workflow.save_password(account, value)
            else:
                self.workflow.settings[key] = value
        
        # Mock common workflow imports
        sys.modules['workflow'] = Mock()
        sys.modules['workflow'].Workflow = lambda: self.workflow
        sys.modules['workflow'].web = self.workflow.web
        sys.modules['workflow'].ICON_WARNING = self.workflow.ICON_WARNING
        sys.modules['workflow'].ICON_ERROR = self.workflow.ICON_ERROR
        sys.modules['workflow'].ICON_INFO = self.workflow.ICON_INFO
        
        return self.workflow
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up mock environment."""
        if self.workflow:
            self.workflow.cleanup()
        
        # Restore original modules
        import sys
        for name, module in self.original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def create_mock_workflow(args: List[str] = None, **config) -> MockWorkflow:
    """Create a mock workflow instance for testing."""
    workflow = MockWorkflow(args)
    
    # Set up configuration
    for key, value in config.items():
        if key.startswith('password_'):
            account = key.replace('password_', '')
            workflow.save_password(account, value)
        else:
            workflow.settings[key] = value
    
    return workflow