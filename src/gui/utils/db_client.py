"""
Direct SQLite Database Client for PyQt GUI Application
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import uuid
from datetime import datetime
import requests
from urllib.parse import urljoin

# Add backend path to import database module
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database import PromptManagerDB


class DatabaseClient:
    """Direct SQLite database client for GUI application"""
    
    def __init__(self, db_path: str = None):
        """Initialize database client"""
        if db_path is None:
            # Use the same database path as backend
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / "src" / "backend" / "data" / "prompt_manager.db"
        
        self.db = PromptManagerDB(str(db_path))
        
    def check_connection(self) -> bool:
        """Check if database connection is working"""
        try:
            # Simple test query
            tasks = self.db.get_all_tasks()
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
            
    # Task API methods
    def get_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks"""
        try:
            tasks = self.db.get_all_tasks()
            return [self._format_task(task) for task in tasks]
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []
    
    def _format_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Format task data for frontend compatibility"""
        if not task:
            return task
            
        # Ensure variables is a dictionary
        variables = task.get('variables', '{}')
        if isinstance(variables, str):
            try:
                variables = json.loads(variables)
            except json.JSONDecodeError:
                variables = {}
        
        # Get versions for this task
        versions = self.db.get_task_versions(task['id'])
        formatted_versions = [self._format_version(v) for v in versions]
        
        return {
            'id': task['id'],
            'name': task['name'],
            'isFavorite': bool(task.get('is_favorite', False)),
            'variables': variables,
            'versions': formatted_versions,
            'createdAt': task.get('created_at', ''),
            'updatedAt': task.get('updated_at', '')
        }
    
    def _format_version(self, version: Dict[str, Any]) -> Dict[str, Any]:
        """Format version data for frontend compatibility"""
        if not version:
            return version
            
        # Get results for this version
        results = self.db.get_version_results(version['id'])
        formatted_results = [self._format_result(r) for r in results]
        
        return {
            'id': version['id'],
            'task_id': version['task_id'],
            'name': version['name'],
            'content': version.get('content', ''),
            'system_prompt': version.get('system_prompt', 'You are a helpful AI Assistant'),
            'description': version.get('description', ''),
            'results': formatted_results,
            'createdAt': version.get('created_at', ''),
            'updatedAt': version.get('updated_at', '')
        }
    
    def _format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format result data for frontend compatibility"""
        if not result:
            return result
            
        # Parse JSON fields
        input_data = result.get('input_data', '{}')
        if isinstance(input_data, str):
            try:
                input_data = json.loads(input_data)
            except json.JSONDecodeError:
                input_data = {}
                
        output = result.get('output', '{}')
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except json.JSONDecodeError:
                output = {}
        
        return {
            'inputData': input_data,
            'output': output,
            'timestamp': result.get('timestamp', ''),
            'endpoint': {
                'name': result.get('model', 'Unknown'),
                'defaultModel': result.get('model', ''),
                'baseUrl': result.get('provider', '')
            }
        }
        
    def create_task(self, task_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Create a new task"""
        try:
            # create_task returns the created task directly
            task = self.db.create_task(task_id, name)
            if task:
                return self._format_task(task)
            return None
        except Exception as e:
            print(f"Error creating task: {e}")
            return None
        
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task"""
        try:
            # Handle favorite status
            if 'isFavorite' in updates:
                success = self.db.update_task(task_id, is_favorite=updates['isFavorite'])
                if not success:
                    return None
                    
            # Handle other updates
            if 'name' in updates:
                # Task name updates would need to be added to database.py
                pass
                
            task = self.db.get_task_by_id(task_id)
            return self._format_task(task) if task else None
        except Exception as e:
            print(f"Error updating task: {e}")
            return None
        
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        try:
            return self.db.delete_task(task_id)
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False
            
    # Version API methods
    def get_versions(self, task_id: str) -> List[Dict[str, Any]]:
        """Get versions for a task"""
        try:
            versions = self.db.get_task_versions(task_id)
            return [self._format_version(v) for v in versions]
        except Exception as e:
            print(f"Error getting versions: {e}")
            return []
        
    def create_version(self, task_id: str, version_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new version"""
        try:
            version_id = version_data.get('versionId', f'v{int(datetime.now().timestamp() * 1000)}')
            # create_version returns the created version directly
            version = self.db.create_version(
                version_id=version_id,
                task_id=task_id,
                name=version_data.get('name', ''),
                content=version_data.get('content', ''),
                system_prompt=version_data.get('system_prompt', 'You are a helpful AI Assistant'),
                description=version_data.get('description', '')
            )
            
            if version:
                return self._format_version(version)
            return None
        except Exception as e:
            print(f"Error creating version: {e}")
            return None
        
    def update_version(self, version_id: str, **updates) -> bool:
        """Update a version"""
        try:
            # Filter out any None values and pass all updates to database
            filtered_updates = {k: v for k, v in updates.items() if v is not None}
            
            success = self.db.update_version(version_id, **filtered_updates)
            return success
        except Exception as e:
            print(f"Error updating version: {e}")
            return False
        
    def delete_version(self, task_id: str, version_id: str) -> bool:
        """Delete a version"""
        try:
            return self.db.delete_version(version_id)
        except Exception as e:
            print(f"Error deleting version: {e}")
            return False
            
    # Variables API methods  
    def get_variables(self, task_id: str) -> Dict[str, Any]:
        """Get task variables (actual variable values, not just extracted names)"""
        try:
            task = self.db.get_task_by_id(task_id)
            if task and 'variables' in task:
                variables = task['variables']
                if isinstance(variables, str):
                    try:
                        return json.loads(variables)
                    except json.JSONDecodeError:
                        return {}
                return variables if isinstance(variables, dict) else {}
            return {}
        except Exception as e:
            print(f"Error getting variables: {e}")
            return {}
        
    def update_variables(self, task_id: str, variables: Dict[str, Any]) -> bool:
        """Update template variables for a task"""
        try:
            return self.db.update_task(task_id, variables=variables)
        except Exception as e:
            print(f"Error updating variables: {e}")
            return False
            
    # LLM API methods
    def get_llm_endpoints(self) -> Dict[str, Any]:
        """Get LLM endpoints configuration"""
        try:
            endpoints = self.db.get_all_llm_endpoints()
            
            # Find default endpoint (database.py already formats to camelCase)
            default_endpoint = None
            active_endpoint = None
            for ep in endpoints:
                if ep.get('isDefault', False):
                    default_endpoint = ep
                    active_endpoint = ep  # Use default as active for now
                    break
            
            return {
                'endpoints': endpoints,  # No need to format again, database already does it
                'activeEndpointId': active_endpoint['id'] if active_endpoint else None,
                'defaultEndpointId': default_endpoint['id'] if default_endpoint else None
            }
        except Exception as e:
            print(f"Error getting LLM endpoints: {e}")
            return {'endpoints': [], 'activeEndpointId': None, 'defaultEndpointId': None}
    
    def _format_endpoint(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Format endpoint data for frontend compatibility"""
        return {
            'id': endpoint['id'],
            'name': endpoint['name'],
            'description': endpoint.get('description', ''),
            'baseUrl': endpoint['base_url'],
            'apiKey': endpoint.get('api_key', ''),
            'defaultModel': endpoint.get('default_model', ''),
            'contextSize': endpoint.get('context_size', 8192),
            'isDefault': bool(endpoint.get('is_default', False)),
            'createdAt': endpoint.get('created_at', ''),
            'updatedAt': endpoint.get('updated_at', '')
        }
        
    def add_llm_endpoint(self, endpoint_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a new LLM endpoint"""
        try:
            # create_llm_endpoint returns the created endpoint directly (already formatted)
            endpoint = self.db.create_llm_endpoint(endpoint_data)
            
            if endpoint:
                return endpoint  # No need to format again, database already does it
            return None
        except Exception as e:
            print(f"Error adding LLM endpoint: {e}")
            return None
        
    def update_llm_endpoint(self, endpoint_id: str, 
                           updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an LLM endpoint"""
        try:
            success = self.db.update_llm_endpoint(
                endpoint_id=endpoint_id,
                name=updates.get('name'),
                base_url=updates.get('baseUrl'),
                api_key=updates.get('apiKey'),
                default_model=updates.get('defaultModel'),
                context_size=updates.get('contextSize'),
                description=updates.get('description'),
                is_default=updates.get('isDefault')  # Fixed: add missing isDefault field
            )
            
            if success:
                endpoint = self.db.get_llm_endpoint_by_id(endpoint_id)
                return endpoint if endpoint else None  # No need to format, database already does it
            return None
        except Exception as e:
            print(f"Error updating LLM endpoint: {e}")
            return None
        
    def delete_llm_endpoint(self, endpoint_id: str) -> bool:
        """Delete an LLM endpoint"""
        try:
            return self.db.delete_llm_endpoint(endpoint_id)
        except Exception as e:
            print(f"Error deleting LLM endpoint: {e}")
            return False
            
    def set_active_endpoint(self, endpoint_id: str) -> bool:
        """Set active LLM endpoint (for now, same as default)"""
        return self.set_default_endpoint(endpoint_id)
            
    def set_default_endpoint(self, endpoint_id: str) -> bool:
        """Set default LLM endpoint"""
        try:
            # First, unset all other defaults
            endpoints = self.db.get_all_llm_endpoints()
            for ep in endpoints:
                if ep['id'] != endpoint_id and ep.get('is_default', False):
                    self.db.update_llm_endpoint(ep['id'], is_default=False)
            
            # Set the new default
            return self.db.update_llm_endpoint(endpoint_id, is_default=True)
        except Exception as e:
            print(f"Error setting default endpoint: {e}")
            return False
            
    def call_llm(self, task_id: str, version_id: str, input_data: Dict[str, Any],
                system_prompt: str, endpoint: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Call LLM API (requires implementing LLM call logic)"""
        # For now, return a mock response
        # This would need to be implemented with actual LLM API calls
        print("LLM call not implemented in direct database mode")
        return None
        
    def test_llm_models(self, base_url: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Test LLM models endpoint"""
        try:
            # Ensure base URL ends with /models
            if not base_url.endswith('/'):
                base_url += '/'
            models_url = urljoin(base_url, 'models')
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                models_url, 
                headers=headers,
                timeout=30,  # 30 second timeout
                verify=True  # Verify SSL certificates
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Format response for GUI
                models = data.get('data', [])
                model_names = [model.get('id', 'Unknown') for model in models[:10]]  # Show first 10
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'models': models,
                    'model_count': len(models),
                    'sample_models': model_names,
                    'message': f'Successfully connected! Found {len(models)} models.',
                    'raw_response': data
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'message': f'Failed to connect. Status: {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timed out after 30 seconds',
                'message': 'Connection timed out. Check your URL and internet connection.'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error',
                'message': 'Could not connect to the endpoint. Check the URL and network connection.'
            }
        except requests.exceptions.SSLError:
            return {
                'success': False,
                'error': 'SSL certificate error',
                'message': 'SSL certificate verification failed. Check if the endpoint has a valid certificate.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Unexpected error: {str(e)}'
            }
        
    def test_llm_chat(self, base_url: str, api_key: str, model: str, 
                     message: str) -> Optional[Dict[str, Any]]:
        """Test LLM chat endpoint"""
        try:
            # Ensure base URL ends with /chat/completions
            if not base_url.endswith('/'):
                base_url += '/'
            chat_url = urljoin(base_url, 'chat/completions')
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': model or 'gpt-3.5-turbo',
                'messages': [
                    {
                        'role': 'user',
                        'content': message
                    }
                ],
                'max_tokens': 100,  # Keep it short for testing
                'temperature': 0.7
            }
            
            response = requests.post(
                chat_url,
                headers=headers,
                json=payload,
                timeout=60,  # 60 second timeout for chat
                verify=True
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract response content
                choices = data.get('choices', [])
                if choices:
                    content = choices[0].get('message', {}).get('content', 'No response content')
                else:
                    content = 'No choices in response'
                
                usage = data.get('usage', {})
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'response_content': content,
                    'model_used': data.get('model', model),
                    'usage': usage,
                    'message': f'Chat test successful! Model responded.',
                    'raw_response': data
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'message': f'Chat test failed. Status: {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timed out after 60 seconds',
                'message': 'Chat request timed out. The endpoint may be slow or unresponsive.'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error',
                'message': 'Could not connect to the chat endpoint. Check the URL and network connection.'
            }
        except requests.exceptions.SSLError:
            return {
                'success': False,
                'error': 'SSL certificate error',
                'message': 'SSL certificate verification failed. Check if the endpoint has a valid certificate.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Unexpected error: {str(e)}'
            }


# For backward compatibility, provide the same interface
class APIClient(DatabaseClient):
    """Alias for DatabaseClient to maintain compatibility"""
    pass
