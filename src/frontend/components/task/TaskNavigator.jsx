// src/frontend/components/task/TaskNavigator.jsx
import React, { useState, useMemo } from 'react';
import { useStore } from '../../store.jsx';

const TaskNavigator = ({ tasks, currentTask, onSelectTask }) => {
  const { createTask, deleteTask } = useStore();
  const [activeTab, setActiveTab] = useState('all'); // all, recent, favorites

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

  const taskList = useMemo(() => Object.values(tasks), [tasks]);

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--bg-secondary)' }}>
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center justify-between mb-4">
          <h2 className="panel-title">Tasks</h2>
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
      <div className="flex-1 overflow-y-auto p-5">
        <div className="space-y-1">
          {taskList.map(task => {
            const isActive = currentTask === task.id;
            const versionCount = task.versions ? Object.keys(task.versions).length : 0;

            return (
              <div
                key={task.id}
                className="task-item group flex items-center justify-between"
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
                    {versionCount} versions • Modified {formatTimeAgo(task.updatedAt)}
                  </div>
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

      {/* Footer */}
      <div className="p-4 border-t" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex gap-2">
          <button className="btn btn-secondary w-full" onClick={handleNewTask}>
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