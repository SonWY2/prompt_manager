#!/usr/bin/env python3
"""
SQLite 데이터베이스 내용 확인 스크립트
"""

from database import PromptManagerDB
import json

def check_database():
    print("🔍 SQLite 데이터베이스 내용 확인")
    
    db = PromptManagerDB()
    
    # Tasks 조회
    tasks = db.get_all_tasks()
    print(f"\n📋 Tasks ({len(tasks)}개):")
    
    for task in tasks:
        print(f"  🎯 Task: {task['name']} (ID: {task['id']})")
        print(f"     Variables: {json.dumps(task['variables'], ensure_ascii=False)}")
        
        # Versions 조회
        for version in task['versions']:
            print(f"     📄 Version: {version['name']} (ID: {version['id']})")
            print(f"        Content: {version['content']}")
            print(f"        Variables: {json.dumps(version['variables'], ensure_ascii=False)}")
    
    # Settings 조회
    settings = db.get_all_settings()
    print(f"\n⚙️ Settings ({len(settings)}개):")
    for key, value in settings.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 데이터베이스 확인 완료")

if __name__ == "__main__":
    check_database()
