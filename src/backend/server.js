// Template rendering function

// 환경 변수 로드 - dotenv가 없는 경우 처리
try {
  require('dotenv').config();
} catch (error) {
  console.warn('dotenv 모듈을 찾을 수 없습니다. 환경 변수를 .env 파일에서 로드하지 않습니다.');
  // 필요한 기본 환경 변수 설정
  process.env.SERVER_PORT = process.env.SERVER_PORT || 3000;
  process.env.ALLOWED_FRONTEND_PORTS = process.env.ALLOWED_FRONTEND_PORTS || '';
  process.env.OPENAI_BASE_URL = process.env.OPENAI_BASE_URL || 'http://localhost:8000/v1';
  process.env.OPENAI_MODEL = process.env.OPENAI_MODEL || 'mistralai/Mistral-7B-Instruct-v0.2';
}

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const { callLLM } = require('./lib/llm.js'); // LLM 모듈 import

const app = express();
const PORT = process.env.SERVER_PORT || 3000; // 환경변수로 백엔드 포트 설정 가능

// CORS 설정을 환경변수로 관리
// 기본적으로 지원할 포트들
const defaultPorts = ['5173', '3030'];

// 환경변수에서 추가 포트 목록 가져오기
const additionalPorts = process.env.ALLOWED_FRONTEND_PORTS 
  ? process.env.ALLOWED_FRONTEND_PORTS.split(',') 
  : [];

// 허용할 모든 포트 목록 생성
const allowedPorts = [...new Set([...defaultPorts, ...additionalPorts])];

// 허용할 원본 목록 생성
const allowedOrigins = [];
for (const port of allowedPorts) {
  allowedOrigins.push(`http://localhost:${port}`);
  allowedOrigins.push(`http://127.0.0.1:${port}`);
}

console.log(`[${new Date().toISOString()}] 허용된 프론트엔드 원본:`, allowedOrigins);

// Express 미들웨어 설정
app.use(cors({
  origin: allowedOrigins,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  credentials: true
}));
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '../../dist')));

// API를 제외한 모든 경로에 대해 SPA 지원
app.use((req, res, next) => {
  // 모든 API 요청은 통과
  if (req.path.startsWith('/api/')) {
    return next();
  }
  
  // GET 요청은 정적 파일로 처리
  if (req.method === 'GET') {
    return res.sendFile(path.join(__dirname, '../../dist/index.html'));
  }
  
  // 그 외 요청은 404 응답
  res.status(404).send(`Cannot ${req.method} ${req.path}`);
});

// 요청 로깅 미들웨어 (템플릿 변수 API는 로깅 생략)
app.use((req, res, next) => {
  // 템플릿 변수 API는 로깅 생략 (너무 빈번함)
  if (req.path.includes('/variables')) {
    return next();
  }
  
  const startTime = Date.now();
  console.log(`[${new Date().toISOString()}] => ${req.method} ${req.originalUrl} 요청 시작`);
  
  // GET 요청이 아닌 경우에만 파라미터와 쿼리 로깅
  if (req.method !== 'GET') {
    console.log(`요청 파라미터:`, req.params);
    console.log(`요청 쿼리:`, req.query);
  }
  
  // 원래 응답 메서드를 저장
  const originalSend = res.send;
  const originalJson = res.json;
  const originalStatus = res.status;
  
  // 상태 코드 추적
  let currentStatus = 200;
  res.status = function(code) {
    currentStatus = code;
    return originalStatus.apply(this, arguments);
  };
  
  // 응답 메서드 오버라이드 (오류나 느린 요청만 로깅)
  res.send = function() {
    const duration = Date.now() - startTime;
    if (currentStatus >= 400 || duration > 1000) {
      console.log(`[${new Date().toISOString()}] <= ${req.method} ${req.originalUrl} 응답 완료 (${currentStatus}) - ${duration}ms`);
    }
    return originalSend.apply(this, arguments);
  };
  
  res.json = function() {
    const duration = Date.now() - startTime;
    if (currentStatus >= 400 || duration > 1000) {
      console.log(`[${new Date().toISOString()}] <= ${req.method} ${req.originalUrl} JSON 응답 완료 (${currentStatus}) - ${duration}ms`);
    }
    return originalJson.apply(this, arguments);
  };
  
  next();
});

