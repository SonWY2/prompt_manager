// LLM API 호출 함수 (OpenAI 호환 API 사용)
const axios = require('axios');

async function callLLM(prompt, systemPrompt = "You are a helpful assistant.", llmConfig = null) {
  console.log(`[${new Date().toISOString()}] LLM API 호출 시작 - 프롬프트 길이: ${prompt.length} 문자, 시스템 프롬프트 길이: ${systemPrompt.length} 문자`);
  
  try {
    // LLM 설정 결정 - llmConfig가 제공되면 사용, 아니면 환경변수 사용
    const config = llmConfig || {
      baseUrl: process.env.OPENAI_BASE_URL || 'http://localhost:8000/v1',
      apiKey: process.env.OPENAI_API_KEY || '',
      model: process.env.OPENAI_MODEL || 'mistralai/Mistral-7B-Instruct-v0.2'
    };
    
    console.log(`[${new Date().toISOString()}] LLM 설정:`, {
      baseUrl: config.baseUrl,
      model: config.model,
      hasApiKey: !!config.apiKey
    });
    
    // 메시지 배열 생성 - system prompt가 비어있지 않은 경우에만 추가
    const messages = [];
    
    if (systemPrompt && systemPrompt.trim() !== "") {
      messages.push({ role: "system", content: systemPrompt });
    }
    
    messages.push({ role: "user", content: prompt });
    
    console.log(`[${new Date().toISOString()}] 메시지 구성 완료 - 총 ${messages.length}개 메시지`);
    
    // 요청 헤더 구성
    const headers = {
      'Content-Type': 'application/json'
    };
    
    // API 키가 있으면 헤더에 추가
    if (config.apiKey) {
      headers['Authorization'] = `Bearer ${config.apiKey}`;
    }
    
    // LLM 서버로 요청 보내기
    const response = await axios.post(`${config.baseUrl}/chat/completions`, {
      model: config.model,
      messages: messages,
      temperature: 0.7,
      max_tokens: 1024
    }, {
      headers: headers,
      timeout: 30000 // 30초 타임아웃
    });
    
    // 응답 처리
    const assistantResponse = response.data.choices[0].message.content;
    console.log(`[${new Date().toISOString()}] LLM API 호출 성공 - 응답 길이: ${assistantResponse.length} 문자`);
    
    return {
      prompt: prompt,
      system_prompt: systemPrompt,
      response: assistantResponse,
      timestamp: new Date().toISOString(),
      model: config.model,
      endpoint: config.baseUrl
    };
  } catch (error) {
    console.error(`[${new Date().toISOString()}] LLM API 호출 오류:`, error.message);
    
    // 오류 발생 시, 기본 응답 사용 (개발 모드에서 유용)
    if (process.env.NODE_ENV !== 'production') {
      console.warn(`[${new Date().toISOString()}] 개발 모드: 모의 응답 사용`);
      
      const mockResponses = [
        "사용자의 요청에 따라 생성된 응답입니다. 다양한 내용을 포함할 수 있습니다.",
        "프롬프트 매니저를 통해 테스트하고 있는 응답입니다. API 호출 시 오류가 발생하여 모의 응답을 사용합니다.",
        "서버 연결 오류가 발생하여 모의 응답을 생성합니다. 실제 API 호출이 가능한지 확인해 보세요."
      ];
      
      const randomResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
      
      return {
        prompt: prompt,
        system_prompt: systemPrompt,
        response: randomResponse + "\n\n입력된 프롬프트: " + prompt.substring(0, 100) + (prompt.length > 100 ? "..." : ""),
        timestamp: new Date().toISOString(),
        error: error.message,
        model: 'mock-model',
        endpoint: 'mock-endpoint'
      };
    }
    
    // 실제 프로덕션 환경에서는 오류 전파
    throw new Error(`LLM API 호출 오류: ${error.message}`);
  }
}

module.exports = { callLLM };