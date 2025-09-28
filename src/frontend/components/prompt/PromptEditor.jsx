// src/frontend/components/prompt/PromptEditor.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useStore } from '../../store.jsx';

 // Highlight Editor Component (overlay highlighter to avoid cursor jump)
const HighlightEditor = ({ value, onChange, onBlur, placeholder, className, style }) => {
  const containerRef = useRef(null);
  const textareaRef = useRef(null);
  const overlayContentRef = useRef(null);

  const escapeHtml = (text) => {
    if (text == null) return '';
    return String(text)
      .replace(/&/g, '&')
      .replace(/</g, '<')
      .replace(/>/g, '>')
      .replace(/"/g, '"')
      .replace(/'/g, '&#39;');
  };

  const renderHighlightedContent = (text) => {
    if (!text) return null;
    
    // Split text by variables and render each part
    const parts = text.split(/(\{\{[^}]+\}\})/g);
    
    const renderedElements = parts.map((part, index) => {
      if (part.match(/\{\{[^}]+\}\}/)) {
        // This is a variable
        const variable = part.slice(2, -2).trim();
        const element = (
          <span 
            key={index} 
            className="variable-highlight"
          >
            {`{{${variable}}}`}
          </span>
        );
        return element;
      } else if (part.length > 0) {
        // Render ALL text parts (including whitespace) as transparent to maintain layout
        const element = (
          <span 
            key={index} 
            style={{ 
              color: 'transparent'
            }}
          >
            {part}
          </span>
        );
        return element;
      } else {
        // 빈 문자열도 빈 span으로 렌더링해서 위치를 유지
        const element = (
          <span 
            key={index}
          >
            {part}
          </span>
        );
        return element;
      }
    });
    
    return renderedElements;
  };

  const handleScrollSync = (e) => {
    const t = e.currentTarget;
    if (overlayContentRef.current) {
      overlayContentRef.current.style.transform = `translate(${-t.scrollLeft}px, ${-t.scrollTop}px)`;
    }
  };

  // Keep overlay transform in sync if value changes and textarea has scrolled
  useEffect(() => {
    if (overlayContentRef.current && textareaRef.current) {
      const t = textareaRef.current;
      const overlay = overlayContentRef.current;
      const overlayContainer = overlay.parentElement;
      const mainContainer = containerRef.current;
      
      overlay.style.transform = `translate(${-t.scrollLeft}px, ${-t.scrollTop}px)`;
      
      // Position overlay to match textarea
    }
  }, [value]);

  return (
    <div
      ref={containerRef}
      className={`highlight-editor ${className || ''}`}
      style={{
        position: 'relative',
        // container keeps visual styles via existing CSS + incoming style
        ...style
      }}
    >
      {/* Highlight overlay - only shows variable highlighting */}
      <div
        aria-hidden="true"
        className="highlight-overlay"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          overflow: 'hidden',
          pointerEvents: 'none',
          zIndex: 1,
          padding: 0,
          margin: 0,
          border: 'none',
          fontFamily: 'inherit',
          fontSize: 'inherit',
          lineHeight: 'inherit',
          boxSizing: 'border-box'
        }}
      >
        <div
          ref={overlayContentRef}
          className="overlay-content"
          style={{
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
            overflowWrap: 'break-word',
            minHeight: '100%',
            fontFamily: 'inherit',
            fontSize: 'inherit',
            lineHeight: 'inherit',
            padding: '12px',
            margin: 0,
            border: 'none',
            color: 'transparent',
            boxSizing: 'border-box'
          }}
        >
          {renderHighlightedContent(value)}
        </div>
      </div>

      {/* Real input (caret/selection lives here); never rewrite DOM so no cursor jump */}
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
        onBlur={onBlur}
        onScroll={handleScrollSync}
        placeholder={placeholder}
        spellCheck={false}
        autoCorrect="off"
        autoCapitalize="off"
        className="highlight-input"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          width: '100%',
          height: '100%',
          background: 'transparent',
          color: 'var(--text-primary)',
          border: 'none',
          resize: 'none',
          outline: 'none',
          fontFamily: 'inherit',
          fontSize: '13px',
          lineHeight: '1.5',
          padding: '12px',
          margin: 0,
          boxSizing: 'border-box',
          zIndex: 2
        }}
      />
    </div>
  );
};

