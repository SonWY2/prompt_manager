import React from 'react';

function LLMEndpointList({
  endpoints,
  selectedEndpointId,
  activeEndpointId,
  defaultEndpointId,
  onSelect,
  onEdit,
  onDelete,
  onCreateNew,
  activeEndpoint
}) {
  
  return (
    <div className="h-full flex flex-col">
      {/* Active Endpoint Summary */}
      {activeEndpoint && (
        <div className="p-3 border-b" style={{ borderColor: 'var(--border-primary)' }}>
          <div className="text-xs mb-2 uppercase tracking-wide font-medium" style={{ color: 'var(--text-muted)' }}>
            Active Provider
          </div>
          <div className="flex items-center gap-2 p-2 rounded text-sm" style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--accent-success)'}}>
            <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0"></div>
            <div className="font-medium truncate" style={{ color: 'var(--accent-success)' }}>
              {activeEndpoint.name}
            </div>
          </div>
        </div>
      )}
      
      {/* Endpoint List */}
      <div className="flex-1 overflow-y-auto">
        {endpoints.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-center px-4">
            <div className="text-2xl mb-2 opacity-30">⚙️</div>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              No providers configured
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-dim)' }}>
              Add your first LLM endpoint below
            </p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {endpoints.map(endpoint => {
              const isSelected = selectedEndpointId === endpoint.id;
              const isActive = activeEndpointId === endpoint.id;
              const isDefault = defaultEndpointId === endpoint.id;
              
              return (
                <div
                  key={endpoint.id}
                  className={`group relative p-3 rounded cursor-pointer transition-all duration-200 border ${
                    isSelected 
                      ? 'border-purple-500 bg-purple-500/10' 
                      : 'border-transparent hover:border-gray-600 hover:bg-gray-800/50'
                  }`}
                  onClick={() => onSelect(endpoint.id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                        isActive ? 'bg-green-500' : 'bg-gray-500'
                      }`} />
                      <span className={`font-medium text-sm truncate ${
                        isSelected ? 'text-white' : 'text-gray-200'
                      }`}>
                        {endpoint.name}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {isDefault && (
                        <div className={`w-1.5 h-1.5 rounded-full ${
                          isSelected ? 'bg-white' : 'bg-purple-400'
                        }`} title="Default Provider" />
                      )}
                      
                      <button
                        onClick={(e) => { 
                          e.stopPropagation(); 
                          onEdit(endpoint.id); 
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-600 transition-all"
                        title="Edit endpoint"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  
                  <div className={`text-xs font-mono truncate ${
                    isSelected ? 'text-gray-300' : 'text-gray-400'
                  }`}>
                    {endpoint.baseUrl}
                  </div>
                  
                  {endpoint.defaultModel && (
                    <div className={`text-xs mt-1 truncate ${
                      isSelected ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      Model: {endpoint.defaultModel}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
      
      {/* Footer Actions - Julius Style */}
      <div className="border-t p-3" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-primary)' }}>
        <div className="space-y-2">
          <button
            onClick={onCreateNew}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded transition-all duration-200"
            style={{ 
              background: 'var(--accent-primary)', 
              color: 'white',
              border: 'none'
            }}
            onMouseEnter={(e) => e.target.style.background = 'var(--accent-secondary)'}
            onMouseLeave={(e) => e.target.style.background = 'var(--accent-primary)'}
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add Provider
          </button>
          
          <button
            onClick={() => selectedEndpointId && onDelete(selectedEndpointId)}
            disabled={!selectedEndpointId}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ 
              background: selectedEndpointId ? 'var(--accent-danger)' : 'var(--bg-tertiary)', 
              color: selectedEndpointId ? 'white' : 'var(--text-muted)',
              border: 'none'
            }}
            onMouseEnter={(e) => {
              if (!e.target.disabled) {
                e.target.style.background = '#dc2626';
              }
            }}
            onMouseLeave={(e) => {
              if (!e.target.disabled) {
                e.target.style.background = 'var(--accent-danger)';
              }
            }}
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Remove Provider
          </button>
        </div>
        
        {/* Status indicators */}
        <div className="mt-3 pt-3 border-t flex items-center justify-between text-xs" style={{ borderColor: 'var(--border-secondary)' }}>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
            <span style={{ color: 'var(--text-dim)' }}>{endpoints.length} provider{endpoints.length !== 1 ? 's' : ''}</span>
          </div>
          {selectedEndpointId && (
            <span style={{ color: 'var(--text-dim)' }}>Selected</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default LLMEndpointList;