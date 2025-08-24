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
        <div className="p-4 border-b" style={{ borderColor: 'var(--border-primary)' }}>
          <div className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>Active Provider</div>
          <div className="p-2 rounded text-sm" style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--accent-success)'}}>
            <div className="font-medium truncate" style={{ color: 'var(--accent-success)' }}>{activeEndpoint.name}</div>
          </div>
        </div>
      )}
      
      {/* Endpoint List */}
      <div className="flex-1 overflow-y-auto p-2">
        {endpoints.length === 0 ? (
          <div className="text-center py-10" style={{ color: 'var(--text-muted)' }}>
            <p className="text-sm">No endpoints registered.</p>
          </div>
        ) : (
          <div className="space-y-1">
            {endpoints.map(endpoint => {
              const isSelected = selectedEndpointId === endpoint.id;
              return (
                <div
                  key={endpoint.id}
                  className="group task-item"
                  style={{
                    padding: '8px 10px',
                    background: isSelected ? 'var(--accent-primary)' : 'transparent',
                    color: isSelected ? 'white' : 'var(--text-primary)',
                  }}
                  onClick={() => onSelect(endpoint.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-sm truncate" style={{ color: isSelected ? 'white' : 'var(--text-primary)' }}>
                      {endpoint.name}
                    </div>
                    <div className="flex items-center gap-2">
                      {activeEndpointId === endpoint.id && (
                        <span className="inline-block w-2 h-2 rounded-full" style={{ background: 'var(--accent-success)' }} title="Active" />
                      )}
                      {defaultEndpointId === endpoint.id && (
                        <span className="inline-block w-2 h-2 rounded-full" style={{ background: 'var(--accent-secondary)' }} title="Default" />
                      )}
                    </div>
                  </div>
                  <div className="text-xs truncate" style={{ color: isSelected ? 'rgba(255,255,255,0.7)' : 'var(--text-muted)' }}>
                    {endpoint.baseUrl}
                  </div>
                  <div className="absolute right-2 bottom-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => { e.stopPropagation(); onEdit(endpoint.id); }}
                      className="p-1 rounded hover:bg-gray-600"
                      title="Edit"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); onDelete(endpoint.id); }}
                      className="p-1 rounded hover:bg-gray-600"
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
      
      {/* Add New Endpoint Button */}
      <div className="p-4 border-t" style={{ borderColor: 'var(--border-primary)' }}>
        <button
          onClick={onCreateNew}
          className="btn btn-primary w-full"
        >
          + Add New Endpoint
        </button>
      </div>
    </div>
  );
}

export default LLMEndpointList;