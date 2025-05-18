import React, { useState } from 'react';
import { useStore } from '../../store.jsx';
import Button from '../common/Button.jsx';

function TaskActions() {
  const { createTask } = useStore();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [taskName, setTaskName] = useState('');
  const [taskGroup, setTaskGroup] = useState('기본 그룹');
  const [newGroupName, setNewGroupName] = useState('');
  const [availableGroups] = useState(['기본 그룹', '마케팅', '고객 지원', '제품 개발', '기술 문서']);
  
  const handleCreateTask = async () => {
    if (!taskName.trim()) return;
    
    // 새 그룹 옵션을 선택한 경우 newGroupName을 사용
    const finalGroup = taskGroup === '__new__' && newGroupName.trim() 
      ? newGroupName.trim() 
      : taskGroup;
    
    try {
      await createTask(taskName, finalGroup);
      setTaskName('');
      setTaskGroup('기본 그룹');
      setNewGroupName('');
      setShowCreateForm(false);
    } catch (error) {
      console.error("Failed to create task:", error);
    }
  };
  
  return (
    <div className="p-3 border-t border-gray-300 dark:border-gray-700">
      {showCreateForm ? (
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">태스크 이름</label>
            <input
              type="text"
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
              placeholder="새 태스크 이름 입력..."
              value={taskName}
              onChange={(e) => setTaskName(e.target.value)}
              autoFocus
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">그룹</label>
            <select
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
              value={taskGroup}
              onChange={(e) => setTaskGroup(e.target.value)}
            >
              {availableGroups.map((group) => (
                <option key={group} value={group}>{group}</option>
              ))}
              <option value="__new__">새 그룹 추가...</option>
            </select>
          </div>
          
          {taskGroup === '__new__' && (
            <div>
              <label className="block text-sm font-medium mb-1">새 그룹 이름</label>
              <input
                type="text"
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
                placeholder="새 그룹 이름 입력..."
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
              />
            </div>
          )}
          
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              size="small"
              onClick={() => {
                setShowCreateForm(false);
                setTaskName('');
                setTaskGroup('기본 그룹');
                setNewGroupName('');
              }}
            >
              취소
            </Button>
            <Button
              variant="primary"
              size="small"
              onClick={handleCreateTask}
            >
              생성
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="primary"
            className="w-full"
            onClick={() => setShowCreateForm(true)}
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            태스크 추가
          </Button>
          <Button
            variant="outline"
            className="w-full"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
            </svg>
            가져오기
          </Button>
        </div>
      )}
    </div>
  );
}

export default TaskActions;