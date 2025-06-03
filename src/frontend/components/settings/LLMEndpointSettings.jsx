import React, { useState, useEffect } from 'react';
import { useStore } from '../../store.jsx';
import LLMEndpointList from './LLMEndpointList.jsx';
import LLMEndpointForm from './LLMEndpointForm.jsx';

function LLMEndpointSettings() {
  const {
    llmEndpoints,
    activeLlmEndpointId,
    defaultLlmEndpointId,
    loadLlmEndpoints,
    addLlmEndpoint,
    updateLlmEndpoint,
    deleteLlmEndpoint,
    setActiveLlmEndpoint,
    setDefaultLlmEndpoint
  } = useStore();
  
  const [selectedEndpointId, setSelectedEndpointId] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  
  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    loadLlmEndpoints().catch(error => {
      console.error('LLM endpoints 로드 실패:', error);
    });
  }, [loadLlmEndpoints]);
  
  // 선택된 엔드포인트 정보 가져오기
  const selectedEndpoint = selectedEndpointId 
    ? llmEndpoints.find(ep => ep.id === selectedEndpointId) 
    : null;
  
  const activeEndpoint = activeLlmEndpointId 
    ? llmEndpoints.find(ep => ep.id === activeLlmEndpointId) 
    : null;
  
  // 엔드포인트 선택
  const handleSelectEndpoint = (endpointId) => {
    setSelectedEndpointId(endpointId);
    setIsEditing(false);
    setIsCreating(false);
  };
  
  // 새 엔드포인트 추가 모드
  const handleCreateNew = () => {
    setSelectedEndpointId(null);
    setIsEditing(false);
    setIsCreating(true);
  };
  
  // 편집 모드
  const handleEdit = (endpointId) => {
    setSelectedEndpointId(endpointId);
    setIsEditing(true);
    setIsCreating(false);
  };
  
  // 엔드포인트 삭제
  const handleDelete = async (endpointId) => {
    const endpoint = llmEndpoints.find(ep => ep.id === endpointId);
    if (!endpoint) return;
    
    if (window.confirm(`정말 '${endpoint.name}' 엔드포인트를 삭제하시겠습니까?`)) {
      try {
        await deleteLlmEndpoint(endpointId);
        
        // 삭제된 엔드포인트가 선택되어 있었다면 선택 해제
        if (selectedEndpointId === endpointId) {
          setSelectedEndpointId(null);
          setIsEditing(false);
        }
        
        alert('엔드포인트가 삭제되었습니다.');
      } catch (error) {
        console.error('엔드포인트 삭제 실패:', error);
        alert(`삭제 실패: ${error.message}`);
      }
    }
  };
  
  // 엔드포인트 활성화
  const handleActivate = async (endpointId) => {
    try {
      await setActiveLlmEndpoint(endpointId);
      alert('활성 엔드포인트가 설정되었습니다.');
    } catch (error) {
      console.error('엔드포인트 활성화 실패:', error);
      alert(`활성화 실패: ${error.message}`);
    }
  };
  
  // 기본값으로 설정
  const handleSetDefault = async (endpointId) => {
    try {
      await setDefaultLlmEndpoint(endpointId);
      alert('기본 엔드포인트가 설정되었습니다.');
    } catch (error) {
      console.error('기본 엔드포인트 설정 실패:', error);
      alert(`설정 실패: ${error.message}`);
    }
  };
  
  // 폼 저장 처리
  const handleSaveEndpoint = async (endpointData) => {
    try {
      if (isEditing && selectedEndpointId) {
        // 기존 엔드포인트 업데이트
        await updateLlmEndpoint(selectedEndpointId, endpointData);
        alert('엔드포인트가 업데이트되었습니다.');
      } else if (isCreating) {
        // 새 엔드포인트 생성
        const newEndpoint = await addLlmEndpoint(endpointData);
        setSelectedEndpointId(newEndpoint.id);
        alert('새 엔드포인트가 생성되었습니다.');
      }
      
      setIsEditing(false);
      setIsCreating(false);
    } catch (error) {
      console.error('엔드포인트 저장 실패:', error);
      alert(`저장 실패: ${error.message}`);
    }
  };
  
  // 폼 취소 처리
  const handleCancelForm = () => {
    setIsEditing(false);
    setIsCreating(false);
    if (isCreating) {
      setSelectedEndpointId(null);
    }
  };
  
  return (
    <div className="h-full flex">
      {/* 좌측 패널 - 엔드포인트 목록 */}
      <div className="w-1/5 border-r border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <LLMEndpointList
          endpoints={llmEndpoints}
          selectedEndpointId={selectedEndpointId}
          activeEndpointId={activeLlmEndpointId}
          defaultEndpointId={defaultLlmEndpointId}
          onSelect={handleSelectEndpoint}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onCreateNew={handleCreateNew}
          activeEndpoint={activeEndpoint}
        />
      </div>
      
      {/* 우측 메인 콘텐츠 영역 */}
      <div className="flex-1 bg-white dark:bg-gray-900">
        {(isCreating || isEditing) ? (
          <LLMEndpointForm
            endpoint={isEditing ? selectedEndpoint : null}
            isEditing={isEditing}
            onSave={handleSaveEndpoint}
            onCancel={handleCancelForm}
          />
        ) : selectedEndpoint ? (
          // 엔드포인트 상세 정보 표시
          <div className="p-6">
            <div className="max-w-2xl">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                    {selectedEndpoint.name}
                  </h2>
                  {selectedEndpoint.description && (
                    <p className="text-gray-600 dark:text-gray-400">
                      {selectedEndpoint.description}
                    </p>
                  )}
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(selectedEndpointId)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                  >
                    편집
                  </button>
                  
                  {activeLlmEndpointId !== selectedEndpointId && (
                    <button
                      onClick={() => handleActivate(selectedEndpointId)}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
                    >
                      활성화
                    </button>
                  )}
                  
                  {defaultLlmEndpointId !== selectedEndpointId && (
                    <button
                      onClick={() => handleSetDefault(selectedEndpointId)}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded transition-colors"
                    >
                      기본값으로 설정
                    </button>
                  )}
                </div>
              </div>
              
              {/* 엔드포인트 상세 정보 */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Base URL
                    </label>
                    <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded border">
                      <code className="text-sm text-gray-900 dark:text-gray-100">
                        {selectedEndpoint.baseUrl}
                      </code>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      기본 모델
                    </label>
                    <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded border">
                      <code className="text-sm text-gray-900 dark:text-gray-100">
                        {selectedEndpoint.defaultModel || '설정되지 않음'}
                      </code>
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    API 키
                  </label>
                  <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded border">
                    <code className="text-sm text-gray-500 dark:text-gray-400">
                      {selectedEndpoint.apiKey ? '••••••••••••••••' : '설정되지 않음'}
                    </code>
                  </div>
                </div>
                
                <div className="flex gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <span className={`inline-block w-3 h-3 rounded-full ${
                      activeLlmEndpointId === selectedEndpointId ? 'bg-green-500' : 'bg-gray-300'
                    }`} />
                    <span className="text-gray-600 dark:text-gray-400">
                      {activeLlmEndpointId === selectedEndpointId ? '현재 사용 중' : '비활성화됨'}
                    </span>
                  </div>
                  
                  {defaultLlmEndpointId === selectedEndpointId && (
                    <div className="flex items-center gap-2">
                      <span className="inline-block w-3 h-3 rounded-full bg-purple-500" />
                      <span className="text-gray-600 dark:text-gray-400">기본값</span>
                    </div>
                  )}
                </div>
                
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    생성일: {new Date(selectedEndpoint.createdAt).toLocaleDateString('ko-KR')}
                    {selectedEndpoint.updatedAt && (
                      <> • 수정일: {new Date(selectedEndpoint.updatedAt).toLocaleDateString('ko-KR')}</>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // 아무것도 선택되지 않은 상태
          <div className="p-6 h-full flex items-center justify-center">
            <div className="text-center text-gray-500 dark:text-gray-400">
              <div className="text-6xl mb-4">⚙️</div>
              <h3 className="text-xl font-medium mb-2">LLM Endpoint 설정</h3>
              <p className="mb-4">
                왼쪽 목록에서 엔드포인트를 선택하거나 새로 추가하세요.
              </p>
              <button
                onClick={handleCreateNew}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                새 엔드포인트 추가
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default LLMEndpointSettings;