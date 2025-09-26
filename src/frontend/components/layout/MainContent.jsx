import React, { useState } from 'react';
import PromptEditor from '../prompt/PromptEditor.jsx';
import ResultViewer from '../result/ResultViewer.jsx';
import LLMEndpointSettings from '../settings/LLMEndpointSettings.jsx';

const MainContentPlaceholder = () => (
  <div className="flex items-center justify-center h-full p-4">
    <div className="text-center">
      <div className="text-6xl mb-4">✨</div>
      <h3 className="text-xl font-semibold text-primary mb-4">Prompt Manager에 오신 것을 환영합니다!</h3>
      <p className="text-secondary max-w-md mx-auto mb-2">
        왼쪽 패널에서 기존 태스크를 선택하거나, 새로운 태스크를 생성하여 프롬프트 관리를 시작하세요.
      </p>
      <p className="text-muted text-sm">
        태스크를 선택하면 프롬프트 편집기 및 결과 뷰어가 여기에 표시됩니다.
      </p>
    </div>
  </div>
);

const MainContent = ({ currentTask, currentVersion, view }) => {
  const [activeTab, setActiveTab] = useState('editor');

  if (view === 'settings') {
    return <LLMEndpointSettings />;
  }

  if (view === 'task-list' || !currentTask) {
    return <MainContentPlaceholder />;
  }

  return (
    <>
      <div className="tab-container mb-2">
        <button
          className={`tab ${activeTab === 'editor' ? 'active' : ''}`}
          onClick={() => setActiveTab('editor')}
        >
          Prompt Editor
        </button>
        <button
          className={`tab ${activeTab === 'result' ? 'active' : ''}`}
          onClick={() => setActiveTab('result')}
        >
          Result Viewer
        </button>
      </div>
      <div className="tab-content">
        {activeTab === 'editor' ? (
          <PromptEditor taskId={currentTask} versionId={currentVersion} />
        ) : (
          <ResultViewer taskId={currentTask} versionId={currentVersion} />
        )}
      </div>
    </>
  );
};

export default MainContent;
