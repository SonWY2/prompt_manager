#!/usr/bin/env node

const axios = require('axios');

// 설정 정보
const FRONTEND_PORT = process.env.VITE_PORT || 3030;
const BACKEND_PORT = process.env.SERVER_PORT || 3000;

console.log('🔍 프론트엔드/백엔드 연결 테스트');
console.log('=====================================');

async function testConnections() {
  console.log(`📋 설정 정보:`);
  console.log(`  - 프론트엔드 포트: ${FRONTEND_PORT}`);
  console.log(`  - 백엔드 포트: ${BACKEND_PORT}`);
  console.log('');

  // 1. 백엔드 직접 연결 테스트
  console.log('🔌 백엔드 직접 연결 테스트...');
  try {
    const response = await axios.get(`http://localhost:${BACKEND_PORT}/api/tasks`, {
      timeout: 3000
    });
    console.log(`  ✅ 백엔드 연결 성공 (${response.status})`);
    console.log(`  📊 응답 데이터: ${JSON.stringify(response.data).substring(0, 100)}...`);
  } catch (error) {
    console.log(`  ❌ 백엔드 연결 실패: ${error.message}`);
    if (error.code === 'ECONNREFUSED') {
      console.log(`  💡 해결방법: 먼저 'npm run backend' 실행 필요`);
    }
  }

  console.log('');

  // 2. 프록시 테스트 (프론트엔드가 실행 중인 경우)
  console.log('🔄 프록시 연결 테스트...');
  try {
    const response = await axios.get(`http://localhost:${FRONTEND_PORT}/api/tasks`, {
      timeout: 3000
    });
    console.log(`  ✅ 프록시 연결 성공 (${response.status})`);
    console.log(`  📊 프록시를 통한 응답: ${JSON.stringify(response.data).substring(0, 100)}...`);
  } catch (error) {
    console.log(`  ❌ 프록시 연결 실패: ${error.message}`);
    if (error.code === 'ECONNREFUSED') {
      console.log(`  💡 해결방법: 'npm run dev' 실행 필요`);
    }
  }

  console.log('');
  console.log('🚀 완전한 테스트를 위해 다음 명령어 실행:');
  console.log('   npm run dev:all');
}

testConnections().catch(console.error);
