// LLM API 호출 함수 (OpenAI 호환 API 사용)
const axios = require('axios');

async function callLLM(prompt) {
  console.log(`[${new Date().toISOString()}] LLM API 호출 시작 - 길이: ${prompt.length} 문자`);
  
  try {
    // 환경변수에서 설정 값 가져오기
    const baseUrl = process.env.OPENAI_BASE_URL || 'http://localhost:8000/v1'; // 기본값
    const model = process.env.OPENAI_MODEL || 'mistralai/Mistral-7B-Instruct-v0.2'; // 기본값
    
    console.log(`[${new Date().toISOString()}] API 설정 - URL: ${baseUrl}, 모델: ${model}`);
    
    // vLLM 서버로 요청 보내기
    const response = await axios.post(`${baseUrl}/chat/completions`, {
      model: model,
      messages: [
        { role: "system", content: "You are a helpful assistant." },
        { role: "user", content: prompt }
      ],
      temperature: 0.7,
      max_tokens: 1024
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // 응답 처리
    const assistantResponse = response.data.choices[0].message.content;
    console.log(`[${new Date().toISOString()}] LLM API 호출 성공 - 응답 길이: ${assistantResponse.length} 문자`);
    
    return {
      prompt: prompt,
      response: assistantResponse,
      timestamp: new Date().toISOString(),
      model: model
    };
  } catch (error) {
    console.error(`[${new Date().toISOString()}] LLM API 호출 오류:`, error.message);
    
    // 오류 발생 시, 기본 응답 사용 (개발 모드에서 유용)
    if (process.env.NODE_ENV !== 'production') {
      console.warn(`[${new Date().toISOString()}] 개발 모드: 모의 응답 사용`);
      
      const mockResponses = [
        "프롬프트 매니저를 통해 테스트하고 있는 응답입니다. API 호출 시 오류가 발생하여 모의 응답을 사용합니다.",
        "서버 연결 오류가 발생하여 모의 응답을 생성합니다. 실제 API 호출이 가능한지 확인해 보세요.",
        "기본 모의 응답입니다. 환경변수 설정을 확인해주세요."
      ];
      
      const randomResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
      
      return {
        prompt: prompt,
        response: randomResponse + "\n\n[오류 발생] " + error.message + "\n\n입력된 프롬프트: " + prompt.substring(0, 100) + (prompt.length > 100 ? "..." : ""),
        timestamp: new Date().toISOString(),
        error: error.message
      };
    }
    
    // 실제 프로덕션 환경에서는 오류 전파
    throw new Error(`LLM API 호출 오류: ${error.message}`);
  }
}

module.exports = { callLLM };