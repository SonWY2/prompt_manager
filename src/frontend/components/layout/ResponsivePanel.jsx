import React, { useRef, useEffect } from 'react';

// 리사이징 가능한 패널 컴포넌트
function ResponsivePanel({ 
  children, 
  width, 
  onResize, 
  minWidth = 10,
  maxWidth = 50, 
  resizeFrom = 'right',
  className = '' 
}) {
  const panelRef = useRef(null);
  const resizerRef = useRef(null);
  
  useEffect(() => {
    const resizer = resizerRef.current;
    let startX, startWidth, containerWidth;
    
    function startResize(e) {
      startX = e.clientX;
      const panel = panelRef.current;
      startWidth = panel.offsetWidth;
      containerWidth = panel.parentNode.offsetWidth;
      document.addEventListener('mousemove', resize);
      document.addEventListener('mouseup', stopResize);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }
    
    function resize(e) {
      const deltaX = resizeFrom === 'right' ? e.clientX - startX : startX - e.clientX;
      const newWidth = Math.min(
        Math.max((startWidth + deltaX) / containerWidth * 100, minWidth),
        maxWidth
      );
      onResize(newWidth);
    }
    
    function stopResize() {
      document.removeEventListener('mousemove', resize);
      document.removeEventListener('mouseup', stopResize);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
    
    resizer.addEventListener('mousedown', startResize);
    
    return () => {
      resizer.removeEventListener('mousedown', startResize);
      document.removeEventListener('mousemove', resize);
      document.removeEventListener('mouseup', stopResize);
    };
  }, [onResize, minWidth, maxWidth, resizeFrom]);
  
  return (
    <div 
      ref={panelRef} 
      className={`flex-shrink-0 h-full overflow-hidden relative ${className}`}
      style={{ width: `${width}%` }}
    >
      {children}
      
      <div 
        ref={resizerRef}
        className={`absolute top-0 ${resizeFrom === 'right' ? 'right-0' : 'left-0'} w-1 h-full cursor-col-resize hover:bg-blue-500 opacity-0 hover:opacity-50 transition-opacity z-10`}
      />
    </div>
  );
}

export default ResponsivePanel;