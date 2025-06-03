import React, { useState, useEffect } from 'react';
import { flushSync } from 'react-dom';
import { useStore } from '../../store.jsx';

function TaskTree({ 
  tasks, 
  currentTask, 
  onSelectTask, 
  expandedGroups = {}, 
  onToggleGroup,
  isSearching = false
}) {
  const { deleteGroup, addGroup, deleteTask, availableGroups } = useStore();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [showAddGroup, setShowAddGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [showTaskDeleteConfirm, setShowTaskDeleteConfirm] = useState(null);
  
  // 디버깅: availableGroups 상태 확인 및 자동 UI 업데이트
  useEffect(() => {
    console.log('TaskTree - availableGroups 상태 업데이트:', availableGroups);
    console.log('TaskTree - availableGroups 길이:', availableGroups?.length);
    
    // availableGroups가 변경되면 삭제 확인 상태 초기화 (즉시 UI 업데이트)
    setShowDeleteConfirm(null);
    setShowTaskDeleteConfirm(null);
  }, [availableGroups]);
  // 검색 결과인 경우 플랫한 목록으로 표시
  if (isSearching) {
    return (
      <div className="space-y-1 p-1">
        {tasks.map(([id, task]) => (
          <div 
            key={id}
            className={`p-2 rounded cursor-pointer ${currentTask === id ? 'bg-blue-100 dark:bg-blue-900' : 'hover:bg-gray-200 dark:hover:bg-gray-700'}`}
            onClick={() => onSelectTask(id)}
          >
            <div className="flex items-center">
              <span className="mr-2">📄</span>
              <span className="truncate">{task.name}</span>
            </div>
          </div>
        ))}
      </div>
    );
  }
  
  // 그룹별로 표시 (그룹화된 데이터 사용)
  return (
    <div className="space-y-2 p-1">
      {/* availableGroups를 기준으로 모든 그룹 표시 */}
      {availableGroups.map((groupName, index) => {
        // 해당 그룹에 속한 태스크들 찾기 - 그룹화된 데이터에서 가져오기
        const groupTasks = tasks[groupName] || [];
        
        console.log(`그룹 "${groupName}"의 태스크 수:`, groupTasks.length);
        
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
                        onClick={async () => {
                          try {
                            console.log('그룹 삭제 시작:', groupName);
                            
                            // 즐시 UI 업데이트 (낙관적 업데이트)
                            setShowDeleteConfirm(null);
                            
                            // 백그라운드에서 삭제 수행
                            const result = await deleteGroup(groupName);
                            
                            console.log('그룹 삭제 완료:', result);
                          } catch (error) {
                            console.error('그룹 삭제 오류:', error);
                            // 에러 시에도 UI는 이미 업데이트됨
                          }
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
                    className={`p-2 flex items-center justify-between ${currentTask === task.id ? 'bg-blue-100 dark:bg-blue-900' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`}
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
                            onClick={async () => {
                              try {
                                console.log('태스크 삭제 시작:', task.id);
                                
                                // 즉시 UI 업데이트 (낙관적 업데이트)
                                setShowTaskDeleteConfirm(null);
                                
                                // 백그라운드에서 삭제 수행
                                await deleteTask(task.id);
                                
                                console.log('태스크 삭제 완료:', task.id);
                              } catch (error) {
                                console.error('태스크 삭제 오류:', error);
                                // 에러 시에도 UI는 이미 업데이트됨
                                alert('태스크 삭제 중 오류가 발생했습니다: ' + error.message);
                              }
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
              onKeyPress={async (e) => {
                if (e.key === 'Enter') {
                  if (newGroupName.trim()) {
                    try {
                      const result = await addGroup(newGroupName.trim());
                      console.log('그룹 추가 성공:', result);
                      setNewGroupName('');
                      setShowAddGroup(false);
                    } catch (error) {
                      console.error('그룹 추가 실패:', error);
                      alert('그룹 추가 실패: ' + error.message);
                    }
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
                onClick={async () => {
                  if (newGroupName.trim()) {
                    try {
                      const result = await addGroup(newGroupName.trim());
                      console.log('그룹 추가 성공:', result);
                      setNewGroupName('');
                      setShowAddGroup(false);
                    } catch (error) {
                      console.error('그룹 추가 실패:', error);
                      alert('그룹 추가 실패: ' + error.message);
                    }
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

export default TaskTree;