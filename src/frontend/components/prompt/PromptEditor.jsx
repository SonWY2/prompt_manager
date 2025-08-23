// src/frontend/components/prompt/PromptEditor.jsx
import React, { useState, useEffect } from 'react';
import { useStore } from '../../store.jsx';

const PromptEditor = ({ taskId, versionId }) => {
  const { 
    tasks, 
    updateTaskPrompt, 
    createVersion,
    setCurrentVersion,
    currentVersion,
    updateTask
  } = useStore();
  
  const [promptText, setPromptText] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [taskName, setTaskName] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [variables, setVariables] = useState({});
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    variables: true,
    system: false
  });
  const [newVariable, setNewVariable] = useState({ name: '', value: '' });
  const [isEditingName, setIsEditingName] = useState(false);

  const currentTask = taskId ? tasks[taskId] : null;
  const currentVersionData = currentTask?.versions?.[currentVersion];

  useEffect(() => {
    if (currentTask) {
      setTaskName(currentTask.name || '');
      setSystemPrompt(currentTask.systemPrompt || '');
      setTaskDescription(currentTask.description || '');
    }
    if (currentVersionData) {
      setPromptText(currentVersionData.prompt || '');
      setVariables(currentVersionData.variables || {});
    }
  }, [currentTask, currentVersionData]);

  const extractedVariables = React.useMemo(() => {
    const matches = promptText.match(/\{\{(\w+)\}\}/g) || [];
    return [...new Set(matches.map(match => match.slice(2, -2)))];
  }, [promptText]);

  const handleSave = async () => {
    if (!taskId) return;
    try {
      await updateTaskPrompt(taskId, promptText, variables);
      if (systemPrompt !== currentTask.systemPrompt || taskDescription !== currentTask.description) {
        await updateTask(taskId, { systemPrompt, description: taskDescription });
      }
    } catch (error) {
      console.error('저장 실패:', error);
    }
  };

  const handleSaveName = async () => {
    if (!taskId || !taskName.trim()) return;
    try {
      await updateTask(taskId, { name: taskName.trim() });
      setIsEditingName(false);
    } catch (error) {
      console.error('이름 저장 실패:', error);
    }
  };

  const handleNewVersion = async () => {
    if (!taskId) return;
    try {
      const versionName = prompt('새 버전 이름을 입력하세요:');
      if (versionName) {
        await createVersion(taskId, versionName, promptText, variables);
      }
    } catch (error) {
      console.error('버전 생성 실패:', error);
    }
  };

  const handleAddVariable = () => {
    if (!newVariable.name.trim()) return;
    setVariables(prev => ({ ...prev, [newVariable.name.trim()]: newVariable.value }));
    setNewVariable({ name: '', value: '' });
  };

  const handleRemoveVariable = (variable) => {
    setVariables(prev => {
      const updated = { ...prev };
      delete updated[variable];
      return updated;
    });
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const renderPromptWithVariables = () => {
    let rendered = promptText;
    extractedVariables.forEach(variable => {
      const value = variables[variable] || `{{${variable}}}`;
      rendered = rendered.replace(new RegExp(`\\{\\{${variable}\\}\\}`, 'g'), value);
    });
    return rendered;
  };

  if (!currentTask) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted">태스크를 선택해 주세요</p>
      </div>
    );
  }

  const versions = currentTask.versions ? Object.entries(currentTask.versions) : [];

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {/* Task Name */}
            {isEditingName ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={taskName}
                  onChange={(e) => setTaskName(e.target.value)}
                  className="input text-lg font-semibold bg-transparent border-none p-0 focus:ring-0"
                  onBlur={handleSaveName}
                  onKeyPress={(e) => e.key === 'Enter' && handleSaveName()}
                  autoFocus
                />
              </div>
            ) : (
              <h2 
                className="text-xl font-semibold cursor-pointer hover:opacity-75 transition-opacity"
                style={{ color: 'var(--text-primary)' }}
                onClick={() => setIsEditingName(true)}
                title="클릭하여 이름 편집"
              >
                {currentTask.name} ✏️
              </h2>
            )}
            
            <div className="px-3 py-1 rounded-full text-xs font-medium"
                 style={{ 
                   background: 'rgba(34, 197, 94, 0.2)', 
                   color: 'var(--accent-success)' 
                 }}>
              활성
            </div>
          </div>
          
          <div className="flex gap-2">
            <button 
              className="btn btn-secondary"
              onClick={() => navigator.clipboard.writeText(promptText)}
            >
              📋 복제
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleNewVersion}
            >
              🌿 새 버전
            </button>
          </div>
        </div>

        {/* Version Timeline */}
        {versions.length > 0 && (
          <div className="version-timeline">
            <div className="timeline-line"></div>
            {versions.map(([versionId, version], index) => (
              <div key={versionId} className="timeline-item">
                <div 
                  className={`timeline-dot ${currentVersion === versionId ? 'active' : ''}`}
                  onClick={() => setCurrentVersion(versionId)}
                />
                <div className={`timeline-label ${currentVersion === versionId ? 'active' : ''}`}>
                  {version.name || `v${index + 1}`}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4" style={{ height: 0 }}>
        {/* Description Section */}
        <div className="card">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            📝 프롬프트 설명
          </h3>
          <textarea
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            placeholder="이 프롬프트의 목적과 사용법을 설명하세요..."
            className="w-full h-20 p-3 bg-transparent border rounded-md text-sm resize-y"
            style={{ 
              borderColor: 'var(--border-primary)',
              color: 'var(--text-primary)'
            }}
          />
        </div>

        {/* System Prompt Section */}
        <div className="card">
          <div 
            className="flex items-center justify-between cursor-pointer mb-3"
            onClick={() => toggleSection('system')}
          >
            <h3 className="text-sm font-medium flex items-center gap-2">
              🤖 시스템 프롬프트
            </h3>
            <span>{expandedSections.system ? '▲' : '▼'}</span>
          </div>
          
          {expandedSections.system && (
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="시스템 프롬프트를 입력하세요... (AI의 역할과 지시사항을 정의)"
              className="w-full h-24 p-3 bg-transparent border rounded-md text-sm resize-y"
              style={{ 
                borderColor: 'var(--border-primary)',
                color: 'var(--text-primary)'
              }}
            />
          )}
        </div>

        {/* Main Prompt Section - 가장 큰 영역 */}
        <div className="card">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            💬 메인 프롬프트
          </h3>
          <textarea
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            placeholder="프롬프트를 입력하세요... (변수는 {{variable_name}} 형식으로 사용)"
            className="w-full p-4 bg-transparent border-none resize-none text-sm font-mono"
            style={{ 
              color: 'var(--text-primary)',
              fontFamily: 'Courier New, monospace',
              lineHeight: '1.6',
              height: '300px', // 줄인 높이
              minHeight: '300px',
              resize: 'none'
            }}
          />
        </div>

        {/* Variables Section */}
        <div className="card">
          <div 
            className="flex items-center justify-between cursor-pointer mb-3"
            onClick={() => toggleSection('variables')}
          >
            <h3 className="text-sm font-medium flex items-center gap-2">
              🔧 템플릿 변수
              <span className="text-xs px-2 py-1 rounded bg-gray-700">
                {extractedVariables.length}개
              </span>
            </h3>
            <span>{expandedSections.variables ? '▲' : '▼'}</span>
          </div>
          
          {expandedSections.variables && (
            <div className="space-y-4">
              {/* Add Variable - 변수명과 내용을 동시에 입력 */}
              <div className="grid grid-cols-3 gap-3">
                <input
                  type="text"
                  value={newVariable.name}
                  onChange={(e) => setNewVariable(prev => ({ ...prev, name: e.target.value }))}
                  className="input text-sm"
                  placeholder="변수명"
                />
                <input
                  type="text"
                  value={newVariable.value}
                  onChange={(e) => setNewVariable(prev => ({ ...prev, value: e.target.value }))}
                  className="input text-sm"
                  placeholder="변수값"
                />
                <button 
                  className="btn btn-primary"
                  onClick={handleAddVariable}
                >
                  추가
                </button>
              </div>

              {/* Variable List */}
              <div className="space-y-2">
                {extractedVariables.length === 0 ? (
                  <div className="text-center py-4" style={{ color: 'var(--text-muted)' }}>
                    <p>프롬프트에 변수가 없습니다.</p>
                    <p className="text-xs mt-1">변수를 사용하려면 <code>{'{{변수명}}'}</code> 형식으로 작성하세요.</p>
                  </div>
                ) : (
                  extractedVariables.map(variable => (
                    <div key={variable} className="flex items-start gap-3 p-3 border rounded-lg"
                         style={{ borderColor: 'var(--border-primary)' }}>
                      <div className="flex-shrink-0 pt-1">
                        <span className="variable-badge">{`{{${variable}}}`}</span>
                      </div>
                      <textarea
                        value={variables[variable] || ''}
                        onChange={(e) => setVariables(prev => ({ ...prev, [variable]: e.target.value }))}
                        className="flex-1 h-16 p-2 border rounded resize-y text-sm"
                        style={{ 
                          borderColor: 'var(--border-primary)',
                          background: 'var(--bg-tertiary)',
                          color: 'var(--text-primary)'
                        }}
                        placeholder={`${variable} 값을 입력하세요...`}
                      />
                      <button
                        className="flex-shrink-0 text-xs px-2 py-1 rounded hover:bg-red-600 transition-colors"
                        style={{ color: 'var(--accent-danger)' }}
                        onClick={() => handleRemoveVariable(variable)}
                      >
                        삭제
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button 
            className="btn btn-secondary flex-1"
            onClick={() => setIsPreviewMode(!isPreviewMode)}
          >
            👁️ {isPreviewMode ? '편집 모드' : '미리보기'}
          </button>
          <button 
            className="btn btn-primary flex-1"
            onClick={handleSave}
          >
            💾 저장
          </button>
        </div>

        {/* Preview */}
        {isPreviewMode && (
          <div className="card">
            <h4 className="text-sm font-medium mb-3" style={{ color: 'var(--text-primary)' }}>
              미리보기
            </h4>
            
            {systemPrompt && (
              <div className="mb-4 p-3 rounded border"
                   style={{ 
                     background: 'rgba(34, 197, 94, 0.1)',
                     borderColor: 'var(--accent-success)'
                   }}>
                <div className="text-xs mb-2" style={{ color: 'var(--accent-success)' }}>
                  시스템 프롬프트:
                </div>
                <pre className="whitespace-pre-wrap text-sm"
                     style={{ color: 'var(--text-secondary)' }}>
                  {systemPrompt}
                </pre>
              </div>
            )}
            
            <div className="p-4 rounded border" 
                 style={{ 
                   background: 'rgba(15, 23, 42, 0.8)',
                   borderColor: 'var(--border-secondary)'
                 }}>
              <pre className="whitespace-pre-wrap text-sm font-mono"
                   style={{ color: 'var(--text-secondary)' }}>
                {renderPromptWithVariables()}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PromptEditor;