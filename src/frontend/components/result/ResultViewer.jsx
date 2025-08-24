// src/frontend/components/result/ResultViewer.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useStore } from '../../store.jsx';

const ResultViewer = ({ taskId, versionId }) => {
  const { 
    tasks, 
    llmEndpoints, 
    activeLlmEndpointId,
    callLLM,
    getVersionResults
  } = useStore();
  
  const [activeTab, setActiveTab] = useState('response');
  const [currentResult, setCurrentResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const currentTask = taskId ? tasks[taskId] : null;
  const currentVersion = currentTask?.versions?.find(v => v.id === versionId);
  const activeEndpoint = llmEndpoints.find(ep => ep.id === activeLlmEndpointId);
  
  // 버전의 결과 목록 가져오기
  const versionResults = getVersionResults(taskId, versionId);
  const latestResult = versionResults?.[0];

  // 컴포넌트 마운트 시 최신 결과 설정
  useEffect(() => {
    if (latestResult) {
      setCurrentResult(latestResult);
      setError(null);
    }
  }, [latestResult]);

  // LLM API 호출 함수
  const handleRunPrompt = useCallback(async () => {
    if (!currentTask || !currentVersion || !activeEndpoint) {
      setError('Task, version, or LLM endpoint not available');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // 템플릿 변수들을 기본값으로 처리 (실제 구현시에는 사용자 입력 받아야 함)
      const variables = currentVersion.variables || {};
      const inputData = {};
      
      // Extract variables from prompt content
      const matches = currentVersion.content?.match(/\{\{(\w+)\}\}/g) || [];
      const extractedVars = [...new Set(matches.map(match => match.slice(2, -2)))];
      
      // Set default values for variables if not provided
      extractedVars.forEach(variable => {
        inputData[variable] = variables[variable] || `[${variable}]`;
      });

      console.log('🚀 LLM API 호출 시작:', { 
        taskId, 
        versionId, 
        inputData, 
        endpoint: activeEndpoint.name 
      });

      const result = await callLLM(
        taskId, 
        versionId, 
        inputData, 
        currentVersion.system_prompt
      );

      console.log('✅ LLM API 호출 성공:', result);

      // 결과 설정
      const formattedResult = {
        inputData,
        output: result,
        timestamp: new Date().toISOString(),
        endpoint: activeEndpoint
      };

      setCurrentResult(formattedResult);

    } catch (err) {
      console.error('❌ LLM API 호출 실패:', err);
      setError(err.message || 'Failed to call LLM API');
    } finally {
      setIsLoading(false);
    }
  }, [currentTask, currentVersion, activeEndpoint, callLLM, taskId, versionId]);

  // 토큰 계산 (대략적)
  const calculateTokens = useCallback((text) => {
    if (!text) return 0;
    // 간단한 토큰 추정 (실제로는 더 정확한 토크나이저 필요)
    return Math.ceil(text.length / 4);
  }, []);

  // 비용 계산 (대략적)
  const calculateCost = useCallback((inputTokens, outputTokens, model) => {
    // 간단한 비용 추정 (실제 가격은 모델별로 다름)
    const costs = {
      'gpt-4o': { input: 0.0025, output: 0.01 }, // per 1k tokens
      'gpt-4': { input: 0.03, output: 0.06 },
      'gpt-3.5-turbo': { input: 0.001, output: 0.002 },
      'claude-3-opus': { input: 0.015, output: 0.075 },
      'claude-3-sonnet': { input: 0.003, output: 0.015 },
      'claude-3-haiku': { input: 0.00025, output: 0.00125 },
    };
    
    const modelCost = costs[model] || costs['gpt-3.5-turbo'];
    const totalCost = (inputTokens / 1000 * modelCost.input) + (outputTokens / 1000 * modelCost.output);
    return `$${totalCost.toFixed(4)}`;
  }, []);

  if (!currentTask) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center" style={{ color: 'var(--text-muted)' }}>
          <div className="text-4xl mb-4">📝</div>
          <p>Please select a task</p>
        </div>
      </div>
    );
  }

  if (!activeEndpoint) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center" style={{ color: 'var(--text-muted)' }}>
          <div className="text-4xl mb-4">⚙️</div>
          <p className="mb-2">No LLM provider configured</p>
          <p className="text-xs">Please configure an LLM provider in settings</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center justify-between mb-4">
          <h2 className="panel-title">Result</h2>
          <div className="flex items-center gap-2">
            {isLoading && (
              <div className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                Running...
              </div>
            )}
            {currentResult && !isLoading && (
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                {new Date(currentResult.timestamp).toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>

        {/* Active Provider Info */}
        <div className="flex items-center gap-2 mb-4 p-2 rounded" 
             style={{ background: 'rgba(139, 92, 246, 0.1)', border: '1px solid var(--accent-primary)' }}>
          <div className="w-2 h-2 rounded-full bg-green-500"></div>
          <span className="text-xs font-medium" style={{ color: 'var(--accent-primary)' }}>
            {activeEndpoint.name}
          </span>
          {activeEndpoint.defaultModel && (
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
              • {activeEndpoint.defaultModel}
            </span>
          )}
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
            History ({versionResults?.length || 0})
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
      <div className="flex-1 overflow-y-auto p-5">
        {activeTab === 'response' && (
          <div className="space-y-4">
            {/* Run Button */}
            <button
              onClick={handleRunPrompt}
              disabled={isLoading || !currentVersion}
              className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-lg'
              }`}
              style={{ 
                background: 'var(--accent-primary)', 
                color: 'white',
                border: 'none'
              }}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Running Prompt...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Run Prompt
                </>
              )}
            </button>

            {/* Error Display */}
            {error && (
              <div className="p-4 rounded-lg border" style={{ 
                background: 'rgba(239, 68, 68, 0.1)', 
                borderColor: 'var(--accent-danger)',
                color: 'var(--accent-danger)'
              }}>
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span className="font-medium text-sm">Error</span>
                </div>
                <p className="text-sm">{error}</p>
              </div>
            )}

            {/* Response Display */}
            {currentResult && (
              <>
                {/* AI Response Card */}
                <div className="card">
                  <div className="flex items-start gap-3 mb-4">
                    <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs"
                         style={{ background: 'var(--accent-primary)', color: 'white' }}>
                      🤖
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <div className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                          {currentResult.endpoint?.name || 'AI'} Response
                        </div>
                        <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          {new Date(currentResult.timestamp).toLocaleString()}
                        </div>
                      </div>
                      {currentResult.endpoint?.defaultModel && (
                        <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          {currentResult.endpoint.defaultModel}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="prose prose-sm max-w-none">
                    <div style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                      {currentResult.output?.choices?.[0]?.message?.content ? (
                        <div className="whitespace-pre-wrap">
                          {currentResult.output.choices[0].message.content}
                        </div>
                      ) : currentResult.output?.content ? (
                        <div className="whitespace-pre-wrap">
                          {currentResult.output.content}
                        </div>
                      ) : (
                        <div style={{ color: 'var(--text-muted)' }}>
                          No response content available
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Metrics */}
                {(() => {
                  const responseContent = currentResult.output?.choices?.[0]?.message?.content || 
                                        currentResult.output?.content || '';
                  const inputContent = JSON.stringify(currentResult.inputData);
                  
                  const inputTokens = calculateTokens(inputContent);
                  const outputTokens = calculateTokens(responseContent);
                  const totalTokens = inputTokens + outputTokens;
                  const estimatedCost = calculateCost(inputTokens, outputTokens, currentResult.endpoint?.defaultModel);

                  return (
                    <div className="grid grid-cols-2 gap-4">
                      <div className="metric-card primary">
                        <div className="metric-label">Tokens Used</div>
                        <div className="metric-value primary">{totalTokens.toLocaleString()}</div>
                        <div className="text-xs mt-1" style={{ color: 'var(--text-dim)' }}>
                          {inputTokens} in, {outputTokens} out
                        </div>
                      </div>
                      <div className="metric-card success">
                        <div className="metric-label">Estimated Cost</div>
                        <div className="metric-value success">{estimatedCost}</div>
                        <div className="text-xs mt-1" style={{ color: 'var(--text-dim)' }}>
                          {currentResult.endpoint?.defaultModel || 'Unknown model'}
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* Input Variables (if any) */}
                {currentResult.inputData && Object.keys(currentResult.inputData).length > 0 && (
                  <div className="card">
                    <h3 className="text-sm font-medium mb-3" style={{ color: 'var(--text-primary)' }}>
                      Input Variables
                    </h3>
                    <div className="space-y-2">
                      {Object.entries(currentResult.inputData).map(([key, value]) => (
                        <div key={key} className="flex gap-3">
                          <span className="variable-badge">{`{{${key}}}`}</span>
                          <span className="text-sm flex-1" style={{ color: 'var(--text-secondary)' }}>
                            {value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3">
                  <button 
                    onClick={handleRunPrompt}
                    disabled={isLoading}
                    className="btn btn-secondary flex-1"
                  >
                    🔄 Regenerate
                  </button>
                  <button className="btn btn-success flex-1">
                    ✓ Save
                  </button>
                </div>
              </>
            )}

            {/* No Result State */}
            {!currentResult && !isLoading && !error && (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">🚀</div>
                <h3 className="text-lg font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                  Ready to test your prompt
                </h3>
                <p style={{ color: 'var(--text-muted)' }}>
                  Click "Run Prompt" to see the AI response
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div className="space-y-3">
            {versionResults.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">📚</div>
                <p style={{ color: 'var(--text-muted)' }}>No execution history</p>
              </div>
            ) : (
              versionResults.map((result, index) => (
                <div key={index} className="card cursor-pointer hover:bg-opacity-80 transition-all"
                     onClick={() => setCurrentResult(result)}>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs"
                         style={{ background: 'var(--bg-tertiary)' }}>
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                          Run #{versionResults.length - index}
                        </div>
                        <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          {new Date(result.timestamp).toLocaleString()}
                        </div>
                      </div>
                      
                      {/* Preview of response */}
                      <div className="text-sm line-clamp-2 mb-2" style={{ color: 'var(--text-secondary)' }}>
                        {result.output?.choices?.[0]?.message?.content?.substring(0, 120) || 
                         result.output?.content?.substring(0, 120) || 
                         'No response content'}...
                      </div>
                      
                      {/* Metrics preview */}
                      <div className="flex gap-4 text-xs" style={{ color: 'var(--text-dim)' }}>
                        <span>
                          {calculateTokens(JSON.stringify(result.inputData) + 
                                         (result.output?.choices?.[0]?.message?.content || result.output?.content || ''))} tokens
                        </span>
                        {result.endpoint?.defaultModel && (
                          <span>{result.endpoint.defaultModel}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'comparison' && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">⚖️</div>
            <p style={{ color: 'var(--text-muted)' }}>
              {versionResults.length < 2 ? 'Need at least 2 results to compare' : 'Comparison feature coming soon'}
            </p>
          </div>
        )}

        {activeTab === 'metrics' && (
          <div className="space-y-4">
            {versionResults.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">📊</div>
                <p style={{ color: 'var(--text-muted)' }}>No metrics available</p>
              </div>
            ) : (
              <>
                {(() => {
                  const totalTokens = versionResults.reduce((sum, result) => {
                    const content = result.output?.choices?.[0]?.message?.content || result.output?.content || '';
                    const inputContent = JSON.stringify(result.inputData);
                    return sum + calculateTokens(inputContent) + calculateTokens(content);
                  }, 0);
                  
                  const totalCost = versionResults.reduce((sum, result) => {
                    const content = result.output?.choices?.[0]?.message?.content || result.output?.content || '';
                    const inputContent = JSON.stringify(result.inputData);
                    const inputTokens = calculateTokens(inputContent);
                    const outputTokens = calculateTokens(content);
                    const costStr = calculateCost(inputTokens, outputTokens, result.endpoint?.defaultModel);
                    return sum + parseFloat(costStr.replace('$', ''));
                  }, 0);

                  const avgResponseTime = '1.8s'; // TODO: Track actual response times

                  return (
                    <div className="grid grid-cols-1 gap-4">
                      <div className="metric-card primary">
                        <div className="metric-label">Total Tokens Used</div>
                        <div className="metric-value primary">{totalTokens.toLocaleString()}</div>
                        <div className="text-xs mt-1" style={{ color: 'var(--text-dim)' }}>
                          {versionResults.length} executions
                        </div>
                      </div>
                      <div className="metric-card success">
                        <div className="metric-label">Total Cost</div>
                        <div className="metric-value success">${totalCost.toFixed(4)}</div>
                        <div className="text-xs mt-1" style={{ color: 'var(--text-dim)' }}>
                          Estimated
                        </div>
                      </div>
                      <div className="metric-card">
                        <div className="metric-label">Average Response Time</div>
                        <div className="metric-value" style={{ color: 'var(--text-primary)' }}>
                          {avgResponseTime}
                        </div>
                        <div className="text-xs mt-1" style={{ color: 'var(--text-dim)' }}>
                          Approximate
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </>
            )}
          </div>
        )}
      </div>
    </>
  );
};

export default ResultViewer;