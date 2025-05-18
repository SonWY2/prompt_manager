import React, { useState } from 'react';

function PromptEditor({ versions, currentVersion, onAddVersion, onCallLLM, templateVariables }) {
  const [promptContent, setPromptContent] = useState(currentVersion?.content || '');
  
  return (
    <div className="prompt-editor card">
      <h2 className="text-xl font-semibold mb-4">Prompt Editor</h2>
      
      <div className="version-controls mb-4">
        <button 
          onClick={() => onAddVersion(currentVersion.id, promptContent)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Save as New Version
        </button>
      </div>
      
      <div className="input-group mb-6">
        <label className="block mb-2 font-medium">Prompt Content</label>
        <textarea
          value={promptContent}
          onChange={(e) => setPromptContent(e.target.value)}
          className="w-full h-64 p-3 border rounded focus:ring-2 focus:ring-blue-500"
          placeholder="Edit your prompt here..."
        />
      </div>
      
      <div className="template-variables">
        <h3 className="font-medium mb-3">Available Template Variables</h3>
        <div className="list-group">
          {templateVariables.map((variable, index) => (
            <div key={index} className="list-group-item">
              <span className="bg-blue-100 dark:bg-blue-900 px-2 py-1 rounded">
                {variable}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default PromptEditor;