// In-memory database
let promptData = {
  tasks: {},
  versionHistory: {}
};

// In-memory LLM endpoints data
let llmEndpointsData = {
  endpoints: [],
  activeEndpointId: null,
  defaultEndpointId: null
};

// Load existing data from file
const dataPath = path.join(__dirname, '../../data/prompt-data.json');
if (fs.existsSync(dataPath)) {
  try {
    const data = fs.readFileSync(dataPath, 'utf-8');
    promptData = JSON.parse(data);
    console.log(`[${new Date().toISOString()}] 성공적으로 데이터 파일을 로드했습니다:`, dataPath);
    console.log(`[${new Date().toISOString()}] 태스크 수:`, Object.keys(promptData.tasks).length);
  } catch (error) {
    console.error(`[${new Date().toISOString()}] 데이터 로드 오류:`, error);
  }
} else {
  console.log(`[${new Date().toISOString()}] 데이터 파일이 없습니다. 새 파일을 생성합니다:`, dataPath);
}

// Load LLM endpoints data
const llmEndpointsPath = path.join(__dirname, '../../data/llm-endpoints.json');
if (fs.existsSync(llmEndpointsPath)) {
  try {
    const data = fs.readFileSync(llmEndpointsPath, 'utf-8');
    llmEndpointsData = JSON.parse(data);
    console.log(`[${new Date().toISOString()}] LLM endpoints 데이터 로드 성공:`, llmEndpointsPath);
    console.log(`[${new Date().toISOString()}] 엔드포인트 수:`, llmEndpointsData.endpoints.length);
  } catch (error) {
    console.error(`[${new Date().toISOString()}] LLM endpoints 데이터 로드 오류:`, error);
  }
} else {
  console.log(`[${new Date().toISOString()}] LLM endpoints 파일이 없습니다. 새 파일을 생성합니다.`);
}

// API Endpoints
// 1. Task Management
app.get('/api/tasks', (req, res) => {
  res.json({ 
    tasks: Object.entries(promptData.tasks).map(([id, task]) => ({
      id,
      name: task.name,
      versions: task.versions || []
    }))
  });
});

app.post('/api/tasks', (req, res) => {
  const { taskId, name } = req.body;
  promptData.tasks[taskId] = { 
    name, 
    versions: [] 
  };
  saveData();
  res.status(201).json({ 
    success: true,
    task: {
      id: taskId,
      name,
      versions: []
    }
  });
});


// 새로 추가: 태스크 삭제 API
app.delete('/api/tasks/:taskId', (req, res) => {
  const { taskId } = req.params;
  
  console.log(`[${new Date().toISOString()}] 태스크 삭제 요청:`, taskId);
  
  if (!promptData.tasks[taskId]) {
    return res.status(404).json({ error: 'Task not found' });
  }
  
  // 태스크 삭제
  delete promptData.tasks[taskId];
  
  saveData();
  
  console.log(`[${new Date().toISOString()}] 태스크 삭제 완료:`, taskId);
  
  res.json({ 
    success: true, 
    message: `Task '${taskId}' deleted successfully`
  });
});

// 2. Version Control
app.get('/api/tasks/:taskId/versions', (req, res) => {
  const { taskId } = req.params;
  res.json({ versions: promptData.tasks[taskId]?.versions || [] });
});

// 버전 상세 정보 API
app.get('/api/tasks/:taskId/versions/:versionId', (req, res) => {
  const { taskId, versionId } = req.params;
  console.log(`[${new Date().toISOString()}] 버전 상세 정보 요청:`, { taskId, versionId });
  
  if (!promptData.tasks[taskId]) {
    console.log(`[${new Date().toISOString()}] 태스크를 찾을 수 없습니다:`, taskId);
    return res.status(404).json({ error: 'Task not found' });
  }
  
  const version = promptData.tasks[taskId].versions.find(v => v.id === versionId);
  if (!version) {
    console.log(`[${new Date().toISOString()}] 버전을 찾을 수 없습니다:`, { taskId, versionId });
    return res.status(404).json({ error: 'Version not found' });
  }
  
  console.log(`[${new Date().toISOString()}] 버전 정보 요청 성공:`, version.id);
  res.json({ version });
});

