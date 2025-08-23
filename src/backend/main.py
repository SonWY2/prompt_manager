import os
import json
import datetime
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid

# --- Configuration ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
PROMPT_DATA_PATH = os.path.join(DATA_DIR, 'prompt-data.json')
LLM_ENDPOINTS_PATH = os.path.join(DATA_DIR, 'llm-endpoints.json')

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

# --- Data Loading ---
def load_data(path: str) -> Dict:
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading data from {path}: {e}")
            return {}
    return {}

prompt_data = load_data(PROMPT_DATA_PATH)
if 'tasks' not in prompt_data:
    prompt_data['tasks'] = {}

llm_endpoints_data = load_data(LLM_ENDPOINTS_PATH)
if 'endpoints' not in llm_endpoints_data:
    llm_endpoints_data['endpoints'] = []
if 'activeEndpointId' not in llm_endpoints_data:
    llm_endpoints_data['activeEndpointId'] = None
if 'defaultEndpointId' not in llm_endpoints_data:
    llm_endpoints_data['defaultEndpointId'] = None

# --- Data Saving ---
def save_prompt_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PROMPT_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(prompt_data, f, indent=2, ensure_ascii=False)

def save_llm_endpoints_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LLM_ENDPOINTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(llm_endpoints_data, f, indent=2, ensure_ascii=False)

# --- Pydantic Models ---
class Version(BaseModel):
    id: str
    name: str
    content: str
    system_prompt: str
    description: Optional[str] = None
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

class VersionUpdate(BaseModel):
    content: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None

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
    return {"message": "Python Backend is running!"}

# 1. Task Management
@app.get("/api/tasks")
def get_tasks():
    tasks_list = [
        {
            "id": task_id,
            "name": task.get("name"),
            "versions": task.get("versions", [])
        }
        for task_id, task in prompt_data.get("tasks", {}).items()
    ]
    return {"tasks": tasks_list}

@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    task_id = task.taskId
    if task_id in prompt_data["tasks"]:
        raise HTTPException(status_code=409, detail="Task already exists")

    prompt_data["tasks"][task_id] = {"name": task.name, "versions": []}
    save_prompt_data()

    return {
        "success": True,
        "task": {
            "id": task_id,
            "name": task.name,
            "versions": []
        }
    }

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    if task_id not in prompt_data["tasks"]:
        raise HTTPException(status_code=404, detail="Task not found")

    del prompt_data["tasks"][task_id]
    save_prompt_data()

    return {"success": True, "message": f"Task '{task_id}' deleted successfully"}

# 2. Version Control
@app.get("/api/tasks/{task_id}/versions")
def get_versions(task_id: str):
    if task_id not in prompt_data["tasks"]:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"versions": prompt_data["tasks"][task_id].get("versions", [])}

@app.get("/api/tasks/{task_id}/versions/{version_id}")
def get_version_detail(task_id: str, version_id: str):
    if task_id not in prompt_data["tasks"]:
        raise HTTPException(status_code=404, detail="Task not found")

    version = next((v for v in prompt_data["tasks"][task_id].get("versions", []) if v["id"] == version_id), None)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return {"version": version}

@app.post("/api/tasks/{task_id}/versions", status_code=201)
def create_version(task_id: str, version: VersionCreate):
    if task_id not in prompt_data["tasks"]:
        raise HTTPException(status_code=404, detail="Task not found")

    display_name = version.name.strip() or f"Version {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

    new_version = {
        "id": version.versionId,
        "content": version.content,
        "system_prompt": version.system_prompt or "You are a helpful assistant.",
        "description": version.description,
        "name": display_name,
        "createdAt": datetime.datetime.now().isoformat(),
        "results": []
    }

    prompt_data["tasks"][task_id]["versions"].insert(0, new_version)
    save_prompt_data()

    return {
        "success": True,
        "version": {
            "id": version.versionId,
            "name": display_name
        }
    }

@app.put("/api/tasks/{task_id}/versions/{version_id}")
def update_version(task_id: str, version_id: str, updates: VersionUpdate):
    if task_id not in prompt_data["tasks"]:
        raise HTTPException(status_code=404, detail="Task not found")

    version_index = next((i for i, v in enumerate(prompt_data["tasks"][task_id]["versions"]) if v["id"] == version_id), -1)
    if version_index == -1:
        raise HTTPException(status_code=404, detail="Version not found")

    version = prompt_data["tasks"][task_id]["versions"][version_index]
    update_data = updates.dict(exclude_unset=True)
    version.update(update_data)
    version["updatedAt"] = datetime.datetime.now().isoformat()

    prompt_data["tasks"][task_id]["versions"][version_index] = version
    save_prompt_data()

    return {"success": True}

