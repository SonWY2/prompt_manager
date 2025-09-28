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

def initialize_database():
    """Initialize database with proper error handling"""
    try:
        # Try to read the existing database file
        if os.path.exists(DB_PATH):
            # Attempt to validate JSON structure
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    # File is empty, create default structure
                    create_default_database()
                else:
                    try:
                        json.loads(content)
                    except json.JSONDecodeError as e:
                        # Backup corrupted file and create new one
                        backup_path = f"{DB_PATH}.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        os.rename(DB_PATH, backup_path)
                        create_default_database()
        else:
            create_default_database()
            
        # Initialize TinyDB instance
        db = TinyDB(DB_PATH, indent=2, ensure_ascii=False)
        
        # Ensure all required tables exist
        tables = {
            'tasks': db.table('tasks'),
            'llm_endpoints': db.table('llm_endpoints'), 
            'settings': db.table('settings')
        }
        
        # Initialize settings if they don't exist
        if not tables['settings'].get(doc_id=1):
            tables['settings'].insert({'activeEndpointId': None, 'defaultEndpointId': None})
            
        return db, tables
        
    except Exception as e:
        # Critical database initialization error - create fresh database
        create_default_database()
        db = TinyDB(DB_PATH, indent=2, ensure_ascii=False)
        tables = {
            'tasks': db.table('tasks'),
            'llm_endpoints': db.table('llm_endpoints'),
            'settings': db.table('settings')
        }
        # Initialize settings
        tables['settings'].insert({'activeEndpointId': None, 'defaultEndpointId': None})
        return db, tables

def create_default_database():
    """Create a new database file with default structure"""
    default_structure = {
        "tasks": {},
        "llm_endpoints": {},
        "settings": {
            "1": {
                "activeEndpointId": None,
                "defaultEndpointId": None
            }
        }
    }
    
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(default_structure, f, indent=2, ensure_ascii=False)

# Initialize database with error handling
db, db_tables = initialize_database()
tasks_table = db_tables['tasks']
llm_endpoints_table = db_tables['llm_endpoints']
settings_table = db_tables['settings']


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
    print(f"🔧 [DEBUG] 템플릿 렌더링 시작:")
    print(f"  - 원본 템플릿: {template}")
    print(f"  - 변수 데이터: {data}")
    
    rendered = template
    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"
        print(f"  - 치환: {placeholder} -> {str(value)}")
        rendered = rendered.replace(placeholder, str(value))
    
    print(f"  - 최종 렌더링 결과: {rendered}")
    return rendered


def get_settings():
    """Get settings with error handling"""
    try:
        settings = settings_table.get(doc_id=1)
        if not settings:
            # If settings don't exist, create them
            default_settings = {'activeEndpointId': None, 'defaultEndpointId': None}
            settings_table.insert(default_settings)
            return default_settings
        return settings
    except Exception as e:
        # Return default settings if there's an error
        default_settings = {'activeEndpointId': None, 'defaultEndpointId': None}
        try:
            settings_table.insert(default_settings)
        except Exception as insert_error:
            pass  # Silently handle insert error
        return default_settings

def safe_db_operation(operation_func, fallback_value=None, operation_name="database operation"):
    """Safely execute database operations with error handling"""
    try:
        return operation_func()
    except Exception as e:
        # Silently handle database operation errors
        return fallback_value

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Python Backend with TinyDB is running!"}

# 1. Task Management
@app.get("/api/tasks")
def get_tasks():
    """Get all tasks with error handling"""
    try:
        tasks_list = safe_db_operation(
            lambda: tasks_table.all(),
            fallback_value=[],
            operation_name="get tasks"
        )
        # Ensure all tasks have the isFavorite field for frontend compatibility
        for task in tasks_list:
            if 'isFavorite' not in task:
                task['isFavorite'] = False
        return {"tasks": tasks_list}
    except Exception as e:
        # Silently handle critical errors
        return {"tasks": []}

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
    # Creating version for task
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
    print(f"🔧 [DEBUG] Task 변수 불러오기 요청: task_id={task_id}")
    
    task = tasks_table.get(where('id') == task_id)
    if not task:
        print(f"❌ [ERROR] Task {task_id} 찾을 수 없음")
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 기존 Task에 variables 필드가 없는 경우 추가
    if "variables" not in task:
        print(f"🔧 [DEBUG] Task {task_id}에 variables 필드가 없어서 추가")
        task["variables"] = {}
        tasks_table.update(task, where('id') == task_id)
    
    variables = task.get("variables", {})
    print(f"🔧 [DEBUG] Task {task_id} 변수 불러오기 완료: {variables}")
    
    return {"variables": variables}

