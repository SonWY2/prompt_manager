"""
API Client for PyQt GUI Application
"""

import requests
import json
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin


class APIClient:
    """HTTP client for backend API communication"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, 
                     timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Make HTTP request to API"""
        try:
            url = urljoin(self.base_url, endpoint)
            
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=timeout)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=timeout)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, json=data, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            
            # Return JSON if content exists
            if response.content:
                return response.json()
            else:
                return {'success': True}
                
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to backend server")
        except requests.exceptions.Timeout:
            raise Exception("Request timed out")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception("API endpoint not found")
            elif e.response.status_code == 500:
                raise Exception("Internal server error")
            else:
                try:
                    error_data = e.response.json()
                    raise Exception(error_data.get('error', str(e)))
                except:
                    raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from server")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
            
    def get(self, endpoint: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Make GET request"""
        return self._make_request('GET', endpoint, timeout=timeout)
        
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, 
            timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Make POST request"""
        return self._make_request('POST', endpoint, data, timeout=timeout)
        
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
           timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Make PUT request"""
        return self._make_request('PUT', endpoint, data, timeout=timeout)
        
    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
             timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Make PATCH request"""
        return self._make_request('PATCH', endpoint, data, timeout=timeout)
        
    def delete(self, endpoint: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Make DELETE request"""
        return self._make_request('DELETE', endpoint, timeout=timeout)
        
    def check_connection(self) -> bool:
        """Check if backend server is accessible"""
        try:
            response = self.get('/api/tasks', timeout=5)
            return response is not None
        except:
            return False
            
    # Task API methods
    def get_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks"""
        response = self.get('/api/tasks')
        return response.get('tasks', []) if response else []
        
    def create_task(self, task_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Create a new task"""
        data = {'taskId': task_id, 'name': name}
        response = self.post('/api/tasks', data)
        return response.get('task') if response else None
        
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task"""
        response = self.patch(f'/api/tasks/{task_id}', updates)
        return response.get('task') if response else None
        
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        try:
            self.delete(f'/api/tasks/{task_id}')
            return True
        except:
            return False
            
    # Version API methods
    def get_versions(self, task_id: str) -> List[Dict[str, Any]]:
        """Get versions for a task"""
        response = self.get(f'/api/tasks/{task_id}/versions')
        return response.get('versions', []) if response else []
        
    def create_version(self, task_id: str, version_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new version"""
        response = self.post(f'/api/tasks/{task_id}/versions', version_data)
        return response.get('version') if response else None
        
    def update_version(self, task_id: str, version_id: str, 
                      updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a version"""
        response = self.put(f'/api/tasks/{task_id}/versions/{version_id}', updates)
        return response.get('version') if response else None
        
    def delete_version(self, task_id: str, version_id: str) -> bool:
        """Delete a version"""
        try:
            self.delete(f'/api/tasks/{task_id}/versions/{version_id}')
            return True
        except:
            return False
            
    # Variables API methods  
    def get_variables(self, task_id: str) -> Dict[str, Any]:
        """Get task variables (actual variable values, not just extracted names)"""
        try:
            # Use the correct endpoint that returns variable values as dict
            response = self.get(f'/api/tasks/{task_id}/variables')
            if response and 'variables' in response:
                variables = response['variables']
                # Ensure variables is a dictionary
                if isinstance(variables, dict):
                    return variables
                else:
                    print(f"Warning: API returned non-dict variables: {type(variables)}")
                    return {}
            return {}
        except Exception as e:
            print(f"Error getting variables: {e}")
            return {}
        
    def update_variables(self, task_id: str, variables: Dict[str, Any]) -> bool:
        """Update template variables for a task"""
        try:
            self.put(f'/api/tasks/{task_id}/variables', {'variables': variables})
            return True
        except:
            return False
            
    # LLM API methods
    def get_llm_endpoints(self) -> Dict[str, Any]:
        """Get LLM endpoints configuration"""
        response = self.get('/api/llm-endpoints')
        return {
            'endpoints': response.get('endpoints', []),
            'activeEndpointId': response.get('activeEndpointId'),
            'defaultEndpointId': response.get('defaultEndpointId')
        } if response else {'endpoints': [], 'activeEndpointId': None, 'defaultEndpointId': None}
        
    def add_llm_endpoint(self, endpoint_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a new LLM endpoint"""
        response = self.post('/api/llm-endpoints', endpoint_data)
        return response.get('endpoint') if response else None
        
    def update_llm_endpoint(self, endpoint_id: str, 
                           updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an LLM endpoint"""
        response = self.put(f'/api/llm-endpoints/{endpoint_id}', updates)
        return response.get('endpoint') if response else None
        
    def delete_llm_endpoint(self, endpoint_id: str) -> bool:
        """Delete an LLM endpoint"""
        try:
            self.delete(f'/api/llm-endpoints/{endpoint_id}')
            return True
        except:
            return False
            
    def set_active_endpoint(self, endpoint_id: str) -> bool:
        """Set active LLM endpoint"""
        try:
            self.put(f'/api/llm-endpoints/{endpoint_id}/activate')
            return True
        except:
            return False
            
    def set_default_endpoint(self, endpoint_id: str) -> bool:
        """Set default LLM endpoint"""
        try:
            self.put(f'/api/llm-endpoints/{endpoint_id}/set-default')
            return True
        except:
            return False
            
    def call_llm(self, task_id: str, version_id: str, input_data: Dict[str, Any],
                system_prompt: str, endpoint: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Call LLM API"""
        data = {
            'taskId': task_id,
            'versionId': version_id,
            'inputData': input_data,
            'system_prompt': system_prompt
        }
        if endpoint:
            data['endpoint'] = endpoint
            
        response = self.post('/api/llm/call', data)
        return response.get('result') if response else None
        
    def test_llm_models(self, base_url: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Test LLM models endpoint"""
        data = {'baseUrl': base_url, 'apiKey': api_key}
        return self.post('/api/test-endpoint/models', data)
        
    def test_llm_chat(self, base_url: str, api_key: str, model: str, 
                     message: str) -> Optional[Dict[str, Any]]:
        """Test LLM chat endpoint"""
        data = {
            'baseUrl': base_url,
            'apiKey': api_key,
            'model': model,
            'message': message
        }
        return self.post('/api/test-endpoint/chat', data)
