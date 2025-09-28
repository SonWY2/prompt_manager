// src/frontend/components/result/ResultViewer.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useStore } from '../../store.jsx';

// Helper component for collapsible content
const CollapsibleContent = ({ title, content }) => {
  const [isCollapsed, setIsCollapsed] = useState(true);
  
  if (!content) {
    return null;
  }

  const lines = content.split('\n');
  const canCollapse = lines.length > 3;
  const previewContent = canCollapse ? lines.slice(0, 3).join('\n') : content;

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</h3>
        {canCollapse && (
          <button 
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors hover:bg-purple-100 dark:hover:bg-purple-900"
            style={{ color: 'var(--accent-primary)'}}
          >
            <span>{isCollapsed ? 'Show More' : 'Show Less'}</span>
            <svg xmlns="http://www.w3.org/2000/svg" className={`h-3 w-3 transition-transform ${isCollapsed ? '' : 'rotate-180'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        )}
      </div>
      <div 
        className="max-w-none p-3 rounded-md bg-gray-50 dark:bg-gray-900 text-sm" 
        style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}
      >
        {isCollapsed ? previewContent + (canCollapse ? '\n...' : '') : content}
      </div>
    </div>
  );
};


const ResultViewer = ({ taskId, versionId }) => {
  const { 
    tasks, 
    llmEndpoints, 
    activeLlmEndpointId,
    callLLM,
    getVersionResults,
    deleteHistoryItem,
    renderPrompt
  } = useStore();
  
  const [activeTab, setActiveTab] = useState('response');
  const [currentResult, setCurrentResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

  const currentTask = taskId ? tasks[taskId] : null;
  const currentVersion = currentTask?.versions?.find(v => v.id === versionId);
  const activeEndpoint = llmEndpoints.find(ep => ep.id === activeLlmEndpointId);
  
  const versionResults = getVersionResults(taskId, versionId);
  const latestResult = versionResults?.[0];

  useEffect(() => {
    if (latestResult) {
      setCurrentResult(latestResult);
      setError(null);
    } else {
      setCurrentResult(null);
    }
    setSelectedHistoryItem(null);
  }, [latestResult, versionId]);

  const handleRunPrompt = useCallback(async () => {
    console.log('🔧 [DEBUG] handleRunPrompt 시작 검증:');
    console.log('  - currentTask:', !!currentTask, currentTask?.id);
    console.log('  - currentVersion:', !!currentVersion, currentVersion?.id);
    console.log('  - activeEndpoint:', !!activeEndpoint, activeEndpoint?.id, activeEndpoint?.name);
    console.log('  - activeLlmEndpointId:', activeLlmEndpointId);
    
    if (!currentTask || !currentVersion || !activeEndpoint) {
      console.log('❌ [ERROR] 필수 요소 누락:', {
        hasTask: !!currentTask,
        hasVersion: !!currentVersion, 
        hasActiveEndpoint: !!activeEndpoint
      });
      setError('Task, version, or LLM endpoint not available');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      console.log('🔧 [DEBUG] Run Prompt 시작 - Current Version:', {
        id: currentVersion.id,
        name: currentVersion.name,
        content: currentVersion.content,
        system_prompt: currentVersion.system_prompt,
        variables: currentVersion.variables
      });
      
      // Task 레벨과 Version 레벨 변수를 모두 고려
      const taskVariables = currentTask.variables || {};
      const versionVariables = currentVersion.variables || {};
      const variables = { ...taskVariables, ...versionVariables }; // Version 변수가 Task 변수를 오버라이드
      
      console.log('🔧 [DEBUG] Task 레벨 변수들:', taskVariables);
      console.log('🔧 [DEBUG] Version 레벨 변수들:', versionVariables);
      console.log('🔧 [DEBUG] 최종 병합된 변수들:', variables);
      console.log('🔧 [DEBUG] variables 객체의 키들:', Object.keys(variables));
      console.log('🔧 [DEBUG] variables 객체의 값들:', Object.values(variables));
      
      const inputData = {};
      const matches = currentVersion.content?.match(/\{\{(\w+)\}\}/g) || [];
      console.log('🔧 [DEBUG] 프롬프트에서 추출된 매치:', matches);
      
      const extractedVars = [...new Set(matches.map(match => match.slice(2, -2)))];
      console.log('🔧 [DEBUG] 추출된 변수 이름들:', extractedVars);
      
      extractedVars.forEach(variable => {
        console.log(`🔧 [DEBUG] 변수 '${variable}' 처리:`);
        console.log(`  - variables에 '${variable}' 키 존재 여부:`, variable in variables);
        console.log(`  - variables['${variable}'] 값:`, variables[variable]);
        console.log(`  - typeof variables['${variable}']:`, typeof variables[variable]);
        
        const value = variables[variable] || `[${variable}]`;
        inputData[variable] = value;
        console.log(`  - 최종 치환 결과: {{${variable}}} -> "${value}"`);
      });
      
      console.log('🔧 [DEBUG] 최종 inputData:', inputData);
      console.log('🔧 [DEBUG] LLM 호출 시작 - Endpoint:', activeEndpoint);
      
      const result = await callLLM(taskId, versionId, inputData, currentVersion.system_prompt);
      const formattedResult = {
        inputData,
        output: result,
        timestamp: new Date().toISOString(),
        endpoint: activeEndpoint
      };
      
      console.log('🔧 [DEBUG] LLM 호출 완료 - 결과:', result);
      setCurrentResult(formattedResult);
    } catch (err) {
      console.error('❌ [ERROR] Run Prompt 실패:', err);
      setError(err.message || 'Failed to call LLM API');
    } finally {
      setIsLoading(false);
    }
  }, [currentTask, currentVersion, activeEndpoint, callLLM, taskId, versionId]);

  const calculateTokens = useCallback((text) => {
    if (!text) return 0;
    return Math.ceil(text.length / 4);
  }, []);

  const calculateCost = useCallback((inputTokens, outputTokens, model) => {
    const costs = {
      'gpt-4o': { input: 0.0025, output: 0.01 },
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

  const handleDeleteHistory = async (e, timestamp) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this history item?')) {
      try {
        if (selectedHistoryItem?.timestamp === timestamp) {
          setSelectedHistoryItem(null);
        }
        await deleteHistoryItem(taskId, versionId, timestamp);
      } catch (error) {
        console.error("Failed to delete history item:", error);
        alert("Error: Could not delete the item.");
      }
    }
  };

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

  const HistoryDetailView = ({ result, version }) => {
    if (!result) {
      return (
        <div className="flex items-center justify-center h-full text-center">
          <div>
            <div className="text-2xl mb-2">🔍</div>
            <p style={{ color: 'var(--text-muted)' }}>Select a history item to see details</p>
          </div>
        </div>
      );
    }

    const responseContent = result.output?.choices?.[0]?.message?.content || result.output?.content || 'No content';
    const renderedUserPrompt = renderPrompt(version.content, result.inputData);
    const requestMessage = `---------- System Prompt ----------\n${version.system_prompt}\n\n---------- User Prompt ----------\n${renderedUserPrompt}`;

    return (
      <div className="p-4 space-y-4">
        <CollapsibleContent title="Request Message" content={requestMessage} />
        <CollapsibleContent title="Response" content={responseContent} />
        
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Metrics</h3>
          <div className="grid grid-cols-2 gap-3">
            {(() => {
              const inputContent = JSON.stringify(result.inputData);
              const inputTokens = calculateTokens(requestMessage);
              const outputTokens = calculateTokens(responseContent);
              const totalTokens = inputTokens + outputTokens;
              const estimatedCost = calculateCost(inputTokens, outputTokens, result.endpoint?.defaultModel);
              return (
                <>
                  <div className="p-3 rounded-md bg-gray-50 dark:bg-gray-900">
                    <div className="text-xs text-gray-500 dark:text-gray-400">Model</div>
                    <div className="text-md font-semibold truncate">{result.endpoint?.defaultModel || result.endpoint?.name || 'Unknown'}</div>
                  </div>
                  <div className="p-3 rounded-md bg-gray-50 dark:bg-gray-900">
                    <div className="text-xs text-gray-500 dark:text-gray-400">Tokens Used</div>
                    <div className="text-md font-semibold">{totalTokens.toLocaleString()}</div>
                    <div className="text-xs text-gray-400 dark:text-gray-500">{inputTokens} in, {outputTokens} out</div>
                  </div>
                  <div className="p-3 rounded-md bg-gray-50 dark:bg-gray-900 col-span-2">
                    <div className="text-xs text-gray-500 dark:text-gray-400">Estimated Cost</div>
                    <div className="text-md font-semibold">{estimatedCost}</div>
                  </div>
                </>
              );
            })()}
          </div>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Input Variables</h3>
          <div className="p-3 rounded-md bg-gray-50 dark:bg-gray-900">
            <pre className="text-xs whitespace-pre-wrap">
              {JSON.stringify(result.inputData, null, 2)}
            </pre>
          </div>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Raw Output</h3>
          <div className="p-3 rounded-md bg-gray-50 dark:bg-gray-900">
            <pre className="text-xs whitespace-pre-wrap">
              {JSON.stringify(result.output, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
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

        <div className="tab-container">
          <button className={`tab ${activeTab === 'response' ? 'active' : ''}`} onClick={() => setActiveTab('response')}>Response</button>
          <button className={`tab ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>History ({versionResults?.length || 0})</button>
          <button className={`tab ${activeTab === 'comparison' ? 'active' : ''}`} onClick={() => setActiveTab('comparison')}>Comparison</button>
          <button className={`tab ${activeTab === 'metrics' ? 'active' : ''}`} onClick={() => setActiveTab('metrics')}>Metrics</button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'response' && (
          <div className="overflow-y-auto p-5 h-full space-y-4">
            <button onClick={handleRunPrompt} disabled={isLoading || !currentVersion} className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-lg'}`} style={{ background: 'var(--accent-primary)', color: 'white', border: 'none' }}>
              {isLoading ? (<> <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"> <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle> <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path> </svg> Running Prompt... </>) : (<> <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"> <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /> </svg> Run Prompt </>)}
            </button>
            {error && (<div className="p-4 rounded-lg border" style={{ background: 'rgba(239, 68, 68, 0.1)', borderColor: 'var(--accent-danger)', color: 'var(--accent-danger)' }}> <div className="flex items-center gap-2 mb-2"> <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"> <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" /> </svg> <span className="font-medium text-sm">Error</span> </div> <p className="text-sm">{error}</p> </div>)}
            {currentResult && (<> <div className="card"> <div className="flex items-start gap-3 mb-4"> <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs" style={{ background: 'var(--accent-primary)', color: 'white' }}> 🤖 </div> <div className="flex-1 min-w-0"> <div className="flex items-center justify-between mb-1"> <div className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}> {currentResult.endpoint?.name || 'AI'} Response </div> <div className="text-xs" style={{ color: 'var(--text-muted)' }}> {new Date(currentResult.timestamp).toLocaleString()} </div> </div> {currentResult.endpoint?.defaultModel && (<div className="text-xs" style={{ color: 'var(--text-muted)' }}> {currentResult.endpoint.defaultModel} </div>)} </div> </div> <div className="prose prose-sm max-w-none"> <div style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}> {currentResult.output?.choices?.[0]?.message?.content ? (<div className="whitespace-pre-wrap"> {currentResult.output.choices[0].message.content} </div>) : currentResult.output?.content ? (<div className="whitespace-pre-wrap"> {currentResult.output.content} </div>) : (<div style={{ color: 'var(--text-muted)' }}> No response content available </div>)} </div> </div> </div> {(() => { const responseContent = currentResult.output?.choices?.[0]?.message?.content || currentResult.output?.content || ''; const inputContent = JSON.stringify(currentResult.inputData); const inputTokens = calculateTokens(inputContent); const outputTokens = calculateTokens(responseContent); const totalTokens = inputTokens + outputTokens; const estimatedCost = calculateCost(inputTokens, outputTokens, currentResult.endpoint?.defaultModel); return (<div className="grid grid-cols-2 gap-4"> <div className="metric-card primary"> <div className="metric-label">Tokens Used</div> <div className="metric-value primary">{totalTokens.toLocaleString()}</div> <div className="text-xs mt-1" style={{ color: 'var(--text-dim)' }}> {inputTokens} in, {outputTokens} out </div> </div> <div className="metric-card success"> <div className="metric-label">Estimated Cost</div> <div className="metric-value success">{estimatedCost}</div> <div className="text-xs mt-1" style={{ color: 'var(--text-dim)' }}> {currentResult.endpoint?.defaultModel || 'Unknown model'} </div> </div> </div>); })()} {currentResult.inputData && Object.keys(currentResult.inputData).length > 0 && (<div className="card"> <h3 className="text-sm font-medium mb-3" style={{ color: 'var(--text-primary)' }}> Input Variables </h3> <div className="space-y-2"> {Object.entries(currentResult.inputData).map(([key, value]) => (<div key={key} className="flex gap-3"> <span className="variable-badge">{`{{${key}}}`}</span> <span className="text-sm flex-1" style={{ color: 'var(--text-secondary)' }}> {value} </span> </div>))} </div> </div>)} <div className="flex gap-3"> <button onClick={handleRunPrompt} disabled={isLoading} className="btn btn-secondary flex-1"> 🔄 Regenerate </button> <button className="btn btn-success flex-1"> ✓ Save </button> </div> </>)}
            {!currentResult && !isLoading && !error && (<div className="text-center py-12"> <div className="text-4xl mb-4">🚀</div> <h3 className="text-lg font-medium mb-2" style={{ color: 'var(--text-primary)' }}> Ready to test your prompt </h3> <p style={{ color: 'var(--text-muted)' }}> Click "Run Prompt" to see the AI response </p> </div>)}
          </div>
        )}

        {activeTab === 'history' && (
          <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-5 space-y-3 border-b dark:border-gray-700">
              {versionResults.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">📚</div>
                  <p style={{ color: 'var(--text-muted)' }}>No execution history</p>
                </div>
              ) : (
                versionResults.map((result, index) => (
                  <div key={result.timestamp} 
                       className={`card cursor-pointer hover:bg-opacity-80 transition-all relative group ${selectedHistoryItem?.timestamp === result.timestamp ? 'ring-2 ring-purple-500' : ''}`}
                       onClick={() => setSelectedHistoryItem(result)}>
                    <button 
                      onClick={(e) => handleDeleteHistory(e, result.timestamp)}
                      className="absolute top-2 right-2 p-1 rounded-full hover:bg-red-500 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Delete history item"
                      style={{ background: 'var(--bg-tertiary)'}}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs"
                           style={{ background: 'var(--bg-tertiary)' }}>
                        {versionResults.length - index}
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
                        <div className="text-sm line-clamp-2 mb-2" style={{ color: 'var(--text-secondary)' }}>
                          {result.output?.choices?.[0]?.message?.content?.substring(0, 120) || 
                           result.output?.content?.substring(0, 120) || 
                           'No response content'}...
                        </div>
                        <div className="flex gap-4 text-xs items-center" style={{ color: 'var(--text-dim)' }}>
                          <span>
                            {calculateTokens(JSON.stringify(result.inputData) + 
                                           (result.output?.choices?.[0]?.message?.content || result.output?.content || ''))} tokens
                          </span>
                          {(result.endpoint?.defaultModel || result.endpoint?.name) && (
                            <span className="font-mono p-1 rounded text-xs" style={{background: 'var(--bg-tertiary)'}}>
                              {result.endpoint?.defaultModel || result.endpoint?.name}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="flex-1 overflow-y-auto">
              <HistoryDetailView result={selectedHistoryItem} version={currentVersion} />
            </div>
          </div>
        )}
        {/* Other tabs */}
      </div>
    </div>
  );
};

export default ResultViewer;
