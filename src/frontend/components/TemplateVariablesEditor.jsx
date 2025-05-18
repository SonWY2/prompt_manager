import React, { useState } from 'react';

function TemplateVariablesEditor({ variables = [], onSaveVariables }) {
  const [editingVariables, setEditingVariables] = useState(
    Array.isArray(variables) ? [...variables] : []
  );
  const [newVariable, setNewVariable] = useState('');

  const handleAddVariable = () => {
    if (newVariable.trim() !== '') {
      setEditingVariables([...editingVariables, newVariable.trim()]);
      setNewVariable('');
    }
  };

  const handleRemoveVariable = (index) => {
    const updatedVariables = [...editingVariables];
    updatedVariables.splice(index, 1);
    setEditingVariables(updatedVariables);
  };

  const handleSave = () => {
    onSaveVariables(editingVariables);
  };

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded shadow">
      <h2 className="text-xl font-semibold mb-3">Template Variables</h2>
      
      <div className="mb-4">
          <div className="input-group mb-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={newVariable}
                onChange={(e) => setNewVariable(e.target.value)}
                placeholder="New variable name"
                className="flex-1 p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
              />
              <button
                onClick={handleAddVariable}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Add
              </button>
            </div>
          </div>
      </div>
      
          <ul className="list-group mb-4">
            {editingVariables.map((variable, index) => (
              <li key={index} className="list-group-item">
                <span className="bg-gray-100 dark:bg-gray-600 p-2 rounded">
                  {variable}
                </span>
                <button
                  onClick={() => handleRemoveVariable(index)}
                  className="px-2 py-1 text-red-500 hover:text-red-700"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
      
      <button
        onClick={handleSave}
        className="w-full p-2 bg-green-500 text-white rounded hover:bg-green-600"
      >
        Save Variables
      </button>
    </div>
  );
}

export default TemplateVariablesEditor;
