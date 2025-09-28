#!/usr/bin/env python3
"""
테스트용 데이터 설정 스크립트
"""

from database import PromptManagerDB

def setup_test_data():
    print("🧪 테스트 데이터 설정 시작")
    
    db = PromptManagerDB()
    
    # 기존 task 업데이트 - 변수 값 설정
    task_id = "task-example-1"
    test_variables = {
        "context": "You are a helpful AI assistant",
        "prompt": "what is your name?", 
        "language": "Korean"
    }
    
    print(f"📝 Task {task_id}에 테스트 변수 설정:")
    print(f"   Variables: {test_variables}")
    
    success = db.update_task(task_id, variables=test_variables)
    
    if success:
        print("✅ 테스트 변수 설정 완료")
    else:
        print("❌ 변수 설정 실패")
    
    # 확인
    updated_task = db.get_task_by_id(task_id)
    if updated_task:
        print(f"🔍 업데이트된 Task 확인:")
        print(f"   Name: {updated_task['name']}")
        print(f"   Variables: {updated_task['variables']}")
    else:
        print("❌ Task 조회 실패")
    
    print("✅ 테스트 데이터 설정 완료")

if __name__ == "__main__":
    setup_test_data()
