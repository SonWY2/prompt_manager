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
        <p className="text-muted">태스크를 선택해 주세요</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center justify-between mb-4">
          <h2 className="panel-title">결과</h2>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            응답시간: {mockResult.responseTime}
          </span>
        </div>

        {/* Tabs */}
        <div className="tab-container">
          <button 
            className={`tab ${activeTab === 'response' ? 'active' : ''}`}
            onClick={() => setActiveTab('response')}
          >
            응답
          </button>
          <button 
            className={`tab ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            이력
          </button>
          <button 
            className={`tab ${activeTab === 'comparison' ? 'active' : ''}`}
            onClick={() => setActiveTab('comparison')}
          >
            비교
          </button>
          <button 
            className={`tab ${activeTab === 'metrics' ? 'active' : ''}`}
            onClick={() => setActiveTab('metrics')}
          >
            메트릭
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5">
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
                    {mockResult.model} 응답
                  </div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {mockResult.timestamp}
                  </div>
                </div>
              </div>

              <div className="prose prose-sm max-w-none">
                <div style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                  <h2 style={{ color: 'var(--text-primary)', fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
                    생성형 AI가 중소기업에 가져올 혁신적인 변화
                  </h2>
                  <p className="mb-3">
                    안녕하세요, 사업을 운영하시는 대표님들! 오늘은 최근 화제가 되고 있는 생성형 AI가 우리 비즈니스에 어떤 실질적인 도움을 줄 수 있는지 함께 알아보겠습니다.
                  </p>
                  <h3 style={{ color: 'var(--text-primary)', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                    1. 마케팅 콘텐츠 제작의 효율화
                  </h3>
                  <p className="mb-3">
                    이제 더 이상 비싼 비용을 들여 외주를 맡기지 않아도 됩니다. 생성형 AI를 활용하면 블로그 포스트, 소셜 미디어 콘텐츠 등을 빠르고 효율적으로 제작할 수 있습니다...
                  </p>
                  <h3 style={{ color: 'var(--text-primary)', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                    2. 고객 서비스 자동화
                  </h3>
                  <p>
                    24시간 고객 응대가 가능한 AI 챗봇을 도입하여 고객 만족도를 높이고...
                  </p>
                </div>
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-4">
              <div className="metric-card primary">
                <div className="metric-label">토큰 사용량</div>
                <div className="metric-value primary">{mockResult.tokens.toLocaleString()}</div>
              </div>
              <div className="metric-card success">
                <div className="metric-label">예상 비용</div>
                <div className="metric-value success">{mockResult.estimatedCost}</div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button className="btn btn-secondary flex-1">
                🔄 재생성
              </button>
              <button className="btn btn-success flex-1">
                ✓ 저장
              </button>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📚</div>
            <p className="text-muted">실행 이력이 없습니다</p>
          </div>
        )}

        {activeTab === 'comparison' && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">⚖️</div>
            <p className="text-muted">비교할 결과가 없습니다</p>
          </div>
        )}

        {activeTab === 'metrics' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4">
              <div className="metric-card primary">
                <div className="metric-label">총 토큰 사용량</div>
                <div className="metric-value primary">12,847</div>
              </div>
              <div className="metric-card success">
                <div className="metric-label">총 비용</div>
                <div className="metric-value success">$3.42</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">평균 응답 시간</div>
                <div className="metric-value" style={{ color: 'var(--text-primary)' }}>1.8s</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultViewer;