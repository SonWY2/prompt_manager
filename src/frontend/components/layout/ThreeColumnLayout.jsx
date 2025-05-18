import React, { useState } from 'react';
import ResponsivePanel from './ResponsivePanel.jsx';

// 3단 레이아웃 컴포넌트
function ThreeColumnLayout({ 
  leftPanel, 
  centerPanel, 
  rightPanel, 
  leftPanelWidth = 20, 
  rightPanelWidth = 30 
}) {
  const [leftWidth, setLeftWidth] = useState(leftPanelWidth);
  const [rightWidth, setRightWidth] = useState(rightPanelWidth);
  
  return (
    <div className="flex flex-1 h-full overflow-hidden">
      {/* 왼쪽 패널 - 태스크 네비게이터 */}
      <ResponsivePanel 
        width={leftWidth} 
        onResize={setLeftWidth}
        minWidth={15}
        maxWidth={30}
        className="bg-gray-100 dark:bg-gray-800 border-r border-gray-300 dark:border-gray-700"
      >
        {leftPanel}
      </ResponsivePanel>
      
      {/* 중앙 패널 - 프롬프트 에디터 */}
      <div className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-gray-900">
        {centerPanel}
      </div>
      
      {/* 오른쪽 패널 - 결과 뷰어 */}
      <ResponsivePanel 
        width={rightWidth} 
        onResize={setRightWidth}
        minWidth={20}
        maxWidth={50}
        resizeFrom="left"
        className="bg-gray-50 dark:bg-gray-800 border-l border-gray-300 dark:border-gray-700"
      >
        {rightPanel}
      </ResponsivePanel>
    </div>
  );
}

export default ThreeColumnLayout;