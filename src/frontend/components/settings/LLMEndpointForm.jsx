import React, { useState, useEffect } from 'react';

function LLMEndpointForm({ endpoint, isEditing, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    name: '',
    baseUrl: '',
    apiKey: '',
    defaultModel: '',
    description: '',
    contextSize: '',
  });
  
  const [errors, setErrors] = useState({});
  const [showApiKey, setShowApiKey] = useState(false);
  
  // 컴포넌트 마운트 시 또는 endpoint가 변경될 때 폼 데이터 초기화
  useEffect(() => {
    if (endpoint && isEditing) {
      setFormData({
        name: endpoint.name || '',
        baseUrl: endpoint.baseUrl || '',
        apiKey: endpoint.apiKey || '',
        defaultModel: endpoint.defaultModel || '',
        description: endpoint.description || '',
        contextSize: endpoint.contextSize || '',
      });
    } else {
      // 새로 생성하는 경우 기본값
      setFormData({
        name: '',
        baseUrl: '',
        apiKey: '',
        defaultModel: '',
        description: '',
        contextSize: '',
      });
    }
    setErrors({});
  }, [endpoint, isEditing]);
  
  // 입력 필드 변경 처리
  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // 에러 제거
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };
  
  // 폼 유효성 검사
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = '이름은 필수입니다.';
    }
    
    if (!formData.baseUrl.trim()) {
      newErrors.baseUrl = 'Base URL은 필수입니다.';
    } else {
      // URL 형식 검사
      try {
        new URL(formData.baseUrl);
      } catch {
        newErrors.baseUrl = '올바른 URL 형식이 아닙니다.';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // 저장 처리
  const handleSave = () => {
    if (validateForm()) {
      onSave(formData);
    }
  };
  
  // 프리셋 URL 선택
  const handlePresetUrl = (preset) => {
    const presets = {
      openai: 'https://api.openai.com/v1',
      anthropic: 'https://api.anthropic.com',
      localVllm: 'http://localhost:8000/v1',
      localOllama: 'http://localhost:11434/v1'
    };
    
    if (presets[preset]) {
      handleInputChange('baseUrl', presets[preset]);
    }
  };
  
  // 프리셋 모델 선택
  const handlePresetModel = (preset) => {
    const presets = {
      'gpt-4o': 'gpt-4o',
      'gpt-4-turbo': 'gpt-4-turbo',
      'gpt-3.5-turbo': 'gpt-3.5-turbo',
      'claude-3-opus': 'claude-3-opus-20240229',
      'claude-3-sonnet': 'claude-3-sonnet-20240229',
      'mistral-7b': 'mistralai/Mistral-7B-Instruct-v0.2',
      'llama2-7b': 'meta-llama/Llama-2-7b-chat-hf'
    };
    
    if (presets[preset]) {
      handleInputChange('defaultModel', presets[preset]);
    }
  };
  
  const FormLabel = ({ children, required = false }) => (
    <label className="block text-xs font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
      {children} {required && <span style={{ color: 'var(--accent-danger)' }}>*</span>}
    </label>
  );

  const PresetButton = ({ children, ...props }) => (
    <button
      type="button"
      className="px-2 py-1 text-xs rounded"
      style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)'}}
      {...props}
    >
      {children}
    </button>
  );

  return (
    <div className="p-6">
      <div className="card">
        <div className="mb-6">
          <h2 className="text-lg font-medium" style={{ color: 'var(--text-primary)' }}>
            {isEditing ? 'Edit Endpoint' : 'Add New Endpoint'}
          </h2>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Provide the details for the LLM API endpoint.
          </p>
        </div>
        
        <div className="space-y-5">
          {/* Name */}
          <div>
            <FormLabel required>Name</FormLabel>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className={`input w-full ${errors.name ? 'border-red-500' : ''}`}
              placeholder="e.g., OpenAI GPT-4, Local vLLM Server"
            />
            {errors.name && (
              <p className="mt-1 text-xs text-red-500">{errors.name}</p>
            )}
          </div>
          
          {/* Base URL */}
          <div>
            <FormLabel required>Base URL</FormLabel>
            <div className="space-y-2">
              <input
                type="url"
                value={formData.baseUrl}
                onChange={(e) => handleInputChange('baseUrl', e.target.value)}
                className={`input w-full ${errors.baseUrl ? 'border-red-500' : ''}`}
                placeholder="https://api.openai.com/v1"
              />
              <div className="flex flex-wrap gap-2">
                <PresetButton onClick={() => handlePresetUrl('openai')}>OpenAI</PresetButton>
                <PresetButton onClick={() => handlePresetUrl('anthropic')}>Anthropic</PresetButton>
                <PresetButton onClick={() => handlePresetUrl('localVllm')}>Local vLLM</PresetButton>
                <PresetButton onClick={() => handlePresetUrl('localOllama')}>Local Ollama</PresetButton>
              </div>
            </div>
            {errors.baseUrl && (
              <p className="mt-1 text-sm text-red-500">{errors.baseUrl}</p>
            )}
          </div>
          
          {/* API Key */}
          <div>
            <FormLabel>API Key (Optional)</FormLabel>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={formData.apiKey}
                onChange={(e) => handleInputChange('apiKey', e.target.value)}
                className="input w-full pr-10"
                placeholder="sk-..."
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2"
                style={{ color: 'var(--text-muted)'}}
              >
                {showApiKey ? '👁️' : '🔒'}
              </button>
            </div>
            <p className="mt-1 text-xs" style={{ color: 'var(--text-dim)' }}>
              Leave blank for local servers that do not require an API key.
            </p>
          </div>
          
          {/* Default Model */}
          <div>
            <FormLabel>Default Model (Optional)</FormLabel>
            <div className="space-y-2">
              <input
                type="text"
                value={formData.defaultModel}
                onChange={(e) => handleInputChange('defaultModel', e.target.value)}
                className="input w-full"
                placeholder="gpt-4o, claude-3-opus-20240229, etc."
              />
              <div className="flex flex-wrap gap-2">
                <PresetButton onClick={() => handlePresetModel('gpt-4o')}>GPT-4o</PresetButton>
                <PresetButton onClick={() => handlePresetModel('gpt-4-turbo')}>GPT-4 Turbo</PresetButton>
                <PresetButton onClick={() => handlePresetModel('claude-3-opus')}>Claude 3 Opus</PresetButton>
                <PresetButton onClick={() => handlePresetModel('mistral-7b')}>Mistral 7B</PresetButton>
              </div>
            </div>
          </div>
          
          {/* Context Size */}
          <div>
            <FormLabel>Context Size (Optional)</FormLabel>
            <input
              type="number"
              value={formData.contextSize}
              onChange={(e) => handleInputChange('contextSize', e.target.value)}
              className="input w-full"
              placeholder="e.g., 4096, 8192"
            />
            <p className="mt-1 text-xs" style={{ color: 'var(--text-dim)' }}>
              Specify the context window size of the model.
            </p>
          </div>

          {/* Description */}
          <div>
            <FormLabel>Description (Optional)</FormLabel>
            <textarea
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              rows={3}
              className="input w-full"
              placeholder="A brief description of this endpoint..."
            />
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex justify-end gap-3 mt-8 pt-5 border-t" style={{ borderColor: 'var(--border-primary)' }}>
          <button
            onClick={onCancel}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="btn btn-primary"
          >
            {isEditing ? 'Update Endpoint' : 'Create Endpoint'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default LLMEndpointForm;