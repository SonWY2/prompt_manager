import { createContext, useContext, useState, useCallback, useRef } from 'react';
import { flushSync } from 'react-dom';
import { apiUrl, fetchFromAPI } from './utils/api';

const PromptContext = createContext();

export const useStore = () => useContext(PromptContext);

export const PromptProvider = ({ children }) => {
  const getInitialCurrentTask = () => {
    // URL 기반 라우팅으로 인해 항상 null로 시작
    // App.jsx에서 URL을 처리하여 설정
    return null;
  };
  
  const [tasks, setTasks] = useState({});
  const [currentTask, setCurrentTask] = useState(getInitialCurrentTask);
  const [versions, setVersions] = useState([]);
  const [currentVersion, setCurrentVersion] = useState(null);
  const [currentSystemPrompt, setCurrentSystemPrompt] = useState(''); // 현재 선택된 버전의 system prompt 내용
  const [isEditMode, setIsEditMode] = useState(true); // 편집 모드 상태 추가
  const [templateVariables, setTemplateVariables] = useState({});
  const [llmResults, setLLMResults] = useState([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [serverStatus, setServerStatus] = useState('disconnected'); // 서버 상태 추가
  
  // LLM Endpoints 상태 추가
  const [llmEndpoints, setLlmEndpoints] = useState([]); // 저장된 모든 엔드포인트 목록
  const [activeLlmEndpointId, setActiveLlmEndpointId] = useState(null); // 현재 사용 중인 엔드포인트 ID
  const [defaultLlmEndpointId, setDefaultLlmEndpointId] = useState(null); // 기본값 엔드포인트 ID
  
  // 이력 필터링 상태 추가
  const [historyFilters, setHistoryFilters] = useState({
    versionId: null, // 특정 버전으로 필터링
    model: 'all',    // 특정 모델로 필터링 (all, gpt-4o, mistralai/Mistral-7B-Instruct-v0.2 등)
    dateRange: 'all' // 날짜 범위 필터링 (all, today, last7days, last30days 등)
  });
  
  // 이력 필터링 함수 추가
  const getFilteredResults = useCallback(() => {
    let filtered = [];
    if (!currentTask) return filtered;

    const task = tasks[currentTask];
    if (!task || !task.versions) return filtered;

    task.versions.forEach(version => {
      // 버전 필터링
      if (historyFilters.versionId && version.id !== historyFilters.versionId) {
        return;
      }

      if (version.results) {
        version.results.forEach(result => {
          // 모델 필터링
          if (historyFilters.model !== 'all' && result.output?.model !== historyFilters.model) {
            return;
          }

          // 날짜 필터링
          const resultDate = new Date(result.timestamp);
          const now = new Date();
          let passDateFilter = true;

          if (historyFilters.dateRange === 'today') {
            if (resultDate.toDateString() !== now.toDateString()) {
              passDateFilter = false;
            }
          } else if (historyFilters.dateRange === 'last7days') {
            const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            if (resultDate < sevenDaysAgo) {
              passDateFilter = false;
            }
          } else if (historyFilters.dateRange === 'last30days') {
            const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
            if (resultDate < thirtyDaysAgo) {
              passDateFilter = false;
            }
          }

          if (passDateFilter) {
            filtered.push({
              ...result,
              versionId: version.id, // 결과에 버전 ID 추가
              versionName: version.name // 결과에 버전 이름 추가
            });
          }
        });
      }
    });

    // 최신순 정렬
    return filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  }, [currentTask, tasks, historyFilters]);
  const checkServerStatus = useCallback(async () => {
    try {
      setServerStatus('checking');
      const response = await fetch(apiUrl('/api/tasks'), { 
        method: 'GET',
        signal: AbortSignal.timeout(5000) // 5초 타임아웃
      });
      
      if (response.ok) {
        setServerStatus('connected');
        return true;
      } else {
        setServerStatus('disconnected');
        return false;
      }
    } catch (error) {
      setServerStatus('disconnected');
      return false;
    }
  }, []);
  
  // LLM Endpoints 관리 함수들
  const loadLlmEndpoints = useCallback(async () => {
    try {
      
      const response = await fetch(apiUrl('/api/llm-endpoints'));
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      setLlmEndpoints(data.endpoints || []);
      setActiveLlmEndpointId(data.activeEndpointId);
      setDefaultLlmEndpointId(data.defaultEndpointId);
      
      return data;
    } catch (error) {
      console.error('Error loading LLM endpoints:', error);
      // 서버 연결 실패 시 기본값 설정
      setLlmEndpoints([]);
      setActiveLlmEndpointId(null);
      setDefaultLlmEndpointId(null);
      throw error;
    }
  }, []);
  
  const addLlmEndpoint = useCallback(async (endpointData) => {
    try {
      
      const response = await fetch(apiUrl('/api/llm-endpoints'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(endpointData)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '엔드포인트 추가 실패');
      }
      
      const data = await response.json();
      
      // 상태 업데이트
      setLlmEndpoints(prev => [...prev, data.endpoint]);
      
      // 첫 번째 엔드포인트라면 자동으로 활성화
      if (data.endpoint.isDefault) {
        setActiveLlmEndpointId(data.endpoint.id);
        setDefaultLlmEndpointId(data.endpoint.id);
      }
      
      return data.endpoint;
    } catch (error) {
      console.error('Error adding LLM endpoint:', error);
      throw error;
    }
  }, []);
  
  const updateLlmEndpoint = useCallback(async (id, updates) => {
    try {
      
      const response = await fetch(apiUrl(`/api/llm-endpoints/${id}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '엔드포인트 업데이트 실패');
      }
      
      const data = await response.json();
      
      // 상태 업데이트
      setLlmEndpoints(prev => 
        prev.map(ep => ep.id === id ? data.endpoint : ep)
      );
      
      return data.endpoint;
    } catch (error) {
      console.error('Error updating LLM endpoint:', error);
      throw error;
    }
  }, []);
  
  const deleteLlmEndpoint = useCallback(async (id) => {
    try {
      
      const response = await fetch(apiUrl(`/api/llm-endpoints/${id}`), {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '엔드포인트 삭제 실패');
      }
      
      const data = await response.json();
      
      // 상태 업데이트
      setLlmEndpoints(prev => prev.filter(ep => ep.id !== id));
      
      // 삭제된 엔드포인트가 활성화된 것이었다면 null로 설정
      if (activeLlmEndpointId === id) {
        setActiveLlmEndpointId(null);
      }
      if (defaultLlmEndpointId === id) {
        setDefaultLlmEndpointId(null);
      }
      
      return data;
    } catch (error) {
      console.error('Error deleting LLM endpoint:', error);
      throw error;
    }
  }, [activeLlmEndpointId, defaultLlmEndpointId]);
  
  const setActiveLlmEndpoint = useCallback(async (id) => {
    try {
      
      const response = await fetch(apiUrl(`/api/llm-endpoints/${id}/activate`), {
        method: 'PUT'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '활성 엔드포인트 설정 실패');
      }
      
      const data = await response.json();
      
      setActiveLlmEndpointId(id);
      
      return data;
    } catch (error) {
      console.error('Error setting active LLM endpoint:', error);
      throw error;
    }
  }, []);
  
  const setDefaultLlmEndpoint = useCallback(async (id) => {
    try {
      
      const response = await fetch(apiUrl(`/api/llm-endpoints/${id}/set-default`), {
        method: 'PUT'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '기본 엔드포인트 설정 실패');
      }
      
      const data = await response.json();
      
      setDefaultLlmEndpointId(id);
      
      // 엔드포인트 목록에서 isDefault 플래그 업데이트
      setLlmEndpoints(prev => 
        prev.map(ep => ({
          ...ep,
          isDefault: ep.id === id
        }))
      );
      
      return data;
    } catch (error) {
      console.error('Error setting default LLM endpoint:', error);
      throw error;
    }
  }, []);
  const loadTasks = useCallback(async () => {
    try {
      console.log('🔧 [DEBUG] store.jsx: loadTasks 시작');
      
      const response = await fetch(apiUrl('/api/tasks'));
      const data = await response.json();
      
      console.log('🔧 [DEBUG] store.jsx: loadTasks API 응답:', data);
      
      if (data.tasks) {
        const tasksMap = data.tasks.reduce((acc, task) => {
          // variables 필드가 없으면 빈 객체로 초기화
          if (!task.variables) {
            task.variables = {};
            console.log(`🔧 [DEBUG] store.jsx: Task ${task.id}에 variables 필드 추가`);
          }
          
          console.log(`🔧 [DEBUG] store.jsx: Task ${task.id} 로드, variables:`, task.variables);
          acc[task.id] = task;
          return acc;
        }, {});
        setTasks(tasksMap);
        console.log('🔧 [DEBUG] store.jsx: loadTasks 완료, 총', data.tasks.length, '개 Task 로드');
      }
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  }, []);
  
  const createTask = useCallback(async (name) => {
    try {
      const taskId = `task-${Date.now()}`;
      const response = await fetch(apiUrl('/api/tasks'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ taskId, name })
      });
      
      if (!response.ok) {
        throw new Error('Failed to create task on the server');
      }

      const { task } = await response.json();

      setTasks(prevTasks => ({
        ...prevTasks,
        [task.id]: task
      }));

      return task.id;
    } catch (error) {
      console.error('Error creating task:', error);
      throw error;
    }
  }, []);
  
  const deleteTask = useCallback(async (taskId) => {
    try {
      const response = await fetch(apiUrl(`/api/tasks/${taskId}`), {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete task on the server');
      }

      setTasks(prevTasks => {
        const { [taskId]: deleted, ...newTasks } = prevTasks;
        return newTasks;
      });

      if (currentTask === taskId) {
        setCurrentTask(null);
        setCurrentVersion(null);
        setVersions([]);
        setTemplateVariables([]);
      }
    } catch (error) {
      console.error('Error deleting task:', error);
      throw error;
    }
  }, [currentTask]);

  const toggleFavorite = useCallback(async (taskId) => {
    const originalTask = tasks[taskId];
    if (!originalTask) return;

    const newIsFavorite = !originalTask.isFavorite;

    // Optimistic update
    setTasks(prevTasks => ({
      ...prevTasks,
      [taskId]: { ...originalTask, isFavorite: newIsFavorite },
    }));

    try {
      const response = await fetch(apiUrl(`/api/tasks/${taskId}`), {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isFavorite: newIsFavorite }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.detail || 'Failed to update favorite status on the server');
      }

      // Final update from server response
      setTasks(prevTasks => ({
        ...prevTasks,
        [taskId]: data.task,
      }));
    } catch (error) {
      console.error('Error toggling favorite:', error);
      // Revert the optimistic update
      setTasks(prevTasks => ({
        ...prevTasks,
        [taskId]: originalTask,
      }));
      throw error;
    }
  }, [tasks]);
  
  // 템플릿 변수 관리 - loadVersions보다 먼저 정의
  const templateVariableLoadingRef = useRef(new Set()); // useRef로 변경
  
  const loadTemplateVariables = useCallback(async (taskId) => {
    console.log('🔄 loadTemplateVariables 호출:', taskId);
    
    // 중복 호출 방지 (useRef 사용)
    if (templateVariableLoadingRef.current.has(taskId)) {
      console.log('⏸️ 템플릿 변수 로드 이미 진행 중:', taskId);
      return;
    }
    
    // 서버가 연결되지 않은 경우 서버 요청 생략
    if (serverStatus !== 'connected') {
      console.log('🔌 서버가 연결되지 않아 템플릿 변수 로드를 생략합니다.');
      setTemplateVariables([]);
      return;
    }
    
    // 로딩 상태 설정
    templateVariableLoadingRef.current.add(taskId);
    
    try {
      console.log('📡 템플릿 변수 로드 시작:', taskId);
      
      const response = await fetch(apiUrl(`/api/templates/${taskId}/variables`), {
        signal: AbortSignal.timeout(3000) // 3초 타임아웃
      });
      
      // 응답 상태 확인
      if (!response.ok) {
        setTemplateVariables([]);
        return;
      }
      
      // 응답 본문이 비어있는지 확인
      const text = await response.text();
      if (!text || text.trim() === '') {
        console.warn('⚠️ 템플릿 변수 API에서 빈 응답을 받았습니다.');
        setTemplateVariables([]);
        return;
      }
      
      // JSON 파싱 시도
      try {
        const data = JSON.parse(text);
        setTemplateVariables(data.variables || []);
      } catch (parseError) {
        setTemplateVariables([]);
      }
      
    } catch (error) {
      // 타임아웃이나 연결 오류 시 서버 상태 업데이트
      if (error.name === 'TimeoutError' || error.code === 'ECONNREFUSED') {
        setServerStatus('disconnected');
      }
      console.warn('Unable to load template variables from server:', error);
      setTemplateVariables([]);
    } finally {
      // 로딩 상태 해제 (useRef 사용)
      templateVariableLoadingRef.current.delete(taskId);
    }
  }, [serverStatus]); // 의존성 최소화
  
  // 버전 관리
  const versionsLoadingRef = useRef(new Set()); // useRef로 변경
  
  const loadVersions = useCallback(async (taskId, options = {}) => {
    const { versionToSelect = null } = options;
    if (versionsLoadingRef.current.has(taskId)) {
      return;
    }
    versionsLoadingRef.current.add(taskId);

    try {
      const data = await fetchFromAPI(apiUrl(`/api/tasks/${taskId}/versions`));
      const serverVersions = data.versions || [];

      setTasks(prevTasks => ({
        ...prevTasks,
        [taskId]: {
          ...prevTasks[taskId],
          versions: serverVersions
        }
      }));

      setVersions(serverVersions); // Keep this for other components that might use it directly

      if (serverVersions.length > 0) {
        setCurrentVersion(versionToSelect);
        setCurrentSystemPrompt('You are a helpful assistant.');
        setIsEditMode(false);
        loadTemplateVariables(taskId);
      } else {
        setCurrentVersion(null);
        setCurrentSystemPrompt('You are a helpful assistant.');
        setIsEditMode(true);
        setTemplateVariables([]);
      }
    } catch (error) {
      console.error('Error loading versions:', error);
      setVersions([]);
      setCurrentVersion(null);
      setIsEditMode(true);
    } finally {
      versionsLoadingRef.current.delete(taskId);
    }
  }, [loadTemplateVariables]);
  
  const createVersion = useCallback(async (taskId, name, content, systemPrompt, description) => {
    try {
      const versionId = `v${Date.now()}`;
      const newVersion = {
        versionId: versionId, // The backend expects versionId
        name,
        content,
        system_prompt: systemPrompt,
        description,
      };

      const response = await fetch(apiUrl(`/api/tasks/${taskId}/versions`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newVersion),
      });

      if (!response.ok) {
        throw new Error('Failed to create version on the server');
      }

      // After creating, reload the versions to update the UI
      loadVersions(taskId);

    } catch (error) {
      console.error('Error creating version:', error);
    }
  }, [loadVersions]);
  
  // 버전 선택 및 편집 모드 설정
  const selectVersion = useCallback((versionId, editMode = false) => {
    setCurrentVersion(versionId);
    setIsEditMode(editMode);
    
    // 선택된 버전의 system prompt 설정
    const version = versions.find(v => v.id === versionId);
    if (version) {
      setCurrentSystemPrompt(version.system_prompt || 'You are a helpful assistant.');
    }
  }, [versions]);
  
  const updateVersion = useCallback(async (taskId, versionId, updates) => {
    try {
      const response = await fetch(apiUrl(`/api/tasks/${taskId}/versions/${versionId}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error('Failed to update version on the server');
      }

      // After a successful update, refetch the versions to ensure UI is in sync
      // Pass the current versionId to stay on the same version view
      loadVersions(taskId, { versionToSelect: versionId });

    } catch (error) {
      console.error('Error updating version:', error);
      // Optionally, show an error message to the user
    }
  }, [loadVersions]);
  
  // 버전 상세 정보 확인
  const getVersionDetail = useCallback(async (taskId, versionId) => {
    try {
      console.log(`버전 상세 정보 요청: ${taskId}/${versionId}`);
      
      // 먼저 로드된 버전 목록에서 찾기
      const localVersion = versions.find(v => v.id === versionId);
      if (localVersion) {
        console.log('로컬 버전 정보로 처리함:', localVersion);
        return localVersion;
      }
      
      // 로컬에 없으면 API로 찾기
      const result = await fetchFromAPI(apiUrl(`/api/tasks/${taskId}/versions/${versionId}`));
      return result.version;
    } catch (error) {
      console.error(`버전 상세 정보 가져오기 오류:`, error);
      return null;
    }
  }, [versions]);
  
  const deleteVersion = useCallback(async (taskId, versionId) => {
    try {
      const response = await fetch(apiUrl(`/api/tasks/${taskId}/versions/${versionId}`), {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete version on the server');
      }

      // Refetch versions for the task to update the UI
      loadVersions(taskId);

    } catch (error) {
      console.error('Error deleting version:', error);
      throw error;
    }
  }, [loadVersions]);

  const deleteHistoryItem = useCallback(async (taskId, versionId, resultTimestamp) => {
    try {
      // Optimistically update the UI
      setTasks(prevTasks => {
        const newTasks = { ...prevTasks };
        const task = newTasks[taskId];
        if (task) {
          const version = task.versions.find(v => v.id === versionId);
          if (version) {
            version.results = version.results.filter(r => r.timestamp !== resultTimestamp);
          }
        }
        return newTasks;
      });

      const response = await fetch(apiUrl(`/api/tasks/${taskId}/versions/${versionId}/results/${resultTimestamp}`), {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete history item on the server');
      }
    } catch (error) {
      console.error('Error deleting history item:', error);
      // Revert the optimistic update in case of an error
      loadVersions(taskId);
      throw error;
    }
  }, [loadVersions]);

  const initiateNewVersion = useCallback((taskId) => {
    if (!taskId) {
      console.error("Cannot initiate new version without a task ID.");
      return;
    }
    // By setting the version to a special string and forcing edit mode,
    // we can let the PromptEditor know that it should create a new version on save.
    selectVersion('new-version', true);
  }, [selectVersion]);
  
  const updateVariables = useCallback(async (taskId, variables) => {
    try {
      
      const response = await fetch(apiUrl(`/api/tasks/${taskId}/variables`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ variables })
      });
      
      if (response.ok) {
        // Task 상태의 variables도 업데이트
        setTasks(prevTasks => ({
          ...prevTasks,
          [taskId]: {
            ...prevTasks[taskId],
            variables: variables
          }
        }));
        
        setTemplateVariables(variables);
      }
    } catch (error) {
      console.error('Error updating variables:', error);
    }
  }, []);
  
  const extractVariables = useCallback((content) => {
    // 더 정확한 변수 추출을 위해 영문자, 숫자, 언더스코어, 하이픈만 허용
    const matches = content.match(/\{\{([a-zA-Z_][a-zA-Z0-9_-]*)\}\}/g) || [];
    const variables = matches.map(match => match.slice(2, -2).trim());
    return variables;
  }, []);
  
  const renderPrompt = useCallback((template, variables) => {
    return template.replace(/\{\{([a-zA-Z_][a-zA-Z0-9_-]*)\}\}/g, (match, key) => {
      const trimmedKey = key.trim();
      return variables[trimmedKey] !== undefined ? variables[trimmedKey] : match;
    });
  }, []);
  
  // LLM 통합 - 활성화된 엔드포인트 정보 사용
  const callLLM = useCallback(async (taskId, versionId, inputData, systemPromptContent) => {
    try {
      // 활성화된 엔드포인트 찾기
      const activeEndpoint = llmEndpoints.find(ep => ep.id === activeLlmEndpointId);
      
      const response = await fetch(apiUrl('/api/llm/call'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          taskId,
          versionId,
          inputData,
          system_prompt: systemPromptContent,
          // 활성화된 엔드포인트 정보 전달
          endpoint: activeEndpoint ? {
            baseUrl: activeEndpoint.baseUrl,
            apiKey: activeEndpoint.apiKey,
            defaultModel: activeEndpoint.defaultModel
          } : null
        })
      });
      
      if (!response.ok) {
        throw new Error('LLM API call failed');
      }
      
      const data = await response.json();
      
      const newResult = {
        inputData,
        output: data.result,
        timestamp: new Date().toISOString(),
        endpoint: activeEndpoint
      };

      // Update the main tasks state
      setTasks(prevTasks => {
        const newTasks = { ...prevTasks };
        const task = newTasks[taskId];
        if (task) {
          const version = task.versions.find(v => v.id === versionId);
          if (version) {
            if (!Array.isArray(version.results)) {
              version.results = [];
            }
            version.results.unshift(newResult);
          }
        }
        return newTasks;
      });
      
      // Also update the separate versions state for any components that might still rely on it
      setVersions(prev => prev.map(v => v.id === versionId ? { ...v, results: [newResult, ...(v.results || [])] } : v));
      
      return data.result;
    } catch (error) {
      console.error('Error calling LLM:', error);
      throw error;
    }
  }, [llmEndpoints, activeLlmEndpointId]);
  
  const getVersionResults = useCallback((taskId, versionId) => {
    if (!taskId || !versionId || !tasks[taskId]) {
      return [];
    }
    const task = tasks[taskId];
    const version = task.versions?.find(v => v.id === versionId);
    return version?.results || [];
  }, [tasks]);
  
  const compareVersions = useCallback(async (taskId, version1, version2) => {
    try {
      const response = await fetch(apiUrl(`/api/compare?taskId=${taskId}&version1=${version1}&version2=${version2}`));
      const data = await response.json();
      return data.diff;
    } catch (error) {
      console.error('Error comparing versions:', error);
      return null;
    }
  }, []);
  
  
  // 테마 설정
  const toggleDarkMode = useCallback(() => {
    setIsDarkMode(prev => {
      const newMode = !prev;
      document.documentElement.classList.toggle('dark', newMode);
      return newMode;
    });
  }, []);
  
  return (
    <PromptContext.Provider value={{
      // 상태
      tasks,
      currentTask,
      versions,
      currentVersion,
      currentSystemPrompt, // 현재 선택된 버전의 system prompt 상태 추가
      isEditMode,
      templateVariables,
      llmResults,
      isDarkMode,
      serverStatus, // 서버 상태 추가
      
      // LLM Endpoints 상태 추가
      llmEndpoints,
      activeLlmEndpointId,
      defaultLlmEndpointId,
      
      // 이력 필터링 상태 및 함수 추가
      historyFilters,
      setHistoryFilters,
      getFilteredResults,
      
      // 함수
      loadTasks,
      checkServerStatus, // 서버 상태 체크 함수 추가
      createTask,
      deleteTask,
      toggleFavorite,
      setCurrentTask: (taskId) => {
        setCurrentTask(taskId);
        // URL 기반 라우팅에서 App.jsx가 URL과 함께 관리하므로 localStorage 저장 제거
      },
      loadVersions,
      createVersion,
      setCurrentVersion,
      selectVersion,
      setIsEditMode,
      updateVersion,
      deleteVersion,
      deleteHistoryItem,
      initiateNewVersion, // Add this line
      getVersionDetail,
      loadTemplateVariables,
      updateVariables,
      extractVariables,
      renderPrompt,
      callLLM,
      getVersionResults,
      compareVersions,
      toggleDarkMode,
      
      // LLM Endpoints 관리 함수 추가
      loadLlmEndpoints,
      addLlmEndpoint,
      updateLlmEndpoint,
      deleteLlmEndpoint,
      setActiveLlmEndpoint,
      setDefaultLlmEndpoint
    }}>
      {children}
    </PromptContext.Provider>
  );
};

export default PromptContext;