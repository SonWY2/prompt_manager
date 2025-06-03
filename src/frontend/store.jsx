import { createContext, useContext, useState, useCallback, useRef } from 'react';
import { flushSync } from 'react-dom';
import { apiUrl, fetchFromAPI } from './utils/api';

const PromptContext = createContext();

export const useStore = () => useContext(PromptContext);

export const PromptProvider = ({ children }) => {
  // localStorage에서 초기값 동기적으로 로드
  const getInitialGroups = () => {
    try {
      const savedGroups = localStorage.getItem('availableGroups');
      console.log('getInitialGroups - localStorage에서 가져온 데이터:', savedGroups);
      if (savedGroups) {
        const parsed = JSON.parse(savedGroups);
        console.log('getInitialGroups - 파싱된 그룹 데이터:', parsed);
        return parsed;
      }
    } catch (error) {
      console.error('Error loading groups from localStorage:', error);
    }
    const defaultGroups = ['기본 그룹', '마케팅', '고객 지원', '제품 개발', '기술 문서'];
    console.log('getInitialGroups - 기본 그룹 사용:', defaultGroups);
    return defaultGroups;
  };
  
  const getInitialTasks = () => {
    try {
      const savedTasks = localStorage.getItem('tasks');
      if (savedTasks) {
        return JSON.parse(savedTasks);
      }
    } catch (error) {
      console.error('Error loading tasks from localStorage:', error);
    }
    return {};
  };
  
  const getInitialCurrentTask = () => {
    // URL 기반 라우팅으로 인해 항상 null로 시작
    // App.jsx에서 URL을 처리하여 설정
    return null;
  };
  
  const [tasks, setTasks] = useState(getInitialTasks);
  const [currentTask, setCurrentTask] = useState(getInitialCurrentTask);
  const [versions, setVersions] = useState([]);
  const [currentVersion, setCurrentVersion] = useState(null);
  const [currentSystemPrompt, setCurrentSystemPrompt] = useState(''); // 현재 선택된 버전의 system prompt 내용
  const [isEditMode, setIsEditMode] = useState(true); // 편집 모드 상태 추가
  const [templateVariables, setTemplateVariables] = useState({});
  const [llmResults, setLLMResults] = useState([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [availableGroups, setAvailableGroups] = useState(getInitialGroups);
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
        console.log('서버 상태 체크 성공: connected');
        return true;
      } else {
        setServerStatus('disconnected');
        console.warn('서버 응답 오류:', response.status);
        return false;
      }
    } catch (error) {
      setServerStatus('disconnected');
      console.warn('서버 연결 실패:', error.message);
      return false;
    }
  }, []);
  
  // LLM Endpoints 관리 함수들
  const loadLlmEndpoints = useCallback(async () => {
    try {
      console.log('🔄 LLM Endpoints 로드 시작');
      
      const response = await fetch(apiUrl('/api/llm-endpoints'));
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('✅ LLM Endpoints 로드 성공:', data);
      
      setLlmEndpoints(data.endpoints || []);
      setActiveLlmEndpointId(data.activeEndpointId);
      setDefaultLlmEndpointId(data.defaultEndpointId);
      
      return data;
    } catch (error) {
      console.error('❌ LLM Endpoints 로드 실패:', error);
      // 서버 연결 실패 시 기본값 설정
      setLlmEndpoints([]);
      setActiveLlmEndpointId(null);
      setDefaultLlmEndpointId(null);
      throw error;
    }
  }, []);
  
  const addLlmEndpoint = useCallback(async (endpointData) => {
    try {
      console.log('➕ LLM Endpoint 추가 시작:', endpointData);
      
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
      console.log('✅ LLM Endpoint 추가 성공:', data.endpoint);
      
      // 상태 업데이트
      setLlmEndpoints(prev => [...prev, data.endpoint]);
      
      // 첫 번째 엔드포인트라면 자동으로 활성화
      if (data.endpoint.isDefault) {
        setActiveLlmEndpointId(data.endpoint.id);
        setDefaultLlmEndpointId(data.endpoint.id);
      }
      
      return data.endpoint;
    } catch (error) {
      console.error('❌ LLM Endpoint 추가 오류:', error);
      throw error;
    }
  }, []);
  
  const updateLlmEndpoint = useCallback(async (id, updates) => {
    try {
      console.log('✏️ LLM Endpoint 업데이트 시작:', { id, updates });
      
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
      console.log('✅ LLM Endpoint 업데이트 성공:', data.endpoint);
      
      // 상태 업데이트
      setLlmEndpoints(prev => 
        prev.map(ep => ep.id === id ? data.endpoint : ep)
      );
      
      return data.endpoint;
    } catch (error) {
      console.error('❌ LLM Endpoint 업데이트 오류:', error);
      throw error;
    }
  }, []);
  
  const deleteLlmEndpoint = useCallback(async (id) => {
    try {
      console.log('🗑️ LLM Endpoint 삭제 시작:', id);
      
      const response = await fetch(apiUrl(`/api/llm-endpoints/${id}`), {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '엔드포인트 삭제 실패');
      }
      
      const data = await response.json();
      console.log('✅ LLM Endpoint 삭제 성공:', data.message);
      
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
      console.error('❌ LLM Endpoint 삭제 오류:', error);
      throw error;
    }
  }, [activeLlmEndpointId, defaultLlmEndpointId]);
  
  const setActiveLlmEndpoint = useCallback(async (id) => {
    try {
      console.log('🎟️ 활성 LLM Endpoint 설정 시작:', id);
      
      const response = await fetch(apiUrl(`/api/llm-endpoints/${id}/activate`), {
        method: 'POST'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '활성 엔드포인트 설정 실패');
      }
      
      const data = await response.json();
      console.log('✅ 활성 LLM Endpoint 설정 성공:', data.activeEndpointId);
      
      setActiveLlmEndpointId(id);
      
      return data;
    } catch (error) {
      console.error('❌ 활성 LLM Endpoint 설정 오류:', error);
      throw error;
    }
  }, []);
  
  const setDefaultLlmEndpoint = useCallback(async (id) => {
    try {
      console.log('🏠 기본 LLM Endpoint 설정 시작:', id);
      
      const response = await fetch(apiUrl(`/api/llm-endpoints/${id}/set-default`), {
        method: 'POST'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '기본 엔드포인트 설정 실패');
      }
      
      const data = await response.json();
      console.log('✅ 기본 LLM Endpoint 설정 성공:', data.defaultEndpointId);
      
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
      console.error('❌ 기본 LLM Endpoint 설정 오류:', error);
      throw error;
    }
  }, []);
  const loadTasks = useCallback(async () => {
    try {
      // 서버에서 가져오기 시도
      try {
        const response = await fetch(apiUrl('/api/tasks'));
        const data = await response.json();
        if (data.tasks && data.tasks.length > 0) {
          const tasksMap = data.tasks.reduce((acc, task) => {
            acc[task.id] = task;
            return acc;
          }, {});
          setTasks(tasksMap);
          // 로컬 스토리지에도 저장
          localStorage.setItem('tasks', JSON.stringify(tasksMap));
          return;
        }
      } catch (error) {
        console.warn('서버에서 태스크를 불러오지 못했습니다. 로컬 저장소를 확인합니다.', error);
      }
      
      // 서버에서 데이터를 가져오지 못한 경우 이미 로드된 로컬 데이터 사용
      console.log('로컬 스토리지에서 데이터를 사용합니다.');
      
      // 초기 로드 시 기본 그룹이 localStorage에 없으면 저장
      const savedGroups = localStorage.getItem('availableGroups');
      if (!savedGroups) {
        localStorage.setItem('availableGroups', JSON.stringify(availableGroups));
      }
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  }, []);
  
  const createTask = useCallback(async (name, group = '기본 그룹') => {
    try {
      const taskId = `task-${Date.now()}`;
      console.log('태스크 생성 시작:', { taskId, name, group });
      
      // 새로운 그룹이면 availableGroups에 추가
      setAvailableGroups(prevGroups => {
        if (!prevGroups.includes(group)) {
          console.log('새로운 그룹 추가:', group);
          const newGroups = [...prevGroups, group];
          localStorage.setItem('availableGroups', JSON.stringify(newGroups));
          return newGroups;
        }
        return prevGroups;
      });
      
      try {
        // API 호출 시도
        const response = await fetch(apiUrl('/api/tasks'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ taskId, name, group })
        });
        
        if (!response.ok) {
          console.warn('서버 응답이 정상적이지 않습니다. 로컬에만 저장합니다.');
        } else {
          console.log('서버에 태스크 생성 성공');
        }
      } catch (apiError) {
        // API 호출 실패 시 로그만 남기고 계속 진행
        console.warn('API 서버에 연결할 수 없습니다. 로컬에만 저장합니다.', apiError);
      }
      
      // 서버 응답과 관계없이 로컬 상태 업데이트 진행
      setTasks(prevTasks => {
        const newTasks = {
          ...prevTasks,
          [taskId]: { id: taskId, name, group, versions: [] }
        };
        
        console.log('로컬 상태 업데이트 완료:', newTasks);
        
        // 로컬 스토리지에 저장
        localStorage.setItem('tasks', JSON.stringify(newTasks));
        
        return newTasks;
      });
      
      // setCurrentTask(taskId); // TaskActions에서 처리하도록 제거
      console.log('태스크 생성 완료:', taskId);
      
      return taskId;
    } catch (error) {
      console.error('Error creating task:', error);
      throw error;
    }
  }, []);
  
  const updateTask = useCallback(async (taskId, updates) => {
    try {
      // 서버 API 호출
      try {
        const response = await fetch(apiUrl(`/api/tasks/${taskId}`), {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates)
        });
        
        if (!response.ok) {
          console.warn('서버 태스크 업데이트 실패:', response.status, response.statusText);
        }
      } catch (apiError) {
        console.warn(`태스크 ${taskId} API 업데이트 실패:`, apiError);
        // API 실패는 무시하고 로컬 업데이트 진행
      }
      
      // 상태 업데이트
      setTasks(prevTasks => {
        const newTasks = {
          ...prevTasks,
          [taskId]: {
            ...prevTasks[taskId],
            ...updates
          }
        };
        
        // 로컬 스토리지에 저장
        localStorage.setItem('tasks', JSON.stringify(newTasks));
        
        return newTasks;
      });
      
      return { success: true };
    } catch (error) {
      console.error('Error updating task:', error);
      
      // 에러가 발생해도 강제로 로컬 업데이트 시도
      try {
        setTasks(prevTasks => {
          const newTasks = {
            ...prevTasks,
            [taskId]: {
              ...prevTasks[taskId],
              ...updates
            }
          };
          
          // 로컬 스토리지에 저장
          localStorage.setItem('tasks', JSON.stringify(newTasks));
          
          return newTasks;
        });
        
        return { success: true };
      } catch (updateError) {
        console.error('Forced update failed:', updateError);
        throw error; // 최종적으로 실패한 경우만 오류 반환
      }
    }
  }, []);
  
  // 태스크 삭제 기능
  const deleteTask = useCallback(async (taskId) => {
    try {
      console.log('태스크 삭제 시작:', taskId);
      
      // 즉시 UI 업데이트 (낙관적 업데이트) - 먼저 상태 업데이트
      const deletedTask = tasks[taskId]; // 로백을 위해 보관
      
      setTasks(prevTasks => {
        const { [taskId]: deleted, ...newTasks } = prevTasks;
        
        // 로컬 스토리지에 즉시 저장
        localStorage.setItem('tasks', JSON.stringify(newTasks));
        
        console.log('로컬 상태에서 태스크 삭제 완료:', taskId);
        
        return newTasks;
      });
      
      // 삭제된 태스크가 현재 선택된 태스크인 경우 초기화
      if (currentTask === taskId) {
        // 내부 상태 직접 업데이트 (래퍼 함수 사용 방지)
        setCurrentTask(null);
        setCurrentVersion(null);
        setVersions([]);
        setTemplateVariables([]);
        // URL 기반 라우팅에서 App.jsx가 URL과 함께 처리하므로 localStorage 제거 삭제
        console.log('현재 선택된 태스크가 삭제되어 상태 초기화');
      }
      
      // 백그라운드에서 서버 동기화 수행
      try {
        const response = await fetch(apiUrl(`/api/tasks/${taskId}`), {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
          console.warn('서버 태스크 삭제 실패:', response.status, response.statusText);
          return { 
            success: true, 
            serverSync: false,
            message: '태스크가 로컬에서 삭제되었습니다. (서버 동기화 실패)' 
          };
        } else {
          console.log('서버에서 태스크 삭제 성공:', taskId);
          return { 
            success: true, 
            serverSync: true,
            message: '태스크가 성공적으로 삭제되었습니다.' 
          };
        }
      } catch (apiError) {
        console.warn(`태스크 ${taskId} API 삭제 실패:`, apiError);
        return { 
          success: true, 
          serverSync: false,
          message: '태스크가 로컬에서 삭제되었습니다. (서버 연결 실패)' 
        };
      }
      
    } catch (error) {
      console.error('Error deleting task:', error);
      
      // 예상치 못한 오류 시 로컬 상태 롤백 (옵션)
      // 현재는 이미 UI가 업데이트되었으므로 롤백하지 않음
      
      throw error;
    }
  }, [currentTask, tasks]);
  
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
        console.warn(`❌ 템플릿 변수 API 오류: ${response.status} ${response.statusText}`);
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
        console.log('✅ 템플릿 변수 로드 성공:', taskId, data.variables?.length || 0, '개');
      } catch (parseError) {
        console.warn('❌ 템플릿 변수 응답의 JSON 파싱 실패:', parseError, '응답 내용:', text);
        setTemplateVariables([]);
      }
      
    } catch (error) {
      // 타임아웃이나 연결 오류 시 서버 상태 업데이트
      if (error.name === 'TimeoutError' || error.code === 'ECONNREFUSED') {
        console.warn('🔌 서버 연결 실패로 서버 상태를 disconnected로 업데이트');
        setServerStatus('disconnected');
      }
      console.warn('❌ 서버에서 템플릿 변수를 불러올 수 없습니다. 빈 상태로 설정합니다.', error);
      setTemplateVariables([]);
    } finally {
      // 로딩 상태 해제 (useRef 사용)
      templateVariableLoadingRef.current.delete(taskId);
      console.log('🏁 템플릿 변수 로드 완료:', taskId);
    }
  }, [serverStatus]); // 의존성 최소화
  
  // 버전 관리
  const versionsLoadingRef = useRef(new Set()); // useRef로 변경
  
  const loadVersions = useCallback(async (taskId) => {
    console.log('🔄 loadVersions 호출:', taskId);
    
    // 중복 호출 방지 (useRef 사용)
    if (versionsLoadingRef.current.has(taskId)) {
      console.log('⏸️ 버전 로드 이미 진행 중:', taskId);
      return;
    }
    
    // 로딩 상태 설정
    versionsLoadingRef.current.add(taskId);
    
    try {
      console.log(`📦 태스크의 버전 불러오는 중: ${taskId}`);
      
      let versionsToUse = [];
      let useServerData = false;
      
      // 서버가 연결된 경우에만 서버에서 데이터 가져오기 시도
      if (serverStatus === 'connected') {
        try {
          const data = await fetchFromAPI(apiUrl(`/api/tasks/${taskId}/versions`));
          const serverVersions = data.versions || [];
          
          console.log(`📊 서버에서 불러온 버전 수: ${serverVersions.length}`);
          console.log('🏷️ 서버 버전 ID 목록:', serverVersions.map(v => v.id));
          
          versionsToUse = serverVersions;
          useServerData = true;
          
        } catch (apiError) {
          console.warn('❌ 서버에서 버전을 불러올 수 없습니다. 로컬 데이터를 사용합니다.', apiError);
        }
      } else {
        console.log('🔌 서버가 연결되지 않아 로컬 데이터만 사용합니다.');
      }
      
      // 서버 데이터를 가져오지 못한 경우 로컬 데이터 사용
      if (!useServerData) {
        // localStorage에서 직접 데이터 읽기
        try {
          const savedTasks = localStorage.getItem('tasks');
          if (savedTasks) {
            const tasksData = JSON.parse(savedTasks);
            const task = tasksData[taskId];
            if (task && task.versions && task.versions.length > 0) {
              versionsToUse = task.versions;
              console.log(`💾 로컬에서 불러온 버전 수: ${versionsToUse.length}`);
              console.log('🏷️ 로컬 버전 ID 목록:', versionsToUse.map(v => v.id));
            }
          }
        } catch (storageError) {
          console.warn('❌ localStorage에서 데이터를 읽을 수 없습니다:', storageError);
        }
        
        if (versionsToUse.length === 0) {
          console.log('🙅 로컬에도 버전이 없습니다.');
        }
      }
      
      // 버전 목록 설정
      setVersions(versionsToUse);
      
      // 현재 버전 및 편집 모드 설정
      if (versionsToUse.length > 0) {
        setCurrentVersion(versionsToUse[0].id);
        setCurrentSystemPrompt(versionsToUse[0].system_prompt || 'You are a helpful assistant.'); // system prompt 설정
        setIsEditMode(false); // 버전 로드 시 기본적으로 읽기 모드로 설정
        console.log(`✅ 현재 버전 설정: ${versionsToUse[0].id}`);
      } else {
        setCurrentVersion(null);
        setCurrentSystemPrompt('You are a helpful assistant.'); // 기본 system prompt 설정
        setIsEditMode(true); // 버전이 없으면 편집 모드로 설정
        console.log('✏️ 버전이 없어 편집 모드로 설정');
      }
      
      // 서버 데이터를 사용한 경우 로컬 스토리지도 동기화
      if (useServerData && versionsToUse.length > 0) {
        try {
          const savedTasks = localStorage.getItem('tasks');
          const tasksData = savedTasks ? JSON.parse(savedTasks) : {};
          const task = tasksData[taskId];
          
          if (task) {
            const updatedTask = {
              ...task,
              versions: versionsToUse
            };
            
            const updatedTasks = {
              ...tasksData,
              [taskId]: updatedTask
            };
            
            localStorage.setItem('tasks', JSON.stringify(updatedTasks));
            
            // 메모리 상태도 업데이트
            setTasks(updatedTasks);
          }
        } catch (storageError) {
          console.warn('❌ localStorage 동기화 실패:', storageError);
        }
      }
      
      // 템플릿 변수 로드 (버전이 있고 이미 로딩 중이 아닌 경우에만)
      if (versionsToUse.length > 0 && !templateVariableLoadingRef.current.has(taskId)) {
        console.log('🔎 템플릿 변수 로드 예약:', taskId);
        // 더 긴 디바운싱 적용
        setTimeout(() => {
          // 다시 한 번 체크해서 중복 호출 방지
          if (!templateVariableLoadingRef.current.has(taskId)) {
            loadTemplateVariables(taskId);
          }
        }, 500); // 500ms로 더 늘림
      } else {
        console.log('🙅 버전이 없거나 이미 로딩 중이어서 템플릿 변수 로드를 건너뛱니다:', { 
          taskId, 
          versionsCount: versionsToUse.length,
          alreadyLoading: templateVariableLoadingRef.current.has(taskId)
        });
        setTemplateVariables([]);
      }
      
    } catch (error) {
      console.error('❌ Error loading versions:', error);
      // 최종 fallback: 빈 상태로 설정
      setVersions([]);
      setCurrentVersion(null);
      setIsEditMode(true);
    } finally {
      // 로딩 상태 해제 (useRef 사용)
      versionsLoadingRef.current.delete(taskId);
      console.log('🏁 버전 로드 완료:', taskId);
    }
  }, [serverStatus]); // 의존성 최소화 - tasks, loadTemplateVariables 제거
  
  const addVersion = useCallback(async (taskId, versionId, content, systemPromptContent = 'You are a helpful assistant.', description = '', name = '') => {
    try {
      // 실제 버전 이름 처리: 비어있으면 자동 생성되는 명명 규칙 적용
      const displayName = name.trim() || `버전 ${new Date().toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })}`.replace(/\. /g, '.');
      
      console.log(`버전 추가 시작: ID=${versionId}, 이름=${displayName}`);
      console.log('버전 내용:', { taskId, versionId, content: content.substring(0, 100) + '...', description, name: displayName });
      
      // 서버에 버전 추가 요청
      try {
        const response = await fetch(apiUrl(`/api/tasks/${taskId}/versions`), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            versionId,
            content,
            system_prompt: systemPromptContent,
            description,
            name: displayName
          })
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('서버 버전 추가 실패:', response.status, response.statusText, errorText);
          throw new Error(`서버 오류: ${response.status} ${response.statusText}`);
        }
        
        console.log('서버에 버전 추가 성공');
      } catch (apiError) {
        console.error('API 호출 실패:', apiError);
        // 서버 실패 시에도 로컬 상태는 업데이트 (낙관적 업데이트)
        console.warn('서버 연결 실패, 로컬에만 저장합니다.');
      }
      
      // 로컬 상태 업데이트
      const newVersion = {
        id: versionId,
        content,
        system_prompt: systemPromptContent,
        description,
        name: displayName,
        createdAt: new Date().toISOString(),
        results: []
      };
      
      // 버전 목록 업데이트
      setVersions(prev => {
        const newVersions = [newVersion, ...prev];
        console.log('버전 목록 업데이트:', newVersions.map(v => ({ id: v.id, name: v.name })));
        return newVersions;
      });
      
      // 태스크 내 버전 목록도 동기화
      setTasks(prev => {
        const task = prev[taskId];
        if (!task) return prev;
        
        const updatedTask = {
          ...task,
          versions: [newVersion, ...(task.versions || [])]
        };
        
        const updatedTasks = {
          ...prev,
          [taskId]: updatedTask
        };
        
        // 로컬 스토리지에 저장
        localStorage.setItem('tasks', JSON.stringify(updatedTasks));
        
        return updatedTasks;
      });
      
      // 새로 생성된 버전을 현재 버전으로 설정
      setCurrentVersion(versionId);
      setCurrentSystemPrompt(systemPromptContent); // 새 버전의 system prompt 설정
      setIsEditMode(false); // 새 버전 생성 후 읽기 모드로 전환
      
      console.log('버전 추가 완료:', versionId);
      return { success: true, versionId, name: displayName };
    } catch (error) {
      console.error('Error adding version:', error);
      throw error; // 에러를 상위로 전파
    }
  }, []);
  
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
  
  const updatePromptContent = useCallback((content) => {
    setVersions(prev => 
      prev.map(v => 
        v.id === currentVersion 
          ? { ...v, content, isDirty: true }
          : v
      )
    );
  }, [currentVersion]);
  
  // System Prompt 내용 업데이트 함수
  const updateSystemPromptContent = useCallback((systemPromptContent) => {
    setCurrentSystemPrompt(systemPromptContent);
    setVersions(prev => 
      prev.map(v => 
        v.id === currentVersion 
          ? { ...v, system_prompt: systemPromptContent, isDirty: true }
          : v
      )
    );
  }, [currentVersion]);
  
  const savePromptContent = useCallback(async (taskId, versionId, content, systemPromptContent, versionInfo = {}) => {
    try {
      // 서버 API를 호출하여 버전 내용 저장
      await fetch(apiUrl(`/api/tasks/${taskId}/versions/${versionId}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, system_prompt: systemPromptContent, ...versionInfo })
      });
      
      // 상태 업데이트
      setVersions(prev => 
        prev.map(v => 
          v.id === versionId
            ? { 
                ...v, 
                content, 
                system_prompt: systemPromptContent,
                name: versionInfo.name || v.name,
                description: versionInfo.description || v.description,
                isDirty: false 
              }
            : v
        )
      );
      
      // 태스크 내 버전 업데이트
      setTasks(prev => {
        const task = prev[taskId];
        if (!task) return prev;
        
        const updatedVersions = task.versions.map(v => 
          v.id === versionId ? { 
            ...v, 
            content,
            system_prompt: systemPromptContent,
            name: versionInfo.name || v.name,
            description: versionInfo.description || v.description, 
          } : v
        );
        
        return {
          ...prev,
          [taskId]: {
            ...task,
            versions: updatedVersions
          }
        };
      });
      
      setIsEditMode(false); // 저장 후 읽기 모드로 전환
    } catch (error) {
      console.error('Error saving prompt content:', error);
    }
  }, []);
  
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
  
  // 버전 삭제 - 로컬 모드 지원 (서버 없이도 작동)
  const deleteVersion = useCallback(async (taskId, versionId) => {
    try {
      console.log('버전 삭제 요청:', { taskId, versionId });
      
      // 먼저 로컬에서 버전 존재 확인
      const localVersion = versions.find(v => v.id === versionId);
      if (!localVersion) {
        console.error(`삭제할 버전이 로컬에 존재하지 않습니다: ${versionId}`);
        throw new Error('삭제할 버전을 찾을 수 없습니다.');
      }
      
      console.log('삭제할 버전 확인됨 (로컬):', localVersion);
      
      // 서버 연결 시도 (선택적) - 실패해도 로컬 삭제는 진행
      let serverDeleteSuccess = false;
      try {
        console.log('서버 삭제 시도 중...');
        
        const apiEndpoint = `/api/tasks/${taskId}/versions/${versionId}`;
        const fullUrl = apiUrl(apiEndpoint);
        
        const response = await fetch(fullUrl, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          signal: AbortSignal.timeout(5000) // 5초 타임아웃으로 단축
        });
        
        if (response.ok) {
          const result = await response.json();
          console.log('서버 삭제 성공:', result);
          serverDeleteSuccess = true;
        } else {
          console.warn(`서버 삭제 실패: ${response.status} ${response.statusText}`);
        }
      } catch (serverError) {
        console.warn('서버 삭제 실패 (로컬 삭제는 계속 진행):', serverError.message);
      }
      
      // 로컬 상태 업데이트 (서버 성공 여부와 관계없이 항상 실행)
      console.log('로컬 상태 업데이트 시작...');
      
      // 버전 목록에서 제거
      setVersions(prev => {
        const filtered = prev.filter(v => v.id !== versionId);
        console.log(`버전 목록 업데이트: ${prev.length} -> ${filtered.length}`);
        return filtered;
      });
      
      // 현재 선택된 버전이 삭제된 경우 변경
      if (currentVersion === versionId) {
        console.log('현재 선택된 버전이 삭제되었습니다. 다른 버전 선택');
        
        const remainingVersions = versions.filter(v => v.id !== versionId);
        if (remainingVersions.length > 0) {
          console.log('다음 버전으로 선택:', remainingVersions[0].id);
          setCurrentVersion(remainingVersions[0].id);
          setCurrentSystemPrompt(remainingVersions[0].system_prompt || 'You are a helpful assistant.');
        } else {
          console.log('버전이 더 이상 없습니다.');
          setCurrentVersion(null);
          setCurrentSystemPrompt('You are a helpful assistant.');
        }
      }
      
      // 태스크 데이터에서도 버전 제거
      setTasks(prev => {
        const task = prev[taskId];
        if (!task) {
          console.log('태스크를 찾을 수 없습니다:', taskId);
          return prev;
        }
        
        const updatedTask = {
          ...task,
          versions: (task.versions || []).filter(v => v.id !== versionId)
        };
        
        console.log(`태스크 업데이트: ${task.versions?.length || 0} -> ${updatedTask.versions.length} 버전`);
        
        const updatedTasks = {
          ...prev,
          [taskId]: updatedTask
        };
        
        // 로컬 스토리지에 저장
        try {
          localStorage.setItem('tasks', JSON.stringify(updatedTasks));
          console.log('로컬 스토리지 저장 성공');
        } catch (storageError) {
          console.error('로컬 스토리지 저장 실패:', storageError);
        }
        
        return updatedTasks;
      });
      
      console.log('로컬 버전 삭제 완료');
      
      // 상태 새로고침 (선택적)
      setTimeout(() => {
        console.log('버전 목록 새로고침...');
        loadVersions(taskId);
      }, 300);
      
      // 결과 반환
      return {
        success: true,
        serverSync: serverDeleteSuccess,
        message: serverDeleteSuccess 
          ? '버전이 성공적으로 삭제되었습니다.' 
          : '버전이 로컬에서 삭제되었습니다. (서버 동기화 실패)'
      };
      
    } catch (error) {
      console.error('버전 삭제 오류:', error);
      throw error;
    }
  }, [currentVersion, versions, loadVersions, apiUrl]);
  
  const updateVariables = useCallback(async (taskId, variables) => {
    try {
      await fetch(apiUrl(`/api/templates/${taskId}/variables`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ variables })
      });
      setTemplateVariables(variables);
    } catch (error) {
      console.error('Error updating variables:', error);
    }
  }, []);
  
  const extractVariables = useCallback((content) => {
    const matches = content.match(/{{(.*?)}}/g) || [];
    return matches.map(match => match.slice(2, -2).trim());
  }, []);
  
  const renderPrompt = useCallback((template, variables) => {
    return template.replace(/{{(.*?)}}/g, (_, key) => {
      const trimmedKey = key.trim();
      return variables[trimmedKey] !== undefined ? variables[trimmedKey] : `{{${trimmedKey}}}`;
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
      
      // 결과 추가
      setLLMResults(prev => [data.result, ...prev]);
      
      // 버전에 결과 추가
      setVersions(prev => {
        return prev.map(v => {
          if (v.id === versionId) {
            const results = Array.isArray(v.results) ? v.results : [];
            return {
              ...v,
              results: [
                { 
                  inputData, 
                  output: data.result,
                  timestamp: new Date().toISOString()
                },
                ...results
              ]
            };
          }
          return v;
        });
      });
      
      return data.result;
    } catch (error) {
      console.error('Error calling LLM:', error);
      throw error;
    }
  }, [llmEndpoints, activeLlmEndpointId]);
  
  const getVersionResults = useCallback((taskId, versionId) => {
    const version = versions.find(v => v.id === versionId);
    return version?.results || [];
  }, [versions]);
  
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
  
  // 그룹 추가 기능
  const addGroup = useCallback(async (groupName) => {
    try {
      if (!groupName || !groupName.trim()) {
        throw new Error('그룹 이름이 비어있습니다.');
      }
      
      const trimmedName = groupName.trim();
      
      // 함수형 업데이트로 최신 상태 참조
      return new Promise((resolve, reject) => {
        setAvailableGroups(prevGroups => {
          // 중복 체크
          if (prevGroups.includes(trimmedName)) {
            reject(new Error('이미 존재하는 그룹 이름입니다.'));
            return prevGroups; // 기존 상태 유지
          }
          
          // 새 그룹 추가
          const newGroups = [...prevGroups, trimmedName];
          
          // 로컬 스토리지에 저장
          localStorage.setItem('availableGroups', JSON.stringify(newGroups));
          
          // 성공 알림
          resolve({ success: true, message: `'${trimmedName}' 그룹이 추가되었습니다.` });
          
          return newGroups;
        });
      });
      
    } catch (error) {
      console.error('Error adding group:', error);
      throw error;
    }
  }, []);
  
  // 그룹 삭제 기능
  const deleteGroup = useCallback(async (groupName) => {
    try {
      console.log('=== 그룹 삭제 시작 ===');
      console.log('삭제할 그룹:', groupName);
      console.log('삭제 전 availableGroups:', availableGroups);
      
      // 해당 그룹에 속한 태스크 확인
      const tasksInGroup = Object.entries(tasks).filter(([_, task]) => task.group === groupName);
      console.log('그룹에 속한 태스크 수:', tasksInGroup.length);
      
      // 그룹에 속한 태스크들을 기본 그룹으로 이동
      if (tasksInGroup.length > 0) {
        const updatedTasks = { ...tasks };
        tasksInGroup.forEach(([taskId, task]) => {
          updatedTasks[taskId] = { ...task, group: '기본 그룹' };
        });
        setTasks(updatedTasks);
        localStorage.setItem('tasks', JSON.stringify(updatedTasks));
        console.log('태스크들을 기본 그룹으로 이동 완료');
      }
      
      // availableGroups에서 즉시 삭제
      setAvailableGroups(prevGroups => {
        const newGroups = prevGroups.filter(group => group !== groupName);
        console.log('새로운 그룹 목록:', newGroups);
        
        // 로컬 스토리지에 즉시 저장
        localStorage.setItem('availableGroups', JSON.stringify(newGroups));
        
        return newGroups;
      });
      
      // 서버 API 호출
      try {
        const response = await fetch(apiUrl('/api/groups/' + encodeURIComponent(groupName)), {
          method: 'DELETE'
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('서버 그룹 삭제 성공:', data);
        } else {
          console.warn('서버 그룹 삭제 실패:', response.status, response.statusText);
        }
      } catch (apiError) {
        console.warn('API 서버에 연결할 수 없습니다. 로컬에만 저장합니다.', apiError);
      }
      
      console.log('=== 그룹 삭제 완료 ===');
      return { success: true, message: `'${groupName}' 그룹이 삭제되었습니다.` };
    } catch (error) {
      console.error('Error deleting group:', error);
      
      // 에러가 발생해도 강제로 삭제 시도
      setAvailableGroups(prevGroups => {
        const newGroups = prevGroups.filter(group => group !== groupName);
        localStorage.setItem('availableGroups', JSON.stringify(newGroups));
        return newGroups;
      });
      
      return { success: false, message: `오류가 발생했지만 '${groupName}' 그룹이 삭제되었습니다.` };
    }
  }, [tasks, availableGroups]);
  
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
      availableGroups,
      serverStatus, // 서버 상태 추가
      setAvailableGroups,
      
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
      updateTask,
      deleteTask,
      setCurrentTask: (taskId) => {
        console.log('currentTask 설정:', taskId);
        setCurrentTask(taskId);
        // URL 기반 라우팅에서 App.jsx가 URL과 함께 관리하므로 localStorage 저장 제거
      },
      loadVersions,
      addVersion,
      setCurrentVersion,
      selectVersion,
      setIsEditMode,
      updatePromptContent,
      updateSystemPromptContent, // System Prompt 업데이트 함수 추가
      savePromptContent,
      deleteVersion,
      getVersionDetail,
      loadTemplateVariables,
      updateVariables,
      extractVariables,
      renderPrompt,
      callLLM,
      getVersionResults,
      compareVersions,
      toggleDarkMode,
      deleteGroup,
      addGroup,
      
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