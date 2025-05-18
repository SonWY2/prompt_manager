import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './frontend/App.jsx';
import { PromptProvider } from './frontend/store.jsx';
import './frontend/App.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <PromptProvider>
      <App />
    </PromptProvider>
  </React.StrictMode>
);