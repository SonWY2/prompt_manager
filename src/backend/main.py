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
from tinydb import TinyDB, Query, where

# --- Configuration ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'db.json')

# --- FastAPI App Initialization ---
app = FastAPI()

# --- CORS Middleware ---
allowed_origins = [
    "http://localhost:3030",
    "http://127.0.0.1:3030",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Initialization ---
os.makedirs(DATA_DIR, exist_ok=True)
db = TinyDB(DB_PATH, indent=2, ensure_ascii=False)
tasks_table = db.table('tasks')
llm_endpoints_table = db.table('llm_endpoints')
settings_table = db.table('settings')


# --- Pydantic Models ---
class Version(BaseModel):
    id: str
    name: str
    content: str
    system_prompt: str
    description: Optional[str] = None
    variables: Dict[str, Any] = {}
    createdAt: str
    results: List[Any] = []
    updatedAt: Optional[str] = None

class Task(BaseModel):
    id: str
    name: str
    versions: List[Version] = []

class TaskCreate(BaseModel):
    taskId: str
    name: str

# 부분 업데이트용 태스크 스키마
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

from typing import Dict, Any

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


# --- Helper Functions ---
def render_template(template: str, data: dict) -> str:
    for key, value in data.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template


def get_settings():
    settings = settings_table.get(doc_id=1)
    if not settings:
        # If settings don't exist, create them
        default_settings = {'activeEndpointId': None, 'defaultEndpointId': None}
        settings_table.insert(default_settings)
        return default_settings
    return settings

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Python Backend with TinyDB is running!"}

# 1. Task Management
@app.get("/api/tasks")
def get_tasks():
    tasks_list = tasks_table.all()
    # Ensure all tasks have the isFavorite field for frontend compatibility
    for task in tasks_list:
        if 'isFavorite' not in task:
            task['isFavorite'] = False
    return {"tasks": tasks_list}

@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    task_id = task.taskId
    if tasks_table.contains(where('id') == task_id):
        raise HTTPException(status_code=409, detail="Task already exists")

    new_task = {
        "id": task_id, 
        "name": task.name, 
        "versions": [],
        "variables": {}  # Task 레벨에서 variables 관리
    }
    tasks_table.insert(new_task)

    return {
        "success": True,
        "task": new_task
    }

@app.patch("/api/tasks/{task_id}")
def update_task(task_id: str, updates: TaskUpdate):
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = updates.dict(exclude_unset=True)
    
    task_data = dict(task)
    for key, value in update_data.items():
        task_data[key] = value

    tasks_table.update(task_data, where('id') == task_id)
    
    return {"success": True, "task": task_data}


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    if not tasks_table.contains(where('id') == task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    tasks_table.remove(where('id') == task_id)

    return {"success": True, "message": f"Task '{task_id}' deleted successfully"}

# 2. Version Control
@app.get("/api/tasks/{task_id}/versions")
def get_versions(task_id: str):
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"versions": task.get("versions", [])}

@app.get("/api/tasks/{task_id}/versions/{version_id}")
def get_version_detail(task_id: str, version_id: str):
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    version = next((v for v in task.get("versions", []) if v["id"] == version_id), None)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return {"version": version}

@app.post("/api/tasks/{task_id}/versions", status_code=201)
def create_version(task_id: str, version: VersionCreate):
    print(f"Creating version for task {task_id} with data: {version.dict()}")
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    display_name = version.name.strip() or f"Version {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

    new_version = {
        "id": version.versionId,
        "content": version.content,
        "system_prompt": version.system_prompt or "You are a helpful assistant.",
        "description": version.description,
        "name": display_name,
        "variables": version.variables or {},
        "createdAt": datetime.datetime.now().isoformat(),
        "results": []
    }

    task['versions'].insert(0, new_version)
    tasks_table.update(task, where('id') == task_id)

    return {
        "success": True,
        "version": {
            "id": version.versionId,
            "name": display_name
        }
    }

@app.put("/api/tasks/{task_id}/versions/{version_id}")
def update_version(task_id: str, version_id: str, updates: VersionUpdate):
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    version_index = next((i for i, v in enumerate(task["versions"]) if v["id"] == version_id), -1)
    if version_index == -1:
        raise HTTPException(status_code=404, detail="Version not found")

    version = task["versions"][version_index]
    update_data = updates.dict(exclude_unset=True)
    version.update(update_data)
    version["updatedAt"] = datetime.datetime.now().isoformat()

    task["versions"][version_index] = version
    tasks_table.update(task, where('id') == task_id)

    return {"success": True}

@app.delete("/api/tasks/{task_id}/versions/{version_id}")
def delete_version(task_id: str, version_id: str):
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    versions = task["versions"]
    version_index = next((i for i, v in enumerate(versions) if v["id"] == version_id), -1)

    if version_index == -1:
        raise HTTPException(status_code=404, detail="Version not found")

    deleted_version = versions.pop(version_index)
    tasks_table.update({'versions': versions}, where('id') == task_id)

    return {
        "success": True,
        "message": f"Version {version_id} deleted successfully",
        "deletedVersion": {
            "id": deleted_version["id"],
            "name": deleted_version["name"]
        }
    }

@app.delete("/api/tasks/{task_id}/versions/{version_id}/results/{timestamp}")
def delete_history_item(task_id: str, version_id: str, timestamp: str):
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    version_index = next((i for i, v in enumerate(task["versions"]) if v["id"] == version_id), -1)
    if version_index == -1:
        raise HTTPException(status_code=404, detail="Version not found")

    version = task["versions"][version_index]
    
    results = version.get("results", [])
    result_index = next((i for i, r in enumerate(results) if r["timestamp"] == timestamp), -1)

    if result_index == -1:
        raise HTTPException(status_code=404, detail="History item not found")

    results.pop(result_index)
    
    task["versions"][version_index]["results"] = results
    tasks_table.update(task, where('id') == task_id)

    return {"success": True, "message": "History item deleted successfully"}

# Task Variables Management
@app.get("/api/tasks/{task_id}/variables")
def get_task_variables(task_id: str):
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"variables": task.get("variables", {})}

