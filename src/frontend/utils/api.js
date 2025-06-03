// API 기본 URL 설정 - Vite 프록시 사용
// 개발 모드에서는 Vite 프록시를 통해 '/api'로 요청
// 프로덕션 모드에서는 환경변수 또는 기본값 사용
export const API_BASE_URL = import.meta.env.DEV 
  ? '' // 개발 모드: Vite 프록시 사용
  : (import.meta.env.VITE_API_URL || 'http://localhost:3000'); // 프로덕션 모드

// 디버깅을 위한 로그
if (import.meta.env.DEV) {
  console.log('🔧 개발 모드: Vite 프록시 사용 (/api/* → http://localhost:3000/api/*)');
} else {
  console.log('🚀 프로덕션 모드: API_BASE_URL =', API_BASE_URL);
}

// API URL 생성 함수
export const apiUrl = (path) => `${API_BASE_URL}${path}`;

// 헬퍼 함수: API 호출
export const fetchFromAPI = async (url, options = {}) => {
  console.log(`API 호출: ${options.method || 'GET'} ${url}`);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    console.log(`응답 상태: ${response.status} ${response.statusText}`);
    
    if (!response.ok) {
      throw new Error(`API 요청 실패: ${response.status} ${response.statusText}`);
    }
    
    if (response.status === 204) {
      return { success: true }; // No content
    }
    
    const data = await response.json();
    console.log('응답 데이터:', data);
    return data;
  } catch (error) {
    console.error(`API 요청 오류 (${url}):`, error);
    throw error;
  }
};