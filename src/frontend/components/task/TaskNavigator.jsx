// src/frontend/components/task/TaskNavigator.jsx
import React, { useState, useMemo } from 'react';
import { useStore } from '../../store.jsx';

const TaskNavigator = ({ tasks, currentTask, onSelectTask }) => {
  const { createTask, deleteTask } = useStore();
  const [activeTab, setActiveTab] = useState('all'); // all, recent, favorites
  const [showTaskDeleteConfirm, setShowTaskDeleteConfirm] = useState(null);

  const [isCreatingTask, setIsCreatingTask] = useState(false);
  const [newTaskName, setNewTaskName] = useState('');

  const handleNewTask = async () => {
    if (!newTaskName.trim()) return;
    try {
      await createTask(newTaskName.trim());
      setNewTaskName('');
      setIsCreatingTask(false);
    } catch (error) {
      console.error('태스크 생성 실패:', error);
      alert('태스크 생성에 실패했습니다.');
    }
  };

  const formatTimeAgo = (updatedAt) => {
    if (!updatedAt) return '알 수 없음';
    const now = new Date();
    const updated = new Date(updatedAt);
    const diffInHours = Math.floor((now - updated) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return '방금 전';
    if (diffInHours < 24) return `${diffInHours}시간 전`;
    if (diffInHours < 48) return '어제';
    if (diffInHours < 72) return '2일 전';
    return '3일 전';
  };

  const taskList = useMemo(() => Object.values(tasks), [tasks]);

  return (
    <>
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center justify-between mb-4">
          <h2 className="panel-title">Tasks</h2>
          {isCreatingTask ? (
            <div className="flex items-center gap-2 w-full">
              <input
                type="text"
                value={newTaskName}
                onChange={(e) => setNewTaskName(e.target.value)}
                placeholder="Enter a task name..."
                className="input text-sm flex-1 min-w-0"
                autoFocus
                onKeyPress={(e) => e.key === 'Enter' && handleNewTask()}
              />
              <div className="flex items-center gap-2 flex-shrink-0">
                <button className="btn btn-primary" onClick={handleNewTask}>Create</button>
                <button className="btn btn-secondary" onClick={() => setIsCreatingTask(false)}>Cancel</button>
              </div>
            </div>
          ) : (
            <button
              className="btn btn-primary"
              onClick={() => setIsCreatingTask(true)}
            >
              + New Task
            </button>
          )}
        </div>

        {/* Tabs */}
        <div className="tab-container">
          <button 
            className={`tab ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
          >
            All
          </button>
          <button 
            className={`tab ${activeTab === 'recent' ? 'active' : ''}`}
            onClick={() => setActiveTab('recent')}
          >
            Recent
          </button>
          <button 
            className={`tab ${activeTab === 'favorites' ? 'active' : ''}`}
            onClick={() => setActiveTab('favorites')}
          >
            Favorites
          </button>
        </div>
      </div>

      {/* Task List */}
      <div className="p-5">
        <div className="space-y-1">
          {taskList.map(task => {
            const isActive = currentTask === task.id;
            const versionCount = task.versions ? Object.keys(task.versions).length : 0;

            return (
              <div
                key={task.id}
                className="task-item flex items-center justify-between"
                style={{
                  position: 'relative',
                  padding: '10px 12px',
                  marginBottom: '2px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  background: isActive ? 'var(--accent-primary)' : 'transparent',
                  color: isActive ? 'white' : 'var(--text-primary)',
                  border: isActive ? '1px solid var(--accent-primary)' : '1px solid transparent'
                }}
                onClick={() => onSelectTask(task.id)}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'var(--bg-hover)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'transparent';
                  }
                }}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm">📄</span>
                    <span
                      className={`text-sm font-medium truncate ${
                        isActive ? 'text-white' : 'text-gray-300'
                      }`}
                    >
                      {task.name}
                    </span>
                  </div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {versionCount}개 버전 • 수정 {formatTimeAgo(task.updatedAt)}
                  </div>
                </div>

                <div className="flex items-center ml-2">
                    {showTaskDeleteConfirm === task.id ? (
                    <div className="flex items-center bg-red-100 dark:bg-red-900 rounded px-1">
                        <button
                        className="text-xs text-red-600 dark:text-red-300 px-1"
                        onClick={async (e) => {
                            e.stopPropagation();
                            try {
                            await deleteTask(task.id);
                            setShowTaskDeleteConfirm(null);
                            } catch (error) {
                            console.error('태스크 삭제 오류:', error);
                            alert('태스크 삭제 중 오류가 발생했습니다: ' + error.message);
                            }
                        }}
                        >
                        확인
                        </button>
                        <button
                        className="text-xs text-gray-600 dark:text-gray-300 px-1 ml-1"
                        onClick={(e) => {
                            e.stopPropagation();
                            setShowTaskDeleteConfirm(null);
                        }}
                        >
                        취소
                        </button>
                    </div>
                    ) : (
                    <button
                        className="text-gray-500 hover:text-red-500 rounded p-1 opacity-0 group-hover:opacity-100"
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

                    <button
                        style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        fontSize: '12px',
                        cursor: 'pointer',
                        padding: '2px',
                        borderRadius: '2px',
                        opacity: '0.7',
                        transition: 'opacity 0.15s ease'
                        }}
                        onClick={(e) => {
                        e.stopPropagation();
                        // TODO: Toggle favorite
                        }}
                        onMouseEnter={(e) => e.target.style.opacity = '1'}
                        onMouseLeave={(e) => e.target.style.opacity = '0.7'}
                    >
                        ⭐
                    </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Empty State */}
        {Object.keys(tasks).length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📝</div>
            <p className="text-muted mb-4">No tasks yet</p>
            <p className="text-muted">
              Create your first task
            </p>
          </div>
        )}
      </div>
    </>
  );
};

export default TaskNavigator;