import React, { useState } from 'react';
import { useStore } from '../../../store.jsx';
import Button from '../../common/Button.jsx';
import { apiUrl } from '../../../utils/api';

function TaskDetail({ taskId }) {
  const { tasks, updateTask, addVersion, selectVersion, deleteVersion, getVersionDetail } = useStore();
  
  const [isEditing, setIsEditing] = useState(false);
  const [showVersionForm, setShowVersionForm] = useState(false);
  const [taskName, setTaskName] = useState(tasks[taskId]?.name || '');
  const [taskGroup, setTaskGroup] = useState(tasks[taskId]?.group || '기본 그룹');
  const [newVersionName, setNewVersionName] = useState('');
  const [newVersionDescription, setNewVersionDescription] = useState('');
  const [newVersionContent, setNewVersionContent] = useState('');
  
  const currentTask = tasks[taskId];
  if (!currentTask) return null;
  
  const handleUpdateTask = () => {
    if (!taskName.trim()) return;
    
    updateTask(taskId, {
      name: taskName,
      group: taskGroup
    });
    
    setIsEditing(false);
  };
  
  const handleCreateVersion = () => {
    if (!newVersionContent.trim()) return;
    
    const versionId = `v${Date.now()}`;
    const name = newVersionName.trim() || versionId;
    
    addVersion(taskId, versionId, newVersionContent, newVersionDescription, name);
    
    setNewVersionName('');
    setNewVersionDescription('');
    setNewVersionContent('');
    setShowVersionForm(false);
  };

  // 버전 선택 및 편집 모드로 전환
  const handleSelectVersionForEdit = (versionId) => {
    selectVersion(versionId, true); // 편집 모드로 설정하여 버전 선택
  };
  
  // 버전 선택 (읽기 모드)
  const handleSelectVersion = (versionId) => {
    selectVersion(versionId, false); // 읽기 모드로 설정하여 버전 선택
  };
  
  const hasVersions = currentTask.versions && currentTask.versions.length > 0;
  
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
        
        {showVersionForm && (
          <div className="space-y-3 p-3 mb-3 border border-gray-300 dark:border-gray-700 rounded bg-gray-50 dark:bg-gray-800">
            <div>
              <label className="block text-sm font-medium mb-1">버전 이름 (선택사항)</label>
              <input
                type="text"
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
                placeholder="예: v1.0, 초기 버전, 영어 버전 (빈칸이면 자동생성)"
                value={newVersionName}
                onChange={(e) => setNewVersionName(e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">설명 (선택사항)</label>
              <input
                type="text"
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
                placeholder="예: 변수 추가, 지시문 개선, 결과물 길이 제한 추가"
                value={newVersionDescription}
                onChange={(e) => setNewVersionDescription(e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">프롬프트 내용</label>
              <textarea
                className="w-full h-32 p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white resize-none"
                placeholder="프롬프트 내용을 입력하세요..."
                value={newVersionContent}
                onChange={(e) => setNewVersionContent(e.target.value)}
              />
            </div>
            
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="small"
                onClick={() => {
                  setShowVersionForm(false);
                  setNewVersionName('');
                  setNewVersionDescription('');
                  setNewVersionContent('');
                }}
              >
                취소
              </Button>
              <Button
                variant="primary"
                size="small"
                onClick={handleCreateVersion}
              >
                생성
              </Button>
            </div>
          </div>
        )}
        
        {hasVersions ? (
          <div className="space-y-2">
            {currentTask.versions.map((version) => (
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
                          await deleteVersion(taskId, version.id);
                          
                          // 삭제 성공
                          console.log('버전 삭제 성공!');
                          alert('버전이 삭제되었습니다.');
                        } catch (err) {
                          console.error('삭제 오류:', err);
                          alert(`삭제 중 오류 발생: ${err.message}`);
                        }
                      }
                    } catch (error) {
                      alert(`버전 정보 가져오기 오류: ${error.message}`);
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
            onClick={() => setShowVersionForm(!showVersionForm)}
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