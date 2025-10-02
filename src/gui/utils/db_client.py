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
        """Format result data for frontend compatibility with improved endpoint mapping"""
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
        
        # Try to parse full endpoint info from endpoint_info field first
        endpoint_info = {}
        if result.get('endpoint_info'):
            try:
                endpoint_info = json.loads(result['endpoint_info'])
            except json.JSONDecodeError:
                endpoint_info = {}
        
        # Build comprehensive endpoint data
        endpoint = {}
        if endpoint_info:
            # Use full endpoint info if available
            endpoint = endpoint_info.copy()
        else:
            # Fallback to individual fields for backward compatibility
            endpoint = {
                'name': result.get('provider_name') or result.get('model', 'Unknown'),
                'defaultModel': result.get('model_name') or result.get('model', ''),
                'baseUrl': result.get('provider', ''),
                'provider': result.get('provider_name', 'Unknown')
            }
        
        return {
            'inputData': input_data,
            'output': output,
            'timestamp': result.get('timestamp', ''),
            'endpoint': endpoint,
            'temperature': result.get('temperature', 0.7),  # Include temperature from database
            'userPromptTemplate': result.get('userPromptTemplate'),  # Already converted to camelCase in database.py
            'systemPromptTemplate': result.get('systemPromptTemplate')  # Already converted to camelCase in database.py
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
            # Use database's update_task method which supports all fields including name
            success = self.db.update_task(task_id, **updates)
            if not success:
                return None
                
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
            
            # Get active endpoint ID from settings
            active_endpoint_id = self.db.get_active_endpoint_id()
            
            # Get default endpoint ID
            default_endpoint_id = self.db.get_default_endpoint_id()
            
            # If no active endpoint is set, use default as fallback
            if not active_endpoint_id and default_endpoint_id:
                active_endpoint_id = default_endpoint_id
                # Set it as active for future use
                self.db.set_active_endpoint_id(default_endpoint_id)
            
            return {
                'endpoints': endpoints,  # No need to format again, database already does it
                'activeEndpointId': active_endpoint_id,
                'defaultEndpointId': default_endpoint_id
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
        """Set active LLM endpoint"""
        try:
            return self.db.set_active_endpoint_id(endpoint_id)
        except Exception as e:
            print(f"Error setting active endpoint: {e}")
            return False
            
    def set_default_endpoint(self, endpoint_id: str) -> bool:
        """Set default LLM endpoint"""
        try:
            # First, unset all other defaults
            endpoints = self.db.get_all_llm_endpoints()
            for ep in endpoints:
                if ep['id'] != endpoint_id and ep.get('isDefault', False):  # Use camelCase key
                    self.db.update_llm_endpoint(ep['id'], is_default=False)
            
            # Set the new default
            return self.db.update_llm_endpoint(endpoint_id, is_default=True)
        except Exception as e:
            print(f"Error setting default endpoint: {e}")
            return False
            
    def call_llm(self, task_id: str, version_id: str, input_data: Dict[str, Any],
                system_prompt: str, endpoint: Optional[Dict[str, Any]] = None, 
                temperature: float = 0.7) -> Optional[Dict[str, Any]]:
        """Call LLM API with the given prompt and variables"""
        try:
            if not endpoint:
                raise Exception("No LLM endpoint provided")
                
            # Get version content for prompt template
            version = self.db.get_version_by_id(version_id)
            if not version:
                raise Exception(f"Version {version_id} not found")
                
            user_prompt_template = version.get('content', '')
            
            # Render prompt template with variables
            user_prompt = self._render_prompt_template(user_prompt_template, input_data)
            system_prompt_rendered = self._render_prompt_template(system_prompt, input_data)
            
            # Prepare API request
            base_url = endpoint.get('baseUrl', '').rstrip('/')
            api_key = endpoint.get('apiKey', '')
            model = endpoint.get('defaultModel', 'gpt-3.5-turbo')
            
            if not base_url or not api_key:
                raise Exception("Missing endpoint URL or API key")
                
            # Make API call
            chat_url = f"{base_url}/chat/completions"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': model,
                'messages': [
                    {
                        'role': 'system',
                        'content': system_prompt_rendered
                    },
                    {
                        'role': 'user', 
                        'content': user_prompt
                    }
                ],
                'temperature': temperature
            }
            
            response = requests.post(
                chat_url,
                headers=headers,
                json=payload,
                timeout=120,  # 2 minute timeout
                verify=True
            )
            
            if response.status_code != 200:
                raise Exception(f"API call failed: HTTP {response.status_code} - {response.text}")
                
            result_data = response.json()
            
            # Save result to database with complete endpoint info and temperature
            # Create complete endpoint info including all necessary fields
            complete_endpoint_info = endpoint.copy()  # Start with full endpoint data
            complete_endpoint_info.update({
                'model': model,  # Ensure model field is present
                'modelName': model,  # Alternative model field name
                'defaultModel': model,  # Consistent with UI expectations
                'provider': endpoint.get('name', 'Unknown'),
                'usedModel': model,  # Track actually used model
                'temperature': temperature  # Include temperature in endpoint info
            })
            
            # Save with enhanced information including prompt templates used at execution time
            self.db.add_result(
                version_id=version_id,
                input_data=input_data,
                output=result_data,
                endpoint_info=complete_endpoint_info,
                temperature=temperature,
                user_prompt_template=user_prompt,  # 실행 시점의 렌더링된 최종 user prompt
                system_prompt_template=system_prompt_rendered  # 실행 시점의 렌더링된 최종 system prompt
            )
            
            return result_data
            
        except requests.exceptions.Timeout:
            raise Exception("Request timed out after 2 minutes")
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to LLM endpoint")
        except requests.exceptions.SSLError:
            raise Exception("SSL certificate verification failed")
        except Exception as e:
            print(f"Error in call_llm: {e}")
            raise e
            
    def _render_prompt_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render prompt template with variables"""
        if not template:
            return ""
            
        result = template
        for key, value in variables.items():
            # Replace {{variable}} patterns
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
            
        return result
        
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
