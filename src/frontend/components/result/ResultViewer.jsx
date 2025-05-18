import React, { useState, useEffect } from 'react';
import { useStore } from '../../store.jsx';
import ResultHistory from './ResultHistory.jsx';
import ComparisonView from './ComparisonView.jsx';
import MetricsDisplay from './MetricsDisplay.jsx';
import Tabs from '../common/Tabs.jsx';
import Button from '../common/Button.jsx';

function ResultViewer({ taskId, versionId }) {
  const { 
    tasks, 
    getVersionResults, 
    compareVersions
  } = useStore();
  
  const [activeTab, setActiveTab] = useState('latest');
  const [results, setResults] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);
  const [comparedResults, setComparedResults] = useState(null);
  
  // 결과 데이터 로드
  useEffect(() => {
    if (taskId && versionId) {
      const versionResults = getVersionResults(taskId, versionId);
      setResults(versionResults || []);
      
      if (versionResults && versionResults.length > 0) {
        setSelectedResult(versionResults[0]);
      } else {
        setSelectedResult(null);
      }
    }
  }, [taskId, versionId, getVersionResults]);
  
  // 탭 정의
  const tabs = [
    { id: 'latest', label: '최신 결과' },
    { id: 'history', label: '이력' },
    { id: 'compare', label: '비교' },
    { id: 'metrics', label: '메트릭' },
  ];
  
  // 결과가 없는 경우
  if (!taskId || !versionId) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
        <div className="text-center">
          <p>태스크와 버전을 선택하고 프롬프트를 실행하면 결과가 여기에 표시됩니다.</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-full flex flex-col">
      {/* 헤더 */}
      <div className="p-3 border-b border-gray-300 dark:border-gray-700">
        <h2 className="text-lg font-semibold">결과 뷰어</h2>
        <Tabs 
          tabs={tabs} 
          activeTab={activeTab} 
          onTabChange={setActiveTab}
        />
      </div>
      
      {/* 콘텐츠 영역 */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'latest' && (
          <div className="p-4">
            {selectedResult ? (
              <>
                <div className="mb-3 flex justify-between items-center">
                  <div>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      실행 시각: {new Date(selectedResult.timestamp || 0).toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <Button 
                      variant="outline"
                      size="small"
                      onClick={() => {/* 내보내기 로직 */}}
                    >
                      내보내기
                    </Button>
                  </div>
                </div>
                
                <div className="bg-white dark:bg-gray-900 rounded shadow p-4 mt-2">
                  <h3 className="font-semibold mb-2">LLM 응답:</h3>
                  <pre className="whitespace-pre-wrap bg-gray-50 dark:bg-gray-800 p-3 rounded dark:text-white">
                    {selectedResult.output?.response || "응답 데이터 없음"}
                  </pre>
                </div>
                
                <details className="mt-4">
                  <summary className="cursor-pointer text-blue-600 dark:text-blue-400">
                    사용된 프롬프트 보기
                  </summary>
                  <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-800 rounded text-sm">
                    <pre className="whitespace-pre-wrap dark:text-white">{selectedResult.output?.prompt || "프롬프트 데이터 없음"}</pre>
                  </div>
                </details>
              </>
            ) : (
              <div className="text-center text-gray-500 dark:text-gray-400 py-10">
                <p>아직 결과가 없습니다. 프롬프트를 실행하여 결과를 생성하세요.</p>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'history' && (
          <ResultHistory 
            results={results}
            selectedResult={selectedResult}
            onSelectResult={setSelectedResult}
          />
        )}
        
        {activeTab === 'compare' && (
          <ComparisonView 
            versions={tasks[taskId]?.versions || []}
            currentVersionId={versionId}
            onCompare={(v1, v2) => {
              const compResult = compareVersions(taskId, v1, v2);
              setComparedResults(compResult);
            }}
            comparedResults={comparedResults}
          />
        )}
        
        {activeTab === 'metrics' && selectedResult && (
          <MetricsDisplay result={selectedResult} />
        )}
      </div>
    </div>
  );
}

export default ResultViewer;