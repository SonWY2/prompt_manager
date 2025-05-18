import { createContext, useContext, useState, useCallback } from 'react';
import { apiUrl, fetchFromAPI } from './utils/api';

const PromptContext = createContext();

export const useStore = () => useContext(PromptContext);

export const PromptProvider = ({ children }) => {
  const [tasks, setTasks] = useState({});
  const [currentTask, setCurrentTask] = useState(null);
  const [versions, setVersions] = useState([]);
  const [currentVersion, setCurrentVersion] = useState(null);
  const [isEditMode, setIsEditMode] = useState(true); // 편집 모드 상태 추가
  const [templateVariables, setTemplateVariables] = useState({});
  const [llmResults, setLLMResults] = useState([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  
  // 태스크 관리
  const loadTasks = useCallback(async () => {
    try {
      const response = await fetch(apiUrl('/api/tasks'));
      const data = await response.json();
      if (data.tasks && data.tasks.length > 0) {
        const tasksMap = data.tasks.reduce((acc, task) => {
          acc[task.id] = task;
          return acc;
        }, {});
        setTasks(tasksMap);
      }
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  }, []);
  
  const createTask = useCallback(async (name, group = '기본 그룹') => {
    try {
      const taskId = `task-${Date.now()}`;
      const response = await fetch(apiUrl('/api/tasks'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ taskId, name, group })
      });
      
      if (!response.ok) {
        throw new Error('Failed to create task');
      }
      
      // 상태 업데이트
      setTasks(prev => ({
        ...prev,
        [taskId]: { id: taskId, name, group, versions: [] }
      }));
      setCurrentTask(taskId);
      
      return taskId;
    } catch (error) {
      console.error('Error creating task:', error);
      throw error;
    }
  }, []);
  
  const updateTask = useCallback(async (taskId, updates) => {
    try {
      // 서버 API 호출 (아직 구현되지 않음)
      /*
      await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      */
      
      // 상태 업데이트
      setTasks(prev => ({
        ...prev,
        [taskId]: {
          ...prev[taskId],
          ...updates
        }
      }));
    } catch (error) {
      console.error('Error updating task:', error);
      throw error;
    }
  }, []);
  
  // 버전 관리
  const loadVersions = useCallback(async (taskId) => {
    try {
      console.log(`태스크의 버전 불러오는 중: ${taskId}`);
      
      const data = await fetchFromAPI(apiUrl(`/api/tasks/${taskId}/versions`));
      const versions = data.versions || [];
      
      console.log(`불러온 버전 수: ${versions.length}`);
      console.log('버전 ID 목록:', versions.map(v => v.id));
      
      setVersions(versions);
      if (versions.length > 0) {
        setCurrentVersion(versions[0].id);
        setIsEditMode(false); // 버전 로드 시 기본적으로 읽기 모드로 설정
      } else {
        setCurrentVersion(null);
        setIsEditMode(true); // 버전이 없으면 편집 모드로 설정
      }
      
      // 템플릿 변수 로드
      loadTemplateVariables(taskId);
    } catch (error) {
      console.error('Error loading versions:', error);
      alert(`버전 불러오기 중 오류가 발생했습니다: ${error.message}`);
    }
  }, []);
  
  const addVersion = useCallback(async (taskId, versionId, content, description = '', name = '') => {
    try {
      // 실제 버전 이름 처리: 비어있으면 자동 생성되는 명명 규칙 적용
      const displayName = name.trim() || `버전 ${new Date().toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })}`.replace(/\. /g, '.');
      
      console.log(`버전 추가: ID=${versionId}, 이름=${displayName}`);
      
      await fetch(apiUrl(`/api/tasks/${taskId}/versions`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          versionId,
          content,
          description,
          name: displayName
        })
      });
      
      // 상태 업데이트
      setVersions(prev => [
        { 
          id: versionId, 
          content, 
          description,
          name: displayName,
          createdAt: new Date().toISOString(),
          results: []
        },
        ...prev
      ]);
      setCurrentVersion(versionId);
      setIsEditMode(false); // 새 버전 생성 후 읽기 모드로 전환
    } catch (error) {
      console.error('Error adding version:', error);
    }
  }, []);
  
  // 버전 선택 및 편집 모드 설정
  const selectVersion = useCallback((versionId, editMode = false) => {
    setCurrentVersion(versionId);
    setIsEditMode(editMode);
  }, []);
  
  const updatePromptContent = useCallback((content) => {
    setVersions(prev => 
      prev.map(v => 
        v.id === currentVersion 
          ? { ...v, content, isDirty: true }
          : v
      )
    );
  }, [currentVersion]);
  
  const savePromptContent = useCallback(async (taskId, versionId, content, versionInfo = {}) => {
    try {
      // 서버 API를 호출하여 버전 내용 저장
      await fetch(apiUrl(`/api/tasks/${taskId}/versions/${versionId}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, ...versionInfo })
      });
      
      // 상태 업데이트
      setVersions(prev => 
        prev.map(v => 
          v.id === versionId
            ? { 
                ...v, 
                content, 
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
  
  // 버전 삭제
  const deleteVersion = useCallback(async (taskId, versionId) => {
    try {
      console.log('버전 삭제 요청:', { taskId, versionId });
      console.log(`태스크 ID 유형: ${typeof taskId}, 버전 ID 유형: ${typeof versionId}`);
      console.log(`태스크 ID 값: "${taskId}", 버전 ID 값: "${versionId}"`);
      
      // 삭제 전에 버전 선 확인
      console.log('버전 정보 확인 중...');
      const versionDetail = await getVersionDetail(taskId, versionId);
      
      if (!versionDetail) {
        console.error(`삭제할 버전이 존재하지 않습니다: ${versionId}`);
        throw new Error('삭제할 버전을 찾을 수 없습니다.');
      }
      
      console.log('삭제할 버전 확인됨:', versionDetail);
      
      // 삭제 요청 실행 - API URL 수정: 슬래시 주의해서 확인
      const apiEndpoint = `/api/tasks/${taskId}/versions/${versionId}`;
      console.log(`API 엔드포인트: ${apiEndpoint}`);
      const fullUrl = apiUrl(apiEndpoint);
      console.log(`전체 URL: ${fullUrl}`);
      
      // 실제 API 호출
      try {
        const response = await fetch(fullUrl, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
          const errorText = await response.text().catch(() => '');
          console.error(`삭제 요청 실패: ${response.status} ${response.statusText}`);
          console.error(`오류 내용: ${errorText}`);
          throw new Error(`삭제 실패: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('삭제 성공:', result);
      } catch (error) {
        console.error(`삭제 API 요청 중 오류:`, error);
        throw error;
      }
      
      // 상태 업데이트
      setVersions(prev => {
        const filtered = prev.filter(v => v.id !== versionId);
        console.log(`버전 업데이트: ${prev.length} -> ${filtered.length}`);
        return filtered;
      });
      
      // 현재 선택된 버전이 삭제된 경우 변경
      if (currentVersion === versionId) {
        console.log('현재 선택된 버전이 삭제되었습니다. 다른 버전 선택');
        
        if (versions.length > 1) {
          // 다른 버전이 있으면 처음 버전으로 선택
          const nextVersion = versions.find(v => v.id !== versionId);
          if (nextVersion) {
            console.log('다음 버전으로 선택:', nextVersion.id);
            setCurrentVersion(nextVersion.id);
          } else {
            console.log('선택할 다음 버전이 없습니다.');
            setCurrentVersion(null);
          }
        } else {
          console.log('버전이 더 이상 없습니다.');
          setCurrentVersion(null);
        }
      }
      
      // 태스크에서도 버전 삭제
      setTasks(prev => {
        const task = prev[taskId];
        if (!task) {
          console.log('태스크를 찾을 수 없습니다:', taskId);
          return prev;
        }
        
        const updatedTask = {
          ...task,
          versions: task.versions.filter(v => v.id !== versionId)
        };
        
        console.log(`태스크 업데이트: ${task.versions.length} -> ${updatedTask.versions.length} 버전`);
        
        return {
          ...prev,
          [taskId]: updatedTask
        };
      });
      
      console.log('버전 삭제 완료');
      
      // 상태가 변경되었으니 저장되었는지 확인을 위해 태스크를 다시 로드
      setTimeout(() => {
        loadVersions(taskId);
      }, 500);
    } catch (error) {
      console.error('버전 삭제 오류:', error);
      throw error; // 에러를 상위로 전파하여 컴포넌트에서 처리할 수 있도록 함
    }
  }, [currentVersion, versions, loadVersions, getVersionDetail]);
  
  // 템플릿 변수 관리
  const loadTemplateVariables = async (taskId) => {
    try {
      const response = await fetch(apiUrl(`/api/templates/${taskId}/variables`));
      const data = await response.json();
      setTemplateVariables(data.variables || []);
    } catch (error) {
      console.error('Error loading template variables:', error);
    }
  };
  
  const updateVariables = async (taskId, variables) => {
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
  };
  
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
  
  // LLM 통합
  const callLLM = useCallback(async (taskId, versionId, inputData) => {
    try {
      const response = await fetch(apiUrl('/api/llm/call'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          taskId,
          versionId,
          inputData
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
  }, []);
  
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
      isEditMode,
      templateVariables,
      llmResults,
      isDarkMode,
      
      // 함수
      loadTasks,
      createTask,
      updateTask,
      setCurrentTask,
      loadVersions,
      addVersion,
      setCurrentVersion,
      selectVersion,
      setIsEditMode,
      updatePromptContent,
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
      toggleDarkMode
    }}>
      {children}
    </PromptContext.Provider>
  );
};

export default PromptContext;