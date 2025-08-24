// src/frontend/components/layout/ThreeColumnLayout.jsx
import React from 'react';
import {
  Panel,
  PanelGroup,
  PanelResizeHandle,
} from 'react-resizable-panels';

const ThreeColumnLayout = ({ leftPanel, centerPanel, rightPanel }) => {
  return (
    <PanelGroup direction="horizontal" className="h-full w-full">
      <Panel defaultSize={20} minSize={15}>
        {leftPanel}
      </Panel>
      <PanelResizeHandle />
      <Panel defaultSize={50} minSize={30}>
        {centerPanel}
      </Panel>
      <PanelResizeHandle />
      <Panel defaultSize={30} minSize={20}>
        {rightPanel}
      </Panel>
    </PanelGroup>
  );
};

export default ThreeColumnLayout;
