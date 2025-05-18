import React from 'react';

function VersionTimeline({ versions, currentVersion, onSelectVersion }) {
  if (!versions || versions.length === 0) {
    return (
      <div className="p-3 text-center text-gray-500 dark:text-gray-400">
        <p>아직 버전이 없습니다. 프롬프트를 작성하고 새 버전을 생성해보세요.</p>
      </div>
    );
  }
  
  return (
    <div className="p-3 overflow-x-auto">
      <div className="flex items-center space-x-6">
        {versions.map((version, index) => {
          const date = new Date(version.createdAt || 0);
          const formattedDate = date.toLocaleDateString();
          const isCurrent = version.id === currentVersion;
          
          return (
            <div 
              key={version.id}
              className="group relative"
            >
              <div 
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center cursor-pointer
                  ${isCurrent 
                    ? 'bg-blue-600 text-white shadow-lg' 
                    : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'}
                `}
                onClick={() => onSelectVersion && onSelectVersion(version.id)}
                title={version.name || version.id}
              >
                <span className="text-xs">{index + 1}</span>
              </div>
              
              {/* 버전 정보 툴팁 */}
              <div 
                className="absolute left-1/2 transform -translate-x-1/2 bottom-full mb-2 hidden group-hover:block z-10"
              >
                <div className="bg-gray-800 text-white text-xs rounded p-2 shadow-lg min-w-[150px]">
                  <p className="font-semibold">{version.name || version.id}</p>
                  <p className="text-gray-400 text-xs">{version.id}</p>
                  <p>{formattedDate}</p>
                  {version.description && <p>{version.description}</p>}
                </div>
              </div>
              
              {/* 연결선 */}
              {index < versions.length - 1 && (
                <div className="absolute top-1/2 left-full w-6 h-0.5 bg-gray-300 dark:bg-gray-600"></div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default VersionTimeline;