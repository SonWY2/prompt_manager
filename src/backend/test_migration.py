#!/usr/bin/env python3
"""
SQLite 마이그레이션 테스트 스크립트
"""

from database import PromptManagerDB
import os
import json

def test_migration():
    print("🔄 SQLite 마이그레이션 테스트 시작")
    
    # SQLite DB 초기화
    db = PromptManagerDB()
    
    # 기존 TinyDB 파일 확인
    legacy_path = '../../data/db.json'
    abs_legacy_path = os.path.abspath(legacy_path)
    
    print(f"📁 Legacy DB 경로: {abs_legacy_path}")
    print(f"📁 Legacy DB 존재 여부: {os.path.exists(abs_legacy_path)}")
    
    if os.path.exists(abs_legacy_path):
        try:
            # 파일 크기 확인
            file_size = os.path.getsize(abs_legacy_path)
            print(f"📊 Legacy DB 파일 크기: {file_size} bytes")
            
            if file_size > 0:
                # 마이그레이션 실행
                print("🚀 마이그레이션 실행 중...")
                result = db.migrate_from_tinydb(abs_legacy_path)
                print(f"✅ 마이그레이션 결과: {result}")
                
                # 마이그레이션 후 데이터 확인
                tasks = db.get_all_tasks()
                endpoints = db.get_all_llm_endpoints()
                
                print(f"📋 마이그레이션된 Tasks: {len(tasks)}개")
                print(f"🔗 마이그레이션된 LLM Endpoints: {len(endpoints)}개")
                
                # Task 세부 정보 출력
                for task in tasks:
                    print(f"  - Task: {task['name']} (ID: {task['id']}, Variables: {task['variables']})")
                    
            else:
                print("❌ Legacy DB 파일이 비어있음")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
            print("💡 이것이 바로 SQLite로 마이그레이션이 필요한 이유입니다!")
            
            # 손상된 JSON 파일을 백업하고 빈 상태로 시작
            backup_path = abs_legacy_path + '.corrupted_backup'
            os.rename(abs_legacy_path, backup_path)
            print(f"💾 손상된 파일을 {backup_path}로 백업했습니다.")
            
        except Exception as e:
            print(f"❌ 마이그레이션 오류: {e}")
    else:
        print("📭 Legacy DB 파일이 없습니다. 새로운 SQLite DB로 시작합니다.")
    
    # SQLite DB 파일 위치 확인
    sqlite_path = db.db_path
    abs_sqlite_path = os.path.abspath(sqlite_path)
    
    print(f"🗄️ SQLite DB 경로: {abs_sqlite_path}")
    print(f"🗄️ SQLite DB 존재 여부: {os.path.exists(abs_sqlite_path)}")
    
    if os.path.exists(abs_sqlite_path):
        file_size = os.path.getsize(abs_sqlite_path)
        print(f"📊 SQLite DB 파일 크기: {file_size} bytes")
    
    print("✅ 마이그레이션 테스트 완료")

if __name__ == "__main__":
    test_migration()
