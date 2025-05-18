

// 환경 변수 로드
require('dotenv').config();

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

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

// 요청 로깅 미들웨어
app.use((req, res, next) => {
  const startTime = Date.now();
  console.log(`[${new Date().toISOString()}] => ${req.method} ${req.originalUrl} 요청 시작`);
  console.log(`요청 파라미터:`, req.params);
  console.log(`요청 쿼리:`, req.query);
  
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
  
  // 응답 메서드 오버라이드
  res.send = function() {
    const duration = Date.now() - startTime;
    console.log(`[${new Date().toISOString()}] <= ${req.method} ${req.originalUrl} 응답 완료 (${currentStatus}) - ${duration}ms`);
    return originalSend.apply(this, arguments);
  };
  
  res.json = function() {
    const duration = Date.now() - startTime;
    console.log(`[${new Date().toISOString()}] <= ${req.method} ${req.originalUrl} JSON 응답 완료 (${currentStatus}) - ${duration}ms`);
    return originalJson.apply(this, arguments);
  };
  
  next();
});

// In-memory database
let promptData = {
  tasks: {},
  versionHistory: {}
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

// API Endpoints
// 1. Task Management
app.get('/api/tasks', (req, res) => {
  res.json({ 
    tasks: Object.entries(promptData.tasks).map(([id, task]) => ({
      id,
      name: task.name,
      group: task.group || '기본 그룹',
      versions: task.versions || []
    }))
  });
});

app.post('/api/tasks', (req, res) => {
  const { taskId, name, group } = req.body;
  promptData.tasks[taskId] = { 
    name, 
    group: group || '기본 그룹', 
    versions: [] 
  };
  saveData();
  res.status(201).json({ 
    success: true,
    task: {
      id: taskId,
      name,
      group: group || '기본 그룹',
      versions: []
    }
  });
});

// 새로 추가: 태스크 업데이트 API
app.put('/api/tasks/:taskId', (req, res) => {
  const { taskId } = req.params;
  const updates = req.body;
  
  if (!promptData.tasks[taskId]) {
    return res.status(404).json({ error: 'Task not found' });
  }
  
  // 태스크 정보 업데이트
  promptData.tasks[taskId] = {
    ...promptData.tasks[taskId],
    ...updates
  };
  
  saveData();
  res.json({ 
    success: true,
    task: {
      id: taskId,
      ...promptData.tasks[taskId]
    }
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
  const { versionId, content, description, name } = req.body;
  
  console.log(`[${new Date().toISOString()}] 버전 생성 요청:`, {
    taskId,
    versionId,
    name,
    description: description?.substring(0, 30) + (description?.length > 30 ? '...' : ''),
    contentLength: content?.length || 0
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
  const { content, name, description } = req.body;
  
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
    name: name !== undefined ? name : promptData.tasks[taskId].versions[versionIndex].name,
    description: description !== undefined ? description : promptData.tasks[taskId].versions[versionIndex].description,
    updatedAt: new Date().toISOString()
  };
  
  saveData();
  res.json({ success: true });
});



// 버전 삭제 API - 출력 기록 추가
app.delete('/api/tasks/:taskId/versions/:versionId', (req, res) => {
  const { taskId, versionId } = req.params;
  console.log(`[${new Date().toISOString()}] 버전 삭제 요청:`, { taskId, versionId });
  console.log(`DELETE 요청 URL: ${req.originalUrl}`);
  console.log(`DELETE 요청 파라미터: ${JSON.stringify(req.params)}`);
  
  // 전체 데이터 로깅
  console.log('=== 버전 삭제 디버깅 정보 ===');
  console.log(`요청 경로: ${req.method} ${req.originalUrl}`);
  console.log(`요청 파라미터: taskId=${taskId}, versionId=${versionId}`);
  console.log(`태스크 ID 유형: ${typeof taskId}, 버전 ID 유형: ${typeof versionId}`);
  console.log(`태스크 ID 값: "${taskId}", 버전 ID 값: "${versionId}"`);
  console.log(`요청 헤더:`, req.headers);
  
  // 파라미터 유효성 검사
  if (!taskId || !versionId) {
    console.log('오류: 태스크 ID 또는 버전 ID가 없습니다!');
    return res.status(400).json({ error: 'Task ID and Version ID are required', params: { taskId, versionId } });
  }
  
  // 태스크 체크
  if (!promptData.tasks) {
    console.log('오류: tasks 객체가 없습니다!');
    return res.status(500).json({ error: 'Internal server error: tasks object is undefined' });
  }
  
  if (!promptData.tasks[taskId]) {
    console.log(`오류: 태스크를 찾을 수 없습니다. 태스크 ID: ${taskId}`);
    console.log('전체 태스크 목록:', Object.keys(promptData.tasks));
    return res.status(404).json({ error: 'Task not found', taskId });
  }
  
  // 태스크 확인 성공
  console.log(`태스크 찾음: ${taskId}, 태스크 이름: ${promptData.tasks[taskId].name}`);
  
  // 버전 체크
  if (!promptData.tasks[taskId].versions) {
    console.log(`오류: 태스크에 versions 객체가 없습니다!`);
    return res.status(500).json({ error: 'Internal server error: versions array is undefined' });
  }
  
  console.log(`버전 개수: ${promptData.tasks[taskId].versions.length}`);
  console.log('버전 ID 목록:', promptData.tasks[taskId].versions.map(v => v.id));
  
  const versionIndex = promptData.tasks[taskId].versions.findIndex(v => v.id === versionId);
  if (versionIndex === -1) {
    console.log(`오류: 버전을 찾을 수 없습니다. 버전 ID: ${versionId}`);
    return res.status(404).json({ 
      error: 'Version not found', 
      versionId,
      availableVersions: promptData.tasks[taskId].versions.map(v => ({ id: v.id, name: v.name }))
    });
  }
  
  // 버전 확인 성공
  console.log(`버전 찾음: ${versionId}, 인덱스: ${versionIndex}`);
  console.log(`삭제 전 버전 수: ${promptData.tasks[taskId].versions.length}`);
  
  // 버전 삭제 전 래퍼런스 보관
  const deletedVersion = promptData.tasks[taskId].versions[versionIndex];
  console.log(`삭제될 버전 정보:`, deletedVersion);
  
  // 버전 삭제
  promptData.tasks[taskId].versions.splice(versionIndex, 1);
  
  console.log(`삭제 후 버전 수: ${promptData.tasks[taskId].versions.length}`);
  console.log('=== 디버깅 정보 끝 ===\n');
  
  // 데이터 저장
  saveData();
  res.json({ 
    success: true,
    message: `버전 ${versionId} 삭제 성공`, 
    deletedVersion: {
      id: deletedVersion.id,
      name: deletedVersion.name
    }
  });
  console.log(`[${new Date().toISOString()}] 버전 삭제 성공:`, { taskId, versionId });
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
  const { taskId, versionId, inputData } = req.body;
  
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
  
  try {
    // Store the LLM result
    const result = await callLLM(renderedPrompt);
    
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

// Template rendering function
function renderTemplate(template = "", data = {}) {
  return template.replace(/{{(.*?)}}/g, (_, key) => {
    const trimmedKey = key.trim();
    return data[trimmedKey] !== undefined ? data[trimmedKey] : '';
  });
}

// LLM API 호출 함수 (OpenAI 호환 API 사용)
async function callLLM(prompt) {
  console.log(`[${new Date().toISOString()}] LLM API 호출 시작 - 길이: ${prompt.length} 문자`);
  
  try {
    // 환경변수에서 설정 값 가져오기
    const baseUrl = process.env.OPENAI_BASE_URL || 'http://localhost:8000/v1'; // 기본값
    const model = process.env.OPENAI_MODEL || 'mistralai/Mistral-7B-Instruct-v0.2'; // 기본값
    
    console.log(`[${new Date().toISOString()}] API 설정 - URL: ${baseUrl}, 모델: ${model}`);
    
    // vLLM 서버로 요청 보내기
    const response = await axios.post(`${baseUrl}/chat/completions`, {
      model: model,
      messages: [
        { role: "system", content: "You are a helpful assistant." },
        { role: "user", content: prompt }
      ],
      temperature: 0.7,
      max_tokens: 1024
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // 응답 처리
    const assistantResponse = response.data.choices[0].message.content;
    console.log(`[${new Date().toISOString()}] LLM API 호출 성공 - 응답 길이: ${assistantResponse.length} 문자`);
    
    return {
      prompt: prompt,
      response: assistantResponse,
      timestamp: new Date().toISOString(),
      model: model
    };
  } catch (error) {
    console.error(`[${new Date().toISOString()}] LLM API 호출 오류:`, error.message);
    
    // 오류 발생 시, 기본 응답 사용 (개발 모드에서 유용)
    if (process.env.NODE_ENV !== 'production') {
      console.warn(`[${new Date().toISOString()}] 개발 모드: 모의 응답 사용`);
      
      const mockResponses = [
        "프롬프트 매니저를 통해 테스트하고 있는 응답입니다. API 호출 시 오류가 발생하여 모의 응답을 사용합니다.",
        "서버 연결 오류가 발생하여 모의 응답을 생성합니다. 실제 API 호출이 가능한지 확인해 보세요.",
        "기본 모의 응답입니다. 환경변수 설정을 확인해주세요."
      ];
      
      const randomResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
      
      return {
        prompt: prompt,
        response: randomResponse + "\n\n[오류 발생] " + error.message + "\n\n입력된 프롬프트: " + prompt.substring(0, 100) + (prompt.length > 100 ? "..." : ""),
        timestamp: new Date().toISOString(),
        error: error.message
      };
    }
    
    // 실제 프로덕션 환경에서는 오류 전파
    throw new Error(`LLM API 호출 오류: ${error.message}`);
  }
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

// Start server
app.listen(PORT, () => {
  // 환경 변수 출력
  console.log(`[${new Date().toISOString()}] 환경변수 설정:`);
  console.log(` - OPENAI_BASE_URL: ${process.env.OPENAI_BASE_URL || '(미설정 - 기본값 사용)'}`);
  console.log(` - OPENAI_MODEL: ${process.env.OPENAI_MODEL || '(미설정 - 기본값 사용)'}`);
  
  console.log(`서버 실행 중: http://localhost:${PORT}`);
  console.log(`데이터 저장 경로: ${dataPath}`);
  console.log('현재 저장된 태스크 수:', Object.keys(promptData.tasks).length);
  console.log('현재 메모리에 로드된 프롬프트 데이터:', JSON.stringify(promptData).length, 'bytes');
});