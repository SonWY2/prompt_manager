import React from 'react';

function TaskTree({ 
  tasks, 
  currentTask, 
  onSelectTask, 
  expandedGroups = {}, 
  onToggleGroup,
  isSearching = false
}) {
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
  
  // 그룹별로 표시
  return (
    <div className="space-y-2 p-1">
      {Object.entries(tasks).map(([groupName, groupTasks]) => (
        <div key={groupName} className="border border-gray-200 dark:border-gray-700 rounded">
          <div 
            className="flex items-center p-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
            onClick={() => onToggleGroup(groupName)}
          >
            <span className="mr-2">{expandedGroups[groupName] ? '🔽' : '▶️'}</span>
            <span className="font-medium">{groupName}</span>
            <span className="ml-auto text-xs text-gray-500">{groupTasks.length}개</span>
          </div>
          
          {expandedGroups[groupName] && (
            <div className="pl-4 border-t border-gray-200 dark:border-gray-700">
              {groupTasks.map(task => (
                <div 
                  key={task.id}
                  className={`p-2 flex items-center cursor-pointer ${currentTask === task.id ? 'bg-blue-100 dark:bg-blue-900' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`}
                  onClick={() => onSelectTask(task.id)}
                >
                  <span className="mr-2">📄</span>
                  <span className="truncate">{task.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default TaskTree;