// src/frontend/components/prompt/PromptEditor.jsx
import React, { useState, useEffect } from 'react';
import { useStore } from '../../store.jsx';

const PromptEditor = ({ taskId, versionId }) => {
  const {
    tasks,
    createVersion,
    setCurrentVersion,
    currentVersion,
    updateVersion
  } = useStore();
  
  const [promptText, setPromptText] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [taskName, setTaskName] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [variables, setVariables] = useState({});
  const [activeTab, setActiveTab] = useState('prompt'); // 'prompt' or 'variables'
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [newVariable, setNewVariable] = useState({ name: '', value: '' });
  const [isEditingName, setIsEditingName] = useState(false);

  const currentTask = taskId ? tasks[taskId] : null;
  const currentVersionData = currentTask?.versions?.find(v => v.id === versionId);

  useEffect(() => {
    if (currentTask) {
      setTaskName(currentTask.name || '');
    }
    if (currentVersionData) {
      setPromptText(currentVersionData.content || '');
      setSystemPrompt(currentVersionData.system_prompt || '');
      setTaskDescription(currentVersionData.description || '');
      setVariables(currentVersionData.variables || {});
    }
  }, [currentTask, currentVersionData]);

  const extractedVariables = React.useMemo(() => {
    const matches = promptText.match(/\{\{(\w+)\}\}/g) || [];
    return [...new Set(matches.map(match => match.slice(2, -2)))];
  }, [promptText]);

  const handleSave = async () => {
    if (!taskId || !versionId) return;
    try {
      await updateVersion(taskId, versionId, {
        content: promptText,
        system_prompt: systemPrompt,
        description: taskDescription,
        variables,
      });
    } catch (error) {
      console.error('저장 실패:', error);
    }
  };

  const handleSaveName = async () => {
    if (!taskId || !taskName.trim()) return;
    try {
      // This should ideally be in the store as well
      // For now, let's assume `updateTask` is still there for this purpose
      // await updateTask(taskId, { name: taskName.trim() });
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
        await createVersion(taskId, versionName, promptText, systemPrompt, taskDescription);
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
        <p className="text-muted">Select a task to start editing</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {/* Task Name */}
            {isEditingName ? (
              <input
                type="text"
                value={taskName}
                onChange={(e) => setTaskName(e.target.value)}
                className="input text-lg font-semibold bg-transparent border-none p-0 focus:ring-0"
                onBlur={handleSaveName}
                onKeyPress={(e) => e.key === 'Enter' && handleSaveName()}
                autoFocus
              />
            ) : (
              <h2 
                className="text-lg font-medium cursor-pointer hover:opacity-75 transition-opacity"
                style={{ color: 'var(--text-primary)' }}
                onClick={() => setIsEditingName(true)}
                title="Click to edit name"
              >
                {currentTask.name} ✏️
              </h2>
            )}
            
            <div className="px-2 py-1 rounded text-xs font-medium"
                 style={{ 
                   background: 'rgba(16, 185, 129, 0.2)', 
                   color: 'var(--accent-success)' 
                 }}>
              Active
            </div>
          </div>
          
          <div className="flex gap-2">
            <button className="btn btn-secondary" onClick={() => navigator.clipboard.writeText(promptText)}>
              📋 Copy
            </button>
            <button className="btn btn-primary" onClick={handleNewVersion}>
              🌿 New Version
            </button>
          </div>
        </div>

        {/* Version Timeline */}
        {currentTask.versions && currentTask.versions.length > 0 && (
          <div className="version-timeline">
            <div className="timeline-line"></div>
            {currentTask.versions.map((version, index) => (
              <div key={version.id} className="timeline-item">
                <div 
                  className={`timeline-dot ${currentVersion === version.id ? 'active' : ''}`}
                  onClick={() => setCurrentVersion(version.id)}
                />
                <div className={`timeline-label ${currentVersion === version.id ? 'active' : ''}`}>
                  {version.name || `v${index + 1}`}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="tab-container mt-4">
          <button 
            className={`tab ${activeTab === 'prompt' ? 'active' : ''}`}
            onClick={() => setActiveTab('prompt')}
          >
            Prompt
          </button>
          <button 
            className={`tab ${activeTab === 'variables' ? 'active' : ''}`}
            onClick={() => setActiveTab('variables')}
          >
            Variables ({extractedVariables.length})
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4" style={{ height: 0 }}>
        {activeTab === 'prompt' ? (
          /* Prompt Tab */
          <div className="space-y-4">
            {/* Description */}
            <div className="card">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                📝 Prompt Description
              </h3>
              <textarea
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                placeholder="Describe the purpose and usage of this prompt..."
                className="w-full h-16 p-3 bg-transparent border rounded text-sm"
                style={{ 
                  borderColor: 'var(--border-primary)',
                  color: 'var(--text-primary)'
                }}
              />
            </div>

            {/* System Prompt */}
            <div className="card">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                🤖 System Prompt
              </h3>
              <textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="Define AI role and instructions..."
                className="w-full h-20 p-3 bg-transparent border rounded text-sm"
                style={{ 
                  borderColor: 'var(--border-primary)',
                  color: 'var(--text-primary)'
                }}
              />
            </div>

            {/* Main Prompt */}
            <div className="card">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                💬 Main Prompt
              </h3>
              <textarea
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                placeholder="Enter prompt... (Use {{variable_name}} for variables)"
                className="w-full p-3 bg-transparent border-none text-sm font-mono"
                style={{ 
                  color: 'var(--text-primary)',
                  fontFamily: 'SF Mono, Monaco, monospace',
                  lineHeight: '1.5',
                  height: '300px',
                  minHeight: '300px',
                  resize: 'none'
                }}
              />
            </div>

            {/* Preview */}
            {isPreviewMode && (
              <div className="card">
                <h4 className="text-sm font-medium mb-3">Preview</h4>
                
                {systemPrompt && (
                  <div className="mb-4 p-3 rounded border"
                       style={{ 
                         background: 'rgba(16, 185, 129, 0.1)',
                         borderColor: 'var(--accent-success)'
                       }}>
                    <div className="text-xs mb-2" style={{ color: 'var(--accent-success)' }}>
                      System:
                    </div>
                    <pre className="whitespace-pre-wrap text-sm" style={{ color: 'var(--text-secondary)' }}>
                      {systemPrompt}
                    </pre>
                  </div>
                )}
                
                <div className="p-3 rounded border" 
                     style={{ 
                       background: 'var(--bg-tertiary)',
                       borderColor: 'var(--border-primary)'
                     }}>
                  <pre className="whitespace-pre-wrap text-sm font-mono" style={{ color: 'var(--text-secondary)' }}>
                    {renderPromptWithVariables()}
                  </pre>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Variables Tab */
          <div className="space-y-4">
            {/* Add Variable */}
            <div className="card">
              <h3 className="text-sm font-medium mb-3">Add Variable</h3>
              <div className="space-y-3">
                <input
                  type="text"
                  value={newVariable.name}
                  onChange={(e) => setNewVariable(prev => ({ ...prev, name: e.target.value }))}
                  className="input text-sm w-full"
                  placeholder="Variable Name (e.g., topic, tone, audience)"
                />
                <div className="flex gap-2">
                  <textarea
                    value={newVariable.value}
                    onChange={(e) => setNewVariable(prev => ({ ...prev, value: e.target.value }))}
                    className="input text-sm flex-1"
                    placeholder="Variable Value (supports multiline text, documents, etc.)"
                    rows="3"
                    style={{ resize: 'vertical', minHeight: '60px' }}
                  />
                  <button 
                    className="btn btn-primary" 
                    onClick={handleAddVariable}
                    style={{ alignSelf: 'flex-start', minWidth: '60px' }}
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>

            {/* Variable List */}
            <div className="space-y-3">
              {extractedVariables.length === 0 ? (
                <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
                  <p>No variables in prompt.</p>
                  <p className="text-xs mt-1">Use <code>{'{{'}variable_name{'}}'}</code> format in your prompt.</p>
                </div>
              ) : (
                extractedVariables.map(variable => (
                  <div key={variable} className="card">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 pt-2">
                        <span className="variable-badge">{`{{${variable}}}`}</span>
                      </div>
                      <div className="flex-1">
                        <label className="block text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
                          {variable}
                        </label>
                        <textarea
                          value={variables[variable] || ''}
                          onChange={(e) => setVariables(prev => ({ ...prev, [variable]: e.target.value }))}
                          className="w-full p-2 border rounded text-sm"
                          style={{ 
                            borderColor: 'var(--border-primary)',
                            background: 'var(--bg-tertiary)',
                            color: 'var(--text-primary)',
                            resize: 'vertical',
                            minHeight: '80px'
                          }}
                          placeholder={`Enter value for ${variable}... (supports multiline text)`}
                          rows="3"
                        />
                      </div>
                      <button
                        className="flex-shrink-0 text-xs px-2 py-1 rounded transition-colors"
                        style={{ 
                          color: 'var(--accent-danger)',
                          background: 'transparent',
                          border: '1px solid var(--accent-danger)',
                          marginTop: '20px'
                        }}
                        onClick={() => handleRemoveVariable(variable)}
                        onMouseEnter={(e) => {
                          e.target.style.background = 'var(--accent-danger)';
                          e.target.style.color = 'white';
                        }}
                        onMouseLeave={(e) => {
                          e.target.style.background = 'transparent';
                          e.target.style.color = 'var(--accent-danger)';
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="flex gap-2 p-4 border-t" style={{ borderColor: 'var(--border-primary)' }}>
        <button 
          className="btn btn-secondary flex-1"
          onClick={() => setIsPreviewMode(!isPreviewMode)}
        >
          👁️ {isPreviewMode ? 'Edit Mode' : 'Preview'}
        </button>
        <button
          className="btn btn-primary flex-1"
          onClick={handleSave}
          disabled={!taskId || !versionId}
        >
          💾 Save
        </button>
      </div>
    </div>
  );
};

export default PromptEditor;