@app.delete("/api/tasks/{task_id}/versions/{version_id}")
def delete_version(task_id: str, version_id: str):
    if task_id not in prompt_data["tasks"]:
        raise HTTPException(status_code=404, detail="Task not found")

    versions = prompt_data["tasks"][task_id]["versions"]
    version_index = next((i for i, v in enumerate(versions) if v["id"] == version_id), -1)

    if version_index == -1:
        raise HTTPException(status_code=404, detail="Version not found")

    deleted_version = versions.pop(version_index)
    save_prompt_data()

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
    if task_id not in prompt_data["tasks"]:
        raise HTTPException(status_code=404, detail="Task not found")

    variables = set()
    for version in prompt_data["tasks"][task_id].get("versions", []):
        content = version.get("content", "")
        matches = [m[2:-2].strip() for m in re.findall(r"{{.*?}}", content)]
        variables.update(matches)

    return {"variables": list(variables)}

# 4. LLM API Integration
@app.post("/api/llm/call")
async def call_llm_endpoint(call: LLMCall):
    # This is a placeholder implementation as it requires an actual LLM call
    # which might involve external libraries like httpx or aiohttp.
    # The original nodejs code used 'axios' and a custom 'callLLM' function.
    # Replicating that would require more information on the `llm.js` module.

    task = prompt_data["tasks"].get(call.taskId)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    version = next((v for v in task["versions"] if v["id"] == call.versionId), None)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    rendered_prompt = render_template(version["content"], call.inputData)

    # In a real scenario, you would make an async HTTP request here.
    # For now, we'll just return a dummy response.
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

    save_prompt_data()

    return {"result": dummy_result}

# 5. LLM Endpoints Management
@app.get("/api/llm-endpoints")
def get_llm_endpoints():
    return llm_endpoints_data

@app.post("/api/llm-endpoints", status_code=201)
def create_llm_endpoint(endpoint: LLMEndpoint):
    new_endpoint = endpoint.dict()
    llm_endpoints_data["endpoints"].append(new_endpoint)

    if len(llm_endpoints_data["endpoints"]) == 1:
        llm_endpoints_data["activeEndpointId"] = new_endpoint["id"]
        llm_endpoints_data["defaultEndpointId"] = new_endpoint["id"]
        new_endpoint["isDefault"] = True

    save_llm_endpoints_data()
    return {"success": True, "endpoint": new_endpoint}

@app.put("/api/llm-endpoints/{endpoint_id}")
def update_llm_endpoint(endpoint_id: str, updates: LLMEndpointUpdate):
    endpoint_index = next((i for i, ep in enumerate(llm_endpoints_data["endpoints"]) if ep["id"] == endpoint_id), -1)
    if endpoint_index == -1:
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    endpoint = llm_endpoints_data["endpoints"][endpoint_index]
    update_data = updates.dict(exclude_unset=True)
    endpoint.update(update_data)

    llm_endpoints_data["endpoints"][endpoint_index] = endpoint
    save_llm_endpoints_data()

    return {"success": True, "endpoint": endpoint}

@app.delete("/api/llm-endpoints/{endpoint_id}")
def delete_llm_endpoint(endpoint_id: str):
    endpoints = llm_endpoints_data["endpoints"]
    endpoint_index = next((i for i, ep in enumerate(endpoints) if ep["id"] == endpoint_id), -1)

    if endpoint_index == -1:
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    deleted_endpoint = endpoints.pop(endpoint_index)

    if llm_endpoints_data["activeEndpointId"] == endpoint_id:
        llm_endpoints_data["activeEndpointId"] = endpoints[0]["id"] if endpoints else None
    if llm_endpoints_data["defaultEndpointId"] == endpoint_id:
        llm_endpoints_data["defaultEndpointId"] = endpoints[0]["id"] if endpoints else None
        if endpoints:
            endpoints[0]["isDefault"] = True

    save_llm_endpoints_data()

    return {"success": True, "message": f"LLM endpoint '{deleted_endpoint['name']}' deleted."}

@app.post("/api/llm-endpoints/{endpoint_id}/activate")
def activate_llm_endpoint(endpoint_id: str):
    if not any(ep["id"] == endpoint_id for ep in llm_endpoints_data["endpoints"]):
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    llm_endpoints_data["activeEndpointId"] = endpoint_id
    save_llm_endpoints_data()

    return {"success": True, "activeEndpointId": endpoint_id}

@app.post("/api/llm-endpoints/{endpoint_id}/set-default")
def set_default_llm_endpoint(endpoint_id: str):
    endpoint_found = False
    for ep in llm_endpoints_data["endpoints"]:
        if ep["id"] == endpoint_id:
            ep["isDefault"] = True
            endpoint_found = True
        else:
            ep["isDefault"] = False

    if not endpoint_found:
        raise HTTPException(status_code=404, detail="LLM endpoint not found")

    llm_endpoints_data["defaultEndpointId"] = endpoint_id
    save_llm_endpoints_data()

    return {"success": True, "defaultEndpointId": endpoint_id}

import re

# --- Server Startup ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("SERVER_PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
