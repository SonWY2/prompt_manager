import React from 'react';

function MetricsDisplay({ result }) {
  if (!result) {
    return (
      <div className="p-4 text-center text-gray-500 dark:text-gray-400">
        <p>메트릭을 표시할 결과가 없습니다.</p>
      </div>
    );
  }
  
  // 실제 응답에서 메트릭 데이터를 추출
  // 이 예제에서는 가상의 메트릭 데이터 사용
  const metrics = {
    responseTime: Math.random() * 2 + 0.5, // 0.5 ~ 2.5초
    inputTokens: Math.floor(Math.random() * 100 + 50), // 50 ~ 150 토큰
    outputTokens: Math.floor(Math.random() * 200 + 100), // 100 ~ 300 토큰
    totalCost: (Math.random() * 0.01).toFixed(5), // $0.00000 ~ $0.01000
  };
  
  return (
    <div className="p-4">
      <h3 className="font-medium mb-4">성능 메트릭</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white dark:bg-gray-900 p-4 rounded shadow">
          <div className="text-sm text-gray-500 dark:text-gray-400">응답 시간</div>
          <div className="text-2xl font-bold mt-1">{metrics.responseTime.toFixed(2)}초</div>
        </div>
        
        <div className="bg-white dark:bg-gray-900 p-4 rounded shadow">
          <div className="text-sm text-gray-500 dark:text-gray-400">총 비용</div>
          <div className="text-2xl font-bold mt-1">${metrics.totalCost}</div>
        </div>
        
        <div className="bg-white dark:bg-gray-900 p-4 rounded shadow">
          <div className="text-sm text-gray-500 dark:text-gray-400">입력 토큰</div>
          <div className="text-2xl font-bold mt-1">{metrics.inputTokens}</div>
        </div>
        
        <div className="bg-white dark:bg-gray-900 p-4 rounded shadow">
          <div className="text-sm text-gray-500 dark:text-gray-400">출력 토큰</div>
          <div className="text-2xl font-bold mt-1">{metrics.outputTokens}</div>
        </div>
      </div>
      
      <div className="mt-6">
        <h4 className="font-medium mb-3">최적화 제안</h4>
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded border border-blue-200 dark:border-blue-800">
          <ul className="list-disc list-inside space-y-2 text-sm">
            <li>프롬프트에서 반복되는 지시사항을 줄여 입력 토큰을 줄일 수 있습니다.</li>
            <li>변수를 더 효율적으로 사용하여 출력 품질을 높일 수 있습니다.</li>
            <li>더 명확한 지시사항으로 더 정확한 응답을 얻을 수 있습니다.</li>
          </ul>
        </div>
      </div>
      
      <div className="mt-6">
        <h4 className="font-medium mb-3">이전 버전과 비교</h4>
        <p className="text-gray-500 dark:text-gray-400 text-sm italic">
          아직 구현되지 않았습니다. 버전별 메트릭 비교 기능을 추가해주세요.
        </p>
      </div>
    </div>
  );
}

export default MetricsDisplay;