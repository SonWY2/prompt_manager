// src/frontend/components/layout/ThreeColumnLayout.jsx
import React from 'react';

const ThreeColumnLayout = ({ 
  leftPanel, 
  centerPanel, 
  rightPanel 
}) => {
  return (
    <div className="flex h-full">
      {/* Left Panel - Fixed 320px */}
      <div 
        className="panel flex-shrink-0"
        style={{ width: '320px', minWidth: '320px', maxWidth: '320px' }}
      >
        {leftPanel}
      </div>
      
      {/* Center Panel - Fixed calculated width */}
      <div 
        className="panel flex-shrink-0"
        style={{ 
          width: 'calc(100vw - 320px - 400px)', 
          minWidth: 'calc(100vw - 320px - 400px)',
          maxWidth: 'calc(100vw - 320px - 400px)'
        }}
      >
        {centerPanel}
      </div>
      
      {/* Right Panel - Fixed 400px */}
      <div 
        className="panel flex-shrink-0"
        style={{ width: '400px', minWidth: '400px', maxWidth: '400px' }}
      >
        {rightPanel}
      </div>
    </div>
  );
};

export default ThreeColumnLayout;