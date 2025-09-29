import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

class PromptManagerDB:
    def __init__(self, db_path: str = "data/prompt_manager.db"):
        """SQLite 데이터베이스 초기화"""
        
        # data 디렉토리 생성
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 테이블 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('PRAGMA foreign_keys = ON')  # 외래키 활성화
            
            # Tasks 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    is_favorite BOOLEAN DEFAULT FALSE,
                    variables TEXT DEFAULT '{}',  -- JSON 문자열로 저장
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Versions 테이블  
            conn.execute('''
                CREATE TABLE IF NOT EXISTS versions (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    content TEXT DEFAULT '',
                    system_prompt TEXT DEFAULT 'You are a helpful AI Assistant',
                    description TEXT DEFAULT '',
                    variables TEXT DEFAULT '{}',  -- JSON 문자열로 저장
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
                )
            ''')
            
            # Results 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS results (
                    id TEXT PRIMARY KEY,
                    version_id TEXT NOT NULL,
                    input_data TEXT NOT NULL,  -- JSON 문자열로 저장
                    output TEXT NOT NULL,      -- JSON 문자열로 저장
                    endpoint_info TEXT,        -- JSON 문자열로 저장
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (version_id) REFERENCES versions (id) ON DELETE CASCADE
                )
            ''')
            
            # LLM Endpoints 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS llm_endpoints (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_url TEXT NOT NULL,
                    api_key TEXT,
                    default_model TEXT,
                    description TEXT,
                    context_size INTEGER,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Settings 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 인덱스 생성
            conn.execute('CREATE INDEX IF NOT EXISTS idx_versions_task_id ON versions (task_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_results_version_id ON results (version_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_results_timestamp ON results (timestamp DESC)')
            
            conn.commit()
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('PRAGMA foreign_keys = ON')
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn
    
    # === Tasks ===
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """모든 Task 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT t.*, 
                       COUNT(v.id) as version_count
                FROM tasks t
                LEFT JOIN versions v ON t.id = v.task_id
                GROUP BY t.id, t.name, t.is_favorite, t.variables, t.created_at, t.updated_at
                ORDER BY t.updated_at DESC
            ''')
            
            tasks = []
            for row in cursor.fetchall():
                task = dict(row)
                # JSON 문자열을 파싱
                task['variables'] = json.loads(task['variables']) if task['variables'] else {}
                task['isFavorite'] = bool(task['is_favorite'])  # 프론트엔드 호환성
                
                # 버전들 조회
                task['versions'] = self.get_task_versions(task['id'])
                tasks.append(task)
            
            return tasks
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """특정 Task 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            task = dict(row)
            task['variables'] = json.loads(task['variables']) if task['variables'] else {}
            task['isFavorite'] = bool(task['is_favorite'])
            task['versions'] = self.get_task_versions(task_id)
            
            return task
    
    def create_task(self, task_id: str, name: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """새 Task 생성"""
        variables = variables or {}
        variables_json = json.dumps(variables, ensure_ascii=False)
        
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO tasks (id, name, variables, is_favorite)
                VALUES (?, ?, ?, FALSE)
            ''', (task_id, name, variables_json))
            conn.commit()
        
        return self.get_task_by_id(task_id)
    
    def update_task(self, task_id: str, **updates) -> bool:
        """Task 업데이트"""
        if not updates:
            return False
        
        # variables가 딕셔너리면 JSON 문자열로 변환
        if 'variables' in updates:
            updates['variables'] = json.dumps(updates['variables'], ensure_ascii=False)
        
        # is_favorite 필드명 변환
        if 'isFavorite' in updates:
            updates['is_favorite'] = updates.pop('isFavorite')
        
        # 업데이트 시간 추가
        updates['updated_at'] = datetime.now().isoformat()
        
        # 동적 쿼리 생성
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE tasks SET {set_clause} WHERE id = ?"
        values = list(updates.values()) + [task_id]
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_task(self, task_id: str) -> bool:
        """Task 삭제 (CASCADE로 관련 데이터도 함께 삭제)"""
        with self.get_connection() as conn:
            cursor = conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # === Versions ===
    def get_task_versions(self, task_id: str) -> List[Dict[str, Any]]:
        """특정 Task의 모든 Version 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM versions 
                WHERE task_id = ? 
                ORDER BY created_at DESC
            ''', (task_id,))
            
            versions = []
            for row in cursor.fetchall():
                version = dict(row)
                version['variables'] = json.loads(version['variables']) if version['variables'] else {}
                
                # 결과들 조회
                version['results'] = self.get_version_results(version['id'])
                versions.append(version)
            
            return versions
    
    def get_version_by_id(self, version_id: str) -> Optional[Dict[str, Any]]:
        """특정 Version 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM versions WHERE id = ?', (version_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            version = dict(row)
            version['variables'] = json.loads(version['variables']) if version['variables'] else {}
            version['results'] = self.get_version_results(version_id)
            
            return version
    
    def create_version(self, version_id: str, task_id: str, name: str, 
                      content: str = '', system_prompt: str = 'You are a helpful AI Assistant',
                      description: str = '', variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """새 Version 생성"""
        variables = variables or {}
        variables_json = json.dumps(variables, ensure_ascii=False)
        
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO versions (id, task_id, name, content, system_prompt, description, variables)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (version_id, task_id, name, content, system_prompt, description, variables_json))
            conn.commit()
        
        return self.get_version_by_id(version_id)
    
    def update_version(self, version_id: str, **updates) -> bool:
        """Version 업데이트"""
        if not updates:
            return False
        
        # variables가 딕셔너리면 JSON 문자열로 변환
        if 'variables' in updates:
            updates['variables'] = json.dumps(updates['variables'], ensure_ascii=False)
        
        # 업데이트 시간 추가
        updates['updated_at'] = datetime.now().isoformat()
        
        # 동적 쿼리 생성
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE versions SET {set_clause} WHERE id = ?"
        values = list(updates.values()) + [version_id]
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_version(self, version_id: str) -> bool:
        """Version 삭제"""
        with self.get_connection() as conn:
            cursor = conn.execute('DELETE FROM versions WHERE id = ?', (version_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # === Results ===
    def get_version_results(self, version_id: str) -> List[Dict[str, Any]]:
        """특정 Version의 모든 Result 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM results 
                WHERE version_id = ? 
                ORDER BY timestamp DESC
            ''', (version_id,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['inputData'] = json.loads(result['input_data']) if result['input_data'] else {}
                result['output'] = json.loads(result['output']) if result['output'] else {}
                result['endpoint'] = json.loads(result['endpoint_info']) if result['endpoint_info'] else {}
                
                # 프론트엔드 호환성을 위해 기존 필드명도 유지
                result.pop('input_data', None)
                result.pop('endpoint_info', None)
                results.append(result)
            
            return results
    
    def add_result(self, version_id: str, input_data: Dict[str, Any], 
                   output: Dict[str, Any], endpoint_info: Dict[str, Any] = None) -> str:
        """새 Result 추가"""
        result_id = str(uuid.uuid4())
        input_data_json = json.dumps(input_data, ensure_ascii=False)
        output_json = json.dumps(output, ensure_ascii=False)
        endpoint_info_json = json.dumps(endpoint_info or {}, ensure_ascii=False)
        
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO results (id, version_id, input_data, output, endpoint_info)
                VALUES (?, ?, ?, ?, ?)
            ''', (result_id, version_id, input_data_json, output_json, endpoint_info_json))
            conn.commit()
        
        return result_id
    
    def delete_result(self, version_id: str, timestamp: str) -> bool:
        """특정 Result 삭제 (timestamp 기준)"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM results 
                WHERE version_id = ? AND timestamp = ?
            ''', (version_id, timestamp))
            conn.commit()
            return cursor.rowcount > 0
    
    # === LLM Endpoints ===
    def _convert_endpoint_to_frontend_format(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """데이터베이스 형식(snake_case)을 프론트엔드 형식(camelCase)으로 변환"""
        return {
            'id': endpoint.get('id'),
            'name': endpoint.get('name'),
            'baseUrl': endpoint.get('base_url'),
            'apiKey': endpoint.get('api_key'),
            'defaultModel': endpoint.get('default_model'),
            'description': endpoint.get('description'),
            'contextSize': endpoint.get('context_size'),
            'isDefault': bool(endpoint.get('is_default', False)),
            'createdAt': endpoint.get('created_at'),
            'updatedAt': endpoint.get('updated_at')
        }
    def get_all_llm_endpoints(self) -> List[Dict[str, Any]]:
        """모든 LLM Endpoint 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM llm_endpoints ORDER BY created_at DESC')
            endpoints = []
            for row in cursor.fetchall():
                endpoint = dict(row)
                # snake_case를 camelCase로 변환 (프론트엔드 호환성)
                endpoint = self._convert_endpoint_to_frontend_format(endpoint)
                endpoints.append(endpoint)
            return endpoints
    
    def get_llm_endpoint_by_id(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """특정 LLM Endpoint 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM llm_endpoints WHERE id = ?', (endpoint_id,))
            row = cursor.fetchone()
            if not row:
                return None
            endpoint = dict(row)
            # snake_case를 camelCase로 변환 (프론트엔드 호환성)
            return self._convert_endpoint_to_frontend_format(endpoint)
    
    def create_llm_endpoint(self, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 LLM Endpoint 생성"""
        endpoint_id = endpoint_data.get('id', str(uuid.uuid4()))
        
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO llm_endpoints 
                (id, name, base_url, api_key, default_model, description, context_size, is_default)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                endpoint_id, 
                endpoint_data.get('name'),
                endpoint_data.get('baseUrl'),
                endpoint_data.get('apiKey'),
                endpoint_data.get('defaultModel'),
                endpoint_data.get('description'),
                endpoint_data.get('contextSize'),
                endpoint_data.get('isDefault', False)
            ))
            conn.commit()
        
        return self.get_llm_endpoint_by_id(endpoint_id)
    
    def update_llm_endpoint(self, endpoint_id: str, **updates) -> bool:
        """LLM Endpoint 업데이트"""
        if not updates:
            return False
        
        # 필드명 변환
        field_mapping = {
            'baseUrl': 'base_url',
            'apiKey': 'api_key', 
            'defaultModel': 'default_model',
            'contextSize': 'context_size',
            'isDefault': 'is_default'
        }
        
        for old_key, new_key in field_mapping.items():
            if old_key in updates:
                updates[new_key] = updates.pop(old_key)
        
        updates['updated_at'] = datetime.now().isoformat()
        
        # 동적 쿼리 생성
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE llm_endpoints SET {set_clause} WHERE id = ?"
        values = list(updates.values()) + [endpoint_id]
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_llm_endpoint(self, endpoint_id: str) -> bool:
        """LLM Endpoint 삭제"""
        with self.get_connection() as conn:
            cursor = conn.execute('DELETE FROM llm_endpoints WHERE id = ?', (endpoint_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # === Settings ===
    def get_setting(self, key: str) -> Optional[str]:
        """설정값 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
    
    def get_all_settings(self) -> Dict[str, str]:
        """모든 설정값 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT key, value FROM settings')
            return {row['key']: row['value'] for row in cursor.fetchall()}
    
    def set_setting(self, key: str, value: str) -> None:
        """설정값 저장/업데이트"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now().isoformat()))
            conn.commit()

    def migrate_from_tinydb(self, json_file_path: str) -> bool:
        """TinyDB JSON 파일에서 SQLite로 마이그레이션"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Tasks 마이그레이션
            if 'tasks' in data:
                for task_key, task_data in data['tasks'].items():
                    task_id = task_data.get('id', task_key)
                    
                    # Task 생성
                    self.create_task(
                        task_id=task_id,
                        name=task_data.get('name', ''),
                        variables=task_data.get('variables', {})
                    )
                    
                    # Task 업데이트 (is_favorite 등)
                    if task_data.get('isFavorite'):
                        self.update_task(task_id, isFavorite=True)
                    
                    # Versions 마이그레이션
                    if 'versions' in task_data:
                        for version_data in task_data['versions']:
                            version_id = version_data.get('id')
                            if version_id:
                                # Version 생성
                                self.create_version(
                                    version_id=version_id,
                                    task_id=task_id,
                                    name=version_data.get('name', ''),
                                    content=version_data.get('content', ''),
                                    system_prompt=version_data.get('system_prompt', 'You are a helpful AI Assistant'),
                                    description=version_data.get('description', ''),
                                    variables=version_data.get('variables', {})
                                )
                                
                                # Results 마이그레이션
                                if 'results' in version_data:
                                    for result_data in version_data['results']:
                                        self.add_result(
                                            version_id=version_id,
                                            input_data=result_data.get('inputData', {}),
                                            output=result_data.get('output', {}),
                                            endpoint_info=result_data.get('endpoint', {})
                                        )
            
            # LLM Endpoints 마이그레이션
            if 'llm_endpoints' in data:
                for endpoint_key, endpoint_data in data['llm_endpoints'].items():
                    self.create_llm_endpoint(endpoint_data)
            
            # Settings 마이그레이션
            if 'settings' in data:
                for setting_key, setting_data in data['settings'].items():
                    if isinstance(setting_data, dict):
                        for key, value in setting_data.items():
                            self.set_setting(key, str(value))
                    else:
                        self.set_setting(setting_key, str(setting_data))
            
            return True
            
        except Exception as e:
            return False
