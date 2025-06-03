import React, { useState, useEffect, useRef } from 'react';
import { useStore } from '../../store.jsx';
import { apiUrl } from '../../utils/api';
import VersionTimeline from './VersionTimeline.jsx';
import VariableManager from './VariableManager.jsx';
import Button from '../common/Button.jsx';

function PromptEditor({ taskId, versionId }) {
  const { 
    tasks, 
    versions, 
    loadVersions,
    addVersion,
    updatePromptContent,
    savePromptContent,
    deleteVersion,
    getVersionDetail,
    extractVariables,
    updateVariables,
    setCurrentVersion,
    isEditMode, // 전역 편집 모드 상태 사용
    setIsEditMode, // 편집 모드 설정 함수
    templateVariables,
    renderPrompt,
    callLLM
  } = useStore();
  
  const [promptContent, setPromptContent] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [renderedPrompt, setRenderedPrompt] = useState('');
  const [variableValues, setVariableValues] = useState({});
  const [versionInfo, setVersionInfo] = useState({
    name: '',
    description: ''
  });
  
  // 태스크 변경 시 버전 로드 (강화된 디바운싱 및 중복 호출 방지)
  const loadVersionsTimerRef = useRef(null);
  const lastTaskIdRef = useRef(null);
  
  useEffect(() => {
    if (taskId && taskId !== lastTaskIdRef.current) {
      console.log('🔄 PromptEditor: 태스크 변경 감지:', { from: lastTaskIdRef.current, to: taskId });
      
      // 이전 타이머 취소
      if (loadVersionsTimerRef.current) {
        clearTimeout(loadVersionsTimerRef.current);
      }
      
      // 새로운 타이머 설정
      loadVersionsTimerRef.current = setTimeout(() => {
        console.log('📦 PromptEditor: 버전 로드 실행:', taskId);
        loadVersions(taskId);
        loadVersionsTimerRef.current = null;
      }, 200); // 200ms 디바운싱
      
      // 마지막 taskId 기록
      lastTaskIdRef.current = taskId;
    }
    
    // 컴포넌트 언마운트 시 정리
    return () => {
      if (loadVersionsTimerRef.current) {
        clearTimeout(loadVersionsTimerRef.current);
        loadVersionsTimerRef.current = null;
      }
    };
  }, [taskId]); // loadVersions 의존성 제거
  
  // 버전 변경 시 프롬프트 내용 설정
  useEffect(() => {
    if (versionId && versions.length > 0) {
      const version = versions.find(v => v.id === versionId);
      if (version) {
        setPromptContent(version.content || '');
        setVersionInfo({
          name: version.name || version.id,
          description: version.description || ''
        });
        
        // 프롬프트에서 변수 추출 및 값 초기화
        const extractedVars = extractVariables(version.content || '');
        setVariableValues(prev => {
          const newValues = { ...prev };
          extractedVars.forEach(varName => {
            if (!newValues[varName]) {
              newValues[varName] = '';
            }
          });
          return newValues;
        });
      }
    } else {
      // 버전이 없는 경우에는 편집 모드 활성화
      setIsEditMode(true);
    }
  }, [versionId, versions, extractVariables, setIsEditMode]);
  
  // 프롬프트 미리보기 렌더링
  useEffect(() => {
    if (showPreview) {
      const rendered = renderPrompt(promptContent, variableValues);
      setRenderedPrompt(rendered);
    }
  }, [showPreview, promptContent, variableValues, renderPrompt]);
  
  // 변수 값 업데이트
  const handleVariableChange = (varName, value, action = 'update') => {
    if (action === 'add') {
      // 새 변수 추가
      setVariableValues(prev => ({
        ...prev,
        [varName]: value
      }));
      // 변수 목록 업데이트 호출
      updateVariables(taskId, [...Object.keys(variableValues), varName]);
    } 
    else if (action === 'remove') {
      // 변수 제거
      setVariableValues(prev => {
        const newValues = { ...prev };
        delete newValues[varName];
        return newValues;
      });
      // 변수 목록 업데이트 호출
      updateVariables(taskId, Object.keys(variableValues).filter(v => v !== varName));
    } 
    else {
      // 변수 값만 업데이트
      setVariableValues(prev => ({
        ...prev,
        [varName]: value
      }));
    }
  };
  
  // 버전 선택
  const handleSelectVersion = (selectedVersionId) => {
    setCurrentVersion(selectedVersionId);
  };
  
  // 새 버전 생성
  const handleCreateVersion = () => {
    const newVersionId = `v${Date.now()}`;
    addVersion(taskId, newVersionId, promptContent, versionInfo.description, versionInfo.name);
  };
  
  // 버전 정보 업데이트
  const handleVersionInfoChange = (key, value) => {
    setVersionInfo(prev => ({
      ...prev,
      [key]: value
    }));
  };
  
  // LLM 호출
  const handleExecute = async () => {
    try {
      await callLLM(taskId, versionId, variableValues);
    } catch (error) {
      console.error("Failed to execute prompt:", error);
      alert("프롬프트 실행 중 오류가 발생했습니다.");
    }
  };
  
  // 태스크와 버전 정보 가져오기 - 다른 코드보다 먼저 정의
  const currentTask = tasks[taskId];
  const currentVersion = versions.find(v => v.id === versionId);

  // 현재 태스크가 없는 경우
  if (!taskId) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
        <div className="text-center">
          <p className="mb-3">👈 왼쪽에서 태스크를 선택하거나 새 태스크를 생성하세요</p>
        </div>
      </div>
    );
  }
  
  // 버전이 없는 경우 새 버전 생성 안내 메시지 표시
  if (versions.length === 0) {
    return (
      <div className="h-full flex flex-col">
        {/* 헤더 */}
        <div className="p-3 border-b border-gray-300 dark:border-gray-700 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold">{currentTask?.name || '태스크 이름'}</h2>
            <div className="text-sm text-gray-500 dark:text-gray-400">아직 버전이 없습니다.</div>
          </div>
        </div>
        
        {/* 빈 상태 안내 */}
        <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
          <div className="text-center">
            <div className="text-6xl mb-4">📄</div>
            <h3 className="text-lg font-medium mb-2">아직 버전이 없습니다.</h3>
            <p className="mb-4">프롬프트를 작성하고 첫 번째 버전을 생성해보세요!</p>
          </div>
        </div>
        
        {/* 새 버전 생성 영역 */}
        <div className="p-4 border-t border-gray-300 dark:border-gray-700">
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1">버전 이름 (선택사항)</label>
              <input
                type="text"
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
                placeholder="예: v1.0, 초기 버전, 영어 버전 (빈칸이면 자동생성)"
                value={versionInfo.name}
                onChange={(e) => handleVersionInfoChange('name', e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">설명 (선택사항)</label>
              <input
                type="text"
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
                placeholder="예: 변수 추가, 지시문 개선, 결과물 길이 제한 추가"
                value={versionInfo.description}
                onChange={(e) => handleVersionInfoChange('description', e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">프롬프트 내용</label>
              <textarea
                className="w-full h-32 p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white resize-none"
                placeholder="프롬프트 내용을 입력하세요..."
                value={promptContent}
                onChange={(e) => setPromptContent(e.target.value)}
              />
            </div>
            
            <Button
              variant="primary"
              className="w-full"
              onClick={handleCreateVersion}
              disabled={!promptContent.trim()}
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              첫 번째 버전 생성
            </Button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-full flex flex-col">
      {/* 헤더 */}
      <div className="p-3 border-b border-gray-300 dark:border-gray-700 flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold">{currentTask?.name || '태스크 이름'}</h2>
          <div className="flex gap-2 items-center">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {versionId ? `현재 버전: ${currentVersion?.name || versionId}` : '버전을 선택하세요'}
            </span>
            {currentVersion?.description && (
              <span className="text-sm text-gray-500 dark:text-gray-400">- {currentVersion.description}</span>
            )}
          </div>
        </div>
        
        <div className="flex gap-2">
          <Button 
            variant={showPreview ? 'primary' : 'default'}
            onClick={() => setShowPreview(!showPreview)}
          >
            {showPreview ? '에디터 보기' : '미리보기'}
          </Button>
          <Button 
            variant="success"
            onClick={handleExecute}
            disabled={!versionId}
          >
            실행
          </Button>
          {versionId && (
            <Button
              variant="danger"
              onClick={async () => {
                try {
                  // 버전 정보 확인
                  const versionInfo = await getVersionDetail(taskId, versionId);
                  
                  if (!versionInfo) {
                    alert('삭제할 버전을 찾을 수 없습니다.');
                    return;
                  }
                  
                  // 삭제 확인
                  if (window.confirm(`정말 이 버전(${versionInfo.name || versionInfo.id})을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다!`)) {
                    // 스토어의 deleteVersion 함수 사용
                    await deleteVersion(taskId, versionId);
                    console.log('버전 삭제 성공!');
                    alert('버전이 삭제되었습니다.');
                  }
                } catch (error) {
                  console.error('삭제 오류:', error);
                  alert(`삭제 중 오류 발생: ${error.message}`);
                }
              }}
            >
              삭제
            </Button>
          )}
        </div>
      </div>
      
      {/* 버전 타임라인 */}
      <div className="border-b border-gray-300 dark:border-gray-700">
        <VersionTimeline 
          versions={versions}
          currentVersion={versionId}
          onSelectVersion={handleSelectVersion}
        />
      </div>
      
      {/* 에디터 / 미리보기 */}
      <div className="flex-1 overflow-hidden">
        {!showPreview ? (
          <div className="h-full p-3">
            {/* 버전 정보 필드 */}
            {versionId && (
              <div className="mb-3 grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1">버전 이름</label>
                  <input
                    type="text"
                    value={versionInfo.name}
                    onChange={(e) => handleVersionInfoChange('name', e.target.value)}
                    className={`w-full p-2 border border-gray-300 dark:border-gray-600 rounded 
                      ${isEditMode 
                        ? 'bg-white dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500' 
                        : 'bg-gray-100 dark:bg-gray-800 cursor-not-allowed'}`}
                    placeholder="버전 이름..."
                    disabled={!isEditMode}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">설명</label>
                  <input
                    type="text"
                    value={versionInfo.description}
                    onChange={(e) => handleVersionInfoChange('description', e.target.value)}
                    className={`w-full p-2 border border-gray-300 dark:border-gray-600 rounded 
                      ${isEditMode 
                        ? 'bg-white dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500' 
                        : 'bg-gray-100 dark:bg-gray-800 cursor-not-allowed'}`}
                    placeholder="버전에 대한 설명..."
                    disabled={!isEditMode}
                  />
                </div>
              </div>
            )}
            
            <textarea
              value={promptContent}
              onChange={(e) => {
                setPromptContent(e.target.value);
                updatePromptContent(e.target.value);
              }}
              className={`w-full h-full p-3 border border-gray-300 dark:border-gray-600 rounded 
                ${isEditMode 
                  ? 'bg-white dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500' 
                  : 'bg-gray-100 dark:bg-gray-800 cursor-not-allowed'}`}
              placeholder="프롬프트를 작성하세요..."
              disabled={!isEditMode}
            />
          </div>
        ) : (
          <div className="h-full p-4 overflow-y-auto bg-gray-50 dark:bg-gray-800">
            <div className="bg-white dark:bg-gray-900 p-4 rounded shadow">
              <pre className="whitespace-pre-wrap dark:text-white">{renderedPrompt}</pre>
            </div>
          </div>
        )}
      </div>
      
      {/* 변수 관리자 */}
      <div className="border-t border-gray-300 dark:border-gray-700">
        <VariableManager 
          variables={Object.keys(variableValues)}
          values={variableValues}
          onChange={handleVariableChange}
        />
      </div>
      
      {/* 하단 컨트롤 */}
      <div className="p-3 border-t border-gray-300 dark:border-gray-700 flex justify-between">
        {versionId ? (
          isEditMode ? (
            <>
              <Button 
                variant="outline"
                onClick={() => setIsEditMode(false)}
              >
                취소
              </Button>
              <Button 
                variant="primary"
                onClick={() => {
                  savePromptContent(taskId, versionId, promptContent, versionInfo);
                  setIsEditMode(false);
                }}
              >
                저장
              </Button>
            </>
          ) : (
            <>
              <Button 
                variant="default"
                onClick={() => setIsEditMode(true)}
              >
                편집
              </Button>
              <Button 
                variant="primary"
                onClick={handleCreateVersion}
              >
                새 버전 생성
              </Button>
            </>
          )
        ) : (
          <>
            <div></div>
            <Button 
              variant="primary"
              onClick={handleCreateVersion}
              disabled={!promptContent.trim()}
            >
              새 버전 생성
            </Button>
          </>
        )}
      </div>
    </div>
  );
}

export default PromptEditor;