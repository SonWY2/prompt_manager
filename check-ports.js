#!/usr/bin/env node

// 실시간 연결 상태 체크
const net = require('net');

console.log('🔍 실시간 포트 상태 체크');
console.log('==========================');

function checkPort(port, name) {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    
    socket.setTimeout(1000);
    
    socket.on('connect', () => {
      console.log(`✅ ${name}: 포트 ${port} 활성화`);
      socket.destroy();
      resolve(true);
    });
    
    socket.on('timeout', () => {
      console.log(`❌ ${name}: 포트 ${port} 응답 없음`);
      socket.destroy();
      resolve(false);
    });
    
    socket.on('error', () => {
      console.log(`❌ ${name}: 포트 ${port} 사용 불가`);
      resolve(false);
    });
    
    socket.connect(port, 'localhost');
  });
}

async function checkAllPorts() {
  console.log('포트 상태 확인 중...\n');
  
  const backend = await checkPort(3000, '백엔드 서버');
  const frontend = await checkPort(3030, '프론트엔드 서버');
  
  console.log('\n📊 결과 요약:');
  
  if (backend && frontend) {
    console.log('🎉 모든 서버가 정상 실행 중입니다!');
    console.log('🌐 브라우저에서 http://localhost:3030 접속 가능');
  } else if (backend && !frontend) {
    console.log('⚠️  백엔드만 실행 중입니다.');
    console.log('💡 프론트엔드 실행: npm run dev');
  } else if (!backend && frontend) {
    console.log('⚠️  프론트엔드만 실행 중입니다.');
    console.log('💡 백엔드 실행: npm run backend');
  } else {
    console.log('❌ 두 서버 모두 실행되지 않았습니다.');
    console.log('💡 동시 실행: npm run dev:all');
  }
  
  console.log('\n🚀 권장 명령어: npm run dev:all');
}

checkAllPorts().catch(console.error);