@app.put("/api/tasks/{task_id}/variables")
def update_task_variables(task_id: str, variables: Dict[str, Any]):
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task["variables"] = variables
    tasks_table.update(task, where('id') == task_id)
    
    return {"success": True, "variables": variables}

# 3. Template Variable Management
@app.get("/api/templates/{task_id}/variables")
def get_template_variables(task_id: str):
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    variables = set()
    for version in task.get("versions", []):
        content = version.get("content", "")
        matches = [m[2:-2].strip() for m in re.findall(r"{{.*?}}", content)]
        variables.update(matches)

    return {"variables": list(variables)}

# 4. LLM API Integration
@app.post("/api/llm/call")
async def call_llm_endpoint(call: LLMCall):
    task = tasks_table.get(where('id') == call.taskId)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    version = next((v for v in task["versions"] if v["id"] == call.versionId), None)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # 활성화된 엔드포인트 가져오기
    settings = get_settings()
    active_endpoint_id = settings.get('activeEndpointId')
    
    if not active_endpoint_id:
        raise HTTPException(status_code=400, detail="No active LLM endpoint configured")
    
    active_endpoint = llm_endpoints_table.get(where('id') == active_endpoint_id)
    if not active_endpoint:
        raise HTTPException(status_code=404, detail="Active LLM endpoint not found")

    # 템플릿 렌더링
    rendered_prompt = render_template(version["content"], call.inputData)
    
    # 실제 LLM API 호출
    try:
        result = await call_actual_llm_api(
            endpoint=active_endpoint,
            system_prompt=call.system_prompt or version.get("system_prompt", "You are a helpful assistant."),
            user_prompt=rendered_prompt,
            model=active_endpoint.get('defaultModel')
        )
    except Exception as e:
        print(f"LLM API 호출 실패: {e}")
        # 실패시 더미 응답 반환
        result = {
            "id": "error-response",
            "object": "chat.completion",
            "created": int(datetime.datetime.now().timestamp()),
            "model": active_endpoint.get('defaultModel', 'unknown'),
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

    # 결과 저장
    if "results" not in version:
        version["results"] = []

    version["results"].insert(0, {
        "inputData": call.inputData,
        "output": result,
        "timestamp": datetime.datetime.now().isoformat(),
        "endpoint": {
            "id": active_endpoint['id'],
            "name": active_endpoint['name'],
            "model": active_endpoint.get('defaultModel')
        }
    })

    tasks_table.update(task, where('id') == call.taskId)

    return {"result": result}


# 실제 LLM API 호출 함수
async def call_actual_llm_api(endpoint: dict, system_prompt: str, user_prompt: str, model: str = None):
    """실제 LLM API 호출"""
    
    base_url = endpoint.get('baseUrl', '').rstrip('/')
    api_key = endpoint.get('apiKey')
    model = model or endpoint.get('defaultModel', 'gpt-3.5-turbo')
    
    if not base_url:
        raise Exception("Base URL is required")
    
    # API 요청 구성
    headers = {
        'Content-Type': 'application/json'
    }
    
    # API 키가 있는 경우 헤더에 추가
    if api_key:
        if 'openai.com' in base_url or 'api.together.xyz' in base_url:
            headers['Authorization'] = f'Bearer {api_key}'
        elif 'openrouter.ai' in base_url:
            headers['Authorization'] = f'Bearer {api_key}'
            # OpenRouter 권장 헤더
            headers['HTTP-Referer'] = 'https://prompt-manager.local'
            headers['X-Title'] = 'Prompt Manager'
        elif 'anthropic.com' in base_url:
            headers['x-api-key'] = api_key
            headers['anthropic-version'] = '2023-06-01'
    
    # Anthropic Claude API
    if 'anthropic.com' in base_url:
        data = {
            'model': model,
            'max_tokens': 4000,
            'messages': [
                {
                    'role': 'user',
                    'content': f"{system_prompt}\n\n{user_prompt}"
                }
            ]
        }
        url = f"{base_url}/messages"
    else:
        # OpenAI 호환 API (OpenAI, Together, vLLM, Ollama 등)
        data = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 4000
        }
        url = f"{base_url}/chat/completions"
    
    print(f"🚀 LLM API 호출: {url}")
    print(f"📝 Model: {model}")
    print(f"💬 Prompt length: {len(user_prompt)} chars")
    
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
                    print(f"❌ API 오류 응답: {response.status} - {error_text}")
                    raise Exception(f"API returned {response.status}: {error_text}")
                
                response_data = await response.json()
                print(f"✅ LLM API 호출 성공")
                
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
                
                return response_data
                
        except aiohttp.ClientError as e:
            print(f"❌ 연결 오류: {e}")
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            raise

