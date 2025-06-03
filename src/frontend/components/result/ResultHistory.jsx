import React from 'react';

function ResultHistory({ results, selectedResult, onSelectResult }) {
  if (!results || results.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 dark:text-gray-400">
        <p>아직 실행 결과가 없습니다.</p>
      </div>
    );
  }
  
  return (
    <div className="p-4">
      <h3 className="font-medium mb-3">이전 실행 결과</h3>
      <div className="space-y-2">
        {results.map((result, index) => (
          <div
            key={`${result.versionId || 'unknown'}-${result.timestamp || Date.now()}-${index}`}
            className={`
              p-3 border rounded cursor-pointer transition-colors
              ${selectedResult === result
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'}
            `}
            onClick={() => onSelectResult(result)}
          >
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {new Date(result.timestamp || 0).toLocaleString()}
              </span>
              <span className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded">
                #{results.length - index}
              </span>
            </div>
            
            <div className="flex flex-wrap gap-2 text-xs text-gray-600 dark:text-gray-400 mb-2">
              {result.versionName && (
                <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                  버전: {result.versionName}
                </span>
              )}
              {result.output?.model && (
                <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded">
                  모델: {result.output.model}
                </span>
              )}
            </div>
            <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              <div className="truncate">
                {result.output?.response ? result.output.response.substring(0, 100) + '...' : "내용 없음"}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ResultHistory;