app.post('/api/tasks/:taskId/versions', (req, res) => {
  const { taskId } = req.params;
  const { versionId, content, description, name, system_prompt } = req.body;
  
  console.log(`[${new Date().toISOString()}] 버전 생성 요청:`, {
    taskId,
    versionId,
    name,
    description: description?.substring(0, 30) + (description?.length > 30 ? '...' : ''),
    contentLength: content?.length || 0,
    systemPromptLength: system_prompt?.length || 0
  });
  
  if (!promptData.tasks[taskId]) {
    console.log(`[${new Date().toISOString()}] 태스크 없음:`, taskId);
    return res.status(404).json({ error: 'Task not found' });
  }

  // 버전 이름 처리 - 이름이 없으면 현재 날짜/시간 기반으로 자동 생성
  const displayName = name.trim() || `버전 ${new Date().toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })}`.replace(/\. /g, '.');
  
  console.log(`[${new Date().toISOString()}] 버전 이름 처리:`, { original: name, final: displayName });

  promptData.tasks[taskId].versions.unshift({
    id: versionId,
    content,
    system_prompt: system_prompt || "You are a helpful assistant.",
    description,
    name: displayName,
    createdAt: new Date().toISOString(),
    results: []
  });
  
  saveData();
  res.status(201).json({ 
    success: true,
    version: {
      id: versionId,
      name: displayName
    }
  });
});

// 새로 추가: 버전 업데이트 API
app.put('/api/tasks/:taskId/versions/:versionId', (req, res) => {
  const { taskId, versionId } = req.params;
  const { content, name, description, system_prompt } = req.body;
  
  if (!promptData.tasks[taskId]) {
    return res.status(404).json({ error: 'Task not found' });
  }
  
  const versionIndex = promptData.tasks[taskId].versions.findIndex(v => v.id === versionId);
  if (versionIndex === -1) {
    return res.status(404).json({ error: 'Version not found' });
  }
  
  // 버전 정보 업데이트
  promptData.tasks[taskId].versions[versionIndex] = {
    ...promptData.tasks[taskId].versions[versionIndex],
    content: content !== undefined ? content : promptData.tasks[taskId].versions[versionIndex].content,
    system_prompt: system_prompt !== undefined ? system_prompt : promptData.tasks[taskId].versions[versionIndex].system_prompt,
    name: name !== undefined ? name : promptData.tasks[taskId].versions[versionIndex].name,
    description: description !== undefined ? description : promptData.tasks[taskId].versions[versionIndex].description,
    updatedAt: new Date().toISOString()
  };
  
  saveData();
  res.json({ success: true });
});



