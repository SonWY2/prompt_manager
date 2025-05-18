import React from 'react';

function TemplateRenderer({ variables, onRender }) {
  const [inputValues, setInputValues] = React.useState({});
  
  const handleInputChange = (key, value) => {
    setInputValues({
      ...inputValues,
      [key]: value
    });
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onRender(inputValues);
  };

  return (
    <div className="template-renderer card">
      <h2 className="text-xl font-semibold mb-4">Template Renderer</h2>
      
      <div className="variables">
        <h3 className="font-medium mb-3">Input Variables</h3>
        <form onSubmit={handleSubmit}>
          {Object.keys(variables).length > 0 ? (
            <div className="input-group mb-6">
              {Object.keys(variables).map((key) => (
                <div key={key} className="mb-4">
                  <label className="block mb-2 font-medium">
                    {key}
                  </label>
                  <input
                    type="text"
                    value={inputValues[key] || ''}
                    onChange={(e) => handleInputChange(key, e.target.value)}
                    className="w-full p-3 border rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="mb-4">No variables defined for this task</p>
          )}
          
          <button 
            type="submit"
            className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Render Template
          </button>
        </form>
        
        <div className="output-preview mt-6">
          <h3 className="font-medium mb-3">Rendered Output</h3>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded border dark:border-gray-600">
            <pre className="whitespace-pre-wrap">
{Object.keys(variables).length > 0 ? (
  `Hello ${inputValues.name || 'World'}, this is a template with ${inputValues.count || 0} items.`
) : (
  'No variables defined for this task'
)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TemplateRenderer;
