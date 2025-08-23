// src/frontend/components/task/TaskNavigator.jsx
import React, { useState, useMemo } from 'react';
import { useStore } from '../../store.jsx';

const TaskNavigator = ({ tasks, currentTask, onSelectTask }) => {
  const { createTask } = useStore();
  const [activeTab, setActiveTab] = useState('all'); // all, recent, favorites
  const [expandedFolders, setExpandedFolders] = useState(['marketing']); // Start with marketing expanded

  // Organize tasks into folders (mock data structure for demonstration)
  const folderStructure = useMemo(() => {
    const folders = {
      marketing: { name: '마케팅 콘텐츠', icon: '📂', tasks: [] },
      development: { name: '개발 도구', icon: '📁', tasks: [] },
      analysis: { name: '데이터 분석', icon: '📁', tasks: [] },
      support: { name: '고객 서비스', icon: '📁', tasks: [] }
    };

    // Categorize tasks (simple categorization based on task name keywords)
    Object.entries(tasks).forEach(([id, task]) => {
      const name = task.name.toLowerCase();
      if (name.includes('블로그') || name.includes('소셜') || name.includes('마케팅') || name.includes('캐') || name.includes('이메일')) {
        folders.marketing.tasks.push({ id, ...task });
      } else if (name.includes('개발') || name.includes('코드') || name.includes('API')) {
        folders.development.tasks.push({ id, ...task });
      } else if (name.includes('분석') || name.includes('데이터') || name.includes('리포트')) {
        folders.analysis.tasks.push({ id, ...task });
      } else if (name.includes('고객') || name.includes('서비스') || name.includes('지원')) {
        folders.support.tasks.push({ id, ...task });
      } else {
        folders.marketing.tasks.push({ id, ...task }); // Default to marketing
      }
    });

    return folders;
  }, [tasks]);

  const handleNewTask = async () => {
    try {
      const taskName = prompt('새 태스크 이름을 입력하세요:');
      if (taskName && taskName.trim()) {
        await createTask(taskName.trim());
      }
    } catch (error) {
      console.error('태스크 생성 실패:', error);
      alert('태스크 생성에 실패했습니다.');
    }
  };

  const toggleFolder = (folderId) => {
    setExpandedFolders(prev => 
      prev.includes(folderId) 
        ? prev.filter(id => id !== folderId)
        : [...prev, folderId]
    );
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

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center justify-between mb-4">
          <h2 className="panel-title">태스크</h2>
          <button 
            className="btn btn-primary"
            onClick={handleNewTask}
          >
            + 새 태스크
          </button>
        </div>

        {/* Tabs */}
        <div className="tab-container">
          <button 
            className={`tab ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
          >
            전체
          </button>
          <button 
            className={`tab ${activeTab === 'recent' ? 'active' : ''}`}
            onClick={() => setActiveTab('recent')}
          >
            최근
          </button>
          <button 
            className={`tab ${activeTab === 'favorites' ? 'active' : ''}`}
            onClick={() => setActiveTab('favorites')}
          >
            즐겨찾기
          </button>
        </div>
      </div>

      {/* Task List */}
      <div className="flex-1 overflow-y-auto p-5">
        {Object.entries(folderStructure).map(([folderId, folder]) => {
          const isExpanded = expandedFolders.includes(folderId);
          const taskCount = folder.tasks.length;
          
          if (taskCount === 0) return null;

          return (
            <div key={folderId} className="mb-6">
              {/* Folder Header */}
              <button
                className="flex items-center justify-between w-full p-2 hover:bg-gray-800/30 rounded-md transition-colors"
                onClick={() => toggleFolder(folderId)}
              >
                <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-dim)' }}>
                  <span>{isExpanded ? '▼' : '▶'}</span>
                  <span>{folder.icon}</span>
                  <span>{folder.name}</span>
                </div>
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  {taskCount}
                </span>
              </button>

              {/* Tasks in Folder */}
              {isExpanded && (
                <div className="mt-2 space-y-1">
                  {folder.tasks.map(task => {
                    const isActive = currentTask === task.id;
                    const versionCount = task.versions ? Object.keys(task.versions).length : 1;
                    
                    return (
                      <div
                        key={task.id}
                        className={`relative p-3 ml-6 rounded-lg cursor-pointer transition-all ${
                          isActive 
                            ? 'bg-indigo-500/15 border-l-4 border-indigo-500' 
                            : 'hover:bg-gray-800/30'
                        }`}
                        onClick={() => onSelectTask(task.id)}
                      >
                        <div className="flex items-start justify-between">
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
                          
                          {/* Favorite Star */}
                          <button 
                            className="text-sm opacity-70 hover:opacity-100"
                            onClick={(e) => {
                              e.stopPropagation();
                              // TODO: Toggle favorite
                            }}
                          >
                            ⭐
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}

        {/* Empty State */}
        {Object.keys(tasks).length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📝</div>
            <p className="text-muted mb-4">아직 태스크가 없습니다</p>
            <button 
              className="btn btn-primary"
              onClick={handleNewTask}
            >
              첫 번째 태스크 생성하기
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskNavigator;