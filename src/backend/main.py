import os
import json
import datetime
import re
import aiohttp
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid

from database import PromptManagerDB

# --- Configuration ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')

# --- FastAPI App Initialization ---
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Initialization ---
db = PromptManagerDB()

# 기존 TinyDB 데이터가 있다면 마이그레이션
legacy_db_path = os.path.join(DATA_DIR, 'db.json')
if os.path.exists(legacy_db_path) and os.path.getsize(legacy_db_path) > 0:
    try:
        print("🔄 기존 TinyDB 데이터 발견, SQLite로 마이그레이션 시도...")
        if db.migrate_from_tinydb(legacy_db_path):
            # 마이그레이션 성공 시 기존 파일 백업
            backup_path = os.path.join(DATA_DIR, f'db_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            os.rename(legacy_db_path, backup_path)
            print(f"Migration completed, existing data backed up to {backup_path}")
        else:
            print("Migration failed, manual data verification required")
    except Exception as e:
        print(f"Migration error: {e}")

# --- Pydantic Models ---
class TaskCreate(BaseModel):
    taskId: str
    name: str

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    isFavorite: Optional[bool] = None
    variables: Optional[Dict[str, Any]] = None

class VersionCreate(BaseModel):
    versionId: str
    content: str
    description: Optional[str] = None
    name: str
    system_prompt: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None

class VersionUpdate(BaseModel):
    content: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None

class LLMCall(BaseModel):
    taskId: str
    versionId: str
    inputData: Dict[str, str]
    system_prompt: Optional[str] = None
    endpoint: Optional[Dict[str, Any]] = None

class LLMEndpoint(BaseModel):
    id: str = Field(default_factory=lambda: f"llm-ep-{uuid.uuid4()}")
    name: str
    baseUrl: str
    apiKey: Optional[str] = None
    defaultModel: Optional[str] = None
    description: Optional[str] = None
    contextSize: Optional[int] = None
    isDefault: bool = False
    createdAt: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())

class LLMEndpointUpdate(BaseModel):
    name: Optional[str] = None
    baseUrl: Optional[str] = None
    apiKey: Optional[str] = None
    defaultModel: Optional[str] = None
    description: Optional[str] = None
    contextSize: Optional[int] = None

class TestEndpointModelsRequest(BaseModel):
    baseUrl: str
    apiKey: Optional[str] = None

class TestEndpointChatRequest(BaseModel):
    baseUrl: str
    apiKey: Optional[str] = None
    model: str
    message: str

# --- Helper Functions ---
def render_template(template: str, data: dict) -> str:
    rendered = template
    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"
        rendered = rendered.replace(placeholder, str(value))
    return rendered

def get_settings():
    """Get settings with error handling"""
    try:
        settings = db.get_all_settings()
        if not settings:
            # Default settings
            default_settings = {'activeEndpointId': None, 'defaultEndpointId': None}
            for key, value in default_settings.items():
                db.set_setting(key, str(value) if value else "")
            return default_settings
        
        # Convert string values back to appropriate types
        processed_settings = {}
        for key, value in settings.items():
            if value == "" or value == "None":
                processed_settings[key] = None
            else:
                processed_settings[key] = value
        
        return processed_settings
    except Exception as e:
        print(f"Settings error: {e}")
        return {'activeEndpointId': None, 'defaultEndpointId': None}

# --- API Routes ---

# Health Check
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "database": "sqlite"}

# === Tasks ===
@app.get("/api/tasks")
def get_tasks():
    """Get all tasks with error handling"""
    try:
        tasks_list = db.get_all_tasks()
        return {"tasks": tasks_list}
    except Exception as e:
        print(f"Error getting tasks: {e}")
        return {"tasks": []}

