import React from 'react';

function TaskNavigator({ tasks, onCreateTask, onSelectTask, currentTask }) {
  const [newTaskName, setNewTaskName] = React.useState('');
  
  const handleCreate = () => {
    if (newTaskName.trim()) {
      onCreateTask(`task-${Date.now()}`, newTaskName);
      setNewTaskName('');
    }
  };

  return (
    <div className="task-navigator bg-white dark:bg-gray-800 p-4 shadow-md">
      <h2 className="text-xl font-bold mb-4">Tasks</h2>
      
      <div className="task-list mb-4">
        {Object.entries(tasks).map(([taskId, task]) => (
          <div 
            key={taskId}
            onClick={() => onSelectTask(taskId)}
            className={`p-2 cursor-pointer rounded ${
              taskId === currentTask 
                ? 'bg-blue-500 text-white' 
                : 'hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            {task.name}
          </div>
        ))}
      </div>
      
      <div className="create-task">
        <input
          type="text"
          value={newTaskName}
          onChange={(e) => setNewTaskName(e.target.value)}
          placeholder="New task name"
          className="w-full p-2 border dark:border-gray-600 rounded mb-2"
        />
        <button
          onClick={handleCreate}
          className="w-full p-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Create Task
        </button>
      </div>
    </div>
  );
}

export default TaskNavigator;
