// API 기본 URL 설정
export const API_BASE_URL = 'http://localhost:3000';

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