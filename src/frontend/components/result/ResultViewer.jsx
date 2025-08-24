// src/frontend/components/result/ResultViewer.jsx
import React, { useState } from 'react';
import { useStore } from '../../store.jsx';

const ResultViewer = ({ taskId, versionId }) => {
  const { tasks } = useStore();
  const [activeTab, setActiveTab] = useState('response'); // response, history, comparison, metrics
  
  const currentTask = taskId ? tasks[taskId] : null;
  const currentVersion = currentTask?.versions?.[versionId];

  // Mock data for demonstration
  const mockResult = {
    content: "# 생성형 AI가 중소기업에 가져올 혁신적인 변화\n\n안녕하세요, 사업을 운영하시는 대표님들! 오늘은 최근 화제가 되고 있는 생성형 AI가 우리 비즈니스에 어떤 실질적인 도움을 줄 수 있는지 함께 알아보겠습니다.\n\n## 1. 마케팅 콘텐츠 제작의 효율화\n\n이제 더 이상 비싼 비용을 들여 외주를 맡기지 않아도 됩니다. 생성형 AI를 활용하면 블로그 포스트, 소셜 미디어 콘텐츠 등을 빠르고 효율적으로 제작할 수 있습니다...\n\n## 2. 고객 서비스 자동화\n\n24시간 고객 응대가 가능한 AI 챗봇을 도입하여 고객 만족도를 높이고...",
    responseTime: "2.3s",
    timestamp: "2024.03.15 14:32",
    model: "GPT-4",
    tokens: 1247,
    estimatedCost: "$0.037"
  };

  if (!currentTask) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted">Please select a task</p>
      </div>
    );
  }

  // This component now has its own internal tabs, which is a bit redundant
  // but we will keep it for now to preserve functionality.
  // A future refactor could move this tab state into the parent MainContent component.
  return (
    <>
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center justify-between mb-4">
          <h2 className="panel-title">Result</h2>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            Response Time: {mockResult.responseTime}
          </span>
        </div>

        {/* Tabs */}
        <div className="tab-container">
          <button 
            className={`tab ${activeTab === 'response' ? 'active' : ''}`}
            onClick={() => setActiveTab('response')}
          >
            Response
          </button>
          <button 
            className={`tab ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            History
          </button>
          <button 
            className={`tab ${activeTab === 'comparison' ? 'active' : ''}`}
            onClick={() => setActiveTab('comparison')}
          >
            Comparison
          </button>
          <button 
            className={`tab ${activeTab === 'metrics' ? 'active' : ''}`}
            onClick={() => setActiveTab('metrics')}
          >
            Metrics
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-5">
        {activeTab === 'response' && (
          <div className="space-y-4">
            {/* AI Response Card */}
            <div className="card">
              <div className="flex items-start gap-3 mb-4">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs"
                     style={{ background: 'var(--gradient-ai)' }}>
                  ✨
                </div>
                <div>
                  <div className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                    {mockResult.model} Response
                  </div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {mockResult.timestamp}
                  </div>
                </div>
              </div>

              <div className="prose prose-sm max-w-none">
                <div style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                  <h2 style={{ color: 'var(--text-primary)', fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
                    Generative AI's Impact on Small Businesses
                  </h2>
                  <p className="mb-3">
                    Hello, business owners! Today, let's explore how generative AI can practically help your business.
                  </p>
                  <h3 style={{ color: 'var(--text-primary)', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                    1. Streamlining Marketing Content Creation
                  </h3>
                  <p className="mb-3">
                    You no longer need to spend a fortune on outsourcing. With generative AI, you can create blog posts, social media content, and more, quickly and efficiently...
                  </p>
                  <h3 style={{ color: 'var(--text-primary)', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                    2. Automating Customer Service
                  </h3>
                  <p>
                    Implement a 24/7 AI chatbot to increase customer satisfaction...
                  </p>
                </div>
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-4">
              <div className="metric-card primary">
                <div className="metric-label">Tokens Used</div>
                <div className="metric-value primary">{mockResult.tokens.toLocaleString()}</div>
              </div>
              <div className="metric-card success">
                <div className="metric-label">Estimated Cost</div>
                <div className="metric-value success">{mockResult.estimatedCost}</div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button className="btn btn-secondary flex-1">
                🔄 Regenerate
              </button>
              <button className="btn btn-success flex-1">
                ✓ Save
              </button>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📚</div>
            <p className="text-muted">No execution history</p>
          </div>
        )}

        {activeTab === 'comparison' && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">⚖️</div>
            <p className="text-muted">No results to compare</p>
          </div>
        )}

        {activeTab === 'metrics' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4">
              <div className="metric-card primary">
                <div className="metric-label">Total Tokens Used</div>
                <div className="metric-value primary">12,847</div>
              </div>
              <div className="metric-card success">
                <div className="metric-label">Total Cost</div>
                <div className="metric-value success">$3.42</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Average Response Time</div>
                <div className="metric-value" style={{ color: 'var(--text-primary)' }}>1.8s</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default ResultViewer;