@app.put("/api/tasks/{task_id}/variables")
def update_task_variables(task_id: str, request_data: Dict[str, Any]):
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 요청 데이터에서 variables 추출
    if 'variables' in request_data:
        # 프론트엔드가 { variables: {...} } 형태로 보낸 경우
        variables = request_data['variables']
    else:
        # 프론트엔드가 직접 변수들을 보낸 경우 (이전 형태)
        variables = request_data
    
    # 중첩된 variables 구조 정리 
    def clean_variables(data):
        """재귀적으로 중첩된 'variables' 키를 정리"""
        if isinstance(data, dict):
            if 'variables' in data and len(data) == 1:
                # 'variables' 키만 있는 경우, 그 값을 재귀적으로 정리
                return clean_variables(data['variables'])
            else:
                # 일반적인 딕셔너리인 경우, 각 값에 대해 재귀적으로 정리
                cleaned = {}
                for k, v in data.items():
                    if k == 'variables' and isinstance(v, dict):
                        # 'variables' 키의 값이 딕셔너리인 경우 정리
                        cleaned_v = clean_variables(v)
                        # 정리된 결과가 실제 변수들(string 값)인지 확인
                        if isinstance(cleaned_v, dict) and all(isinstance(val, (str, int, float)) for val in cleaned_v.values()):
                            cleaned[k] = cleaned_v
                        elif isinstance(cleaned_v, dict):
                            # 여전히 중첩된 구조라면 더 정리
                            cleaned.update(cleaned_v)
                        else:
                            cleaned[k] = cleaned_v
                    else:
                        cleaned[k] = v
                return cleaned
        return data
    
    # 새로운 variables를 정리
    cleaned_variables = clean_variables(variables)
    
    task["variables"] = cleaned_variables
    tasks_table.update(task, where('id') == task_id)
    
    print(f"✅ Task {task_id} 변수 저장 완료: {cleaned_variables}")
    return {"success": True, "variables": cleaned_variables}