@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    try:
        new_task = db.create_task(task.taskId, task.name)
        return {"success": True, "task": new_task}
    except Exception as e:
        print(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@app.patch("/api/tasks/{task_id}")
def update_task(task_id: str, updates: TaskUpdate):
    try:
        success = db.update_task(task_id, **updates.dict(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task")

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    try:
        success = db.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"success": True, "message": f"Task {task_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")

# === Versions ===
@app.get("/api/tasks/{task_id}/versions")
def get_task_versions(task_id: str):
    try:
        versions = db.get_task_versions(task_id)
        return {"versions": versions}
    except Exception as e:
        print(f"Error getting versions: {e}")
        return {"versions": []}

@app.get("/api/tasks/{task_id}/versions/{version_id}")
def get_version(task_id: str, version_id: str):
    try:
        version = db.get_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        return version
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting version: {e}")
        raise HTTPException(status_code=500, detail="Failed to get version")

@app.post("/api/tasks/{task_id}/versions", status_code=201)
def create_version(task_id: str, version: VersionCreate):
    try:
        new_version = db.create_version(
            version_id=version.versionId,
            task_id=task_id,
            name=version.name,
            content=version.content,
            system_prompt=version.system_prompt or "You are a helpful AI Assistant",
            description=version.description or "",
            variables=version.variables
        )
        return {"success": True, "version": new_version}
    except Exception as e:
        print(f"Error creating version: {e}")
        raise HTTPException(status_code=500, detail="Failed to create version")

@app.put("/api/tasks/{task_id}/versions/{version_id}")
def update_version(task_id: str, version_id: str, updates: VersionUpdate):
    try:
        success = db.update_version(version_id, **updates.dict(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating version: {e}")
        raise HTTPException(status_code=500, detail="Failed to update version")

@app.delete("/api/tasks/{task_id}/versions/{version_id}")
def delete_version(task_id: str, version_id: str):
    try:
        success = db.delete_version(version_id)
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")
        return {"success": True, "message": f"Version {version_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting version: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete version")

@app.delete("/api/tasks/{task_id}/versions/{version_id}/results/{timestamp}")
def delete_history_item(task_id: str, version_id: str, timestamp: str):
    try:
        success = db.delete_result(version_id, timestamp)
        if not success:
            raise HTTPException(status_code=404, detail="History item not found")
        return {"success": True, "message": "History item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting history item: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete history item")

# Task Variables Management
@app.get("/api/tasks/{task_id}/variables")
def get_task_variables(task_id: str):
    try:
        task = db.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        variables = task.get("variables", {})
        return {"variables": variables}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting task variables: {e}")
        return {"variables": {}}

@app.put("/api/tasks/{task_id}/variables")
def update_task_variables(task_id: str, request_data: Dict[str, Any]):
    try:
        # Extract variables from request
        if 'variables' in request_data:
            variables = request_data['variables']
        else:
            variables = request_data
        
        success = db.update_task(task_id, variables=variables)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"success": True, "variables": variables}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating task variables: {e}")
        raise HTTPException(status_code=500, detail="Failed to update variables")

# Template Variable Management
@app.get("/api/templates/{task_id}/variables")
def get_template_variables(task_id: str):
    try:
        task = db.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        variables = set()
        for version in task.get("versions", []):
            content = version.get("content", "")
            matches = [m[2:-2].strip() for m in re.findall(r"{{.*?}}", content)]
            variables.update(matches)

        return {"variables": list(variables)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting template variables: {e}")
        return {"variables": []}

# LLM API Integration
@app.post("/api/llm/call")
async def call_llm_endpoint(call: LLMCall):
    try:
        task = db.get_task_by_id(call.taskId)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        version = db.get_version_by_id(call.versionId)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        # Get active endpoint
        settings = get_settings()
        active_endpoint_id = settings.get('activeEndpointId')
        
        if not active_endpoint_id:
            raise HTTPException(status_code=400, detail="No active LLM endpoint configured")
        
        active_endpoint = db.get_llm_endpoint_by_id(active_endpoint_id)
        if not active_endpoint:
            raise HTTPException(status_code=404, detail="Active LLM endpoint not found")

        # Template rendering
        rendered_prompt = render_template(version["content"], call.inputData)
        system_prompt = call.system_prompt or version.get("system_prompt", "You are a helpful assistant.")
        
        # Call actual LLM API
        try:
            # DB에서 조회한 endpoint는 이미 camelCase로 변환되어 있으므로
            # snake_case로 다시 변환해서 call_actual_llm_api에 전달
            endpoint_for_api = {
                'base_url': active_endpoint.get('baseUrl'),
                'api_key': active_endpoint.get('apiKey'), 
                'default_model': active_endpoint.get('defaultModel')
            }
            
            result = await call_actual_llm_api(
                endpoint=endpoint_for_api,
                system_prompt=system_prompt,
                user_prompt=rendered_prompt,
                model=active_endpoint.get('defaultModel')
            )
        except Exception as e:
            # LLM API call failed - return error response
            result = {
                "id": "error-response",
                "object": "chat.completion",
                "created": int(datetime.datetime.now().timestamp()),
                "model": active_endpoint.get('default_model', 'unknown'),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Error calling LLM API: {str(e)}\n\nRendered prompt was: {rendered_prompt}"
                    },
                    "finish_reason": "error"
                }],
                "error": str(e)
            }

        # Save result
        endpoint_info = {
            "id": active_endpoint['id'],
            "name": active_endpoint['name'],
            "model": active_endpoint.get('default_model')
        }
        
        db.add_result(
            version_id=call.versionId,
            input_data=call.inputData,
            output=result,
            endpoint_info=endpoint_info
        )

        return {"result": result}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in LLM call: {e}")
        raise HTTPException(status_code=500, detail="Failed to call LLM API")

# Actual LLM API call function
async def call_actual_llm_api(endpoint: dict, system_prompt: str, user_prompt: str, model: str = None):
    """실제 LLM API 호출"""
    
    base_url = endpoint.get('base_url', '').rstrip('/')
    api_key = endpoint.get('api_key')
    model = model or endpoint.get('default_model', 'gpt-3.5-turbo')
    
    if not base_url:
        raise Exception("Base URL is required")
    
    # API 요청 구성
    headers = {
        'Content-Type': 'application/json'
    }
    
    if api_key:
        if 'openai.com' in base_url or 'api.together.xyz' in base_url:
            headers['Authorization'] = f'Bearer {api_key}'
        elif 'openrouter.ai' in base_url:
            headers['Authorization'] = f'Bearer {api_key}'
            headers['HTTP-Referer'] = 'https://prompt-manager.local'
            headers['X-Title'] = 'Prompt Manager'
        elif 'anthropic.com' in base_url:
            headers['x-api-key'] = api_key
            headers['anthropic-version'] = '2023-06-01'
        else:
            # 기본적으로 Bearer 토큰 사용
            headers['Authorization'] = f'Bearer {api_key}'
    
    # Anthropic Claude API
    if 'anthropic.com' in base_url:
        combined_content = f"{system_prompt}\n\n{user_prompt}"
        data = {
            'model': model,
            'max_tokens': 4000,
            'messages': [
                {
                    'role': 'user',
                    'content': combined_content
                }
            ]
        }
        url = f"{base_url}/messages"
    else:
        # OpenAI 호환 API (OpenAI, Together, vLLM, Ollama 등)
        messages = []
        
        # System prompt가 비어있지 않은 경우에만 추가
        if system_prompt and system_prompt.strip():
            messages.append({'role': 'system', 'content': system_prompt.strip()})
        
        # User prompt는 필수이므로 확인 후 추가
        if user_prompt and user_prompt.strip():
            messages.append({'role': 'user', 'content': user_prompt.strip()})
        else:
            raise Exception("User prompt cannot be empty")
        
        data = {
            'model': model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 4000
        }
        url = f"{base_url}/chat/completions"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url, 
                headers=headers, 
                json=data,
                timeout=aiohttp.ClientTimeout(total=60)  # 60초 타임아웃
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API returned {response.status}: {error_text}")
                
                response_data = await response.json()
                
                # Anthropic 응답을 OpenAI 형식으로 변환
                if 'anthropic.com' in base_url:
                    return {
                        "id": response_data.get('id', 'claude-response'),
                        "object": "chat.completion",
                        "created": int(datetime.datetime.now().timestamp()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response_data.get('content', [{}])[0].get('text', '')
                            },
                            "finish_reason": response_data.get('stop_reason', 'stop')
                        }],
                        "usage": {
                            "prompt_tokens": response_data.get('usage', {}).get('input_tokens', 0),
                            "completion_tokens": response_data.get('usage', {}).get('output_tokens', 0),
                            "total_tokens": response_data.get('usage', {}).get('input_tokens', 0) + response_data.get('usage', {}).get('output_tokens', 0)
                        }
                    }
                
                return response_data
                
        except aiohttp.ClientTimeout:
            raise Exception("Request timeout")
        except Exception as e:
            raise Exception(f"Network error: {str(e)}")

