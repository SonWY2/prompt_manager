import React, { useState, useEffect, useCallback, useMemo } from 'react';

// 컴포넌트들을 함수 외부로 이동
const FormSection = ({ title, subtitle, children }) => (
  <div className="mb-8">
    <div className="mb-4">
      <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
        {title}
      </h3>
      {subtitle && (
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
          {subtitle}
        </p>
      )}
    </div>
    {children}
  </div>
);

const FormField = ({ label, required = false, error, children, description }) => (
  <div className="mb-6">
    <label className="block text-xs font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
      {label} 
      {required && <span style={{ color: 'var(--accent-danger)' }}> *</span>}
    </label>
    {children}
    {description && (
      <p className="mt-2 text-xs" style={{ color: 'var(--text-dim)' }}>
        {description}
      </p>
    )}
    {error && (
      <p className="mt-2 text-xs flex items-center gap-1" style={{ color: 'var(--accent-danger)' }}>
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
        {error}
      </p>
    )}
  </div>
);

const PresetButton = ({ children, onClick, icon }) => (
  <button
    type="button"
    onClick={onClick}
    className="flex items-center gap-2 px-3 py-2 text-xs rounded border transition-all duration-200 hover:border-purple-500 hover:bg-purple-500/10"
    style={{ 
      background: 'var(--bg-tertiary)', 
      color: 'var(--text-secondary)',
      border: '1px solid var(--border-primary)'
    }}
  >
    {icon && <span className="text-xs">{icon}</span>}
    {children}
  </button>
);