# Variables 데이터 정리 유틸리티 엔드포인트
@app.post("/api/tasks/{task_id}/variables/cleanup")
def cleanup_task_variables(task_id: str):
    """중첩된 variables 구조를 정리하는 유틸리티"""
    task = tasks_table.get(where('id') == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    original_variables = task.get('variables', {})
    
    def extract_actual_variables(data, depth=0):
        """중첩된 구조에서 실제 변수들(string 값)만 추출"""
        if depth > 10:  # 무한 재귀 방지
            return {}
            
        actual_vars = {}
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str):
                    # 문자열 값이면 실제 변수
                    actual_vars[k] = v
                elif isinstance(v, dict):
                    # 딕셔너리면 재귀적으로 탐색
                    nested_vars = extract_actual_variables(v, depth + 1)
                    actual_vars.update(nested_vars)
        return actual_vars
    
    cleaned_variables = extract_actual_variables(original_variables)
    
    task["variables"] = cleaned_variables
    tasks_table.update(task, where('id') == task_id)
    
    return {"success": True, "cleaned_variables": cleaned_variables, "original_variables": original_variables}

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
    system_prompt = call.system_prompt or version.get("system_prompt", "You are a helpful assistant.")
    
    print(f"🔧 [DEBUG] LLM API 호출 준비:")
    print(f"  - Task ID: {call.taskId}")
    print(f"  - Version ID: {call.versionId}")
    print(f"  - System Prompt: {system_prompt}")
    print(f"  - Rendered User Prompt: {rendered_prompt}")
    print(f"  - Active Endpoint: {active_endpoint.get('name')} ({active_endpoint.get('baseUrl')})")
    
    # 실제 LLM API 호출
    try:
        result = await call_actual_llm_api(
            endpoint=active_endpoint,
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
    print(f"🔧 [DEBUG] API 키 처리:")
    print(f"  - API 키 존재 여부: {bool(api_key)}")
    print(f"  - API 키 길이: {len(api_key) if api_key else 0}")
    if api_key:
        masked_key = api_key[:8] + '*' * (len(api_key) - 12) + api_key[-4:] if len(api_key) > 12 else api_key[:4] + '*' * 4
        print(f"  - API 키 (마스킹): {masked_key}")
    print(f"  - Base URL: {base_url}")
    
    if api_key:
        if 'openai.com' in base_url or 'api.together.xyz' in base_url:
            headers['Authorization'] = f'Bearer {api_key}'
            print(f"  - OpenAI/Together 형식 Authorization 헤더 추가")
        elif 'openrouter.ai' in base_url:
            headers['Authorization'] = f'Bearer {api_key}'
            headers['HTTP-Referer'] = 'https://prompt-manager.local'
            headers['X-Title'] = 'Prompt Manager'
            print(f"  - OpenRouter 형식 Authorization 헤더 추가")
        elif 'anthropic.com' in base_url:
            headers['x-api-key'] = api_key
            headers['anthropic-version'] = '2023-06-01'
            print(f"  - Anthropic 형식 x-api-key 헤더 추가")
        else:
            # 기본적으로 Bearer 토큰 사용
            headers['Authorization'] = f'Bearer {api_key}'
            print(f"  - 기본 Bearer 토큰 형식으로 Authorization 헤더 추가")
    else:
        print(f"  - API 키가 없어서 인증 헤더 추가하지 않음")
    
    print(f"🔧 [DEBUG] 최종 요청 헤더: {headers}")
    
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
        print(f"🔧 [DEBUG] Anthropic ChatML 메시지 구성:")
        print(f"  - Model: {model}")
        print(f"  - URL: {url}")
        print(f"  - Combined Content: {combined_content}")
        print(f"  - Messages: {data['messages']}")
    else:
        # OpenAI 호환 API (OpenAI, Together, vLLM, Ollama 등)
        messages = []
        
        # System prompt가 비어있지 않은 경우에만 추가
        if system_prompt and system_prompt.strip():
            messages.append({'role': 'system', 'content': system_prompt.strip()})
            print(f"🔧 [DEBUG] System message 추가: {system_prompt.strip()}")
        else:
            print(f"⚠️ [WARNING] System prompt가 비어있음, 메시지에 포함하지 않음")
        
        # User prompt는 필수이므로 확인 후 추가
        if user_prompt and user_prompt.strip():
            messages.append({'role': 'user', 'content': user_prompt.strip()})
            print(f"🔧 [DEBUG] User message 추가: {user_prompt.strip()}")
        else:
            print(f"❌ [ERROR] User prompt가 비어있음!")
            raise Exception("User prompt cannot be empty")
        
        data = {
            'model': model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 4000
        }
        url = f"{base_url}/chat/completions"
        print(f"🔧 [DEBUG] OpenAI 호환 ChatML 메시지 구성:")
        print(f"  - Model: {model}")
        print(f"  - URL: {url}")
        print(f"  - Messages count: {len(messages)}")
        print(f"  - Full Messages: {messages}")
    
    # Making LLM API call
    print(f"🔧 [DEBUG] 실제 API 요청:")
    print(f"  - URL: {url}")
    print(f"  - Headers: {headers}")
    print(f"  - Data: {data}")
    
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
                    print(f"❌ [ERROR] LLM API 호출 실패: {response.status} - {error_text}")
                    raise Exception(f"API returned {response.status}: {error_text}")
                
                response_data = await response.json()
                print(f"✅ [DEBUG] LLM API 응답 성공:")
                print(f"  - Status: {response.status}")
                print(f"  - Response: {response_data}")
                
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
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            raise

# 5. LLM Endpoints Management
@app.get("/api/llm-endpoints")
def get_llm_endpoints():
    """Get all LLM endpoints with error handling"""
    try:
        endpoints = safe_db_operation(
            lambda: llm_endpoints_table.all(),
            fallback_value=[],
            operation_name="get LLM endpoints"
        )
        settings = get_settings()
        active_id = settings.get('activeEndpointId')
        default_id = settings.get('defaultEndpointId')
        return {"endpoints": endpoints, "activeEndpointId": active_id, "defaultEndpointId": default_id}
    except Exception as e:
        # Silently handle critical errors
        return {"endpoints": [], "activeEndpointId": None, "defaultEndpointId": None}


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