# === LLM Endpoints ===
@app.get("/api/llm-endpoints")
def get_llm_endpoints():
    try:
        endpoints = db.get_all_llm_endpoints()
        settings = get_settings()
        
        return {
            "endpoints": endpoints,
            "activeEndpointId": settings.get('activeEndpointId'),
            "defaultEndpointId": settings.get('defaultEndpointId')
        }
    except Exception as e:
        print(f"Error getting LLM endpoints: {e}")
        return {"endpoints": [], "activeEndpointId": None, "defaultEndpointId": None}

@app.post("/api/llm-endpoints", status_code=201)
def create_llm_endpoint(endpoint: LLMEndpoint):
    try:
        endpoint_data = endpoint.dict()
        
        # If this is the very first endpoint, make it the default and active one
        existing_endpoints = db.get_all_llm_endpoints()
        if not existing_endpoints:
            endpoint_data["isDefault"] = True
            db.set_setting('activeEndpointId', endpoint_data['id'])
            db.set_setting('defaultEndpointId', endpoint_data['id'])

        new_endpoint = db.create_llm_endpoint(endpoint_data)
        return {"success": True, "endpoint": new_endpoint}
    except Exception as e:
        print(f"Error creating LLM endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to create LLM endpoint")

@app.put("/api/llm-endpoints/{endpoint_id}")
def update_llm_endpoint(endpoint_id: str, updates: LLMEndpointUpdate):
    try:
        update_data = updates.dict(exclude_unset=True)
        success = db.update_llm_endpoint(endpoint_id, **update_data)
        if not success:
            raise HTTPException(status_code=404, detail="LLM endpoint not found")
        
        updated_endpoint = db.get_llm_endpoint_by_id(endpoint_id)
        return {"success": True, "endpoint": updated_endpoint}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating LLM endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to update LLM endpoint")