// 스타일 객체들을 상수로 분리
const styles = {
  container: { background: 'var(--bg-primary)' },
  header: { borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' },
  closeButton: { color: 'var(--text-muted)' },
  input: { 
    background: 'var(--bg-tertiary)', 
    border: '1px solid var(--border-primary)',
    color: 'var(--text-primary)'
  },
  inputError: {
    background: 'var(--bg-tertiary)', 
    border: '1px solid #ef4444',
    color: 'var(--text-primary)'
  },
  previewCard: { background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' },
  previewItem: { background: 'var(--bg-tertiary)' },
  primaryButton: { 
    background: 'var(--accent-primary)', 
    color: 'white',
    border: 'none'
  },
  secondaryButton: { 
    background: 'var(--bg-tertiary)', 
    color: 'var(--text-primary)',
    border: '1px solid var(--border-primary)'
  }
};

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
  const [isLoading, setIsLoading] = useState(false);
  
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
    setShowApiKey(false);
  }, [endpoint, isEditing]);
  
  // 입력 필드 변경 처리 - useCallback으로 메모이제이션
  const handleInputChange = useCallback((field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // 에러 제거
    setErrors(prev => {
      if (prev[field]) {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      }
      return prev;
    });
  }, []);
  
  // 폼 유효성 검사 - useCallback으로 메모이제이션
  const validateForm = useCallback(() => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    if (!formData.baseUrl.trim()) {
      newErrors.baseUrl = 'Base URL is required';
    } else {
      // URL 형식 검사
      try {
        new URL(formData.baseUrl);
      } catch {
        newErrors.baseUrl = 'Please enter a valid URL format';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData.name, formData.baseUrl]);
  
  // 저장 처리 - useCallback으로 메모이제이션
  const handleSave = useCallback(async () => {
    if (validateForm()) {
      setIsLoading(true);
      try {
        await onSave(formData);
      } finally {
        setIsLoading(false);
      }
    }
  }, [validateForm, onSave, formData]);
  
  // 프리셋 핸들러들 - useCallback으로 메모이제이션
  const handlePresetUrl = useCallback((preset) => {
    const presets = {
      openai: 'https://api.openai.com/v1',
      anthropic: 'https://api.anthropic.com',
      localVllm: 'http://localhost:8000/v1',
      localOllama: 'http://localhost:11434/v1',
      together: 'https://api.together.xyz/v1',
      huggingface: 'https://api-inference.huggingface.co/v1'
    };
    
    if (presets[preset]) {
      handleInputChange('baseUrl', presets[preset]);
    }
  }, [handleInputChange]);
  
  const handlePresetModel = useCallback((preset) => {
    const presets = {
      'gpt-4o': 'gpt-4o',
      'gpt-4o-mini': 'gpt-4o-mini',
      'gpt-4-turbo': 'gpt-4-turbo',
      'gpt-3.5-turbo': 'gpt-3.5-turbo',
      'claude-3-5-sonnet': 'claude-3-5-sonnet-20241022',
      'claude-3-opus': 'claude-3-opus-20240229',
      'claude-3-sonnet': 'claude-3-sonnet-20240229',
      'claude-3-haiku': 'claude-3-haiku-20240307',
      'llama-3-8b': 'meta-llama/Meta-Llama-3-8B-Instruct',
      'llama-3-70b': 'meta-llama/Meta-Llama-3-70B-Instruct',
      'mistral-7b': 'mistralai/Mistral-7B-Instruct-v0.2',
      'mixtral-8x7b': 'mistralai/Mixtral-8x7B-Instruct-v0.1'
    };
    
    if (presets[preset]) {
      handleInputChange('defaultModel', presets[preset]);
    }
  }, [handleInputChange]);

  // API Key 가시성 토글
  const toggleApiKeyVisibility = useCallback(() => {
    setShowApiKey(prev => !prev);
  }, []);

  // 개별 입력 핸들러들 - useMemo로 메모이제이션
  const inputHandlers = useMemo(() => ({
    name: (e) => handleInputChange('name', e.target.value),
    baseUrl: (e) => handleInputChange('baseUrl', e.target.value),
    apiKey: (e) => handleInputChange('apiKey', e.target.value),
    defaultModel: (e) => handleInputChange('defaultModel', e.target.value),
    description: (e) => handleInputChange('description', e.target.value),
    contextSize: (e) => handleInputChange('contextSize', e.target.value),
  }), [handleInputChange]);

  return (
    <div className="h-full flex flex-col" style={styles.container}>
      {/* Header */}
      <div className="flex-shrink-0 p-6 border-b" style={styles.header}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              {isEditing ? (
                <span className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Edit LLM Provider
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Add New LLM Provider
                </span>
              )}
            </h1>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Configure your LLM API endpoint settings and authentication details.
            </p>
          </div>
          
          <button
            onClick={onCancel}
            className="p-2 rounded transition-all duration-200 hover:bg-gray-700"
            style={styles.closeButton}
            title="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Basic Configuration */}
            <div className="lg:col-span-2 space-y-8">
              <FormSection 
                title="Basic Configuration" 
                subtitle="Essential information for your LLM provider"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <FormField 
                    label="Provider Name" 
                    required 
                    error={errors.name}
                    description="A friendly name to identify this provider"
                  >
                    <input
                      type="text"
                      value={formData.name}
                      onChange={inputHandlers.name}
                      className={`w-full px-4 py-3 rounded-lg text-sm transition-all duration-200 ${
                        errors.name ? 'border-red-500 focus:border-red-500' : 'focus:border-purple-500'
                      }`}
                      style={errors.name ? styles.inputError : styles.input}
                      placeholder="e.g., OpenAI GPT-4, Local Claude, Anthropic API"
                    />
                  </FormField>
                  
                  <FormField 
                    label="Context Window Size" 
                    description="Maximum tokens for input and output combined"
                  >
                    <input
                      type="number"
                      value={formData.contextSize}
                      onChange={inputHandlers.contextSize}
                      className="w-full px-4 py-3 rounded-lg text-sm transition-all duration-200 focus:border-purple-500"
                      style={styles.input}
                      placeholder="e.g., 4096, 8192, 32768, 200000"
                    />
                  </FormField>
                </div>
                
                <FormField 
                  label="Description" 
                  description="Optional description for this provider configuration"
                >
                  <textarea
                    value={formData.description}
                    onChange={inputHandlers.description}
                    rows={3}
                    className="w-full px-4 py-3 rounded-lg text-sm transition-all duration-200 focus:border-purple-500 resize-none"
                    style={styles.input}
                    placeholder="Describe the purpose or specific configuration of this endpoint..."
                  />
                </FormField>
              </FormSection>
              
              <FormSection 
                title="API Configuration" 
                subtitle="Connection and authentication settings"
              >
                <FormField 
                  label="Base URL" 
                  required 
                  error={errors.baseUrl}
                  description="The base URL for the API endpoint (including /v1 if applicable)"
                >
                  <div className="space-y-3">
                    <input
                      type="url"
                      value={formData.baseUrl}
                      onChange={inputHandlers.baseUrl}
                      className={`w-full px-4 py-3 rounded-lg text-sm font-mono transition-all duration-200 ${
                        errors.baseUrl ? 'border-red-500 focus:border-red-500' : 'focus:border-purple-500'
                      }`}
                      style={errors.baseUrl ? styles.inputError : styles.input}
                      placeholder="https://api.openai.com/v1"
                    />
                    
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      <PresetButton onClick={() => handlePresetUrl('openai')} icon="🤖">
                        OpenAI
                      </PresetButton>
                      <PresetButton onClick={() => handlePresetUrl('anthropic')} icon="🧠">
                        Anthropic
                      </PresetButton>
                      <PresetButton onClick={() => handlePresetUrl('together')} icon="🤝">
                        Together AI
                      </PresetButton>
                      <PresetButton onClick={() => handlePresetUrl('huggingface')} icon="🤗">
                        HuggingFace
                      </PresetButton>
                      <PresetButton onClick={() => handlePresetUrl('localVllm')} icon="🏠">
                        Local vLLM
                      </PresetButton>
                      <PresetButton onClick={() => handlePresetUrl('localOllama')} icon="🦙">
                        Local Ollama
                      </PresetButton>
                    </div>
                  </div>
                </FormField>
                
                <FormField 
                  label="API Key" 
                  description="Leave blank for local servers that don't require authentication"
                >
                  <div className="relative">
                    <input
                      type={showApiKey ? 'text' : 'password'}
                      value={formData.apiKey}
                      onChange={inputHandlers.apiKey}
                      className="w-full px-4 py-3 pr-12 rounded-lg text-sm font-mono transition-all duration-200 focus:border-purple-500"
                      style={styles.input}
                      placeholder="sk-... or leave blank for local endpoints"
                    />
                    <button
                      type="button"
                      onClick={toggleApiKeyVisibility}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded hover:bg-gray-600 transition-colors"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      {showApiKey ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                        </svg>
                      )}
                    </button>
                  </div>
                </FormField>
              </FormSection>
              
              <FormSection 
                title="Model Configuration" 
                subtitle="Default model and inference settings"
              >
                <FormField 
                  label="Default Model" 
                  description="The model to use by default when no specific model is requested"
                >
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={formData.defaultModel}
                      onChange={inputHandlers.defaultModel}
                      className="w-full px-4 py-3 rounded-lg text-sm font-mono transition-all duration-200 focus:border-purple-500"
                      style={styles.input}
                      placeholder="gpt-4o, claude-3-5-sonnet-20241022, etc."
                    />
                    
                    <div className="space-y-3">
                      <div>
                        <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
                          Popular OpenAI Models:
                        </p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                          <PresetButton onClick={() => handlePresetModel('gpt-4o')}>
                            GPT-4o
                          </PresetButton>
                          <PresetButton onClick={() => handlePresetModel('gpt-4o-mini')}>
                            GPT-4o Mini
                          </PresetButton>
                          <PresetButton onClick={() => handlePresetModel('gpt-4-turbo')}>
                            GPT-4 Turbo
                          </PresetButton>
                          <PresetButton onClick={() => handlePresetModel('gpt-3.5-turbo')}>
                            GPT-3.5 Turbo
                          </PresetButton>
                        </div>
                      </div>
                      
                      <div>
                        <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
                          Anthropic Claude Models:
                        </p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                          <PresetButton onClick={() => handlePresetModel('claude-3-5-sonnet')}>
                            Claude 3.5 Sonnet
                          </PresetButton>
                          <PresetButton onClick={() => handlePresetModel('claude-3-opus')}>
                            Claude 3 Opus
                          </PresetButton>
                          <PresetButton onClick={() => handlePresetModel('claude-3-sonnet')}>
                            Claude 3 Sonnet
                          </PresetButton>
                          <PresetButton onClick={() => handlePresetModel('claude-3-haiku')}>
                            Claude 3 Haiku
                          </PresetButton>
                        </div>
                      </div>
                      
                      <div>
                        <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
                          Open Source Models:
                        </p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                          <PresetButton onClick={() => handlePresetModel('llama-3-8b')}>
                            Llama 3 8B
                          </PresetButton>
                          <PresetButton onClick={() => handlePresetModel('llama-3-70b')}>
                            Llama 3 70B
                          </PresetButton>
                          <PresetButton onClick={() => handlePresetModel('mistral-7b')}>
                            Mistral 7B
                          </PresetButton>
                          <PresetButton onClick={() => handlePresetModel('mixtral-8x7b')}>
                            Mixtral 8x7B
                          </PresetButton>
                        </div>
                      </div>
                    </div>
                  </div>
                </FormField>
              </FormSection>
            </div>
            
            {/* Right Column - Preview & Actions */}
            <div className="lg:col-span-1">
              <div className="sticky top-6 space-y-6">
                {/* Configuration Preview */}
                <div className="p-4 rounded-lg border" style={styles.previewCard}>
                  <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                    Configuration Preview
                  </h3>
                  <div className="space-y-3 text-xs">
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Name:</span>
                      <div className="mt-1 p-2 rounded font-mono" style={styles.previewItem}>
                        {formData.name || 'Not specified'}
                      </div>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Endpoint:</span>
                      <div className="mt-1 p-2 rounded font-mono break-all" style={styles.previewItem}>
                        {formData.baseUrl || 'Not specified'}
                      </div>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Model:</span>
                      <div className="mt-1 p-2 rounded font-mono" style={styles.previewItem}>
                        {formData.defaultModel || 'Not specified'}
                      </div>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Auth:</span>
                      <div className="mt-1 p-2 rounded font-mono" style={styles.previewItem}>
                        {formData.apiKey ? '✓ API Key configured' : 'No authentication'}
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Quick Actions */}
                <div className="space-y-3">
                  <button
                    onClick={handleSave}
                    disabled={isLoading}
                    className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-lg'
                    }`}
                    style={styles.primaryButton}
                  >
                    {isLoading ? (
                      <>
                        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Saving...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        {isEditing ? 'Update Provider' : 'Create Provider'}
                      </>
                    )}
                  </button>
                  
                  <button
                    onClick={onCancel}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 hover:bg-gray-700 disabled:opacity-50"
                    style={styles.secondaryButton}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LLMEndpointForm;