// 버전 삭제 API - 안전한 에러 처리 추가
app.delete('/api/tasks/:taskId/versions/:versionId', (req, res) => {
  const { taskId, versionId } = req.params;
  
  try {
    console.log(`[${new Date().toISOString()}] 버전 삭제 요청:`, { taskId, versionId });
    
    // 파라미터 유효성 검사
    if (!taskId || !versionId) {
      console.log('오류: 태스크 ID 또는 버전 ID가 없습니다!');
      return res.status(400).json({ 
        error: 'Task ID and Version ID are required', 
        params: { taskId, versionId } 
      });
    }
    
    // promptData 객체 존재 확인
    if (!promptData || !promptData.tasks) {
      console.log('오류: promptData 또는 tasks 객체가 없습니다!');
      return res.status(500).json({ 
        error: 'Internal server error: data structure not initialized' 
      });
    }
    
    // 태스크 존재 확인
    if (!promptData.tasks[taskId]) {
      console.log(`오류: 태스크를 찾을 수 없습니다. 태스크 ID: ${taskId}`);
      console.log('전체 태스크 목록:', Object.keys(promptData.tasks));
      return res.status(404).json({ 
        error: 'Task not found', 
        taskId,
        availableTasks: Object.keys(promptData.tasks)
      });
    }
    
    console.log(`태스크 찾음: ${taskId}, 태스크 이름: ${promptData.tasks[taskId].name}`);
    
    // 버전 배열 존재 확인
    if (!Array.isArray(promptData.tasks[taskId].versions)) {
      console.log(`오류: 태스크에 versions 배열이 없습니다!`);
      return res.status(500).json({ 
        error: 'Internal server error: versions array not found' 
      });
    }
    
    console.log(`버전 개수: ${promptData.tasks[taskId].versions.length}`);
    console.log('버전 ID 목록:', promptData.tasks[taskId].versions.map(v => v.id));
    
    // 버전 찾기
    const versionIndex = promptData.tasks[taskId].versions.findIndex(v => v.id === versionId);
    if (versionIndex === -1) {
      console.log(`오류: 버전을 찾을 수 없습니다. 버전 ID: ${versionId}`);
      return res.status(404).json({ 
        error: 'Version not found', 
        versionId,
        availableVersions: promptData.tasks[taskId].versions.map(v => ({ id: v.id, name: v.name }))
      });
    }
    
    // 버전 삭제 전 정보 백업
    const deletedVersion = { ...promptData.tasks[taskId].versions[versionIndex] };
    console.log(`삭제될 버전 정보:`, { id: deletedVersion.id, name: deletedVersion.name });
    
    // 버전 삭제 실행
    promptData.tasks[taskId].versions.splice(versionIndex, 1);
    console.log(`삭제 후 버전 수: ${promptData.tasks[taskId].versions.length}`);
    
    // 데이터 저장 (안전한 방식)
    try {
      saveData();
      console.log('데이터 저장 성공');
    } catch (saveError) {
      console.error('데이터 저장 실패:', saveError);
      // 저장 실패 시 메모리 상태는 이미 변경됨을 알림
      return res.status(500).json({
        error: 'Failed to save data to disk, but version deleted from memory',
        deletedVersion: { id: deletedVersion.id, name: deletedVersion.name }
      });
    }
    
    // 성공 응답
    res.json({ 
      success: true,
      message: `버전 ${versionId} 삭제 성공`, 
      deletedVersion: {
        id: deletedVersion.id,
        name: deletedVersion.name
      }
    });
    
    console.log(`[${new Date().toISOString()}] 버전 삭제 성공:`, { taskId, versionId });
    
  } catch (error) {
    console.error('버전 삭제 중 예상치 못한 오류:', error);
    res.status(500).json({
      error: 'Internal server error during version deletion',
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
});

// 3. Template Variable Management
app.get('/api/templates/:taskId/variables', (req, res) => {
  const { taskId } = req.params;
  const task = promptData.tasks[taskId];
  
  if (!task) {
    return res.status(404).json({ error: 'Task not found' });
  }

  // Extract variables from all versions of the prompt
  const variables = new Set();
  task.versions.forEach(version => {
    const matches = version.content ? (version.content.match(/{{(.*?)}}/g) || []) : [];
    matches.forEach(match => {
      variables.add(match.slice(2, -2).trim());
    });
  });
  
  res.json({ variables: Array.from(variables) });
});

app.post('/api/templates/:taskId/variables', (req, res) => {
  const { taskId } = req.params;
  const { variables } = req.body;
  
  // Store variables in task metadata
  if (!promptData.tasks[taskId]) {
    return res.status(404).json({ error: 'Task not found' });
  }
  
  promptData.tasks[taskId].variables = variables;
  saveData();
  res.json({ success: true });
});

// 4. LLM API Integration
app.post('/api/llm/call', async (req, res) => {
  const { taskId, versionId, inputData, system_prompt, endpoint } = req.body;
  
  // Find the task and version
  const task = promptData.tasks[taskId];
  if (!task) {
    return res.status(404).json({ error: 'Task not found' });
  }
  
  const version = task.versions.find(v => v.id === versionId);
  if (!version) {
    return res.status(404).json({ error: 'Version not found' });
  }
  
  // Replace placeholders with input data
  const renderedPrompt = renderTemplate(version.content, inputData);
  
  // Use system prompt from request body, version, or default
  const systemPromptToUse = system_prompt || version.system_prompt || "You are a helpful assistant.";
  
  // LLM endpoint 정보 결정
  let llmConfig = {
    baseUrl: process.env.OPENAI_BASE_URL || 'http://localhost:8000/v1',
    apiKey: process.env.OPENAI_API_KEY || '',
    model: process.env.OPENAI_MODEL || 'mistralai/Mistral-7B-Instruct-v0.2'
  };
  
  // 프런트엔드에서 전달된 endpoint 정보가 있으면 사용
  if (endpoint && endpoint.baseUrl) {
    llmConfig = {
      baseUrl: endpoint.baseUrl,
      apiKey: endpoint.apiKey || '',
      model: endpoint.defaultModel || llmConfig.model
    };
    console.log(`[${new Date().toISOString()}] 사용자 정의 엔드포인트 사용:`, {
      baseUrl: llmConfig.baseUrl,
      model: llmConfig.model,
      hasApiKey: !!llmConfig.apiKey
    });
  } else {
    // 활성화된 엔드포인트가 없으면 기본값 사용
    console.log(`[${new Date().toISOString()}] 기본 엔드포인트 사용 (환경변수):`, {
      baseUrl: llmConfig.baseUrl,
      model: llmConfig.model
    });
  }
  
  try {
    // Store the LLM result
    const result = await callLLM(renderedPrompt, systemPromptToUse, llmConfig);
    
    if (!version.results) {
      version.results = [];
    }
    
    version.results.unshift({
      inputData,
      output: result,
      timestamp: new Date().toISOString()
    });
    
    saveData();
    res.json({ result });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 5. Version Comparison
app.get('/api/compare', (req, res) => {
  const { taskId, version1, version2 } = req.query;
  
  const task = promptData.tasks[taskId];
  if (!task) {
    return res.status(404).json({ error: 'Task not found' });
  }
  
  const v1 = task.versions.find(v => v.id === version1);
  const v2 = task.versions.find(v => v.id === version2);
  
  if (!v1 || !v2) {
    return res.status(404).json({ error: 'One or both versions not found' });
  }
  
  // Compare versions using json-diff
  const diff = require('json-diff').diff(v1, v2);
  res.json({ diff });
});

// 6. Variable Presets (새 기능)
app.get('/api/variable-presets/:taskId', (req, res) => {
  const { taskId } = req.params;
  
  const task = promptData.tasks[taskId];
  if (!task) {
    return res.status(404).json({ error: 'Task not found' });
  }
  
  res.json({ presets: task.variablePresets || [] });
});

app.post('/api/variable-presets/:taskId', (req, res) => {
  const { taskId } = req.params;
  const { presetId, name, values } = req.body;
  
  const task = promptData.tasks[taskId];
  if (!task) {
    return res.status(404).json({ error: 'Task not found' });
  }
  
  if (!task.variablePresets) {
    task.variablePresets = [];
  }
  
  // 기존 프리셋 업데이트 또는 새 프리셋 추가
  const existingPresetIndex = task.variablePresets.findIndex(p => p.id === presetId);
  if (existingPresetIndex >= 0) {
    task.variablePresets[existingPresetIndex] = { id: presetId, name, values };
  } else {
    task.variablePresets.push({ id: presetId, name, values });
  }
  
  saveData();
  res.json({ success: true });
});


// 8. LLM Endpoints Management APIs
// LLM 엔드포인트 목록 조회
app.get('/api/llm-endpoints', (req, res) => {
  try {
    res.json({
      endpoints: llmEndpointsData.endpoints || [],
      activeEndpointId: llmEndpointsData.activeEndpointId,
      defaultEndpointId: llmEndpointsData.defaultEndpointId
    });
  } catch (error) {
    console.error(`[${new Date().toISOString()}] LLM 엔드포인트 목록 조회 오류:`, error);
    res.status(500).json({ error: 'Failed to fetch LLM endpoints' });
  }
});

// LLM 엔드포인트 추가
app.post('/api/llm-endpoints', (req, res) => {
  try {
    const { name, baseUrl, apiKey, defaultModel, description } = req.body;
    
    if (!name || !baseUrl) {
      return res.status(400).json({ error: 'Name and baseUrl are required' });
    }
    
    const endpointId = `llm-ep-${Date.now()}`;
    const newEndpoint = {
      id: endpointId,
      name: name.trim(),
      baseUrl: baseUrl.trim(),
      apiKey: apiKey || '',
      defaultModel: defaultModel || '',
      description: description || '',
      isDefault: false,
      createdAt: new Date().toISOString()
    };
    
    llmEndpointsData.endpoints.push(newEndpoint);
    
    // 첫 번째 엔드포인트라면 자동으로 활성화
    if (llmEndpointsData.endpoints.length === 1) {
      llmEndpointsData.activeEndpointId = endpointId;
      llmEndpointsData.defaultEndpointId = endpointId;
      newEndpoint.isDefault = true;
    }
    
    saveLlmEndpointsData();
    
    console.log(`[${new Date().toISOString()}] LLM 엔드포인트 추가 성공:`, newEndpoint.name);
    
    res.status(201).json({
      success: true,
      endpoint: newEndpoint
    });
  } catch (error) {
    console.error(`[${new Date().toISOString()}] LLM 엔드포인트 추가 오류:`, error);
    res.status(500).json({ error: 'Failed to create LLM endpoint' });
  }
});

// LLM 엔드포인트 업데이트
app.put('/api/llm-endpoints/:id', (req, res) => {
  try {
    const { id } = req.params;
    const updates = req.body;
    
    const endpointIndex = llmEndpointsData.endpoints.findIndex(ep => ep.id === id);
    if (endpointIndex === -1) {
      return res.status(404).json({ error: 'LLM endpoint not found' });
    }
    
    // 엔드포인트 정보 업데이트
    llmEndpointsData.endpoints[endpointIndex] = {
      ...llmEndpointsData.endpoints[endpointIndex],
      ...updates,
      updatedAt: new Date().toISOString()
    };
    
    saveLlmEndpointsData();
    
    console.log(`[${new Date().toISOString()}] LLM 엔드포인트 업데이트 성공:`, id);
    
    res.json({
      success: true,
      endpoint: llmEndpointsData.endpoints[endpointIndex]
    });
  } catch (error) {
    console.error(`[${new Date().toISOString()}] LLM 엔드포인트 업데이트 오류:`, error);
    res.status(500).json({ error: 'Failed to update LLM endpoint' });
  }
});

// LLM 엔드포인트 삭제
app.delete('/api/llm-endpoints/:id', (req, res) => {
  try {
    const { id } = req.params;
    
    const endpointIndex = llmEndpointsData.endpoints.findIndex(ep => ep.id === id);
    if (endpointIndex === -1) {
      return res.status(404).json({ error: 'LLM endpoint not found' });
    }
    
    const deletedEndpoint = llmEndpointsData.endpoints[endpointIndex];
    
    // 엔드포인트 삭제
    llmEndpointsData.endpoints.splice(endpointIndex, 1);
    
    // 삭제된 엔드포인트가 활성화된 것이거나 기본값이었다면 다른 것으로 변경
    if (llmEndpointsData.activeEndpointId === id || llmEndpointsData.defaultEndpointId === id) {
      if (llmEndpointsData.endpoints.length > 0) {
        const newActiveId = llmEndpointsData.endpoints[0].id;
        llmEndpointsData.activeEndpointId = newActiveId;
        llmEndpointsData.defaultEndpointId = newActiveId;
        llmEndpointsData.endpoints[0].isDefault = true;
      } else {
        llmEndpointsData.activeEndpointId = null;
        llmEndpointsData.defaultEndpointId = null;
      }
    }
    
    saveLlmEndpointsData();
    
    console.log(`[${new Date().toISOString()}] LLM 엔드포인트 삭제 성공:`, deletedEndpoint.name);
    
    res.json({
      success: true,
      message: `LLM endpoint '${deletedEndpoint.name}' deleted successfully`
    });
  } catch (error) {
    console.error(`[${new Date().toISOString()}] LLM 엔드포인트 삭제 오류:`, error);
    res.status(500).json({ error: 'Failed to delete LLM endpoint' });
  }
});

// 활성 LLM 엔드포인트 설정
app.post('/api/llm-endpoints/:id/activate', (req, res) => {
  try {
    const { id } = req.params;
    
    const endpoint = llmEndpointsData.endpoints.find(ep => ep.id === id);
    if (!endpoint) {
      return res.status(404).json({ error: 'LLM endpoint not found' });
    }
    
    llmEndpointsData.activeEndpointId = id;
    saveLlmEndpointsData();
    
    console.log(`[${new Date().toISOString()}] 활성 LLM 엔드포인트 설정:`, endpoint.name);
    
    res.json({
      success: true,
      activeEndpointId: id
    });
  } catch (error) {
    console.error(`[${new Date().toISOString()}] 활성 LLM 엔드포인트 설정 오류:`, error);
    res.status(500).json({ error: 'Failed to set active LLM endpoint' });
  }
});

// 기본 LLM 엔드포인트 설정
app.post('/api/llm-endpoints/:id/set-default', (req, res) => {
  try {
    const { id } = req.params;
    
    const endpoint = llmEndpointsData.endpoints.find(ep => ep.id === id);
    if (!endpoint) {
      return res.status(404).json({ error: 'LLM endpoint not found' });
    }
    
    // 기존 기본값 제거
    llmEndpointsData.endpoints.forEach(ep => {
      ep.isDefault = false;
    });
    
    // 새로운 기본값 설정
    endpoint.isDefault = true;
    llmEndpointsData.defaultEndpointId = id;
    
    saveLlmEndpointsData();
    
    console.log(`[${new Date().toISOString()}] 기본 LLM 엔드포인트 설정:`, endpoint.name);
    
    res.json({
      success: true,
      defaultEndpointId: id
    });
  } catch (error) {
    console.error(`[${new Date().toISOString()}] 기본 LLM 엔드포인트 설정 오류:`, error);
    res.status(500).json({ error: 'Failed to set default LLM endpoint' });
  }
});
function renderTemplate(template = "", data = {}) {
  return template.replace(/{{(.*?)}}/g, (_, key) => {
    const trimmedKey = key.trim();
    return data[trimmedKey] !== undefined ? data[trimmedKey] : '';
  });
}

// Data persistence
function saveData() {
  try {
    // 디렉토리가 없는 경우 생성
    const dataDir = path.dirname(dataPath);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
    
    fs.writeFileSync(dataPath, JSON.stringify(promptData, null, 2), 'utf-8');
    console.log(`[${new Date().toISOString()}] 데이터 저장 성공: ${dataPath}`);
  } catch (error) {
    console.error(`[${new Date().toISOString()}] 데이터 저장 오류:`, error);
  }
}

// LLM Endpoints data persistence
function saveLlmEndpointsData() {
  try {
    // 디렉토리가 없는 경우 생성
    const dataDir = path.dirname(llmEndpointsPath);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
    
    fs.writeFileSync(llmEndpointsPath, JSON.stringify(llmEndpointsData, null, 2), 'utf-8');
    console.log(`[${new Date().toISOString()}] LLM endpoints 데이터 저장 성공: ${llmEndpointsPath}`);
  } catch (error) {
    console.error(`[${new Date().toISOString()}] LLM endpoints 데이터 저장 오류:`, error);
  }
}

// 오치 또는 안전한 서버 리스타트
// 실제 내용만 로깅
// 로깅 준다

app.listen(PORT, () => {
  // 환경 변수 출력
  console.log(`[${new Date().toISOString()}] 환경변수 설정:`);
  console.log(` - OPENAI_BASE_URL: ${process.env.OPENAI_BASE_URL || '(미설정 - 기본값 사용)'}`);
  console.log(` - OPENAI_MODEL: ${process.env.OPENAI_MODEL || '(미설정 - 기본값 사용)'}`);
  
  console.log(`🚀 서버 실행 중: http://localhost:${PORT}`);
  console.log(`💾 데이터 저장 경로: ${dataPath}`);
  console.log(`📁 현재 저장된 태스크 수: ${Object.keys(promptData.tasks).length}`);
  console.log(`📊 현재 메모리에 로드된 프롬프트 데이터: ${JSON.stringify(promptData).length} bytes`);
  console.log('\n🎉 준비 완료! 프론트엔드에서 연결하세요.');
});