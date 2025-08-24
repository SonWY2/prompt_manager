// src/frontend/components/prompt/PromptEditor.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useStore } from '../../store.jsx';

// Highlight Editor Component for syntax highlighting of variables
const HighlightEditor = ({ value, onChange, placeholder, className, style }) => {
  const editorRef = useRef(null);
  const [isComposing, setIsComposing] = useState(false);

  // Function to highlight variables in text
  const highlightText = (text) => {
    if (!text) return '';
    
    // Replace {{ }} variables with highlighted spans
    return text.replace(/\{\{([^}]+)\}\}/g, (match, variable) => {
      return `<span class="variable-highlight">{{${variable.trim()}}}</span>`;
    });
  };

  // Update editor content when value changes
  useEffect(() => {
    if (editorRef.current && !isComposing) {
      const currentHTML = editorRef.current.innerHTML;
      const expectedHTML = highlightText(value) || '';
      
      // Only update if HTML content actually needs to change
      if (currentHTML !== expectedHTML) {
        const selection = window.getSelection();
        const range = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
        
        // Store cursor position more accurately
        let cursorPosition = 0;
        let shouldRestoreCursor = false;
        
        if (range && editorRef.current.contains(range.startContainer)) {
          shouldRestoreCursor = true;
          
          // Calculate cursor position by counting characters
          const textContent = editorRef.current.textContent || '';
          const rangeBefore = range.cloneRange();
          rangeBefore.selectNodeContents(editorRef.current);
          rangeBefore.setEnd(range.startContainer, range.startOffset);
          cursorPosition = rangeBefore.toString().length;
        }
        
        // Update innerHTML with highlighted content
        editorRef.current.innerHTML = expectedHTML;
        
        // Restore cursor position if needed
        if (shouldRestoreCursor) {
          requestAnimationFrame(() => {
            try {
              const textContent = editorRef.current.textContent || '';
              
              // Ensure cursor position is within bounds
              cursorPosition = Math.min(cursorPosition, textContent.length);
              
              if (cursorPosition === 0) {
                // If cursor should be at the beginning
                const firstTextNode = getFirstTextNode(editorRef.current);
                if (firstTextNode) {
                  const newRange = document.createRange();
                  newRange.setStart(firstTextNode, 0);
                  newRange.collapse(true);
                  selection.removeAllRanges();
                  selection.addRange(newRange);
                }
                return;
              }
              
              // Find the correct text node and offset
              const { node, offset } = findTextNodeAtPosition(editorRef.current, cursorPosition);
              
              if (node) {
                const newRange = document.createRange();
                newRange.setStart(node, Math.min(offset, node.textContent.length));
                newRange.collapse(true);
                
                selection.removeAllRanges();
                selection.addRange(newRange);
              }
            } catch (e) {
              console.warn('Cursor restoration failed:', e);
              // Fallback: place cursor at the end
              try {
                const lastTextNode = getLastTextNode(editorRef.current);
                if (lastTextNode) {
                  const newRange = document.createRange();
                  newRange.setStart(lastTextNode, lastTextNode.textContent.length);
                  newRange.collapse(true);
                  selection.removeAllRanges();
                  selection.addRange(newRange);
                }
              } catch (fallbackError) {
                console.warn('Fallback cursor placement failed:', fallbackError);
              }
            }
          });
        }
      }
    }
  }, [value, isComposing]);
  
  // Helper function to find first text node
  const getFirstTextNode = (element) => {
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    return walker.nextNode();
  };
  
  // Helper function to find last text node  
  const getLastTextNode = (element) => {
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    let lastNode = null;
    while (walker.nextNode()) {
      lastNode = walker.currentNode;
    }
    return lastNode;
  };
  
  // Helper function to find text node at specific position
  const findTextNodeAtPosition = (element, position) => {
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    let currentPosition = 0;
    
    while (walker.nextNode()) {
      const node = walker.currentNode;
      const nodeLength = node.textContent.length;
      
      if (currentPosition + nodeLength >= position) {
        return {
          node: node,
          offset: position - currentPosition
        };
      }
      
      currentPosition += nodeLength;
    }
    
    // If position is beyond content, return last text node
    const lastNode = getLastTextNode(element);
    return {
      node: lastNode,
      offset: lastNode ? lastNode.textContent.length : 0
    };
  };

  const handleInput = (e) => {
    if (!isComposing && onChange) {
      const text = e.target.innerText || '';
      onChange(text);
    }
  };

  const handleCompositionStart = () => {
    setIsComposing(true);
  };

  const handleCompositionEnd = (e) => {
    setIsComposing(false);
    if (onChange) {
      const text = e.target.innerText || '';
      onChange(text);
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const text = e.clipboardData.getData('text/plain');
    document.execCommand('insertText', false, text);
  };

  const handleKeyDown = (e) => {
    // Handle Enter key for consistent line breaks
    if (e.key === 'Enter') {
      e.preventDefault();
      document.execCommand('insertLineBreak');
      return;
    }
    
    // Handle Tab key (optional: insert spaces instead of losing focus)
    if (e.key === 'Tab') {
      e.preventDefault();
      document.execCommand('insertText', false, '  '); // Insert 2 spaces
      return;
    }
  };

  return (
    <div
      ref={editorRef}
      contentEditable
      className={`highlight-editor ${className || ''}`}
      style={{
        ...style,
        whiteSpace: 'pre-wrap',
        wordWrap: 'break-word',
        outline: 'none',
      }}
      onInput={handleInput}
      onCompositionStart={handleCompositionStart}
      onCompositionEnd={handleCompositionEnd}
      onPaste={handlePaste}
      onKeyDown={handleKeyDown}
      data-placeholder={placeholder}
      suppressContentEditableWarning={true}
    />
  );
};

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
  const [taskVariables, setTaskVariables] = useState({});  // Task 레벨 variables
  const [activeTab, setActiveTab] = useState('prompt'); // 'prompt' or 'variables'
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [newVariable, setNewVariable] = useState({ name: '', value: '' });
  const [isEditingName, setIsEditingName] = useState(false);

  const currentTask = taskId ? tasks[taskId] : null;

  // Task variables 로드
  useEffect(() => {
    const loadTaskVariables = async () => {
      if (!taskId) return;
      try {
        const response = await fetch(`/api/tasks/${taskId}/variables`);
        if (response.ok) {
          const data = await response.json();
          setTaskVariables(data.variables || {});
        }
      } catch (error) {
        console.error('Task variables 로드 실패:', error);
      }
    };
    loadTaskVariables();
  }, [taskId]);

  useEffect(() => {
    const currentVersionData = currentTask?.versions?.find(v => v.id === versionId);

    if (currentTask) {
      setTaskName(currentTask.name || '');
    }
    if (currentVersionData) {
      setPromptText(currentVersionData.content || '');
      setSystemPrompt(currentVersionData.system_prompt || 'You are a helpfull AI Assistant');
      setTaskDescription(currentVersionData.description || '');
    } else {
      // Clear fields if no version is selected or found
      setPromptText('');
      setSystemPrompt('You are a helpfull AI Assistant');
      setTaskDescription('');
    }
  }, [versionId, currentTask]); // Depend directly on versionId and currentTask

  const extractedVariables = React.useMemo(() => {
    if (!currentTask) return [];
    const allPromptsContent = new Set();
    if (currentTask.versions) {
      currentTask.versions.forEach(version => {
        if (version.content) allPromptsContent.add(version.content);
        if (version.system_prompt) allPromptsContent.add(version.system_prompt);
      });
    }
    allPromptsContent.add(promptText);
    allPromptsContent.add(systemPrompt);
    const allMatches = [];
    allPromptsContent.forEach(p => {
      const matches = p.match(/\{\{(\w+)\}\}/g) || [];
      allMatches.push(...matches);
    });
    return [...new Set(allMatches.map(match => match.slice(2, -2)))];
  }, [currentTask, promptText, systemPrompt]);

  const displayedVariables = React.useMemo(() => {
    const fromPrompts = extractedVariables;
    const fromState = Object.keys(taskVariables);
    return [...new Set([...fromPrompts, ...fromState])];
  }, [extractedVariables, taskVariables]);

  // Automatically add new variables from prompt to taskVariables
  useEffect(() => {
    const newVars = extractedVariables.filter(v => v && v !== 'variables' && !taskVariables.hasOwnProperty(v));
    if (newVars.length > 0) {
      const updatedVariables = { ...taskVariables };
      newVars.forEach(v => {
        updatedVariables[v] = '';
      });
      saveTaskVariables(updatedVariables);
    }
  }, [extractedVariables, taskVariables]);


  const handleSave = async () => {
    if (!taskId || !versionId) return;
    try {
      await updateVersion(taskId, versionId, {
        content: promptText,
        system_prompt: systemPrompt,
        description: taskDescription,
      });
    } catch (error) {
      console.error('저장 실패:', error);
    }
  };

  // Task variables 저장 함수
  const saveTaskVariables = async (newVariables) => {
    if (!taskId) return;
    try {
      const response = await fetch(`/api/tasks/${taskId}/variables`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({variables: newVariables})
      });
      if (response.ok) {
        setTaskVariables(newVariables);
      }
    } catch (error) {
      console.error('Variables 저장 실패:', error);
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
        console.error('Failed to copy version:', error);
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
            
            <div className="px-2 py-1 rounded text-xs font-medium"
                 style={{ 
                   background: 'rgba(16, 185, 129, 0.2)', 
                   color: 'var(--accent-success)' 
                 }}>
              Active
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
        {!versionId ? (
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
                className="w-full h-2 my-2 cursor-row-resize bg-gray-200 dark:bg-gray-700 hover:bg-blue-400 transition-colors"
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
                className="w-full h-2 my-2 cursor-row-resize bg-gray-200 dark:bg-gray-700 hover:bg-blue-400 transition-colors"
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
    
    .highlight-editor:focus {
      border-color: var(--accent-primary);
      box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.2);
    }
    
    .highlight-editor * {
      white-space: pre-wrap;
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
      white-space: nowrap;
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
    
    .highlight-editor div {
      display: inline;
    }
    
    .highlight-editor p {
      margin: 0;
      display: inline;
    }
  `;
  
  document.head.appendChild(styleElement);
};

// Initialize styles when component is loaded
addHighlightStyles();