# 5. LLM Endpoints Management
@app.get("/api/llm-endpoints")
def get_llm_endpoints():
    endpoints = llm_endpoints_table.all()
    settings = get_settings()
    active_id = settings.get('activeEndpointId')
    default_id = settings.get('defaultEndpointId')
    return {"endpoints": endpoints, "activeEndpointId": active_id, "defaultEndpointId": default_id}


@app.post("/api/llm-endpoints", status_code=201)
def create_llm_endpoint(endpoint: LLMEndpoint):
    new_endpoint_data = endpoint.dict()

    # If this is the very first endpoint, make it the default and active one.
    if not llm_endpoints_table.all():
        new_endpoint_data["isDefault"] = True
        settings = get_settings()
        settings_table.update({
            'activeEndpointId': new_endpoint_data['id'],
            'defaultEndpointId': new_endpoint_data['id']
        }, doc_ids=[1])

    llm_endpoints_table.insert(new_endpoint_data)
    # Re-fetch to ensure we return the data as it is in the DB
    new_endpoint = llm_endpoints_table.get(where('id') == new_endpoint_data['id'])
    return {"success": True, "endpoint": new_endpoint}


@app.put("/api/llm-endpoints/{endpoint_id}")
def update_llm_endpoint(endpoint_id: str, updates: LLMEndpointUpdate):
    if not llm_endpoints_table.contains(where('id') == endpoint_id):
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    update_data = updates.dict(exclude_unset=True)
    llm_endpoints_table.update(update_data, where('id') == endpoint_id)

    updated_endpoint = llm_endpoints_table.get(where('id') == endpoint_id)
    return {"success": True, "endpoint": updated_endpoint}


@app.delete("/api/llm-endpoints/{endpoint_id}")
def delete_llm_endpoint(endpoint_id: str):
    deleted_endpoint = llm_endpoints_table.get(where('id') == endpoint_id)
    if not deleted_endpoint:
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    llm_endpoints_table.remove(where('id') == endpoint_id)

    settings = get_settings()
    update_payload = {}
    if settings.get('activeEndpointId') == endpoint_id:
        update_payload['activeEndpointId'] = None
    if settings.get('defaultEndpointId') == endpoint_id:
        update_payload['defaultEndpointId'] = None

    if update_payload:
        settings_table.update(update_payload, doc_ids=[1])

    return {"success": True, "message": f"LLM endpoint '{deleted_endpoint.get('name', 'N/A')}' deleted."}


@app.post("/api/llm-endpoints/{endpoint_id}/activate")
def activate_llm_endpoint(endpoint_id: str):
    if not llm_endpoints_table.contains(where('id') == endpoint_id):
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    settings_table.update({'activeEndpointId': endpoint_id}, doc_ids=[1])
    return {"success": True, "activeEndpointId": endpoint_id}


@app.post("/api/llm-endpoints/{endpoint_id}/set-default")
def set_default_llm_endpoint(endpoint_id: str):
    if not llm_endpoints_table.contains(where('id') == endpoint_id):
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    # Unset previous default
    llm_endpoints_table.update({'isDefault': False}, where('isDefault') == True)
    # Set new default
    llm_endpoints_table.update({'isDefault': True}, where('id') == endpoint_id)

    # Update settings
    settings_table.update({'defaultEndpointId': endpoint_id}, doc_ids=[1])

    return {"success": True, "defaultEndpointId": endpoint_id}


# Test Endpoint Models
class TestEndpointModelsRequest(BaseModel):
    baseUrl: str
    apiKey: Optional[str] = None


class TestEndpointChatRequest(BaseModel):
    baseUrl: str
    apiKey: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    message: str = "Hello, this is a test message."


# Test Endpoints
@app.post("/api/test-endpoint/models")
async def test_models_endpoint(request: TestEndpointModelsRequest):
    """Test the /v1/models endpoint of an LLM provider"""
    print("Received request for /api/test-endpoint/models")
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
        
        # Correctly construct the URL
        url = f"{base_url}/models"
        print(f"{url=}")
        print(f"{headers=}")
        
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
    print("Received request for /api/test-endpoint/chat")
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
            # OpenAI compatible format
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
            
        print(f"{base_url=} {api_key=} {model=} {message=}")
        print(f"{headers=}")
        print(f"{data=}")
        
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
                    return {
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
                
                return response_data
                
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


# --- Server Startup ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("SERVER_PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
