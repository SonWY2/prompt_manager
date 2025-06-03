import React, { useState, useEffect } from 'react';
import { useStore } from '../../store.jsx';
import TaskTreeOptimized from './TaskTreeOptimized.jsx';
import TaskActions from './TaskActions.jsx';
import TaskDetail from './detail/TaskDetail.jsx';
import Search from '../common/Search.jsx';
import Button from '../common/Button.jsx';

function TaskNavigator({ tasks, currentTask, onSelectTask, isFullScreen = false }) {
  const { availableGroups } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('tree'); // 'tree', 'recent', 'favorites', 'detail'
  const [expandedGroups, setExpandedGroups] = useState({});
  
  // 디버깅: availableGroups 상태 확인
  useEffect(() => {
    console.log('TaskNavigator - availableGroups 상태:', availableGroups);
    console.log('TaskNavigator - availableGroups 길이:', availableGroups?.length);
  }, [availableGroups]);
  
  // 태스크 삭제 시 화면 전환 처리
  useEffect(() => {
    // currentTask가 null이 되면 (삭제된 경우) tree 뷰로 전환
    if (!currentTask && viewMode === 'detail') {
      console.log('태스크가 삭제되어 tree 뷰로 전환');
      setViewMode('tree');
    }
  }, [currentTask, viewMode]);
  
  // 태스크 목록에서 현재 선택된 태스크가 사라진 경우 처리
  useEffect(() => {
    if (currentTask && tasks && !tasks[currentTask]) {
      console.log('현재 선택된 태스크가 더 이상 존재하지 않음:', currentTask);
      onSelectTask(null); // 태스크 선택 해제
    }
  }, [tasks, currentTask, onSelectTask]);
  
  // 태스크 선택 시 자동으로 상세 보기로 전환 (전체 화면 모드가 아닌 경우에만)
  useEffect(() => {
    if (currentTask && !isFullScreen) {
      setViewMode('detail');
    } else if (isFullScreen) {
      // 전체 화면 모드에서는 항상 tree 모드 유지
      setViewMode('tree');
    }
  }, [currentTask, isFullScreen]);
  
  // 새로운 태스크가 추가될 때 해당 그룹 자동 확장
  useEffect(() => {
    if (currentTask && tasks[currentTask]) {
      const taskGroup = tasks[currentTask].group;
      if (taskGroup) {
        setExpandedGroups(prev => ({
          ...prev,
          [taskGroup]: true
        }));
      }
    }
  }, [currentTask, tasks]);
  
  // 그룹화된 태스크 (폴더 구조)
  const getGroupedTasks = () => {
    return Object.entries(tasks || {}).reduce((acc, [id, task]) => {
      if (!task) return acc; // 태스크가 유효한지 확인
      
      const group = task.group || '기본 그룹';
      if (!acc[group]) acc[group] = [];
      acc[group].push({ id, ...task });
      return acc;
    }, {});
  };
  
  // 검색 필터링
  const filteredTasks = Object.entries(tasks || {}).filter(([id, task]) => {
    return task && task.name && task.name.toLowerCase().includes((searchQuery || '').toLowerCase());
  });
  
  // 최근 작업한 태스크
  const getRecentTasks = () => {
    return Object.entries(tasks || {})
      .filter(([_, task]) => task && task.name) // 태스크가 유효한 경우만 포함
      .sort((a, b) => {
        const aLastUpdated = a[1]?.versions && a[1].versions.length > 0 
          ? new Date(a[1].versions[a[1].versions.length - 1]?.createdAt || 0) 
          : new Date(0);
        const bLastUpdated = b[1]?.versions && b[1].versions.length > 0 
          ? new Date(b[1].versions[b[1].versions.length - 1]?.createdAt || 0) 
          : new Date(0);
        return bLastUpdated - aLastUpdated;
      })
      .slice(0, 5)
      .map(([id, task]) => ({ id, ...task }));
  };
  
  // 태스크 선택 이벤트 (전체 화면 모드에서는 상세 보기로 가지 않음)
  const handleSelectTask = (taskId) => {
    onSelectTask(taskId);
    
    if (!isFullScreen && taskId) {
      // 사이드바 모드에서만 상세 보기로 전환
      setViewMode('detail');
    }
  };
  
  // 뒤로가기 버튼 핸들러
  const handleBack = () => {
    setViewMode('tree');
  };
  
  // 빈 상태 표시
  const isEmpty = !tasks || Object.keys(tasks).length === 0;
  
  return (
    <div className="h-full flex flex-col">
      <div className="p-3 border-b border-gray-300 dark:border-gray-700">
        <h2 className="text-lg font-semibold mb-2">
          {isFullScreen ? '그룹 & 태스크 관리' : '태스크'}
        </h2>
        {!isEmpty && (
          <Search 
            placeholder="태스크 검색..." 
            value={searchQuery} 
            onChange={setSearchQuery}
          />
        )}
      </div>
      
      {/* 전체 화면 모드에서는 detail 보기를 제공하지 않음 */}
      {!isFullScreen && viewMode === 'detail' && currentTask ? (
        <>
          <div className="p-2 border-b border-gray-300 dark:border-gray-700">
            <Button
              variant="outline"
              size="small"
              className="w-full"
              onClick={handleBack}
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
              </svg>
              태스크 목록으로 돌아가기
            </Button>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            <TaskDetail taskId={currentTask} />
          </div>
        </>
      ) : (
        <>
          {!isEmpty && (
            <div className="flex p-2 gap-1 border-b border-gray-300 dark:border-gray-700">
              <button 
                className={`px-3 py-1 rounded text-sm ${viewMode === 'tree' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700'}`}
                onClick={() => setViewMode('tree')}
              >
                전체
              </button>
              <button 
                className={`px-3 py-1 rounded text-sm ${viewMode === 'recent' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700'}`}
                onClick={() => setViewMode('recent')}
              >
                최근
              </button>
              <button 
                className={`px-3 py-1 rounded text-sm ${viewMode === 'favorites' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700'}`}
                onClick={() => setViewMode('favorites')}
              >
                즐겨찾기
              </button>
            </div>
          )}
          
          <div className="flex-1 overflow-y-auto p-1">
            {isEmpty ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center p-4">
                  <div className="text-gray-400 text-5xl mb-4">📋</div>
                  <h3 className="text-lg font-medium mb-2">태스크가 없습니다</h3>
                  <p className="text-gray-500 dark:text-gray-400 mb-4">
                    {isFullScreen 
                      ? '아래 버튼을 눌러 첫 번째 태스크를 생성해보세요.'
                      : '새 태스크를 생성해서 시작해보세요.'
                    }
                  </p>
                </div>
              </div>
            ) : (
              viewMode === 'tree' && (
                <TaskTreeOptimized 
                  tasks={searchQuery ? filteredTasks : getGroupedTasks()}
                  currentTask={currentTask}
                  onSelectTask={handleSelectTask}
                  expandedGroups={expandedGroups}
                  onToggleGroup={(group) => {
                    setExpandedGroups({
                      ...expandedGroups,
                      [group]: !expandedGroups[group]
                    });
                  }}
                  isSearching={searchQuery.length > 0}
                  isFullScreen={isFullScreen} // 전체 화면 모드 플래그 전달
                />
              )
            )}
            
            {!isEmpty && viewMode === 'recent' && (
              <div className="space-y-1">
                {getRecentTasks().map(task => (
                  <div 
                    key={task.id}
                    className={`p-2 rounded cursor-pointer ${
                      currentTask === task.id && !isFullScreen 
                        ? 'bg-blue-100 dark:bg-blue-900' 
                        : 'hover:bg-gray-200 dark:hover:bg-gray-700'
                    }`}
                    onClick={() => handleSelectTask(task.id)}
                  >
                    <div className="flex items-center">
                      <span className="mr-2">📄</span>
                      <span className="truncate">{task.name}</span>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {task.versions && task.versions.length > 0 
                        ? `마지막 업데이트: ${new Date(task.versions[task.versions.length - 1].createdAt || 0).toLocaleDateString()}`
                        : '버전 없음'}
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {!isEmpty && viewMode === 'favorites' && (
              <div className="p-3 text-center text-gray-500 dark:text-gray-400">
                <p>태스크에 별표를 표시하여 즐겨찾기에 추가하세요</p>
              </div>
            )}
          </div>
          
          <TaskActions />
        </>
      )}
    </div>
  );
}

export default TaskNavigator;