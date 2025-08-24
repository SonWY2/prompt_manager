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
    
    if (window.confirm(`Are you sure you want to delete '${endpoint.name}' provider?\n\nThis action cannot be undone.`)) {
      try {
        await deleteLlmEndpoint(endpointId);
        
        // 삭제된 엔드포인트가 선택되어 있었다면 선택 해제
        if (selectedEndpointId === endpointId) {
          setSelectedEndpointId(null);
          setIsEditing(false);
        }
        
        // Success notification could be added here
      } catch (error) {
        console.error('엔드포인트 삭제 실패:', error);
        alert(`Failed to delete provider: ${error.message}`);
      }
    }
  };
  
  // 엔드포인트 활성화
  const handleActivate = async (endpointId) => {
    try {
      await setActiveLlmEndpoint(endpointId);
      // Success notification could be added here
    } catch (error) {
      console.error('엔드포인트 활성화 실패:', error);
      alert(`Activation failed: ${error.message}`);
    }
  };
  
  // 기본값으로 설정
  const handleSetDefault = async (endpointId) => {
    try {
      await setDefaultLlmEndpoint(endpointId);
      // Success notification could be added here
    } catch (error) {
      console.error('기본 엔드포인트 설정 실패:', error);
      alert(`Failed to set default: ${error.message}`);
    }
  };
  
  // 폼 저장 처리
  const handleSaveEndpoint = async (endpointData) => {
    try {
      if (isEditing && selectedEndpointId) {
        // 기존 엔드포인트 업데이트
        await updateLlmEndpoint(selectedEndpointId, endpointData);
      } else if (isCreating) {
        // 새 엔드포인트 생성
        const newEndpoint = await addLlmEndpoint(endpointData);
        setSelectedEndpointId(newEndpoint.id);
      }
      
      setIsEditing(false);
      setIsCreating(false);
    } catch (error) {
      console.error('엔드포인트 저장 실패:', error);
      throw error; // Re-throw to let the form handle the error
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
      <div className="flex-shrink-0 w-80 border-r" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}>
        <div className="h-full flex flex-col">
          {/* Panel Header */}
          <div className="flex-shrink-0 p-4 border-b" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-primary)' }}>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg" style={{ background: 'var(--accent-primary)' }}>
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
              </div>
              <div>
                <h2 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                  LLM Providers
                </h2>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  Manage API endpoints
                </p>
              </div>
            </div>
          </div>
          
          {/* List Content */}
          <div className="flex-1">
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
        </div>
      </div>
      
      {/* Right Panel - Main Content */}
      <div className="flex-1 min-w-0">
        {(isCreating || isEditing) ? (
          <LLMEndpointForm
            endpoint={isEditing ? selectedEndpoint : null}
            isEditing={isEditing}
            onSave={handleSaveEndpoint}
            onCancel={handleCancelForm}
          />
        ) : selectedEndpoint ? (
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex-shrink-0 p-6 border-b" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-xl" style={{ background: 'var(--bg-tertiary)' }}>
                    <svg className="w-6 h-6" style={{ color: 'var(--accent-primary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                    </svg>
                  </div>
                  <div>
                    <h1 className="text-xl font-semibold flex items-center gap-3" style={{ color: 'var(--text-primary)' }}>
                      {selectedEndpoint.name}
                      {activeLlmEndpointId === selectedEndpointId && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full" style={{ background: 'rgba(16, 185, 129, 0.2)', color: 'var(--accent-success)' }}>
                          <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
                          Active
                        </span>
                      )}
                      {defaultLlmEndpointId === selectedEndpointId && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full" style={{ background: 'rgba(139, 92, 246, 0.2)', color: 'var(--accent-primary)' }}>
                          <div className="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
                          Default
                        </span>
                      )}
                    </h1>
                    {selectedEndpoint.description && (
                      <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                        {selectedEndpoint.description}
                      </p>
                    )}
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(selectedEndpointId)}
                    className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-all duration-200 hover:bg-gray-700"
                    style={{ background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border-primary)' }}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Edit
                  </button>
                  
                  {activeLlmEndpointId !== selectedEndpointId && (
                    <button
                      onClick={() => handleActivate(selectedEndpointId)}
                      className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-all duration-200"
                      style={{ background: 'var(--accent-success)', color: 'white', border: 'none' }}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      Activate
                    </button>
                  )}
                  
                  {defaultLlmEndpointId !== selectedEndpointId && (
                    <button
                      onClick={() => handleSetDefault(selectedEndpointId)}
                      className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-all duration-200"
                      style={{ background: 'var(--accent-primary)', color: 'white', border: 'none' }}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                      </svg>
                      Set Default
                    </button>
                  )}
                </div>
              </div>
            </div>
            
            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="max-w-4xl">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  {/* Base URL Card */}
                  <div className="p-4 rounded-lg border" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }}>
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg" style={{ background: 'var(--bg-tertiary)' }}>
                        <svg className="w-4 h-4" style={{ color: 'var(--accent-primary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                        </svg>
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>API Endpoint</h3>
                        <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>Base URL for API requests</p>
                        <div className="p-3 rounded-lg font-mono text-sm break-all" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-primary)', color: 'var(--accent-primary)' }}>
                          {selectedEndpoint.baseUrl}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Model Card */}
                  <div className="p-4 rounded-lg border" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }}>
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg" style={{ background: 'var(--bg-tertiary)' }}>
                        <svg className="w-4 h-4" style={{ color: 'var(--accent-secondary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Default Model</h3>
                        <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>Model used by default</p>
                        <div className="p-3 rounded-lg font-mono text-sm" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-primary)', color: selectedEndpoint.defaultModel ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                          {selectedEndpoint.defaultModel || 'Not specified'}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Authentication Card */}
                  <div className="p-4 rounded-lg border" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }}>
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg" style={{ background: 'var(--bg-tertiary)' }}>
                        <svg className="w-4 h-4" style={{ color: selectedEndpoint.apiKey ? 'var(--accent-success)' : 'var(--text-muted)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                        </svg>
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Authentication</h3>
                        <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>API key configuration</p>
                        <div className="p-3 rounded-lg font-mono text-sm flex items-center gap-2" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-primary)' }}>
                          {selectedEndpoint.apiKey ? (
                            <>
                              <div className="w-2 h-2 rounded-full bg-green-500"></div>
                              <span style={{ color: 'var(--accent-success)' }}>API Key configured</span>
                            </>
                          ) : (
                            <>
                              <div className="w-2 h-2 rounded-full bg-gray-500"></div>
                              <span style={{ color: 'var(--text-muted)' }}>No authentication</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Context Size Card */}
                  <div className="p-4 rounded-lg border" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }}>
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg" style={{ background: 'var(--bg-tertiary)' }}>
                        <svg className="w-4 h-4" style={{ color: 'var(--accent-warning)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                        </svg>
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Context Window</h3>
                        <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>Maximum token capacity</p>
                        <div className="p-3 rounded-lg font-mono text-sm" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-primary)', color: selectedEndpoint.contextSize ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                          {selectedEndpoint.contextSize ? `${selectedEndpoint.contextSize.toLocaleString()} tokens` : 'Not specified'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Metadata */}
                <div className="p-4 rounded-lg border" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }}>
                  <h3 className="text-sm font-medium mb-3" style={{ color: 'var(--text-primary)' }}>Metadata</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Created:</span>
                      <div className="font-mono mt-1" style={{ color: 'var(--text-primary)' }}>
                        {new Date(selectedEndpoint.createdAt).toLocaleString()}
                      </div>
                    </div>
                    {selectedEndpoint.updatedAt && (
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Last Updated:</span>
                        <div className="font-mono mt-1" style={{ color: 'var(--text-primary)' }}>
                          {new Date(selectedEndpoint.updatedAt).toLocaleString()}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md mx-auto p-8">
              <div className="mb-6">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center" style={{ background: 'var(--bg-tertiary)' }}>
                  <svg className="w-8 h-8" style={{ color: 'var(--text-muted)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                  LLM Provider Settings
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                  Select a provider from the sidebar to view its configuration, or create a new one to get started with your AI workflows.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={handleCreateNew}
                  className="flex items-center justify-center gap-2 px-4 py-2 text-sm rounded-lg transition-all duration-200"
                  style={{ background: 'var(--accent-primary)', color: 'white', border: 'none' }}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Add Your First Provider
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default LLMEndpointSettings;