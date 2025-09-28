// src/frontend/components/task/TaskNavigator.jsx
import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useStore } from '../../store.jsx';

const TaskNavigator = ({ tasks, currentTask, onSelectTask }) => {
  const { createTask, deleteTask, toggleFavorite } = useStore();
  const [activeTab, setActiveTab] = useState('all'); // all, recent, favorites
  const [containerWidth, setContainerWidth] = useState(null);
  const tabContainerRef = useRef(null);

  // 컨테이너 너비 모니터링
  useEffect(() => {
    const updateWidth = () => {
      if (tabContainerRef.current) {
        const width = tabContainerRef.current.offsetWidth;
        setContainerWidth(width);
        console.log('[TaskNavigator] Tab container width:', width);
      }
    };

    // 초기 너비 설정
    updateWidth();

    // 리사이즈 이벤트 리스너
    window.addEventListener('resize', updateWidth);
    
    return () => {
      window.removeEventListener('resize', updateWidth);
    };
  }, []);

  // 반응형 탭 텍스트 결정
  const getTabText = (tabType) => {
    if (containerWidth === null) return tabType.charAt(0).toUpperCase() + tabType.slice(1);
    
    // 매우 작은 화면 (200px 미만)에서는 아이콘/짧은 텍스트 사용
    if (containerWidth < 200) {
      switch(tabType) {
        case 'all': return 'All';
        case 'recent': return 'New';
        case 'favorites': return '★';
        default: return tabType;
      }
    }
    
    // 작은 화면 (280px 미만)에서는 줄인 텍스트 사용
    if (containerWidth < 280) {
      switch(tabType) {
        case 'all': return 'All';
        case 'recent': return 'Recent';
        case 'favorites': return 'Fav';
        default: return tabType;
      }
    }
    
    // 기본 텍스트
    switch(tabType) {
      case 'all': return 'All';
      case 'recent': return 'Recent';
      case 'favorites': return 'Favorites';
      default: return tabType.charAt(0).toUpperCase() + tabType.slice(1);
    }
  };

  const handleNewTask = async () => {
    const taskName = prompt("Enter a name for the new task:");
    if (taskName && taskName.trim()) {
      try {
        await createTask(taskName.trim());
      } catch (error) {
        console.error('Failed to create task:', error);
        alert('Failed to create task.');
      }
    }
  };

  const handleDeleteTask = async () => {
    if (!currentTask) {
      alert("Please select a task to delete.");
      return;
    }
    const taskToDelete = tasks[currentTask];
    if (window.confirm(`Are you sure you want to delete the task "${taskToDelete.name}"?`)) {
      try {
        await deleteTask(currentTask);
      } catch (error) {
        console.error('Failed to delete task:', error);
        alert('Failed to delete task.');
      }
    }
  };

  const formatTimeAgo = (updatedAt) => {
    if (!updatedAt) return 'Unknown';
    const now = new Date();
    const updated = new Date(updatedAt);
    const diffInHours = Math.floor((now - updated) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 48) return 'Yesterday';
    return `${Math.floor(diffInHours / 24)} days ago`;
  };

  const filteredTasks = useMemo(() => {
    let taskArray = Object.values(tasks);

    switch (activeTab) {
      case 'recent':
        return taskArray.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
      case 'favorites':
        return taskArray.filter(task => task.isFavorite).sort((a, b) => a.name.localeCompare(b.name));
      case 'all':
      default:
        return taskArray.sort((a, b) => a.name.localeCompare(b.name));
    }
  }, [tasks, activeTab]);

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--bg-secondary)' }}>
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center justify-between mb-4">
          <h2 className="panel-title">Tasks</h2>
        </div>

        {/* Tabs */}
        <div className="tab-container" ref={tabContainerRef}>
          <button 
            className={`tab ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
            title="All tasks"
          >
            {getTabText('all')}
          </button>
          <button 
            className={`tab ${activeTab === 'recent' ? 'active' : ''}`}
            onClick={() => setActiveTab('recent')}
            title="Recently modified tasks"
          >
            {getTabText('recent')}
          </button>
          <button 
            className={`tab ${activeTab === 'favorites' ? 'active' : ''}`}
            onClick={() => setActiveTab('favorites')}
            title="Favorite tasks"
          >
            {getTabText('favorites')}
          </button>
        </div>
      </div>

      {/* Task List */}
      <div className="flex-1 overflow-y-auto p-5">
        <div className="space-y-1">
          {filteredTasks.map(task => {
            const isActive = currentTask === task.id;
            const versionCount = task.versions ? Object.keys(task.versions).length : 0;

            return (
              <div
                key={task.id}
                className={`task-item group flex items-center justify-between ${isActive ? 'is-active' : ''}`}
                onClick={() => onSelectTask(task.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm">📄</span>
                    <span
                      className="text-sm font-medium truncate"
                    >
                      {task.name}
                    </span>
                  </div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {versionCount} versions • Modified {formatTimeAgo(task.updatedAt)}
                  </div>
                </div>
                <button 
                  type="button"
                  className={`favorite-btn opacity-0 group-hover:opacity-100 transition-opacity ${task.isFavorite ? 'is-fav' : ''}`}
                  aria-pressed={task.isFavorite}
                  title={task.isFavorite ? 'Remove from favorites' : 'Add to favorites'}
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent task selection
                    toggleFavorite(task.id);
                  }}
                >
                  <span>
                    {task.isFavorite ? '★' : '☆'}
                  </span>
                </button>
              </div>
            );
          })}
        </div>

        {/* Empty State */}
        {filteredTasks.length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📝</div>
            <p className="text-muted mb-4">No tasks in this view</p>
            <p className="text-muted">
              {activeTab === 'favorites' ? 'Star some tasks to see them here.' : 'Create a new task to get started.'}
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex gap-2">
          <button className="btn btn-primary w-full" onClick={handleNewTask}>
            + New Task
          </button>
          <button
            className="btn btn-danger w-full"
            onClick={handleDeleteTask}
            disabled={!currentTask}
          >
            Delete Task
          </button>
        </div>
      </div>
    </div>
  );
};

export default TaskNavigator;
