import React, { useState, useEffect } from 'react';

function LLMEndpointForm({ endpoint, isEditing, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    name: '',
    baseUrl: '',
    apiKey: '',
    defaultModel: '',
    description: ''
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
        description: endpoint.description || ''
      });
    } else {
      // 새로 생성하는 경우 기본값
      setFormData({
        name: '',
        baseUrl: '',
        apiKey: '',
        defaultModel: '',
        description: ''
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
  
  return (
    <div className="p-6">
      <div className="max-w-2xl">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            {isEditing ? '엔드포인트 편집' : '새 엔드포인트 추가'}
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            LLM API 엔드포인트 정보를 입력하세요.
          </p>
        </div>
        
        <div className="space-y-6">
          {/* 이름 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              이름 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 placeholder-gray-400 dark:bg-gray-800 dark:text-gray-200 dark:placeholder-gray-500 ${
                errors.name
                  ? 'border-red-500 dark:border-red-500'
                  : 'border-gray-300 dark:border-gray-600'
              }`}
              placeholder="예: OpenAI GPT-4, Local vLLM Server"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.name}</p>
            )}
          </div>
          
          {/* Base URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Base URL <span className="text-red-500">*</span>
            </label>
            <div className="space-y-2">
              <input
                type="url"
                value={formData.baseUrl}
                onChange={(e) => handleInputChange('baseUrl', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 placeholder-gray-400 dark:bg-gray-800 dark:text-gray-200 dark:placeholder-gray-500 ${
                  errors.baseUrl
                    ? 'border-red-500 dark:border-red-500'
                    : 'border-gray-300 dark:border-gray-600'
                }`}
                placeholder="https://api.openai.com/v1"
              />
              
              {/* URL 프리셋 버튼들 */}
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => handlePresetUrl('openai')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded"
                >
                  OpenAI
                </button>
                <button
                  type="button"
                  onClick={() => handlePresetUrl('anthropic')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded"
                >
                  Anthropic
                </button>
                <button
                  type="button"
                  onClick={() => handlePresetUrl('localVllm')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded"
                >
                  Local vLLM
                </button>
                <button
                  type="button"
                  onClick={() => handlePresetUrl('localOllama')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded"
                >
                  Local Ollama
                </button>
              </div>
            </div>
            {errors.baseUrl && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.baseUrl}</p>
            )}
          </div>
          
          {/* API 키 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              API 키 (선택사항)
            </label>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={formData.apiKey}
                onChange={(e) => handleInputChange('apiKey', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 placeholder-gray-400 dark:bg-gray-800 dark:text-gray-200 dark:placeholder-gray-500 pr-10"
                placeholder="sk-..."
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {showApiKey ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L9.878 9.878M12 12l-3.12-3.12a10.054 10.054 0 00-1.558 3.029M9.878 9.878l3.12-3.12m0 0l3.12 3.12m-3.12-3.12l3.12 3.12" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              로컬 서버인 경우 비워두어도 됩니다.
            </p>
          </div>
          
          {/* 기본 모델 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              기본 모델 (선택사항)
            </label>
            <div className="space-y-2">
              <input
                type="text"
                value={formData.defaultModel}
                onChange={(e) => handleInputChange('defaultModel', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 placeholder-gray-400 dark:bg-gray-800 dark:text-gray-200 dark:placeholder-gray-500"
                placeholder="gpt-4o, claude-3-opus-20240229, mistralai/Mistral-7B-Instruct-v0.2"
              />
              
              {/* 모델 프리셋 버튼들 */}
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => handlePresetModel('gpt-4o')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded"
                >
                  GPT-4o
                </button>
                <button
                  type="button"
                  onClick={() => handlePresetModel('gpt-4-turbo')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded"
                >
                  GPT-4 Turbo
                </button>
                <button
                  type="button"
                  onClick={() => handlePresetModel('claude-3-opus')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded"
                >
                  Claude 3 Opus
                </button>
                <button
                  type="button"
                  onClick={() => handlePresetModel('mistral-7b')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded"
                >
                  Mistral 7B
                </button>
              </div>
            </div>
          </div>
          
          {/* 설명 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              설명 (선택사항)
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 placeholder-gray-400 dark:bg-gray-800 dark:text-gray-200 dark:placeholder-gray-500 resize-none"
              placeholder="이 엔드포인트에 대한 설명을 입력하세요..."
            />
          </div>
        </div>
        
        {/* 액션 버튼들 */}
        <div className="flex justify-end gap-3 mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onCancel}
            className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            취소
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            {isEditing ? '업데이트' : '생성'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default LLMEndpointForm;