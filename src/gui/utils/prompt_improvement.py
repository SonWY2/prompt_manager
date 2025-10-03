"""
Prompt Improvement Utility
프롬프트 개선 방법론 관리 유틸리티
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional


class PromptImprovementManager:
    """프롬프트 개선 방법론을 관리하는 클래스"""
    
    def __init__(self):
        self.improvement_methods: List[Dict] = []
        self.custom_template: Dict = {}
        self.self_discover_templates: Dict = {}
        self.load_templates()
        
    def load_templates(self):
        """YAML 파일에서 개선 템플릿을 로드"""
        try:
            # Get config file path
            config_path = Path(__file__).parent.parent.parent / "config" / "prompt_improvement_templates.yaml"
            
            if not config_path.exists():
                print(f"Warning: Config file not found at {config_path}")
                self._load_default_templates()
                return
                
            # Load YAML file
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            self.improvement_methods = config.get('improvement_methods', [])
            self.custom_template = config.get('custom_template', {})
            self.self_discover_templates = config.get('self_discover_templates', {})
            
            print(f"Loaded {len(self.improvement_methods)} improvement methods from config")
            if self.self_discover_templates:
                print(f"Loaded Self-Discover templates: {list(self.self_discover_templates.keys())}")
            
        except Exception as e:
            print(f"Error loading improvement templates: {e}")
            self._load_default_templates()
            
    def _load_default_templates(self):
        """기본 템플릿 로드 (fallback)"""
        self.improvement_methods = [
            {
                'id': 'clarity',
                'name': '명확성 개선',
                'description': '프롬프트를 더 명확하고 구체적으로 개선합니다',
                'icon': '💡',
                'template': '아래 입력된 프롬프트를 분석하고, LLM이 더 명확하게 이해할 수 있도록 개선해주세요:\n\n{main_prompt}\n\n개선된 프롬프트만 출력해주세요:'
            }
        ]
        self.custom_template = {
            'id': 'custom',
            'name': '커스텀 개선',
            'description': '사용자가 직접 작성한 개선 지침을 사용합니다',
            'icon': '✏️',
            'placeholder': '개선 지침을 입력하세요. {main_prompt}를 사용하여 원본 프롬프트를 참조할 수 있습니다.'
        }
        
    def get_all_methods(self) -> List[Dict]:
        """모든 개선 방법론 목록 반환"""
        return self.improvement_methods.copy()
        
    def get_method_by_id(self, method_id: str) -> Optional[Dict]:
        """ID로 특정 개선 방법론 가져오기"""
        for method in self.improvement_methods:
            if method.get('id') == method_id:
                return method.copy()
        return None
        
    def get_custom_template(self) -> Dict:
        """커스텀 템플릿 정보 반환"""
        return self.custom_template.copy()
        
    def apply_template(self, template: str, main_prompt: str) -> str:
        """템플릿에 main_prompt를 적용하여 최종 프롬프트 생성"""
        return template.replace('{main_prompt}', main_prompt)
        
    def get_method_names(self) -> List[str]:
        """모든 방법론의 이름 목록 반환"""
        return [method.get('name', 'Unknown') for method in self.improvement_methods]
        
    def get_method_descriptions(self) -> Dict[str, str]:
        """방법론 ID와 설명의 매핑 반환"""
        return {
            method.get('id', ''): method.get('description', '')
            for method in self.improvement_methods
        }
    
    def is_multi_stage_method(self, method_id: str) -> bool:
        """특정 메서드가 다단계 프로세스인지 확인"""
        method = self.get_method_by_id(method_id)
        return method is not None and method.get('is_multi_stage', False)
    
    def get_self_discover_templates(self) -> Dict:
        """Self-Discover 템플릿들 반환"""
        return self.self_discover_templates.copy()
    
    def get_self_discover_stage_template(self, stage: str) -> Optional[str]:
        """특정 단계의 Self-Discover 템플릿 반환
        
        Args:
            stage: 'stage1_select', 'stage1_adapt', 'stage1_implement', 'stage2_solve'
            
        Returns:
            해당 단계의 템플릿 문자열, 없으면 None
        """
        return self.self_discover_templates.get(stage)
    
    def apply_self_discover_template(self, stage: str, **kwargs) -> Optional[str]:
        """Self-Discover 템플릿에 변수를 적용
        
        Args:
            stage: 템플릿 단계
            **kwargs: 템플릿 변수들 (main_prompt, selected_modules, adapted_modules, reasoning_structure 등)
            
        Returns:
            변수가 적용된 템플릿 문자열
        """
        template = self.get_self_discover_stage_template(stage)
        if not template:
            return None
        
        # Replace all provided variables in the template
        result = template
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        return result
