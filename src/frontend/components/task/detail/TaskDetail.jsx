import React, { useState, useEffect } from 'react';
import { useStore } from '../../../store.jsx';
import Button from '../../common/Button.jsx';
import { apiUrl } from '../../../utils/api';

function TaskDetail({ taskId }) {
  const { tasks, versions, updateTask, addVersion, selectVersion, deleteVersion, getVersionDetail, loadVersions, initiateNewVersion } = useStore();
  
  const [isEditing, setIsEditing] = useState(false);
  const [taskName, setTaskName] = useState('');
  const [taskGroup, setTaskGroup] = useState('');

  const currentTask = tasks[taskId];

  useEffect(() => {
    if (currentTask) {
      setTaskName(currentTask.name);
      setTaskGroup(currentTask.group);
    }
  }, [currentTask]);

  // 태스크가 변경될 때 버전 로드
  useEffect(() => {
    if (taskId) {
      loadVersions(taskId);
    }
  }, [taskId, loadVersions]);

  if (!currentTask) return null;

  const handleUpdateTask = () => {
    if (!taskName.trim()) return;
    
    updateTask(taskId, {
      name: taskName,
      group: taskGroup
    });
    
    setIsEditing(false);
  };
  

  // 버전 선택 및 편집 모드로 전환
  const handleSelectVersionForEdit = (versionId) => {
    selectVersion(versionId, true); // 편집 모드로 설정하여 버전 선택
  };
  
  // 버전 선택 (읽기 모드)
  const handleSelectVersion = (versionId) => {
    selectVersion(versionId, false); // 읽기 모드로 설정하여 버전 선택
  };
  
  const hasVersions = versions && versions.length > 0;
  
  return (
    <div className="p-4">
      {isEditing ? (
        <div className="space-y-3 mb-4">
          <h2 className="text-lg font-semibold">태스크 정보 수정</h2>
          <div>
            <label className="block text-sm font-medium mb-1">태스크 이름</label>
            <input
              type="text"
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
              value={taskName}
              onChange={(e) => setTaskName(e.target.value)}
              autoFocus
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">그룹</label>
            <input
              type="text"
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
              value={taskGroup}
              onChange={(e) => setTaskGroup(e.target.value)}
            />
          </div>
          
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              size="small"
              onClick={() => {
                setIsEditing(false);
                setTaskName(currentTask.name);
                setTaskGroup(currentTask.group);
              }}
            >
              취소
            </Button>
            <Button
              variant="primary"
              size="small"
              onClick={handleUpdateTask}
            >
              저장
            </Button>
          </div>
        </div>
      ) : (
        <div className="mb-4 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold">{currentTask.name}</h2>
            <div className="text-sm text-gray-500 dark:text-gray-400">그룹: {currentTask.group}</div>
          </div>
          <Button
            variant="outline"
            size="small"
            onClick={() => setIsEditing(true)}
          >
            수정
          </Button>
        </div>
      )}
      
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-medium">버전 관리</h3>
        </div>
        
        
        
        {hasVersions ? (
          <div className="space-y-2">
            {versions.map((version) => (
              <div 
                key={version.id}
                className="p-3 border border-gray-300 dark:border-gray-700 rounded flex justify-between items-center hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer relative group"
                onClick={() => handleSelectVersion(version.id)}
              >
                {/* X 삭제 버튼 */}
                <button
                  className="absolute top-1 left-1 p-1 rounded-full bg-red-500 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={async (e) => {
                    e.stopPropagation(); // 클릭 버블링 방지
                    
                    // 로딩 상태 표시를 위한 UI 개선 (옵션)
                    const deleteButton = e.target.closest('button');
                    const originalText = deleteButton.innerHTML;
                    deleteButton.innerHTML = '<div class="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>';
                    deleteButton.disabled = true;
                    
                    try {
                      // 버전 정보 확인
                      const versionInfo = await getVersionDetail(taskId, version.id);
                      
                      if (!versionInfo) {
                        alert('삭제할 버전을 찾을 수 없습니다.');
                        return;
                      }
                      
                      // 삭제 확인
                      if (window.confirm(`정말 이 버전(${versionInfo.name || versionInfo.id})을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다!`)) {
                        // 스토어의 deleteVersion 함수 사용
                        try {
                          const result = await deleteVersion(taskId, version.id);
                          
                          // 삭제 성공
                          console.log('버전 삭제 성공!', result);
                          
                          // 성공 메시지 표시 (사용자 경험 개선)
                          const successMsg = document.createElement('div');
                          successMsg.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded shadow-lg z-50';
                          successMsg.textContent = result.message || '버전이 삭제되었습니다.';
                          document.body.appendChild(successMsg);
                          setTimeout(() => {
                            if (successMsg.parentNode) {
                              successMsg.parentNode.removeChild(successMsg);
                            }
                          }, 3000);
                          
                          // 버전 목록 새로고침 (안전하게 처리)
                          setTimeout(() => {
                            loadVersions(taskId);
                          }, 500);
                          
                        } catch (err) {
                          console.error('삭제 오류:', err);
                          
                          // 사용자 친화적 에러 메시지
                          let userMessage = '삭제 중 오류가 발생했습니다.';
                          
                          if (err.message.includes('서버에 연결할 수 없습니다')) {
                            userMessage = '서버에 연결할 수 없습니다.\n\n다음을 확인해주세요:\n1. 백엔드 서버가 실행 중인지 확인\n2. 네트워크 연결 상태 확인\n3. 브라우저 새로고침 후 재시도';
                          } else if (err.message.includes('서버 내부 오류')) {
                            userMessage = '서버에서 오류가 발생했습니다.\n\n다음을 확인해주세요:\n1. 서버 로그 확인\n2. 잠시 후 다시 시도\n3. 백엔드 서버 재시작';
                          } else if (err.message.includes('시간이 초과')) {
                            userMessage = '서버 응답 시간이 초과되었습니다.\n\n네트워크 연결을 확인하고 다시 시도해주세요.';
                          }
                          
                          alert(userMessage);
                        }
                      }
                    } catch (error) {
                      console.error('버전 정보 가져오기 오류:', error);
                      alert(`버전 정보를 가져올 수 없습니다: ${error.message}`);
                    } finally {
                      // 로딩 상태 해제
                      deleteButton.innerHTML = originalText;
                      deleteButton.disabled = false;
                    }
                  }}
                  title="버전 삭제"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
                <div>
                  <div className="font-medium">{version.name || version.id}</div>
                  {version.description && <div className="text-sm text-gray-600 dark:text-gray-400">{version.description}</div>}
                  <div className="text-xs text-gray-500 dark:text-gray-500">
                    ID: {version.id} | {new Date(version.createdAt).toLocaleString()}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="small"
                    className="text-xs"
                    onClick={(e) => {
                      e.stopPropagation(); // 버블링 방지
                      handleSelectVersionForEdit(version.id); // 편집 모드로 버전 선택
                    }}
                  >
                    편집
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center p-4 text-gray-500 dark:text-gray-400">
            아직 버전이 없습니다. 새 버전을 생성해보세요.
          </div>
        )}
      </div>

      {/* 하단 바에 새 버전 생성 버튼 배치 */}
      <div className="p-3 border-t border-gray-300 dark:border-gray-700 mt-auto">
        <div className="grid grid-cols-1 gap-2">
          <Button
            variant="primary"
            className="w-full"
            onClick={() => initiateNewVersion(taskId)}
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            새 버전 생성
          </Button>
        </div>
      </div>
    </div>
  );
}

export default TaskDetail;