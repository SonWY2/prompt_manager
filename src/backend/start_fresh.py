#!/usr/bin/env python3
"""
손상된 JSON 파일 문제를 우회하고 새로운 SQLite DB로 시작
"""

from database import PromptManagerDB
import os

def start_fresh():
    print("🆕 새로운 SQLite 데이터베이스로 시작")
    
    # SQLite DB 초기화 (손상된 JSON 파일 무시)
    db = PromptManagerDB()
    
    # 기본 데이터 생성
    print("📝 기본 데이터 생성 중...")
    
    # 예제 Task 생성
    task = db.create_task(
        task_id="task-example-1",
        name="예제 프롬프트 테스트",
        variables={
            "prompt": "what is your name?",
            "context": "You are a helpful AI assistant",
            "language": "Korean"
        }
    )
    
    print(f"✅ Task 생성: {task['name']}")
    print(f"   Variables: {task['variables']}")
    
    # 예제 Version 생성
    version = db.create_version(
        version_id="v-example-1",
        task_id="task-example-1",
        name="기본 버전",
        content="{{context}}\n\nQuestion: {{prompt}}\n\nPlease respond in {{language}}.",
        system_prompt="You are a helpful AI assistant. Always be polite and informative.",
        description="기본 프롬프트 템플릿"
    )
    
    print(f"✅ Version 생성: {version['name']}")
    print(f"   Content: {version['content']}")
    
    # 예제 LLM Endpoint 생성 (OpenRouter)
    endpoint = db.create_llm_endpoint({
        'id': 'endpoint-openrouter',
        'name': 'OpenRouter Free',
        'baseUrl': 'https://openrouter.ai/api/v1',
        'apiKey': '',  # 사용자가 나중에 설정
        'defaultModel': 'microsoft/phi-3-mini-4k-instruct:free',
        'description': 'OpenRouter 무료 모델',
        'isDefault': True
    })
    
    print(f"✅ LLM Endpoint 생성: {endpoint['name']}")
    
    # 활성 엔드포인트로 설정
    db.set_setting('activeEndpointId', endpoint['id'])
    db.set_setting('defaultEndpointId', endpoint['id'])
    
    # 결과 확인
    all_tasks = db.get_all_tasks()
    all_endpoints = db.get_all_llm_endpoints()
    settings = db.get_all_settings()
    
    print(f"\n📊 데이터 요약:")
    print(f"   Tasks: {len(all_tasks)}개")
    print(f"   LLM Endpoints: {len(all_endpoints)}개")
    print(f"   Settings: {len(settings)}개")
    
    print(f"\n🗄️ SQLite 파일 위치: {os.path.abspath(db.db_path)}")
    
    print("✅ 새로운 SQLite 데이터베이스 준비 완료!")
    print("\n💡 이제 백엔드 서버를 재시작하세요:")
    print("   cd src/backend && python main.py")

if __name__ == "__main__":
    start_fresh()
