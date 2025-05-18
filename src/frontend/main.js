import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { PromptProvider } from './store.jsx';
import './App.css';

const root = document.getElementById('root');
ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <PromptProvider>
      <App />
    </PromptProvider>
  </React.StrictMode>
);