#!/usr/bin/env python3
"""
손상된 JSON 파일을 백업하고 SQLite로 새로 시작하는 스크립트
"""

from database import PromptManagerDB
import os
import json
import datetime

def fix_and_migrate():
    print("🛠️ JSON 손상 문제 해결 및 SQLite 마이그레이션 시작")
    
    # SQLite DB 초기화
    db = PromptManagerDB()
    
    # 기존 TinyDB 파일 확인
    legacy_path = '../../data/db.json'
    abs_legacy_path = os.path.abspath(legacy_path)
    
    if os.path.exists(abs_legacy_path):
        try:
            # 손상된 JSON 파일 백업
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{abs_legacy_path}.corrupted_backup_{timestamp}"
            
            print(f"💾 손상된 JSON 파일을 백업: {backup_path}")
            os.rename(abs_legacy_path, backup_path)
            
            # 기본 데이터로 새로 시작
            print("🆕 기본 설정으로 새로 시작합니다...")
            
            # 기본 Task 생성 (테스트용)
            test_task = db.create_task(
                task_id="task-example",
                name="예제 Task",
                variables={"prompt": "what is your name?", "context": "You are a helpful assistant"}
            )
            
            print(f"📝 예제 Task 생성: {test_task['name']}")
            
            # 기본 Version 생성
            test_version = db.create_version(
                version_id="v-example-1",
                task_id="task-example", 
                name="Version 1",
                content="{{prompt}}\n\nContext: {{context}}",
                system_prompt="You are a helpful AI assistant",
                description="기본 예제 버전"
            )
            
            print(f"📄 예제 Version 생성: {test_version['name']}")
            
            # 확인
            tasks = db.get_all_tasks()
            print(f"✅ 생성된 Tasks: {len(tasks)}개")
            
            for task in tasks:
                print(f"  - {task['name']}: Variables = {task['variables']}")
                for version in task['versions']:
                    print(f"    └── {version['name']}: {version['content']}")
            
        except Exception as e:
            print(f"❌ 처리 중 오류: {e}")
    
    print("✅ 손상 복구 및 새 시작 완료")

if __name__ == "__main__":
    fix_and_migrate()
