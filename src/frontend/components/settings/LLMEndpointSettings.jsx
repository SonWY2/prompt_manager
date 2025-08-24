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
    <div className="h-full flex" style={{ background: 'var(--bg-primary)' }}>
      {/* Left Panel - Endpoint List */}
      <div className="panel" style={{ width: '320px', background: 'var(--bg-secondary)'}}>
        <div className="panel-header">
          <h2 className="panel-title">LLM Providers</h2>
        </div>
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
      
      {/* Right Panel - Main Content */}
      <div className="flex-1">
        {(isCreating || isEditing) ? (
          <LLMEndpointForm
            endpoint={isEditing ? selectedEndpoint : null}
            isEditing={isEditing}
            onSave={handleSaveEndpoint}
            onCancel={handleCancelForm}
          />
        ) : selectedEndpoint ? (
          <div className="p-6">
            <div className="card">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-lg font-medium" style={{ color: 'var(--text-primary)' }}>
                    {selectedEndpoint.name}
                  </h2>
                  {selectedEndpoint.description && (
                    <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                      {selectedEndpoint.description}
                    </p>
                  )}
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(selectedEndpointId)}
                    className="btn btn-secondary"
                  >
                    Edit
                  </button>
                  
                  {activeLlmEndpointId !== selectedEndpointId && (
                    <button
                      onClick={() => handleActivate(selectedEndpointId)}
                      className="btn btn-success"
                    >
                      Activate
                    </button>
                  )}
                  
                  {defaultLlmEndpointId !== selectedEndpointId && (
                    <button
                      onClick={() => handleSetDefault(selectedEndpointId)}
                      className="btn btn-primary"
                    >
                      Set Default
                    </button>
                  )}
                </div>
              </div>
              
              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-muted)' }}>
                      Base URL
                    </label>
                    <div className="p-2 rounded text-sm" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-primary)' }}>
                      <code>{selectedEndpoint.baseUrl}</code>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-muted)' }}>
                      Default Model
                    </label>
                    <div className="p-2 rounded text-sm" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-primary)' }}>
                      <code>{selectedEndpoint.defaultModel || 'Not set'}</code>
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-muted)' }}>
                    API Key
                  </label>
                  <div className="p-2 rounded text-sm" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-primary)' }}>
                    <code style={{ color: 'var(--text-dim)' }}>
                      {selectedEndpoint.apiKey ? '••••••••••••••••' : 'Not set'}
                    </code>
                  </div>
                </div>
                
                <div className="flex gap-4 text-sm items-center">
                  <div className="flex items-center gap-2">
                    <span className={`inline-block w-2 h-2 rounded-full ${
                      activeLlmEndpointId === selectedEndpointId ? 'bg-green-500' : 'bg-gray-500'
                    }`} />
                    <span style={{ color: 'var(--text-secondary)' }}>
                      {activeLlmEndpointId === selectedEndpointId ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  
                  {defaultLlmEndpointId === selectedEndpointId && (
                    <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                      <span className="inline-block w-2 h-2 rounded-full" style={{ background: 'var(--accent-primary)' }} />
                      <span>Default</span>
                    </div>
                  )}
                </div>
                
                <div className="pt-4 border-t" style={{ borderColor: 'var(--border-primary)' }}>
                  <div className="text-xs" style={{ color: 'var(--text-dim)' }}>
                    Created: {new Date(selectedEndpoint.createdAt).toLocaleString()}
                    {selectedEndpoint.updatedAt && (
                      <> • Updated: {new Date(selectedEndpoint.updatedAt).toLocaleString()}</>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center" style={{ color: 'var(--text-muted)' }}>
              <div className="text-5xl mb-4">⚙️</div>
              <h3 className="text-lg font-medium mb-2" style={{ color: 'var(--text-primary)' }}>LLM Endpoint Settings</h3>
              <p>
                Select an endpoint from the left, or create a new one using the buttons below the list.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default LLMEndpointSettings;