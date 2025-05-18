import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './src/frontend/App.jsx';
import { PromptProvider } from './src/frontend/store.jsx';
import './src/frontend/App.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <PromptProvider>
      <App />
    </PromptProvider>
  </React.StrictMode>
);