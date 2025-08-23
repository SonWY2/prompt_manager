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

  const MainContentPlaceholder = () => (
    <div className="flex items-center justify-center h-full p-4">
      <div className="text-center">
        <div className="text-6xl mb-4">✨</div>
        <h3 className="text-xl font-semibold text-primary mb-4">Prompt Manager에 오신 것을 환영합니다!</h3>
        <p className="text-secondary max-w-md mx-auto mb-2">
          왼쪽 패널에서 기존 태스크를 선택하거나, 새로운 태스크를 생성하여 프롬프트 관리를 시작하세요.
        </p>
        <p className="text-muted text-sm">
          태스크를 선택하면 프롬프트 편집기 및 결과 뷰어가 여기에 표시됩니다.
        </p>
      </div>
    </div>
  );

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          {/* Logo */}
          <div className="app-logo">⚡</div>
          
          {/* Brand & Version */}
          <div className="flex items-center">
            <h1 className="app-title">Prompt Manager</h1>
            <span className="app-version">v1.0.0</span>
          </div>
          
          {/* Current View */}
          <div className="text-muted text-sm ml-4">
            {currentView === 'task-list' ? '📋 메인 화면' : 
             currentView === 'settings' ? '⚙️ 설정' :
             '⚙️ 프롬프트 버전 관리'}
          </div>
        </div>
        
        <div className="header-right">
          {/* Search */}
          <button className="header-icon" title="검색">
            🔍
          </button>
          
          {/* Settings */}
          <button 
            className="header-icon" 
            onClick={handleOpenSettings}
            title="설정"
          >
            ⚙️
          </button>
          
          {/* Dark Mode Toggle */}
          <button 
            className="header-icon"
            onClick={toggleDarkMode}
            title={isDarkMode ? "라이트 모드로 전환" : "다크 모드로 전환"}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
          
          {/* AI Avatar */}
          <div className="header-icon ai-avatar">
            ✨
          </div>
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
          <span>OpenAI API</span>
          <span>모델: gpt-4-turbo</span>
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