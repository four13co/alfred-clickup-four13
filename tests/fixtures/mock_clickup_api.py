#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mock ClickUp API responses for testing.

Provides realistic mock responses for ClickUp API endpoints to enable
comprehensive testing without hitting the actual API.
"""

from typing import Dict, Any, List
import json


class MockClickUpAPI:
    """Mock ClickUp API with realistic responses."""
    
    # Sample data that matches real ClickUp API responses
    SAMPLE_USER = {
        "id": 123456,
        "username": "testuser",
        "email": "test@example.com",
        "color": "#7ce7ff",
        "profilePicture": "https://attachments.clickup.com/profilePictures/123456.jpg",
        "initials": "TU",
        "week_start_day": 1,
        "global_font_support": True,
        "timezone": "America/New_York"
    }
    
    SAMPLE_TEAM = {
        "id": "333",
        "name": "Test Team",
        "color": "#7ce7ff",
        "avatar": None,
        "members": [
            {
                "user": SAMPLE_USER,
                "invited_by": SAMPLE_USER
            }
        ]
    }
    
    SAMPLE_SPACE = {
        "id": "90170402244889",
        "name": "Test Space",
        "private": False,
        "statuses": [
            {
                "id": "p90170402244889_VlN8IJtk",
                "status": "Open",
                "type": "open",
                "orderindex": 0,
                "color": "#d3d3d3"
            },
            {
                "id": "p90170402244889_14GpgqNs",
                "status": "in progress",
                "type": "custom",
                "orderindex": 1,
                "color": "#4194f6"
            },
            {
                "id": "p90170402244889_12wyWBHt",
                "status": "Closed",
                "type": "closed",
                "orderindex": 2,
                "color": "#6bc950"
            }
        ],
        "multiple_assignees": True,
        "features": {
            "due_dates": {"enabled": True, "start_date": False, "remap_due_dates": True, "remap_closed_due_date": False},
            "time_tracking": {"enabled": False},
            "tags": {"enabled": True},
            "time_estimates": {"enabled": True},
            "checklists": {"enabled": True},
            "custom_fields": {"enabled": True},
            "remap_dependencies": {"enabled": True},
            "dependency_warning": {"enabled": True},
            "portfolios": {"enabled": True}
        }
    }
    
    SAMPLE_LIST = {
        "id": "90170402244889",
        "name": "Test List",
        "orderindex": 0,
        "status": None,
        "priority": None,
        "assignee": None,
        "task_count": 3,
        "due_date": None,
        "due_date_time": False,
        "start_date": None,
        "start_date_time": False,
        "folder": {
            "id": "90170402244889",
            "name": "Test Folder",
            "hidden": False,
            "access": True
        },
        "space": SAMPLE_SPACE,
        "archived": False,
        "override_statuses": False,
        "permission_level": "create"
    }
    
    SAMPLE_TASK = {
        "id": "8xdfdjbgd",
        "custom_id": None,
        "name": "Test Task",
        "text_content": "This is a test task",
        "description": "This is a test task description",
        "status": {
            "id": "p90170402244889_VlN8IJtk",
            "status": "Open",
            "color": "#d3d3d3",
            "type": "open",
            "orderindex": 0
        },
        "orderindex": "1.00000000000000000000000000000000",
        "date_created": "1567780450202",
        "date_updated": "1567780450202",
        "date_closed": None,
        "archived": False,
        "creator": SAMPLE_USER,
        "assignees": [SAMPLE_USER],
        "watchers": [SAMPLE_USER],
        "checklists": [],
        "tags": [
            {
                "name": "test",
                "tag_fg": "#ffffff",
                "tag_bg": "#ff0000",
                "creator": 123456
            }
        ],
        "parent": None,
        "priority": {
            "id": "1",
            "priority": "urgent",
            "color": "#f50000",
            "orderindex": "1"
        },
        "due_date": None,
        "start_date": None,
        "points": None,
        "time_estimate": None,
        "time_spent": 0,
        "custom_fields": [],
        "dependencies": [],
        "linked_tasks": [],
        "team_id": "333",
        "url": "https://app.clickup.com/t/8xdfdjbgd",
        "permission_level": "create",
        "list": SAMPLE_LIST,
        "project": {
            "id": "90170402244889",
            "name": "Test Folder",
            "hidden": False,
            "access": True
        },
        "folder": {
            "id": "90170402244889",
            "name": "Test Folder",
            "hidden": False,
            "access": True
        },
        "space": SAMPLE_SPACE
    }
    
    SAMPLE_TAG = {
        "name": "test",
        "tag_fg": "#ffffff",
        "tag_bg": "#ff0000",
        "creator": 123456
    }
    
    @classmethod
    def get_user_response(cls) -> Dict[str, Any]:
        """Get user info response."""
        return {"user": cls.SAMPLE_USER}
    
    @classmethod
    def get_teams_response(cls) -> Dict[str, Any]:
        """Get teams/workspaces response."""
        return {"teams": [cls.SAMPLE_TEAM]}
    
    @classmethod
    def get_spaces_response(cls) -> Dict[str, Any]:
        """Get spaces response."""
        return {"spaces": [cls.SAMPLE_SPACE]}
    
    @classmethod
    def get_lists_response(cls) -> Dict[str, Any]:
        """Get lists response."""
        return {"lists": [cls.SAMPLE_LIST]}
    
    @classmethod
    def get_tasks_response(cls, count: int = 3) -> Dict[str, Any]:
        """Get tasks response."""
        tasks = []
        for i in range(count):
            task = cls.SAMPLE_TASK.copy()
            task["id"] = f"task_{i}"
            task["name"] = f"Test Task {i + 1}"
            tasks.append(task)
        return {"tasks": tasks}
    
    @classmethod
    def get_task_response(cls, task_id: str = "8xdfdjbgd") -> Dict[str, Any]:
        """Get single task response."""
        task = cls.SAMPLE_TASK.copy()
        task["id"] = task_id
        return task
    
    @classmethod
    def get_tags_response(cls) -> Dict[str, Any]:
        """Get tags response."""
        return {"tags": [cls.SAMPLE_TAG]}
    
    @classmethod
    def get_create_task_response(cls, name: str = "New Task") -> Dict[str, Any]:
        """Get create task response."""
        task = cls.SAMPLE_TASK.copy()
        task["id"] = "new_task_123"
        task["name"] = name
        task["date_created"] = "1567780450202"
        task["date_updated"] = "1567780450202"
        return task
    
    @classmethod
    def get_update_task_response(cls, task_id: str = "8xdfdjbgd") -> Dict[str, Any]:
        """Get update task response."""
        task = cls.SAMPLE_TASK.copy()
        task["id"] = task_id
        task["status"]["status"] = "Closed"
        task["status"]["type"] = "closed"
        task["date_closed"] = "1567780450202"
        return task
    
    @classmethod
    def get_error_response(cls, error_code: str, message: str) -> Dict[str, Any]:
        """Get error response."""
        return {
            "err": message,
            "ECODE": error_code
        }
    
    @classmethod
    def get_oauth_019_error(cls) -> Dict[str, Any]:
        """Get OAuth 019 error (wrong API key)."""
        return cls.get_error_response("OAUTH_019", "Token invalid")
    
    @classmethod
    def get_oauth_023_error(cls) -> Dict[str, Any]:
        """Get OAuth 023 error (wrong list/team ID)."""
        return cls.get_error_response("OAUTH_023", "Team not authorized")
    
    @classmethod
    def get_oauth_027_error(cls) -> Dict[str, Any]:
        """Get OAuth 027 error (wrong space/project ID)."""
        return cls.get_error_response("OAUTH_027", "Workspace not authorized")


class MockClickUpAPIServer:
    """Mock server that provides ClickUp API responses based on URL patterns."""
    
    def __init__(self):
        self.api = MockClickUpAPI()
        self.base_url = "https://api.clickup.com/api/v2"
        self.v3_base_url = "https://api.clickup.com/api/v3"
    
    def get_response_for_url(self, url: str, method: str = "GET", 
                           data: Dict = None) -> Dict[str, Any]:
        """Get appropriate response for a given URL."""
        
        # User endpoints
        if url == f"{self.base_url}/user":
            return self.api.get_user_response()
        
        # Team endpoints
        if url == f"{self.base_url}/team":
            return self.api.get_teams_response()
        
        # Check for team-specific endpoints
        if "/team/" in url:
            if url.endswith("/space"):
                return self.api.get_spaces_response()
            elif url.endswith("/list"):
                return self.api.get_lists_response()
            elif "/task" in url:
                return self.api.get_tasks_response()
        
        # Space endpoints
        if "/space/" in url:
            if url.endswith("/tag"):
                return self.api.get_tags_response()
            elif url.endswith("/list"):
                return self.api.get_lists_response()
            elif url.endswith("/folder"):
                return {"folders": []}
        
        # Folder endpoints
        if "/folder/" in url and url.endswith("/list"):
            return self.api.get_lists_response()
        
        # Task endpoints
        if "/task/" in url:
            if method == "POST":
                task_name = data.get("name", "New Task") if data else "New Task"
                return self.api.get_create_task_response(task_name)
            elif method == "PUT":
                task_id = url.split("/task/")[-1]
                return self.api.get_update_task_response(task_id)
            else:
                task_id = url.split("/task/")[-1]
                return self.api.get_task_response(task_id)
        
        # List endpoints
        if "/list/" in url and url.endswith("/task"):
            if method == "POST":
                task_name = data.get("name", "New Task") if data else "New Task"
                return self.api.get_create_task_response(task_name)
        
        # V3 API endpoints
        if self.v3_base_url in url:
            if "/docs" in url:
                return {"docs": []}
            elif "/chat/channels" in url:
                return {"channels": []}
        
        # Default response for unknown endpoints
        return {"message": f"Mock response for {url}"}
    
    def setup_mock_responses(self, mock_web):
        """Set up mock responses for common API endpoints."""
        
        # User endpoint
        mock_web.set_response(
            f"{self.base_url}/user",
            self.api.get_user_response()
        )
        
        # Teams endpoint
        mock_web.set_response(
            f"{self.base_url}/team",
            self.api.get_teams_response()
        )
        
        # Spaces endpoint
        mock_web.set_response(
            f"{self.base_url}/team/333/space",
            self.api.get_spaces_response()
        )
        
        # Lists endpoint
        mock_web.set_response(
            f"{self.base_url}/team/333/list",
            self.api.get_lists_response()
        )
        
        # Tasks endpoint
        mock_web.set_response(
            f"{self.base_url}/team/333/task",
            self.api.get_tasks_response()
        )
        
        # Tags endpoint
        mock_web.set_response(
            f"{self.base_url}/space/90170402244889/tag",
            self.api.get_tags_response()
        )
        
        # Create task endpoint
        mock_web.set_response(
            f"{self.base_url}/list/90170402244889/task",
            self.api.get_create_task_response()
        )
        
        # Update task endpoint
        mock_web.set_response(
            f"{self.base_url}/task/8xdfdjbgd",
            self.api.get_update_task_response()
        )
        
        # Set a default response for any other endpoints
        mock_web.set_default_response({"message": "Default mock response"})