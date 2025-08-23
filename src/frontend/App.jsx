// src/frontend/App.jsx
import React, { useState, useEffect } from 'react';
import { useStore } from './store.jsx';
import TaskNavigator from './components/task/TaskNavigator.jsx';
import PromptEditor from './components/prompt/PromptEditor.jsx';
import ResultViewer from './components/result/ResultViewer.jsx';
import LLMEndpointSettings from './components/settings/LLMEndpointSettings.jsx';
import MainContent from './components/layout/MainContent.jsx';
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
  
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState('editor'); // 'editor' or 'result'
  const [currentView, setCurrentView] = useState('task-list'); 
  const [initialLoadHandled, setInitialLoadHandled] = useState(false);

  // URL 기반 라우팅
  useEffect(() => {
    if (Object.keys(tasks).length === 0 && !initialLoadHandled) {
      return;
    }

    if (initialLoadHandled) {
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const taskIdFromUrl = urlParams.get('task');
    const settingsFromUrl = urlParams.get('settings');
    
    if (settingsFromUrl) {
      setCurrentTask(null);
      setCurrentView('settings');
    } else if (taskIdFromUrl) {
      if (tasks[taskIdFromUrl]) {
          setCurrentTask(taskIdFromUrl);
          setCurrentView('task-detail');
      } else { 
          setCurrentTask(null);
          setCurrentView('task-list');
          window.history.replaceState({}, '', window.location.pathname);
      }
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
      setActiveTab('editor'); // Reset to editor tab on new task selection
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
  
  // 브라우저 뒤로가기/앞으로가기 처리
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


  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <button
            className="header-icon"
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            title={isSidebarCollapsed ? "Show sidebar" : "Collapse sidebar"}
          >
            {isSidebarCollapsed ? '▶️' : '◀️'}
          </button>
          <div className="app-logo">⚡</div>
          <div className="flex items-center">
            <h1 className="app-title">Prompt Manager</h1>
            <span className="app-version">v1.0.0</span>
          </div>
        </div>
        
        <div className="header-right">
          <button className="header-icon" title="검색">🔍</button>
          <button className="header-icon" onClick={handleOpenSettings} title="설정">⚙️</button>
          <button className="header-icon" onClick={toggleDarkMode} title={isDarkMode ? "라이트 모드로 전환" : "다크 모드로 전환"}>
            {isDarkMode ? '☀️' : '🌙'}
          </button>
          <div className="header-icon ai-avatar">✨</div>
        </div>
      </header>
      
      {/* Main Layout */}
      <div className="app-body">
        {/* Sidebar */}
        <aside className={`sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`}>
          <TaskNavigator
            tasks={tasks}
            currentTask={currentTask}
            onSelectTask={handleSelectTask}
          />
        </aside>

        {/* Main Content */}
        <main className="main-content">
          <MainContent
            currentTask={currentTask}
            currentVersion={currentVersion}
            view={currentView}
          />
        </main>
      </div>
      
      {/* Status Bar */}
      <div className="status-bar">
        <div className="status-left">
          <div className="status-indicator">
            <div className={`status-dot ${serverStatus === 'connecting' ? 'connecting' : ''}`} 
                 style={{
                   background: serverStatus === 'connected' ? '#22c55e' : 
                              serverStatus === 'disconnected' ? '#ef4444' : '#f59e0b'
                 }} />
            <span>
              {serverStatus === 'connected' ? '연결됨' :
               serverStatus === 'disconnected' ? '연결 실패' : '연결 중...'}
            </span>
          </div>
        </div>
        <div className="status-right">
          <span>오늘 사용: 142 요청</span>
          <span>잔여 크레딧: $48.23</span>
        </div>
      </div>
    </div>
  );
}

export default App;