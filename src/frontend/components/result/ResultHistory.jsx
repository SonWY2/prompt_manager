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
            key={index}
            className={`
              p-3 border rounded cursor-pointer
              ${selectedResult === result
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'}
            `}
            onClick={() => onSelectResult(result)}
          >
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">
                {new Date(result.timestamp || 0).toLocaleString()}
              </span>
              <span className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded">
                #{results.length - index}
              </span>
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