const PromptEditor = ({ taskId, versionId }) => {
  const {
    tasks,
    createVersion,
    setCurrentVersion,
    currentVersion,
    updateVersion,
    updateVariables
  } = useStore();
  
  const [promptText, setPromptText] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [taskName, setTaskName] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [taskVariables, setTaskVariables] = useState({});  // Task 레벨 variables
  const [activeTab, setActiveTab] = useState('prompt'); // 'prompt' or 'variables'
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [newVariable, setNewVariable] = useState({ name: '', value: '' });
  const [isEditingName, setIsEditingName] = useState(false);
  
  // 자동 저장 관련 상태
  const [saveStatus, setSaveStatus] = useState('saved'); // 'saving', 'saved', 'error'
  const autoSaveTimeoutRef = useRef(null);
  const lastSavedContentRef = useRef({ promptText: '', systemPrompt: '', taskDescription: '' });

  const currentTask = taskId ? tasks[taskId] : null;

  // Task variables를 store의 currentTask에서 직접 가져오기
  useEffect(() => {
    console.log(`🔧 [DEBUG] PromptEditor: Task 변수 로드 useEffect 실행`, { 
      currentTask: !!currentTask, 
      taskId, 
      hasVariables: !!(currentTask?.variables) 
    });
    
    if (currentTask) {
      const variables = currentTask.variables || {};
      console.log(`🔧 [DEBUG] PromptEditor: store에서 Task 변수 로드 완료`, { 
        taskId, 
        variables,
        variableCount: Object.keys(variables).length 
      });
      setTaskVariables(variables);
    } else {
      console.log(`🔧 [DEBUG] PromptEditor: currentTask가 없어서 변수 초기화`);
      setTaskVariables({});
    }
  }, [currentTask, taskId]);

  useEffect(() => {
    const currentVersionData = currentTask?.versions?.find(v => v.id === versionId);

    if (currentTask) {
      setTaskName(currentTask.name || '');
    }
    
    if (currentVersionData) {
      // 기존 버전 데이터 로드
      const content = currentVersionData.content || '';
      const system_prompt = currentVersionData.system_prompt || 'You are a helpfull AI Assistant';
      const description = currentVersionData.description || '';
      
      setPromptText(content);
      setSystemPrompt(system_prompt);
      setTaskDescription(description);
      
      // 초기 로드시 마지막 저장된 내용 설정
      lastSavedContentRef.current = {
        promptText: content,
        systemPrompt: system_prompt,
        taskDescription: description
      };
      setSaveStatus('saved');
    } else {
      // Clear fields if no version is selected or found
      const defaultSystemPrompt = 'You are a helpfull AI Assistant';
      
      setPromptText('');
      setSystemPrompt(defaultSystemPrompt);
      setTaskDescription('');
      
      // 빈 상태로 초기화
      lastSavedContentRef.current = {
        promptText: '',
        systemPrompt: defaultSystemPrompt,
        taskDescription: ''
      };
    }
  }, [versionId, currentTask]); // Depend directly on versionId and currentTask

  const extractedVariables = React.useMemo(() => {
    if (!currentTask) return [];
    
    const allPromptsContent = new Set();
    
    // 기존 버전들의 내용 수집
    if (currentTask.versions) {
      currentTask.versions.forEach((version) => {
        if (version.content) allPromptsContent.add(version.content);
        if (version.system_prompt) allPromptsContent.add(version.system_prompt);
      });
    }
    
    // 현재 편집 중인 내용 추가
    if (promptText) allPromptsContent.add(promptText);
    if (systemPrompt) allPromptsContent.add(systemPrompt);
    
    const allMatches = [];
    allPromptsContent.forEach((p) => {
      // 더 정확한 변수 추출을 위해 영문자, 숫자, 언더스코어, 하이픈만 허용
      const matches = p.match(/\{\{([a-zA-Z_][a-zA-Z0-9_-]*)\}\}/g) || [];
      allMatches.push(...matches);
    });
    
    const extractedVars = [...new Set(allMatches.map(match => match.slice(2, -2)))];
    return extractedVars;
  }, [currentTask, promptText, systemPrompt]);

  const displayedVariables = React.useMemo(() => {
    const fromPrompts = extractedVariables;
    const fromState = Object.keys(taskVariables);
    return [...new Set([...fromPrompts, ...fromState])];
  }, [extractedVariables, taskVariables]);

  // 실제 자동 저장 실행
  const handleAutoSave = useCallback(async () => {
    if (!taskId || !versionId) return;
    
    // 변경사항이 있는지 확인
    const currentContent = {
      promptText,
      systemPrompt,
      taskDescription
    };
    
    const lastSaved = lastSavedContentRef.current;
    const hasChanges = (
      currentContent.promptText !== lastSaved.promptText ||
      currentContent.systemPrompt !== lastSaved.systemPrompt ||
      currentContent.taskDescription !== lastSaved.taskDescription
    );
    
    if (!hasChanges) {
      return; // 변경사항이 없으면 저장하지 않음
    }
    
    try {
      setSaveStatus('saving');
      await updateVersion(taskId, versionId, {
        content: promptText,
        system_prompt: systemPrompt,
        description: taskDescription,
      });
      
      // 저장 완료 후 마지막 저장된 내용 업데이트
      lastSavedContentRef.current = currentContent;
      setSaveStatus('saved');
    } catch (error) {
      // Auto-save failed
      setSaveStatus('error');
      // 5초 후 에러 상태 초기화
      setTimeout(() => setSaveStatus('saved'), 5000);
    }
  }, [taskId, versionId, promptText, systemPrompt, taskDescription, updateVersion]);

  // 자동 저장 함수 (debounced)
  const scheduleAutoSave = useCallback(() => {
    if (!taskId || !versionId) return;
    
    // 이전 타이머 취소
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }
    
    // 2초 후 자동 저장 실행
    autoSaveTimeoutRef.current = setTimeout(() => {
      handleAutoSave();
    }, 2000);
  }, [taskId, versionId, handleAutoSave]);

  // blur 이벤트에서 즉시 저장
  const handleBlurSave = useCallback(() => {
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
      autoSaveTimeoutRef.current = null;
    }
    handleAutoSave();
  }, [handleAutoSave]);

  // 🚫 자동 변수 추가 기능 임시 비활성화 (변수 초기화 문제 해결을 위해)
  // TODO: 나중에 다시 활성화할 때는 로드 타이밍 문제 해결 필요
  /*
  useEffect(() => {
    // 자동으로 새 변수를 추가하는 로직 (현재 비활성화)
  }, [extractedVariables, taskVariables, currentTask]);
  */

  // 컨텐츠 변경 감지 및 자동 저장 스케줄링
  useEffect(() => {
    if (!taskId || !versionId) return;
    
    // 초기 로드가 완료된 후에만 자동 저장 스케줄링
    if (lastSavedContentRef.current.promptText !== undefined) {
      scheduleAutoSave();
    }
  }, [promptText, systemPrompt, taskDescription, scheduleAutoSave]);

  // 컴포넌트 언마운트시 타이머 정리
  useEffect(() => {
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, []);


  const handleSave = async () => {
    if (!taskId || !versionId) return;
    try {
      setSaveStatus('saving');
      await updateVersion(taskId, versionId, {
        content: promptText,
        system_prompt: systemPrompt,
        description: taskDescription,
      });
      
      // 저장 완료 후 마지막 저장된 내용 업데이트
      lastSavedContentRef.current = {
        promptText,
        systemPrompt,
        taskDescription
      };
      setSaveStatus('saved');
    } catch (error) {
      // Save failed
      setSaveStatus('error');
      // 3초 후 에러 상태 초기화
      setTimeout(() => setSaveStatus('saved'), 3000);
    }
  };

  // Task variables 저장 함수
  const saveTaskVariables = async (newVariables) => {
    if (!taskId) return;
    try {
      console.log('🔧 [DEBUG] PromptEditor에서 변수 저장 시작:', newVariables);
      
      // store의 updateVariables 사용하여 상태 동기화
      await updateVariables(taskId, newVariables);
      setTaskVariables(newVariables);
      
      console.log('✅ PromptEditor 변수 저장 완료:', newVariables);
    } catch (error) {
      console.error('❌ PromptEditor 변수 저장 오류:', error);
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
      // Name save failed
    }
  };

  const handleNewVersion = async () => {
    if (!taskId) return;
    try {
      const versionName = prompt('새 버전 이름을 입력하세요:');
      if (versionName) {
        // 새 버전은 빈 상태에서 시작해야 합니다
        const emptyContent = '';
        const defaultSystemPrompt = 'You are a helpful AI Assistant';
        const emptyDescription = '';
        
        await createVersion(taskId, versionName, emptyContent, defaultSystemPrompt, emptyDescription);
      }
    } catch (error) {
      // Version creation failed
    }
  };

  const handleCopyVersion = async () => {
    if (!taskId || !versionId) return;
    const currentVersionData = currentTask?.versions?.find(v => v.id === versionId);
    if (!currentVersionData) return;

    const newName = prompt(`Enter a name for the copied version:`, `${currentVersionData.name} (Copy)`);
    if (newName) {
      try {
        await createVersion(
          taskId,
          newName,
          currentVersionData.content,
          currentVersionData.system_prompt,
          currentVersionData.description
        );
      } catch (error) {
        // Failed to copy version
      }
    }
  };

  const handleAddVariable = async () => {
    if (!newVariable.name.trim()) return;
    const updatedVariables = { ...taskVariables, [newVariable.name.trim()]: newVariable.value };
    await saveTaskVariables(updatedVariables);
    setNewVariable({ name: '', value: '' });
  };

  const handleRemoveVariable = async (variable) => {
    const updatedVariables = { ...taskVariables };
    delete updatedVariables[variable];
    await saveTaskVariables(updatedVariables);
  };

  const renderPromptWithVariables = () => {
    let rendered = promptText;
    displayedVariables.forEach(variable => {
      const value = taskVariables[variable] || `{{${variable}}}`;
      rendered = rendered.replace(new RegExp(`\{\{${variable}\}\}`, 'g'), value);
    });
    return rendered;
  };

  // --- Collapse and Resize Logic ---
  const [collapsedSections, setCollapsedSections] = useState({
    description: false,
    system: false,
    main: false,
  });
  const [heights, setHeights] = useState({
    description: 80,
    system: 96,
  });
  const [dragging, setDragging] = useState(null);
  const editorContainerRef = useRef(null);

  const toggleSection = (section) => {
    setCollapsedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const onDragStart = (e, section) => {
    e.preventDefault();
    setDragging(section);
  };

  const onDragEnd = useCallback(() => {
    setDragging(null);
  }, []);

  const onDrag = useCallback((e) => {
    if (dragging === null || !editorContainerRef.current) return;
    e.preventDefault();

    const rect = editorContainerRef.current.getBoundingClientRect();
    const y = e.clientY - rect.top;

    if (dragging === 'description') {
      const newHeight = y - 20; // Adjust for padding and header
      if (newHeight > 40) {
        setHeights(h => ({ ...h, description: newHeight }));
      }
    } else if (dragging === 'system') {
      const descriptionHeight = collapsedSections.description ? 40 : heights.description;
      const newHeight = y - descriptionHeight - 60; // Adjust for padding, headers, and divider
      if (newHeight > 40) {
        setHeights(h => ({ ...h, system: newHeight }));
      }
    }
  }, [dragging, heights.description, collapsedSections.description]);

  useEffect(() => {
    if (dragging !== null) {
      document.addEventListener('mousemove', onDrag);
      document.addEventListener('mouseup', onDragEnd);
    } else {
      document.removeEventListener('mousemove', onDrag);
      document.removeEventListener('mouseup', onDragEnd);
    }
    return () => {
      document.removeEventListener('mousemove', onDrag);
      document.removeEventListener('mouseup', onDragEnd);
    };
  }, [dragging, onDrag, onDragEnd]);
  // --- End Logic ---

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
            
            <div className="flex gap-2">
              <div className="px-2 py-1 rounded text-xs font-medium"
                   style={{ 
                     background: 'rgba(16, 185, 129, 0.2)', 
                     color: 'var(--accent-success)' 
                   }}>
                Active
              </div>
              
              {/* 저장 상태 표시 */}
              <div className="px-2 py-1 rounded text-xs font-medium flex items-center gap-1"
                   style={{ 
                     background: saveStatus === 'saving' ? 'rgba(234, 179, 8, 0.2)' : 
                                saveStatus === 'error' ? 'rgba(239, 68, 68, 0.2)' : 
                                'rgba(107, 114, 128, 0.1)',
                     color: saveStatus === 'saving' ? '#eab308' : 
                           saveStatus === 'error' ? '#ef4444' : 
                           'var(--text-muted)'
                   }}>
                {saveStatus === 'saving' && (
                  <>
                    <span className="animate-spin">⟳</span>
                    Saving...
                  </>
                )}
                {saveStatus === 'saved' && (
                  <>
                    <span>✓</span>
                    Saved
                  </>
                )}
                {saveStatus === 'error' && (
                  <>
                    <span>✗</span>
                    Error
                  </>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex gap-2">
            <button className="btn btn-secondary" onClick={handleCopyVersion}>
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
              <div
                key={version.id}
                className="timeline-item"
                onClick={() => setCurrentVersion(version.id)}
              >
                <div 
                  className={`timeline-dot ${currentVersion === version.id ? 'active' : ''}`}
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
            Variables ({displayedVariables.length})
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4" style={{ height: 0 }}>
        {!versionId && activeTab === 'prompt' ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-muted">
              <div className="text-2xl mb-2">☝️</div>
              <p>Select a version from the timeline above to start editing.</p>
            </div>
          </div>
        ) : activeTab === 'prompt' ? (
          /* Prompt Tab */
          <div className="flex flex-col h-full" ref={editorContainerRef}>
            {/* Description */}
            <div className="card flex flex-col">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2 cursor-pointer" onClick={() => toggleSection('description')}>
                <span className="transform transition-transform duration-200">{collapsedSections.description ? '▶' : '▼'}</span>
                📝 Prompt Description
              </h3>
              {!collapsedSections.description && (
                <textarea
                  value={taskDescription}
                  onChange={(e) => setTaskDescription(e.target.value)}
                  onBlur={handleBlurSave}
                  placeholder="Describe the purpose and usage of this prompt..."
                  className="w-full p-3 bg-transparent border rounded text-sm"
                  style={{
                    height: `${heights.description}px`,
                    borderColor: 'var(--border-primary)',
                    color: 'var(--text-primary)',
                    resize: 'none'
                  }}
                />
              )}
            </div>
            
            {!collapsedSections.description && (
              <div 
                className="editor-divider my-2 cursor-row-resize"
                onMouseDown={(e) => onDragStart(e, 'description')}
              />
            )}

            {/* System Prompt */}
            <div className="card flex flex-col">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2 cursor-pointer" onClick={() => toggleSection('system')}>
                <span className="transform transition-transform duration-200">{collapsedSections.system ? '▶' : '▼'}</span>
                🤖 System Prompt
              </h3>
              {!collapsedSections.system && (
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  onBlur={handleBlurSave}
                  placeholder="Define AI role and instructions..."
                  className="w-full p-3 bg-transparent border rounded text-sm"
                  style={{
                    height: `${heights.system}px`,
                    borderColor: 'var(--border-primary)',
                    color: 'var(--text-primary)',
                    resize: 'none'
                  }}
                />
              )}
            </div>

            {!collapsedSections.system && (
               <div 
                className="editor-divider my-2 cursor-row-resize"
                onMouseDown={(e) => onDragStart(e, 'system')}
              />
            )}

            {/* Main Prompt */}
            <div className="card flex flex-col flex-1">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2 cursor-pointer" onClick={() => toggleSection('main')}>
                <span className="transform transition-transform duration-200">{collapsedSections.main ? '▶' : '▼'}</span>
                💬 Main Prompt
              </h3>
              {!collapsedSections.main && (
                <HighlightEditor
                  value={promptText}
                  onChange={setPromptText}
                  onBlur={handleBlurSave}
                  placeholder="Enter prompt... (Use {{variable_name}} for variables)"
                  className="w-full h-full p-3 text-sm flex-1"
                  style={{
                    color: 'var(--text-primary)',
                    fontFamily: 'inherit',
                    lineHeight: '1.5',
                    minHeight: '200px'
                  }}
                />
              )}
            </div>

            {/* Preview */}
            {isPreviewMode && (
              <div className="card mt-4">
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
              {displayedVariables.length === 0 ? (
                <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
                  <p>No variables in prompt.</p>
                  <p className="text-xs mt-1">Use <code>{'{{'}variable_name{'}}'}</code> format in your prompt.</p>
                </div>
              ) : (
                displayedVariables.map(variable => (
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
                          value={taskVariables[variable] || ''}
                          onChange={(e) => {
                            const updatedVariables = { ...taskVariables, [variable]: e.target.value };
                            setTaskVariables(updatedVariables);
                            // Auto-save after a delay could be added here
                          }}
                          onBlur={(e) => {
                            // Save on blur for better UX
                            const updatedVariables = { ...taskVariables, [variable]: e.target.value };
                            saveTaskVariables(updatedVariables);
                          }}
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
                          color: extractedVariables.includes(variable) ? 'var(--text-muted)' : 'var(--accent-danger)',
                          background: 'transparent',
                          border: `1px solid ${extractedVariables.includes(variable) ? 'var(--border-primary)' : 'var(--accent-danger)'}`,
                          marginTop: '20px',
                          cursor: extractedVariables.includes(variable) ? 'not-allowed' : 'pointer'
                        }}
                        onClick={() => handleRemoveVariable(variable)}
                        disabled={extractedVariables.includes(variable)}
                        title={extractedVariables.includes(variable) ? "Variable is used in a prompt and cannot be deleted." : "Delete variable"}
                        onMouseEnter={(e) => {
                          if (!extractedVariables.includes(variable)) {
                            e.target.style.background = 'var(--accent-danger)';
                            e.target.style.color = 'white';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!extractedVariables.includes(variable)) {
                            e.target.style.background = 'transparent';
                            e.target.style.color = 'var(--accent-danger)';
                          }
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
          className="btn btn-secondary flex-1"
          onClick={handleSave}
          disabled={!taskId || !versionId || saveStatus === 'saving'}
          title="Force save now (auto-save is enabled)"
        >
          {saveStatus === 'saving' ? (
            <span className="flex items-center gap-1">
              <span className="animate-spin">⟳</span>
              Saving...
            </span>
          ) : (
            <>⚡ Force Save</>
          )}
        </button>
      </div>
    </div>
  );
};

export default PromptEditor;

// Add CSS for variable highlighting
const addHighlightStyles = () => {
  if (document.head.querySelector('[data-highlight-editor]')) {
    return; // Styles already added
  }
  
  const styleElement = document.createElement('style');
  styleElement.setAttribute('data-highlight-editor', 'true');
  styleElement.textContent = `
    .highlight-editor {
      position: relative;
      white-space: pre-wrap;
      word-wrap: break-word;
      overflow-wrap: break-word;
      line-height: 1.5;
      background: var(--bg-tertiary);
      border: 1px solid var(--border-primary);
      border-radius: 6px;
      transition: border-color 0.2s ease;
    }
    
    .highlight-editor:focus,
    .highlight-editor:focus-within {
      border-color: var(--accent-primary);
      box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.2);
    }
    
    .highlight-editor * {
      white-space: pre-wrap;
    }
    
    .highlight-editor .highlight-input {
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      outline: none !important;
      resize: none !important;
      transform: none !important;
      color: var(--text-primary) !important;
      caret-color: var(--text-primary);
      font: inherit !important;
      line-height: inherit !important;
      padding: inherit !important;
    }

    .highlight-editor .highlight-input:focus {
      border: none !important;
      box-shadow: none !important;
      outline: none !important;
      background: transparent !important;
      transform: none !important;
    }

    .highlight-editor .overlay-content .variable-highlight {
      color: var(--accent-primary) !important;
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%);
      border: 1px solid rgba(139, 92, 246, 0.4);
      border-radius: 3px;
      padding: 1px 3px;
      margin: 0;
      display: inline;
      font-weight: 600;
      box-decoration-break: clone;
      -webkit-box-decoration-break: clone;
    }

    .highlight-editor:empty:before {
      content: attr(data-placeholder);
      color: var(--text-muted);
      pointer-events: none;
      font-style: italic;
      white-space: pre-wrap;
    }
    
    .variable-highlight {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
      color: var(--accent-primary);
      padding: 1px 4px;
      border-radius: 4px;
      font-weight: 600;
      border: 1px solid rgba(139, 92, 246, 0.25);
      box-shadow: 0 1px 2px rgba(139, 92, 246, 0.1);
      transition: all 0.2s ease;
      display: inline;
      margin: 0;
      white-space: inherit;
    }
    /* Overlay variable text color */
    .highlight-editor .overlay-content .variable-highlight {
      color: transparent !important; /* hide overlay text; show only background */
      -webkit-box-decoration-break: clone;
      box-decoration-break: clone;
      font-weight: 700;
    }
    
    .highlight-editor:focus .variable-highlight {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.25) 0%, rgba(168, 85, 247, 0.25) 100%);
      border-color: rgba(139, 92, 246, 0.4);
      box-shadow: 0 2px 4px rgba(139, 92, 246, 0.15);
    }
    
    .highlight-editor .variable-highlight:hover {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%);
      border-color: rgba(139, 92, 246, 0.5);
      transform: translateY(-1px);
    }
    
    /* Dark mode adjustments */
    [data-theme="dark"] .variable-highlight {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%);
      border-color: rgba(139, 92, 246, 0.3);
    }
    
    [data-theme="dark"] .highlight-editor:focus .variable-highlight {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%);
      border-color: rgba(139, 92, 246, 0.5);
    }
    
    /* Fix for line breaks and spacing */
    .highlight-editor br {
      line-height: 1.5;
    }

    /* Overlay content sync */
    .highlight-editor .overlay-content {
      font: inherit;
      line-height: inherit;
      padding: inherit;
      white-space: pre-wrap;
      word-break: break-word;
    }

    /* Remove duplicate styles - already defined above */

    /* Prevent inline forcing that broke layout */
    .highlight-editor div,
    .highlight-editor p {
      margin: 0;
      display: block;
    }
  `;
  
  document.head.appendChild(styleElement);
};

// Initialize styles when component is loaded
addHighlightStyles();
