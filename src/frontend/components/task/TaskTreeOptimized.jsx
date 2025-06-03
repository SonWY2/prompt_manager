import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { flushSync } from 'react-dom';
import { useStore } from '../../store.jsx';

function TaskTreeOptimized({ 
  tasks, 
  currentTask, 
  onSelectTask, 
  expandedGroups = {}, 
  onToggleGroup,
  isSearching = false,
  isFullScreen = false // 전체 화면 모드 지원
}) {
  const { deleteGroup, addGroup, deleteTask, availableGroups } = useStore();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [showAddGroup, setShowAddGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [showTaskDeleteConfirm, setShowTaskDeleteConfirm] = useState(null);
  const [hiddenTasks, setHiddenTasks] = useState(new Set()); // 즉시 숨길 태스크들
  const [hiddenGroups, setHiddenGroups] = useState(new Set()); // 즉시 숨길 그룹들
  
  // 태스크 즉시 삭제 (UI만)
  const hideTaskInstantly = useCallback((taskId) => {
    flushSync(() => {
      setHiddenTasks(prev => new Set(prev).add(taskId));
      setShowTaskDeleteConfirm(null);
    });
  }, []);
  
  // 그룹 즉시 삭제 (UI만)
  const hideGroupInstantly = useCallback((groupName) => {
    flushSync(() => {
      setHiddenGroups(prev => new Set(prev).add(groupName));
      setShowDeleteConfirm(null);
    });
  }, []);
  
  // 숨겨진 항목들 정리 (실제 상태 업데이트 후)
  useEffect(() => {
    // availableGroups가 변경되면 hiddenGroups 정리
    setHiddenGroups(prev => {
      const newHidden = new Set();
      prev.forEach(groupName => {
        if (availableGroups.includes(groupName)) {
          newHidden.add(groupName);
        }
      });
      return newHidden;
    });
  }, [availableGroups]);
  
  useEffect(() => {
    // tasks가 변경되면 hiddenTasks 정리
    setHiddenTasks(prev => {
      const newHidden = new Set();
      prev.forEach(taskId => {
        // 검색 모드인 경우
        if (isSearching) {
          const taskExists = tasks.some(([id, task]) => id === taskId);
          if (taskExists) {
            newHidden.add(taskId);
          }
        } else {
          // 그룹 모드인 경우
          const taskExists = tasks && Object.keys(tasks).some(group => 
            tasks[group] && tasks[group].some(task => task.id === taskId)
          );
          if (taskExists) {
            newHidden.add(taskId);
          }
        }
      });
      
      // 변경사항이 있는 경우에만 업데이트
      if (newHidden.size !== prev.size || ![...newHidden].every(id => prev.has(id))) {
        console.log('태스크 상태 변경으로 hiddenTasks 업데이트:', { 이전: [...prev], 이후: [...newHidden] });
        return newHidden;
      }
      
      return prev;
    });
  }, [tasks, isSearching]);
  
  // 필터링된 그룹 목록 (즉시 반영)
  const visibleGroups = useMemo(() => {
    return availableGroups.filter(groupName => !hiddenGroups.has(groupName));
  }, [availableGroups, hiddenGroups]);
  
  // 필터링된 태스크 목록 (즉시 반영)
  const getVisibleTasks = useCallback((groupName) => {
    const groupTasks = tasks[groupName] || [];
    return groupTasks.filter(task => !hiddenTasks.has(task.id));
  }, [tasks, hiddenTasks]);
  
  // 검색 결과인 경우 플랫한 목록으로 표시
  if (isSearching) {
    return (
      <div className="space-y-1 p-1">
        {tasks.map(([id, task]) => (
          !hiddenTasks.has(id) && (
            <div 
              key={id}
              className={`p-2 rounded cursor-pointer ${
                currentTask === id && !isFullScreen 
                  ? 'bg-blue-100 dark:bg-blue-900' 
                  : 'hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
              onClick={() => onSelectTask(id)}
            >
              <div className="flex items-center">
                <span className="mr-2">📄</span>
                <span className="truncate">{task.name}</span>
                {isFullScreen && (
                  <span className="ml-auto text-xs text-gray-500 dark:text-gray-400">
                    {task.group || '기본 그룹'}
                  </span>
                )}
              </div>
            </div>
          )
        ))}
      </div>
    );
  }
  
  // 그룹별로 표시 (그룹화된 데이터 사용)
  return (
    <div className="space-y-2 p-1">
      {/* 즉시 반영되는 그룹 목록 */}
      {visibleGroups.map((groupName, index) => {
        const groupTasks = getVisibleTasks(groupName);
        
        return (
          <div key={`group-${groupName}-${index}`} className="border border-gray-200 dark:border-gray-700 rounded">
            <div 
              className="flex items-center p-2 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <div
                className="flex items-center flex-grow cursor-pointer"
                onClick={() => onToggleGroup(groupName)}
              >
                <span className="mr-2">{expandedGroups[groupName] ? '🔽' : '▶️'}</span>
                <span className="font-medium">{groupName}</span>
                <span className="ml-auto text-xs text-gray-500">{groupTasks.length}개</span>
              </div>
              
              {/* 그룹 삭제 버튼 (기본 그룹은 삭제 불가) */}
              {groupName !== '기본 그룹' && (
                <div className="flex items-center ml-2">
                  {showDeleteConfirm === groupName ? (
                    <div className="flex items-center bg-red-100 dark:bg-red-900 rounded px-1">
                      <button 
                        className="text-xs text-red-600 dark:text-red-300 px-1"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          
                          // 즉시 그룹 숨김
                          hideGroupInstantly(groupName);
                          
                          // 백그라운드에서 실제 삭제
                          setTimeout(async () => {
                            try {
                              await deleteGroup(groupName);
                              console.log('그룹 삭제 완료:', groupName);
                            } catch (error) {
                              console.error('그룹 삭제 오류:', error);
                              // 오류 시 다시 표시
                              setHiddenGroups(prev => {
                                const newSet = new Set(prev);
                                newSet.delete(groupName);
                                return newSet;
                              });
                            }
                          }, 0);
                        }}
                      >
                        확인
                      </button>
                      <button 
                        className="text-xs text-gray-600 dark:text-gray-300 px-1 ml-1"
                        onClick={() => setShowDeleteConfirm(null)}
                      >
                        취소
                      </button>
                    </div>
                  ) : (
                    <button 
                      className="text-gray-500 hover:text-red-500 rounded p-1"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDeleteConfirm(groupName);
                      }}
                      title="그룹 삭제"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>
              )}
            </div>
            
            {/* 그룹이 확장되어 있고 태스크가 있는 경우에만 태스크 목록 표시 */}
            {expandedGroups[groupName] && groupTasks.length > 0 && (
              <div className="pl-4 border-t border-gray-200 dark:border-gray-700">
                {groupTasks.map(task => (
                  <div 
                    key={task.id}
                    className={`p-2 flex items-center justify-between ${
                      currentTask === task.id && !isFullScreen 
                        ? 'bg-blue-100 dark:bg-blue-900' 
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <div 
                      className="flex items-center cursor-pointer flex-grow"
                      onClick={() => onSelectTask(task.id)}
                    >
                      <span className="mr-2">📄</span>
                      <span className="truncate">{task.name}</span>
                    </div>
                    
                    {/* 태스크 삭제 버튼 */}
                    <div className="flex items-center ml-2">
                      {showTaskDeleteConfirm === task.id ? (
                        <div className="flex items-center bg-red-100 dark:bg-red-900 rounded px-1">
                          <button 
                            className="text-xs text-red-600 dark:text-red-300 px-1"
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              
                              // 즉시 태스크 숨김
                              hideTaskInstantly(task.id);
                              
                              // 백그라운드에서 실제 삭제
                              setTimeout(async () => {
                                try {
                                  const result = await deleteTask(task.id);
                                  console.log('태스크 삭제 완료:', task.id, result);
                                  
                                  // 사용자에게 피드백 제공
                                  const message = result.message || '태스크가 삭제되었습니다.';
                                  const bgColor = result.serverSync ? 'bg-green-500' : 'bg-yellow-500';
                                  
                                  const successMsg = document.createElement('div');
                                  successMsg.className = `fixed top-4 right-4 ${bgColor} text-white px-4 py-2 rounded shadow-lg z-50 max-w-sm`;
                                  successMsg.textContent = message;
                                  document.body.appendChild(successMsg);
                                  
                                  setTimeout(() => {
                                    if (successMsg.parentNode) {
                                      successMsg.parentNode.removeChild(successMsg);
                                    }
                                  }, result.serverSync ? 3000 : 5000); // 서버 동기화 실패 시 더 오래 표시
                                  
                                } catch (error) {
                                  console.error('태스크 삭제 오류:', error);
                                  // 오류 시 다시 표시
                                  setHiddenTasks(prev => {
                                    const newSet = new Set(prev);
                                    newSet.delete(task.id);
                                    return newSet;
                                  });
                                  alert('태스크 삭제 중 오류가 발생했습니다: ' + error.message);
                                }
                              }, 0);
                            }}
                          >
                            확인
                          </button>
                          <button 
                            className="text-xs text-gray-600 dark:text-gray-300 px-1 ml-1"
                            onClick={() => setShowTaskDeleteConfirm(null)}
                          >
                            취소
                          </button>
                        </div>
                      ) : (
                        <button 
                          className="text-gray-500 hover:text-red-500 rounded p-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowTaskDeleteConfirm(task.id);
                          }}
                          title="태스크 삭제"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {/* 그룹이 확장되어 있지만 태스크가 없는 경우 빈 상태 표시 */}
            {expandedGroups[groupName] && groupTasks.length === 0 && (
              <div className="pl-4 pt-2 pb-2 border-t border-gray-200 dark:border-gray-700">
                <div className="text-gray-500 dark:text-gray-400 text-sm text-center py-2">
                  이 그룹에는 태스크가 없습니다.
                </div>
              </div>
            )}
          </div>
        );
      })}
      
      {/* 새 그룹 추가 버튼 */}
      <div className="border border-dashed border-gray-300 dark:border-gray-600 rounded p-2">
        {showAddGroup ? (
          <div className="space-y-2">
            <input
              type="text"
              className="w-full p-2 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
              placeholder="새 그룹 이름 입력..."
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  if (newGroupName.trim()) {
                    // 즉시 UI 업데이트
                    flushSync(() => {
                      setNewGroupName('');
                      setShowAddGroup(false);
                    });
                    
                    // 백그라운드에서 그룹 추가
                    setTimeout(async () => {
                      try {
                        await addGroup(newGroupName.trim());
                        console.log('그룹 추가 성공:', newGroupName.trim());
                      } catch (error) {
                        console.error('그룹 추가 실패:', error);
                        alert('그룹 추가 실패: ' + error.message);
                      }
                    }, 0);
                  }
                }
              }}
              autoFocus
            />
            <div className="flex justify-end gap-1">
              <button
                className="px-2 py-1 text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                onClick={() => {
                  setShowAddGroup(false);
                  setNewGroupName('');
                }}
              >
                취소
              </button>
              <button
                className="px-2 py-1 text-xs bg-blue-500 text-white hover:bg-blue-600 rounded"
                onClick={() => {
                  if (newGroupName.trim()) {
                    // 즉시 UI 업데이트
                    flushSync(() => {
                      setNewGroupName('');
                      setShowAddGroup(false);
                    });
                    
                    // 백그라운드에서 그룹 추가
                    setTimeout(async () => {
                      try {
                        await addGroup(newGroupName.trim());
                        console.log('그룹 추가 성공:', newGroupName.trim());
                      } catch (error) {
                        console.error('그룹 추가 실패:', error);
                        alert('그룹 추가 실패: ' + error.message);
                      }
                    }, 0);
                  }
                }}
              >
                추가
              </button>
            </div>
          </div>
        ) : (
          <button
            className="w-full p-2 text-sm text-gray-500 dark:text-gray-400 hover:text-blue-500 dark:hover:text-blue-400 flex items-center justify-center"
            onClick={() => setShowAddGroup(true)}
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            새 그룹 추가
          </button>
        )}
      </div>
    </div>
  );
}

export default TaskTreeOptimized;