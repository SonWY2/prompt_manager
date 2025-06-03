// src/frontend/App.jsx
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
  // 최초 접속 시 URL에 task ID가 없으므로 'task-list' (메인 화면)
  // URL에 task ID가 있으면 'task-detail' (프롬프트 목록 화면)
  const [currentView, setCurrentView] = useState('task-list'); 
  
  const [initialLoadHandled, setInitialLoadHandled] = useState(false); // 초기 로드 핸들링 여부 추적 상태

  // URL에서 태스크 ID 추출 및 초기 상태 설정
  useEffect(() => {
    // tasks가 로드되지 않았고, 아직 초기 로드가 처리되지 않았다면 대기
    if (Object.keys(tasks).length === 0 && !initialLoadHandled) {
      console.log('🔗 App: tasks 데이터 로드 대기 중...');
      return; // tasks가 로드될 때까지 대기
    }

    // 이미 초기 로드가 처리되었으면 다시 실행하지 않음 (tasks 업데이트 시 중복 실행 방지)
    if (initialLoadHandled) {
        console.log('🔗 App: 초기 로드 이미 처리됨. URL 상태 재확인 스킵.');
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const taskIdFromUrl = urlParams.get('task');
    
    console.log('🔗 App: URL에서 태스크 ID 확인:', taskIdFromUrl);
    
    if (taskIdFromUrl) {
      if (tasks[taskIdFromUrl]) {
          // URL에 유효한 태스크 ID가 있고, tasks에 해당 태스크가 로드됨
          console.log('✅ App: URL의 태스크 ID로 화면 설정:', taskIdFromUrl);
          setCurrentTask(taskIdFromUrl);
          setCurrentView('task-detail');
      } else { 
          // URL에 태스크 ID가 있지만, tasks에 해당 태스크가 로드되지 않음 (잘못된 ID이거나 삭제된 ID)
          console.log('❌ App: URL의 태스크 ID가 유효하지 않거나 존재하지 않음. 기본 화면으로 이동:', taskIdFromUrl);
          setCurrentTask(null);
          setCurrentView('task-list');
          // URL에서 task 파라미터 제거
          window.history.replaceState({}, '', window.location.pathname);
      }
    } else {
        // URL에 태스크 ID가 없음 -> 메인 화면
        console.log('📋 App: URL에 태스크 ID 없음. 기본 화면 (태스크 목록)으로 설정.');
        setCurrentTask(null);
        setCurrentView('task-list');
    }
    setInitialLoadHandled(true); // 초기 로드 처리 완료
  }, [tasks, setCurrentTask, initialLoadHandled]); // initialLoadHandled를 의존성에 추가

  // 태스크 선택 핸들러 - URL도 함께 업데이트
  const handleSelectTask = (taskId) => {
    console.log('🎯 App: 태스크 선택:', taskId);
    
    if (taskId) {
      // 태스크 선택 시
      setCurrentTask(taskId);
      setCurrentView('task-detail');
      
      // URL 업데이트 (브라우저 히스토리에 추가)
      const newUrl = `${window.location.pathname}?task=${taskId}`;
      window.history.pushState({ taskId, view: 'task-detail' }, '', newUrl);
      
      console.log('🔗 App: URL 업데이트:', newUrl);
    } else {
      // 태스크 선택 해제 시 (뒤로가기 등)
      setCurrentTask(null);
      setCurrentView('task-list');
      
      // URL에서 task 파라미터 제거
      window.history.pushState({ view: 'task-list' }, '', window.location.pathname);
      
      console.log('🏠 App: 기본 화면으로 돌아가기 (URL 파라미터 제거)');
    }
  };
  
  // 브라우저 뒤로가기/앞으로가기 처리
  useEffect(() => {
    const handlePopState = (event) => {
      console.log('🔄 App: 브라우저 네비게이션 이벤트:', event.state);
      
      const urlParams = new URLSearchParams(window.location.search);
      const taskIdFromUrl = urlParams.get('task');
      
      // popstate 발생 시, tasks 데이터가 이미 로드되었다고 가정
      // 또는, tasks가 비어있을 때도 url에 task 파라미터가 없으면 task-list로 이동
      if (taskIdFromUrl && tasks[taskIdFromUrl]) {
        setCurrentTask(taskIdFromUrl);
        setCurrentView('task-detail');
        console.log('🎯 App: 브라우저 네비게이션으로 태스크 선택:', taskIdFromUrl);
      } else {
        setCurrentTask(null);
        setCurrentView('task-list');
        console.log('🏠 App: 브라우저 네비게이션으로 기본 화면');
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

  // 메인 콘텐츠 영역에 표시될 메시지 컴포넌트
  const MainContentPlaceholder = () => (
    <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400 p-4">
      <div className="text-center space-y-4">
        <div className="text-6xl">✨</div>
        <h3 className="text-xl font-semibold">Prompt Manager에 오신 것을 환영합니다!</h3>
        <p className="max-w-md mx-auto">
          왼쪽 패널에서 기존 태스크를 선택하거나, 새로운 태스크를 생성하여 프롬프트 관리를 시작하세요.
        </p>
        <p className="text-sm text-gray-400">
          태스크를 선택하면 프롬프트 편집기 및 결과 뷰어가 여기에 표시됩니다.
        </p>
      </div>
    </div>
  );

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
              {currentView === 'task-list' ? '📋 메인 화면' : '⚙️ 프롬프트 버전 관리'}
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
        
        {/* 메인 콘텐츠 - 항상 3단 레이아웃 사용 */}
        <div className="flex-1 overflow-hidden">
          <ThreeColumnLayout
            leftPanel={
              <TaskNavigator 
                tasks={tasks}
                currentTask={currentTask}
                onSelectTask={handleSelectTask}
                // isFullScreen prop은 TaskNavigator 내부에서 더 이상 사용하지 않음
                // 대신 TaskNavigator는 항상 사이드바 역할
              />
            }
            centerPanel={
              currentView === 'task-list' ? (
                <MainContentPlaceholder /> // 메인 화면일 때 빈 화면 메시지
              ) : (
                <PromptEditor 
                  taskId={currentTask}
                  versionId={currentVersion}
                />
              )
            }
            rightPanel={
              currentView === 'task-list' ? (
                <MainContentPlaceholder /> // 메인 화면일 때 빈 화면 메시지
              ) : (
                <ResultViewer 
                  taskId={currentTask}
                  versionId={currentVersion}
                />
              )
            }
            leftPanelWidth={20} // 초기 너비 %
            rightPanelWidth={30} // 초기 너비 %
          />
        </div>
      </div>
    </div>
  );
}

export default App;