import React from 'react';

// 탭 컴포넌트
function Tabs({ tabs, activeTab, onTabChange }) {
  return (
    <div className="tab-container mt-2">
      {tabs.map(tab => (
        <button
          key={tab.id}
          className={`tab ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

export default Tabs;
