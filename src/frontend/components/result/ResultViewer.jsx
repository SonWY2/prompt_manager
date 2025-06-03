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
    versions, // versions 가져오기
    llmEndpoints, // llmEndpoints 가져오기
    historyFilters, // historyFilters 가져오기
    setHistoryFilters, // setHistoryFilters 가져오기
    getFilteredResults, // 필터링된 결과 가져오기
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
      
      // 'latest' 탭에서는 현재 버전의 결과 사용
      if (versionResults && versionResults.length > 0) {
        setSelectedResult(versionResults[0]);
      } else {
        setSelectedResult(null);
      }
    }
  }, [taskId, versionId, getVersionResults]);

  // historyFilters 또는 tasks가 변경될 때마다 필터링된 결과 업데이트
  useEffect(() => {
    if (activeTab === 'history') {
      const filtered = getFilteredResults();
      setResults(filtered);
    }
  }, [activeTab, getFilteredResults]);
  
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

  // 필터 변경 핸들러
  const handleFilterChange = (filterName, value) => {
    setHistoryFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };
  
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
                    {selectedResult.output?.model && (
                      <span className="text-sm text-gray-500 dark:text-gray-400 ml-4">
                        모델: {selectedResult.output.model}
                      </span>
                    )}
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
          <>
            {/* 필터링 UI 추가 */}
            <div className="p-4 border-b border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2">
                  <label htmlFor="version-filter" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    버전:
                  </label>
                  <select
                    id="version-filter"
                    className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={historyFilters.versionId || ''}
                    onChange={(e) => handleFilterChange('versionId', e.target.value || null)}
                  >
                    <option value="">모든 버전</option>
                    {versions.map(v => (
                      <option key={v.id} value={v.id}>
                        {v.name || v.id}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <label htmlFor="model-filter" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    모델:
                  </label>
                  <select
                    id="model-filter"
                    className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={historyFilters.model}
                    onChange={(e) => handleFilterChange('model', e.target.value)}
                  >
                    <option value="all">모든 모델</option>
                    {llmEndpoints.map(ep => (
                      ep.defaultModel && (
                        <option key={ep.id} value={ep.defaultModel}>
                          {ep.name} ({ep.defaultModel})
                        </option>
                      )
                    ))}
                    <option value="mock-model">Mock Model</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <label htmlFor="date-filter" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    날짜:
                  </label>
                  <select
                    id="date-filter"
                    className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={historyFilters.dateRange}
                    onChange={(e) => handleFilterChange('dateRange', e.target.value)}
                  >
                    <option value="all">모든 날짜</option>
                    <option value="today">오늘</option>
                    <option value="last7days">지난 7일</option>
                    <option value="last30days">지난 30일</option>
                  </select>
                </div>

                <div className="text-sm text-gray-600 dark:text-gray-400">
                  총 {results.length}개 결과
                </div>
              </div>
            </div>
            
            <ResultHistory 
              results={results}
              selectedResult={selectedResult}
              onSelectResult={setSelectedResult}
            />
          </>
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