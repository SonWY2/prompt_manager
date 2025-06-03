import React from 'react';

function LLMEndpointList({
  endpoints,
  selectedEndpointId,
  activeEndpointId,
  defaultEndpointId,
  onSelect,
  onEdit,
  onDelete,
  onCreateNew,
  activeEndpoint
}) {
  
  return (
    <div className="h-full flex flex-col">
      {/* 헤더 */}
      <div className="p-4 border-b border-gray-300 dark:border-gray-700">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
          LLM Endpoint 설정
        </h3>
        
        {/* 현재 사용 중인 엔드포인트 요약 */}
        {activeEndpoint && (
          <div className="text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 p-2 rounded">
            <div className="font-medium">현재 사용 중</div>
            <div className="truncate">{activeEndpoint.name}</div>
          </div>
        )}
      </div>
      
      {/* 엔드포인트 목록 */}
      <div className="flex-1 overflow-y-auto">
        {endpoints.length === 0 ? (
          <div className="p-4 text-center text-gray-500 dark:text-gray-400">
            <p className="text-sm">등록된 엔드포인트가 없습니다.</p>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {endpoints.map(endpoint => (
              <div
                key={endpoint.id}
                className={`group relative p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedEndpointId === endpoint.id
                    ? 'bg-blue-100 dark:bg-blue-900 border border-blue-300 dark:border-blue-700'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
                onClick={() => onSelect(endpoint.id)}
              >
                {/* 엔드포인트 이름 */}
                <div className="flex items-center justify-between mb-1">
                  <div className="font-medium text-gray-900 dark:text-white truncate">
                    {endpoint.name}
                  </div>
                  
                  {/* 상태 표시 */}
                  <div className="flex items-center gap-1">
                    {activeEndpointId === endpoint.id && (
                      <span className="inline-block w-2 h-2 bg-green-500 rounded-full" title="현재 사용 중" />
                    )}
                    {defaultEndpointId === endpoint.id && (
                      <span className="inline-block w-2 h-2 bg-purple-500 rounded-full" title="기본값" />
                    )}
                  </div>
                </div>
                
                {/* 엔드포인트 URL */}
                <div className="text-xs text-gray-600 dark:text-gray-400 truncate mb-2">
                  {endpoint.baseUrl}
                </div>
                
                {/* 설명 */}
                {endpoint.description && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 truncate mb-2">
                    {endpoint.description}
                  </div>
                )}
                
                {/* 액션 버튼들 */}
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onEdit(endpoint.id);
                    }}
                    className="p-1 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                    title="편집"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(endpoint.id);
                    }}
                    className="p-1 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                    title="삭제"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* 새 엔드포인트 추가 버튼 */}
      <div className="p-4 border-t border-gray-300 dark:border-gray-700">
        <button
          onClick={onCreateNew}
          className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          새 엔드포인트 추가
        </button>
      </div>
    </div>
  );
}

export default LLMEndpointList;