@app.delete("/api/llm-endpoints/{endpoint_id}")
def delete_llm_endpoint(endpoint_id: str):
    try:
        success = db.delete_llm_endpoint(endpoint_id)
        if not success:
            raise HTTPException(status_code=404, detail="LLM endpoint not found")
        
        return {"success": True, "message": f"LLM endpoint {endpoint_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting LLM endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete LLM endpoint")

@app.put("/api/llm-endpoints/{endpoint_id}/activate")
def activate_llm_endpoint(endpoint_id: str):
    try:
        endpoint = db.get_llm_endpoint_by_id(endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=404, detail="LLM endpoint not found")
        
        db.set_setting('activeEndpointId', endpoint_id)
        return {"success": True, "message": f"LLM endpoint {endpoint_id} activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error activating LLM endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate LLM endpoint")

@app.put("/api/llm-endpoints/{endpoint_id}/set-default")
def set_default_llm_endpoint(endpoint_id: str):
    try:
        endpoint = db.get_llm_endpoint_by_id(endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=404, detail="LLM endpoint not found")
        
        db.set_setting('defaultEndpointId', endpoint_id)
        return {"success": True, "message": f"LLM endpoint {endpoint_id} set as default successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error setting default LLM endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to set default LLM endpoint")

# === Test Endpoints ===
@app.post("/api/test-endpoint/models")
async def test_models_endpoint(request: TestEndpointModelsRequest):
    """Test the /v1/models endpoint of an LLM provider"""
    try:
        base_url = request.baseUrl.rstrip('/')
        api_key = request.apiKey
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add API key to headers if provided
        if api_key:
            if 'openai.com' in base_url or 'api.together.xyz' in base_url:
                headers['Authorization'] = f'Bearer {api_key}'
            elif 'openrouter.ai' in base_url:
                headers['Authorization'] = f'Bearer {api_key}'
                headers['HTTP-Referer'] = 'https://prompt-manager.local'
                headers['X-Title'] = 'Prompt Manager'
            elif 'anthropic.com' in base_url:
                headers['x-api-key'] = api_key
                headers['anthropic-version'] = '2023-06-01'
            else:
                headers['Authorization'] = f'Bearer {api_key}'
        
        url = f"{base_url}/models"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status, 
                        detail=f"API returned {response.status}: {error_text}"
                    )
                
                response_data = await response.json()
                return response_data
                
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@app.post("/api/test-endpoint/chat")
async def test_chat_endpoint(request: TestEndpointChatRequest):
    """Test the /v1/chat/completions endpoint of an LLM provider"""
    try:
        base_url = request.baseUrl.rstrip('/')
        api_key = request.apiKey
        model = request.model
        message = request.message
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add API key to headers if provided
        if api_key:
            if 'openai.com' in base_url or 'api.together.xyz' in base_url:
                headers['Authorization'] = f'Bearer {api_key}'
            elif 'openrouter.ai' in base_url:
                headers['Authorization'] = f'Bearer {api_key}'
                headers['HTTP-Referer'] = 'https://prompt-manager.local'
                headers['X-Title'] = 'Prompt Manager'
            elif 'anthropic.com' in base_url:
                headers['x-api-key'] = api_key
                headers['anthropic-version'] = '2023-06-01'
            else:
                headers['Authorization'] = f'Bearer {api_key}'
        
        # Prepare request data based on provider
        if 'anthropic.com' in base_url:
            # Anthropic Claude API format
            data = {
                'model': model,
                'max_tokens': 100,
                'messages': [
                    {
                        'role': 'user',
                        'content': message
                    }
                ]
            }
            url = f"{base_url}/messages"
        else:
            # OpenAI compatible format (올바른 ChatML 형태)
            data = {
                'model': model,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant. Please provide a brief response for testing purposes.'
                    },
                    {
                        'role': 'user',
                        'content': message
                    }
                ],
                'max_tokens': 100,
                'temperature': 0.7
            }
            url = f"{base_url}/chat/completions"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status, 
                        detail=f"API returned {response.status}: {error_text}"
                    )
                
                response_data = await response.json()
                
                # Convert Anthropic response to OpenAI format for consistency
                if 'anthropic.com' in base_url:
                    converted_response = {
                        "id": response_data.get('id', 'claude-test'),
                        "object": "chat.completion",
                        "created": int(datetime.datetime.now().timestamp()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response_data.get('content', [{}])[0].get('text', 'No response')
                            },
                            "finish_reason": response_data.get('stop_reason', 'stop')
                        }],
                        "usage": {
                            "prompt_tokens": response_data.get('usage', {}).get('input_tokens', 0),
                            "completion_tokens": response_data.get('usage', {}).get('output_tokens', 0),
                            "total_tokens": response_data.get('usage', {}).get('input_tokens', 0) + response_data.get('usage', {}).get('output_tokens', 0)
                        }
                    }
                    return converted_response
                
                return response_data
                
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

# === Main ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)