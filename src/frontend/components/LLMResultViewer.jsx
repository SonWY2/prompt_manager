import React from 'react';

function LLMResultViewer({ results }) {
  return (
    <div className="llm-result-viewer">
      <h2>LLM Results</h2>
      {results.length === 0 ? (
        <p>No results yet. Run a prompt to see output.</p>
      ) : (
        <div className="results-list">
          {results.map((result, index) => (
            <div key={index} className="result-item">
              <h3>Result {index + 1}</h3>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default LLMResultViewer;
