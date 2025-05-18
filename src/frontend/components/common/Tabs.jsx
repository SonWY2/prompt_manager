import React from 'react';

// 탭 컴포넌트
function Tabs({ tabs, activeTab, onTabChange }) {
  return (
    <div className="flex border-b border-gray-300 dark:border-gray-700 mt-2">
      {tabs.map(tab => (
        <button
          key={tab.id}
          className={`
            px-4 py-2 text-sm font-medium
            ${activeTab === tab.id
              ? 'text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}
          `}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

export default Tabs;