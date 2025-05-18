import React, { useState } from 'react';
import Button from '../common/Button.jsx';

function ComparisonView({ versions, currentVersionId, onCompare, comparedResults }) {
  const [selectedVersion1, setSelectedVersion1] = useState(currentVersionId);
  const [selectedVersion2, setSelectedVersion2] = useState('');
  const [showDiffOnly, setShowDiffOnly] = useState(true);
  
  const handleCompare = () => {
    if (selectedVersion1 && selectedVersion2) {
      onCompare(selectedVersion1, selectedVersion2);
    }
  };
  
  if (!versions || versions.length < 2) {
    return (
      <div className="p-4 text-center text-gray-500 dark:text-gray-400">
        <p>비교하려면 최소 2개 이상의 버전이 필요합니다.</p>
      </div>
    );
  }
  
  return (
    <div className="p-4">
      <div className="mb-4">
        <h3 className="font-medium mb-2">버전 비교</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm mb-1">첫 번째 버전</label>
            <select
              value={selectedVersion1}
              onChange={(e) => setSelectedVersion1(e.target.value)}
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
            >
              <option value="">선택하세요</option>
              {versions.map(v => (
                <option key={v.id} value={v.id}>
                  {v.id} ({new Date(v.createdAt || 0).toLocaleDateString()})
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm mb-1">두 번째 버전</label>
            <select
              value={selectedVersion2}
              onChange={(e) => setSelectedVersion2(e.target.value)}
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 dark:text-white"
            >
              <option value="">선택하세요</option>
              {versions.filter(v => v.id !== selectedVersion1).map(v => (
                <option key={v.id} value={v.id}>
                  {v.id} ({new Date(v.createdAt || 0).toLocaleDateString()})
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="mt-3 flex justify-end">
          <Button
            variant="primary"
            onClick={handleCompare}
            disabled={!selectedVersion1 || !selectedVersion2}
          >
            비교하기
          </Button>
        </div>
      </div>
      
      {comparedResults && (
        <div className="mt-6">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-medium">비교 결과</h3>
            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={showDiffOnly}
                onChange={() => setShowDiffOnly(!showDiffOnly)}
                className="mr-2"
              />
              차이점만 보기
            </label>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="border border-gray-300 dark:border-gray-700 rounded">
              <div className="p-2 bg-gray-100 dark:bg-gray-800 font-medium border-b border-gray-300 dark:border-gray-700">
                {selectedVersion1}
              </div>
              <pre className="p-3 whitespace-pre-wrap text-sm dark:text-white">
                {versions.find(v => v.id === selectedVersion1)?.content || "콘텐츠 없음"}
              </pre>
            </div>
            
            <div className="border border-gray-300 dark:border-gray-700 rounded">
              <div className="p-2 bg-gray-100 dark:bg-gray-800 font-medium border-b border-gray-300 dark:border-gray-700">
                {selectedVersion2}
              </div>
              <pre className="p-3 whitespace-pre-wrap text-sm dark:text-white">
                {versions.find(v => v.id === selectedVersion2)?.content || "콘텐츠 없음"}
              </pre>
            </div>
          </div>
          
          <div className="mt-6">
            <h4 className="font-medium mb-2">결과 비교</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="border border-gray-300 dark:border-gray-700 rounded">
                <div className="p-2 bg-gray-100 dark:bg-gray-800 font-medium border-b border-gray-300 dark:border-gray-700">
                  {selectedVersion1} 결과
                </div>
                <div className="p-3">
                  <p className="text-gray-500 dark:text-gray-400 text-sm italic">
                    아직 구현되지 않았습니다. 버전별 결과 비교 기능을 추가해주세요.
                  </p>
                </div>
              </div>
              
              <div className="border border-gray-300 dark:border-gray-700 rounded">
                <div className="p-2 bg-gray-100 dark:bg-gray-800 font-medium border-b border-gray-300 dark:border-gray-700">
                  {selectedVersion2} 결과
                </div>
                <div className="p-3">
                  <p className="text-gray-500 dark:text-gray-400 text-sm italic">
                    아직 구현되지 않았습니다. 버전별 결과 비교 기능을 추가해주세요.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ComparisonView;