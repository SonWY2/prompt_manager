// src/frontend/components/prompt/VariableManager.jsx
import React, { useState } from 'react';
import Button from '../common/Button.jsx';

// 변수 값 표시를 위한 재사용 가능한 컴포넌트
const VariableValueDisplay = ({ value, maxLength = 100 }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const showToggle = value.length > maxLength || value.includes('\n'); // 줄바꿈이 있거나 길이가 길면 토글 표시
  const displayedValue = isExpanded || !showToggle ? value : value.substring(0, maxLength) + '...';

  return (
    <div className="text-sm dark:text-white">
      <pre className="whitespace-pre-wrap text-gray-700 dark:text-gray-300"> {/* 줄바꿈 반영을 위한 'whitespace-pre-wrap' 클래스 사용 */}
        {displayedValue.trim() === '' ? <span className="italic text-gray-500">값이 비어 있습니다</span> : displayedValue}
      </pre>
      {showToggle && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-blue-600 dark:text-blue-400 hover:underline mt-1 text-xs"
        >
          {isExpanded ? '간략히 보기' : '더보기'}
        </button>
      )}
    </div>
  );
};


function VariableManager({ variables, values, onChange }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [selectedPreset, setSelectedPreset] = useState('default');
  const [newVariable, setNewVariable] = useState('');
  const [activeVariable, setActiveVariable] = useState(null); // 펼쳐진 변수 편집기
  
  // 변수 값 프리셋 (세트)
  // TODO: 이 프리셋들은 서버에서 로드하거나, 태스크에 종속적인 데이터로 관리되어야 합니다.
  const presets = [
    { id: 'default', name: '기본값' },
    { id: 'preset1', name: '예시 1' },
    { id: 'preset2', name: '예시 2' },
  ];
  
  const handleAddVariable = () => {
    if (!newVariable.trim()) return;
    
    // 실제 구현에서는 부모 컴포넌트에 변수 추가 로직 호출
    onChange(newVariable.trim(), '', 'add'); // 'add' 액션 추가
    setNewVariable('');
  };
  
  const handleRemoveVariable = (variable) => {
    // 실제 구현에서는 부모 컴포넌트에 변수 제거 로직 호출
    onChange(variable, '', 'remove'); // 'remove' 액션 추가
    // 제거된 변수가 현재 활성 변수였다면 비활성화
    if (activeVariable === variable) {
        setActiveVariable(null);
    }
  };
  
  const handleUpdateVariableValue = (variable, value) => {
    onChange(variable, value, 'update'); // 'update' 액션 추가
  };
  
  return (
    <div>
      <div 
        className="p-3 border-b border-gray-300 dark:border-gray-700 flex justify-between items-center cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <h3 className="font-medium">변수 관리</h3>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {variables.length}개 변수
          </span>
        </div>
        <div className="flex items-center gap-2">
          <select 
            value={selectedPreset} 
            onChange={(e) => setSelectedPreset(e.target.value)}
            className="text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1"
            onClick={(e) => e.stopPropagation()}
          >
            {presets.map(preset => (
              <option key={preset.id} value={preset.id}>
                {preset.name}
              </option>
            ))}
          </select>
          <span>{isExpanded ? '▲' : '▼'}</span>
        </div>
      </div>
      
      {isExpanded && (
        <div className="p-3">
          {/* 변수 추가 폼 */}
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={newVariable}
              onChange={(e) => setNewVariable(e.target.value)}
              className="flex-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 dark:text-white"
              placeholder="새 변수 이름..."
            />
            <Button
              variant="primary"
              size="small"
              onClick={handleAddVariable}
            >
              추가
            </Button>
          </div>
          
          {/* 변수 목록 */}
          <div className="space-y-3 max-h-60 overflow-y-auto"> {/* max-h-60과 overflow-y-auto로 스크롤 추가 */}
            {variables.length === 0 ? (
              <div className="text-center text-gray-500 dark:text-gray-400 py-3">
                <p>프롬프트에 변수가 없습니다. 변수를 사용하려면 <code>{'{{변수명}}'}</code> 형식으로 작성하세요.</p>
              </div>
            ) : (
              variables.map(variable => (
                <div key={variable} className="border border-gray-200 dark:border-gray-700 rounded">
                  <div className="flex justify-between items-center px-3 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <div className="font-medium">{`{{${variable}}}`}</div>
                    <div className="flex gap-1">
                      <button
                        className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                        onClick={() => setActiveVariable(activeVariable === variable ? null : variable)}
                      >
                        {activeVariable === variable ? '접기' : '편집'} {/* '펼치기'를 '편집'으로 변경 */}
                      </button>
                      <button
                        className="text-xs text-red-600 dark:text-red-400 hover:underline ml-2"
                        onClick={() => handleRemoveVariable(variable)}
                      >
                        삭제
                      </button>
                    </div>
                  </div>
                  
                  {/* 변수 값 편집 영역 */}
                  <div className={`p-2 ${activeVariable === variable ? 'block' : 'hidden'}`}>
                    <textarea
                      value={values[variable] || ''}
                      onChange={(e) => handleUpdateVariableValue(variable, e.target.value)}
                      className="w-full h-24 border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 dark:text-white resize-y" // resize-y 추가
                      placeholder={`${variable} 값 입력...`}
                    />
                  </div>
                  
                  {/* 변수 값 미리보기 영역 (수정: 줄바꿈 반영 및 길이에 따른 더보기/접기) */}
                  {activeVariable !== variable && (
                    <div className="px-3 py-2">
                        <VariableValueDisplay value={values[variable] || ''} maxLength={50} /> {/* 새로운 컴포넌트 사용 */}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default VariableManager;