import React, { useState } from 'react';
import { flushSync } from 'react-dom';
import { useStore } from '../../store.jsx';
import Button from '../common/Button.jsx';

function TaskActions() {
  const { createTask, availableGroups, addGroup, setCurrentTask } = useStore();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [taskName, setTaskName] = useState('');
  const [taskGroup, setTaskGroup] = useState('기본 그룹');
  const [newGroupName, setNewGroupName] = useState('');
  
  const handleCreateTask = () => {
    if (!taskName.trim()) return;
    
    // 버튼 비활성화로 중복 생성 방지
    const createButton = document.querySelector('[data-create-task-btn]');
    if (createButton) {
      createButton.disabled = true;
    }
    
    try {
      let finalGroup = taskGroup;
      
      console.log('태스크 생성 시작:', { name: taskName, group: finalGroup });
      
      // 즉시 UI 업데이트 (폼 초기화)
      flushSync(() => {
        setTaskName('');
        setTaskGroup('기본 그룹');
        setNewGroupName('');
        setShowCreateForm(false);
      });
      
      // 백그라운드에서 실제 생성
      setTimeout(async () => {
        try {
          // 새 그룹 옵션을 선택한 경우
          if (taskGroup === '__new__' && newGroupName.trim()) {
            try {
              const result = await addGroup(newGroupName.trim());
              console.log('그룹 추가 성공:', result);
              finalGroup = newGroupName.trim();
            } catch (groupError) {
              console.warn('그룹 추가 실패:', groupError);
              finalGroup = '기본 그룹';
              alert('그룹 추가에 실패했습니다: ' + groupError.message + '\n기본 그룹으로 생성합니다.');
            }
          }
          
          const taskId = await createTask(taskName, finalGroup);
          console.log('태스크 생성 완료:', taskId);
          
          // 새로 생성된 태스크를 약간의 지연 후 선택 (서버 상태 업데이트 대기)
          setTimeout(() => {
            setCurrentTask(taskId);
            console.log('새 태스크 선택 완료:', taskId);
          }, 100);
          
        } catch (error) {
          console.error('태스크 생성 오류:', error);
          alert('태스크 생성 중 오류가 발생했습니다: ' + error.message);
        } finally {
          // 버튼 재활성화
          if (createButton) {
            createButton.disabled = false;
          }
        }
      }, 0);
      
    } catch (error) {
      console.error('태스크 생성 UI 오류:', error);
      // 버튼 재활성화
      if (createButton) {
        createButton.disabled = false;
      }
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
              data-create-task-btn="true"
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