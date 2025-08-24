import os
import json
import datetime
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
    isDefault: bool = False
    createdAt: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())

class LLMEndpointUpdate(BaseModel):
    name: Optional[str] = None
    baseUrl: Optional[str] = None
    apiKey: Optional[str] = None
    defaultModel: Optional[str] = None
    description: Optional[str] = None

# --- Helper Functions ---
def render_template(template: str, data: dict) -> str:
    for key, value in data.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Python Backend with TinyDB is running!"}

# 1. Task Management
@app.get("/api/tasks")
def get_tasks():
    tasks_list = tasks_table.all()
    return {"tasks": tasks_list}

@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    task_id = task.taskId
    if tasks_table.contains(where('id') == task_id):
        raise HTTPException(status_code=409, detail="Task already exists")

    new_task = {"id": task_id, "name": task.name, "versions": []}
    tasks_table.insert(new_task)

    return {
        "success": True,
        "task": new_task
    }

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

    rendered_prompt = render_template(version["content"], call.inputData)

    dummy_result = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": int(datetime.datetime.now().timestamp()),
        "model": "dummy-model",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": f"This is a dummy response for the prompt: '{rendered_prompt}'"
            },
            "finish_reason": "stop"
        }]
    }

    if "results" not in version:
        version["results"] = []

    version["results"].insert(0, {
        "inputData": call.inputData,
        "output": dummy_result,
        "timestamp": datetime.datetime.now().isoformat()
    })

    tasks_table.update(task, where('id') == call.taskId)

    return {"result": dummy_result}

# 5. LLM Endpoints Management
@app.get("/api/llm-endpoints")
def get_llm_endpoints():
    endpoints = llm_endpoints_table.all()
    # This part is tricky as TinyDB doesn't have a global config table easily.
    # We can store active/default ids in a separate table or a specific document.
    # For now, we assume the first endpoint is active/default if not set.
    active_id = llm_endpoints_table.get(doc_id=1).get('activeEndpointId') if llm_endpoints_table.get(doc_id=1) else None
    default_id = llm_endpoints_table.get(doc_id=1).get('defaultEndpointId') if llm_endpoints_table.get(doc_id=1) else None

    return {"endpoints": endpoints, "activeEndpointId": active_id, "defaultEndpointId": default_id}

@app.post("/api/llm-endpoints", status_code=201)
def create_llm_endpoint(endpoint: LLMEndpoint):
    new_endpoint = endpoint.dict()

    if not llm_endpoints_table.all():
        new_endpoint["isDefault"] = True
        # Storing active/default ids is not straightforward in tinydb tables.
        # This part of logic might need to be adapted based on how we want to store global state.
        # For now, this logic is simplified.

    llm_endpoints_table.insert(new_endpoint)
    return {"success": True, "endpoint": new_endpoint}

@app.put("/api/llm-endpoints/{endpoint_id}")
def update_llm_endpoint(endpoint_id: str, updates: LLMEndpointUpdate):
    update_data = updates.dict(exclude_unset=True)
    updated_count = llm_endpoints_table.update(update_data, where('id') == endpoint_id)

    if not updated_count:
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    endpoint = llm_endpoints_table.get(where('id') == endpoint_id)
    return {"success": True, "endpoint": endpoint}

@app.delete("/api/llm-endpoints/{endpoint_id}")
def delete_llm_endpoint(endpoint_id: str):
    if not llm_endpoints_table.contains(where('id') == endpoint_id):
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    deleted_endpoint = llm_endpoints_table.get(where('id') == endpoint_id)
    llm_endpoints_table.remove(where('id') == endpoint_id)

    return {"success": True, "message": f"LLM endpoint '{deleted_endpoint['name']}' deleted."}

@app.post("/api/llm-endpoints/{endpoint_id}/activate")
def activate_llm_endpoint(endpoint_id: str):
    # Activating an endpoint is a concept that needs to be stored somewhere.
    # In a simple key-value store, this would be easy. With TinyDB, we could have a
    # separate table for settings, or a specific document.
    # This feature is simplified here. We are not storing the active state.
    if not llm_endpoints_table.contains(where('id') == endpoint_id):
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    return {"success": True, "activeEndpointId": endpoint_id}

@app.post("/api/llm-endpoints/{endpoint_id}/set-default")
def set_default_llm_endpoint(endpoint_id: str):
    if not llm_endpoints_table.contains(where('id') == endpoint_id):
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    llm_endpoints_table.update({'isDefault': False}, where('isDefault') == True)
    llm_endpoints_table.update({'isDefault': True}, where('id') == endpoint_id)

    return {"success": True, "defaultEndpointId": endpoint_id}

import re

# --- Server Startup ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("SERVER_PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
