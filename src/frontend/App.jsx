import React, { useState, useEffect } from 'react';
import { useStore } from './store.jsx';
import ThreeColumnLayout from './components/layout/ThreeColumnLayout.jsx';
import TaskNavigator from './components/task/TaskNavigator.jsx';
import PromptEditor from './components/prompt/PromptEditor.jsx';
import ResultViewer from './components/result/ResultViewer.jsx';
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
    checkServerStatus
  } = useStore();
  
  // URL 기반 라우팅 상태
  const [currentView, setCurrentView] = useState('task-list'); // 'task-list' 또는 'task-detail'
  
  // URL에서 태스크 ID 추출 및 초기 상태 설정
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const taskIdFromUrl = urlParams.get('task');
    
    console.log('🔗 URL에서 태스크 ID 확인:', taskIdFromUrl);
    
    if (taskIdFromUrl && tasks[taskIdFromUrl]) {
      // URL에 유효한 태스크 ID가 있으면 해당 태스크 선택
      console.log('✅ URL의 태스크 ID로 화면 설정:', taskIdFromUrl);
      setCurrentTask(taskIdFromUrl);
      setCurrentView('task-detail');
    } else if (taskIdFromUrl && !tasks[taskIdFromUrl]) {
      // URL에 있는 태스크가 존재하지 않으면 기본 화면으로
      console.log('❌ URL의 태스크 ID가 존재하지 않음, 기본 화면으로 이동');
      setCurrentView('task-list');
      setCurrentTask(null);
      // URL에서 task 파라미터 제거
      window.history.replaceState({}, '', window.location.pathname);
    } else {
      // URL에 태스크 ID가 없으면 기본 화면 (그룹&태스크)
      console.log('📋 기본 화면으로 설정: 그룹&태스크 목록');
      setCurrentView('task-list');
      setCurrentTask(null);
    }
  }, [tasks, setCurrentTask]);
  
  // 태스크 선택 핸들러 - URL도 함께 업데이트
  const handleSelectTask = (taskId) => {
    console.log('🎯 태스크 선택:', taskId);
    
    if (taskId) {
      // 태스크 선택 시
      setCurrentTask(taskId);
      setCurrentView('task-detail');
      
      // URL 업데이트 (브라우저 히스토리에 추가)
      const newUrl = `${window.location.pathname}?task=${taskId}`;
      window.history.pushState({ taskId, view: 'task-detail' }, '', newUrl);
      
      console.log('🔗 URL 업데이트:', newUrl);
    } else {
      // 태스크 선택 해제 시 (뒤로가기 등)
      setCurrentTask(null);
      setCurrentView('task-list');
      
      // URL에서 task 파라미터 제거
      window.history.pushState({ view: 'task-list' }, '', window.location.pathname);
      
      console.log('🏠 기본 화면으로 돌아가기');
    }
  };
  
  // 브라우저 뒤로가기/앞으로가기 처리
  useEffect(() => {
    const handlePopState = (event) => {
      console.log('🔄 브라우저 네비게이션 이벤트:', event.state);
      
      const urlParams = new URLSearchParams(window.location.search);
      const taskIdFromUrl = urlParams.get('task');
      
      if (taskIdFromUrl && tasks[taskIdFromUrl]) {
        setCurrentTask(taskIdFromUrl);
        setCurrentView('task-detail');
        console.log('🎯 브라우저 네비게이션으로 태스크 선택:', taskIdFromUrl);
      } else {
        setCurrentTask(null);
        setCurrentView('task-list');
        console.log('🏠 브라우저 네비게이션으로 기본 화면');
      }
    };
    
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [tasks, setCurrentTask]);
  
  // 앱 초기화 시 데이터 로드 및 서버 상태 체크
  useEffect(() => {
    loadTasks();
    checkServerStatus();
    
    // 5분마다 서버 상태 체크 (너무 빈번하지 않게 조정)
    const interval = setInterval(checkServerStatus, 300000); // 5분 = 300,000ms
    return () => clearInterval(interval);
  }, [loadTasks, checkServerStatus]);

  return (
    <div className={`app ${isDarkMode ? 'dark' : 'light'}`}>
      <div className="flex flex-col h-screen">
        {/* 헤더 */}
        <header className="bg-gray-800 dark:bg-gray-900 text-white p-3 flex justify-between items-center">
          <div className="flex items-center gap-3">
            {/* 홈 버튼 (기본 화면으로 돌아가기) */}
            <button 
              onClick={() => handleSelectTask(null)}
              className="text-xl hover:text-blue-300 transition-colors" 
              title="홈으로 돌아가기"
            >
              🏠
            </button>
            
            <h1 className="text-xl font-bold">
              {currentView === 'task-list' ? '프롬프트 매니저' : 
               currentTask && tasks[currentTask] ? `${tasks[currentTask].name} - 버전 관리` : 
               '프롬프트 매니저'}
            </h1>
            
            {/* 현재 화면 표시 */}
            <div className="text-sm text-gray-300">
              {currentView === 'task-list' ? '📋 그룹 & 태스크' : '⚙️ 프롬프트 버전 관리'}
            </div>
            
            {/* 서버 상태 인디케이터 */}
            <div className="flex items-center gap-1 text-sm">
              <div className={`w-2 h-2 rounded-full ${
                serverStatus === 'connected' ? 'bg-green-500' :
                serverStatus === 'disconnected' ? 'bg-red-500' :
                'bg-yellow-500 animate-pulse'
              }`} />
              <span className="text-xs text-gray-300">
                {serverStatus === 'connected' ? '서버 연결됨' :
                 serverStatus === 'disconnected' ? '서버 연결 실패 (로컬 모드)' :
                 '서버 상태 확인 중...'}
              </span>
              {serverStatus === 'disconnected' && (
                <button 
                  onClick={checkServerStatus}
                  className="ml-1 px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs"
                  title="서버 연결 재시도"
                >
                  재시도
                </button>
              )}
            </div>
          </div>
          
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
        
        {/* 메인 콘텐츠 */}
        <div className="flex-1 overflow-hidden">
          {currentView === 'task-list' ? (
            /* 기본 화면: 그룹&태스크 전체 화면 */
            <div className="h-full">
              <TaskNavigator 
                tasks={tasks}
                currentTask={null} // 기본 화면에서는 선택된 태스크 없음
                onSelectTask={handleSelectTask}
                isFullScreen={true} // 전체 화면 모드 플래그
              />
            </div>
          ) : (
            /* 태스크 선택 시: 3단 레이아웃 (프롬프트 버전 관리) */
            <ThreeColumnLayout
              leftPanel={
                <TaskNavigator 
                  tasks={tasks}
                  currentTask={currentTask}
                  onSelectTask={handleSelectTask}
                  isFullScreen={false} // 사이드바 모드
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
          )}
        </div>
      </div>
    </div>
  );
}

export default App;