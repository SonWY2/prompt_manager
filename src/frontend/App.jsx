import React, { useState, useEffect } from 'react';
import { useStore } from './store.jsx';
import ThreeColumnLayout from './components/layout/ThreeColumnLayout.jsx';
import TaskNavigator from './components/task/TaskNavigator.jsx';
import PromptEditor from './components/prompt/PromptEditor.jsx';
import ResultViewer from './components/result/ResultViewer.jsx';
import './App.css';

function App() {
  const {
    tasks, 
    loadTasks, 
    currentTask, 
    setCurrentTask,
    currentVersion,
    isDarkMode,
    toggleDarkMode
  } = useStore();
  
  // 앱 초기화 시 데이터 로드
  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  return (
    <div className={`app ${isDarkMode ? 'dark' : 'light'}`}>
      <div className="flex flex-col h-screen">
        {/* 헤더 */}
        <header className="bg-gray-800 dark:bg-gray-900 text-white p-3 flex justify-between items-center">
          <h1 className="text-xl font-bold">프롬프트 매니저</h1>
          <div className="flex gap-3 items-center">
            <button 
              className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
              onClick={() => { /* 가이드 표시 */ }}>
              가이드
            </button>
            <button 
              onClick={toggleDarkMode}
              className="p-2 rounded-full bg-gray-700 hover:bg-gray-600"
              title={isDarkMode ? "라이트 모드로 전환" : "다크 모드로 전환"}>
              {isDarkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </header>
        
        {/* 메인 3단 레이아웃 */}
        <ThreeColumnLayout
          leftPanel={
            <TaskNavigator 
              tasks={tasks}
              currentTask={currentTask}
              onSelectTask={setCurrentTask}
            />
          }
          centerPanel={
            <PromptEditor 
              taskId={currentTask}
              versionId={currentVersion}
            />
          }
          rightPanel={
            <ResultViewer 
              taskId={currentTask}
              versionId={currentVersion}
            />
          }
          leftPanelWidth={20} // 초기 너비 %
          rightPanelWidth={30} // 초기 너비 %
        />
      </div>
    </div>
  );
}

export default App;