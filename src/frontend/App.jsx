// src/frontend/App.jsx
import React, { useState, useEffect } from 'react';
import { useStore } from './store.jsx';
import ThreeColumnLayout from './components/layout/ThreeColumnLayout.jsx';
import TaskNavigator from './components/task/TaskNavigator.jsx';
import PromptEditor from './components/prompt/PromptEditor.jsx';
import ResultViewer from './components/result/ResultViewer.jsx';
import LLMEndpointSettings from './components/settings/LLMEndpointSettings.jsx';
import { apiUrl } from './utils/api.js';
import './App.css';

function App() {
  const {
    tasks, 
    loadTasks, 
    currentTask, 
    setCurrentTask,
    currentVersion,
    isDarkMode,
    toggleDarkMode,
    serverStatus,
    checkServerStatus,
    loadLlmEndpoints
  } = useStore();
  
  const [currentView, setCurrentView] = useState('task-list'); 
  const [initialLoadHandled, setInitialLoadHandled] = useState(false);

  // URL routing
  useEffect(() => {
    if (Object.keys(tasks).length === 0 && !initialLoadHandled) return;
    if (initialLoadHandled) return;

    const urlParams = new URLSearchParams(window.location.search);
    const taskIdFromUrl = urlParams.get('task');
    const settingsFromUrl = urlParams.get('settings');
    
    if (settingsFromUrl) {
      setCurrentTask(null);
      setCurrentView('settings');
    } else if (taskIdFromUrl && tasks[taskIdFromUrl]) {
      setCurrentTask(taskIdFromUrl);
      setCurrentView('task-detail');
    } else {
      setCurrentTask(null);
      setCurrentView('task-list');
    }
    setInitialLoadHandled(true);
  }, [tasks, setCurrentTask, initialLoadHandled]);

  const handleSelectTask = (taskId) => {
    if (taskId) {
      setCurrentTask(taskId);
      setCurrentView('task-detail');
      const newUrl = `${window.location.pathname}?task=${taskId}`;
      window.history.pushState({ taskId, view: 'task-detail' }, '', newUrl);
    } else {
      setCurrentTask(null);
      setCurrentView('task-list');
      window.history.pushState({ view: 'task-list' }, '', window.location.pathname);
    }
  };
  
  const handleOpenSettings = () => {
    setCurrentTask(null);
    setCurrentView('settings');
    const newUrl = `${window.location.pathname}?settings=llm-endpoints`;
    window.history.pushState({ view: 'settings' }, '', newUrl);
  };
  
  useEffect(() => {
    const handlePopState = (event) => {
      const urlParams = new URLSearchParams(window.location.search);
      const taskIdFromUrl = urlParams.get('task');
      const settingsFromUrl = urlParams.get('settings');
      
      if (settingsFromUrl) {
        setCurrentTask(null);
        setCurrentView('settings');
      } else if (taskIdFromUrl && tasks[taskIdFromUrl]) {
        setCurrentTask(taskIdFromUrl);
        setCurrentView('task-detail');
      } else {
        setCurrentTask(null);
        setCurrentView('task-list');
      }
    };
    
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [tasks, setCurrentTask]);
  
  useEffect(() => {
    loadTasks();
    loadLlmEndpoints();
    checkServerStatus();
    
    const interval = setInterval(checkServerStatus, 300000);
    return () => clearInterval(interval);
  }, [loadTasks, loadLlmEndpoints, checkServerStatus]);

  const MainContentPlaceholder = () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="text-4xl mb-4">✨</div>
        <h3 className="text-lg font-medium mb-3">Prompt Manager</h3>
        <p className="text-muted mb-2">Select a task to start editing prompts</p>
        <p className="text-muted text-sm">Create or select from the sidebar</p>
      </div>
    </div>
  );

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="app-logo">⚡</div>
          <span className="app-title">Prompt Manager</span>
          <span className="app-version">v1.0</span>
          <span className="text-muted" style={{ marginLeft: '16px' }}>
            {currentView === 'task-list' ? 'Tasks' : 
             currentView === 'settings' ? 'Settings' :
             'Editor'}
          </span>
        </div>
        
        <div className="header-right">
          <button className="header-icon" title="Search">🔍</button>
          <button className="header-icon" onClick={handleOpenSettings} title="Settings">⚙️</button>
          <button className="header-icon" onClick={toggleDarkMode} title="Theme">🌙</button>
          <div className="header-icon ai-avatar">✨</div>
        </div>
      </header>
      
      {/* Main Content */}
      <div className="main-content">
        {currentView === 'settings' ? (
          <LLMEndpointSettings />
        ) : (
          <ThreeColumnLayout
            leftPanel={
              <TaskNavigator 
                tasks={tasks}
                currentTask={currentTask}
                onSelectTask={handleSelectTask}
              />
            }
            centerPanel={
              currentView === 'task-list' ? (
                <MainContentPlaceholder />
              ) : (
                <PromptEditor 
                  taskId={currentTask}
                  versionId={currentVersion}
                />
              )
            }
            rightPanel={
              currentView === 'task-list' ? (
                <MainContentPlaceholder />
              ) : (
                <ResultViewer 
                  taskId={currentTask}
                  versionId={currentVersion}
                />
              )
            }
          />
        )}
      </div>
      
      {/* Status Bar */}
      <div className="status-bar">
        <div className="status-left">
          <div className={`status-dot ${serverStatus === 'connecting' ? 'connecting' : ''}`} 
               style={{
                 background: serverStatus === 'connected' ? '#10b981' : 
                            serverStatus === 'disconnected' ? '#ef4444' : '#f59e0b'
               }} />
          <span>Connected</span>
          <span>OpenAI API</span>
          <span>gpt-4</span>
        </div>
        
        <div className="status-right">
          <span>Requests: 142</span>
          <span>Credits: $48.23</span>
        </div>
      </div>
    </div>
  );
}

export default App;