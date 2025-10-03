"""
Self-Discover Wizard Dialog
Self-Discover 3단계 프로세스를 위한 위저드 다이얼로그
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QStackedWidget, QWidget, QFrame,
    QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from typing import Dict, Any, Optional

from ..utils.db_client import DatabaseClient
from ..utils.prompt_improvement import PromptImprovementManager


class LLMProcessThread(QThread):
    """LLM 호출을 백그라운드에서 처리하는 스레드"""
    
    finished = pyqtSignal(str)  # result text
    error = pyqtSignal(str)     # error message
    
    def __init__(self, db_client: DatabaseClient, prompt: str, endpoint: Dict[str, Any]):
        super().__init__()
        self.db_client = db_client
        self.prompt = prompt
        self.endpoint = endpoint
        
    def run(self):
        """LLM 호출 실행"""
        try:
            if not self.endpoint:
                self.error.emit("No LLM endpoint available")
                return
                
            base_url = self.endpoint.get('baseUrl', '').rstrip('/')
            api_key = self.endpoint.get('apiKey', '')
            model = self.endpoint.get('defaultModel', 'gpt-3.5-turbo')
            
            if not base_url or not api_key:
                self.error.emit("Missing endpoint URL or API key")
                return
                
            import requests
            chat_url = f"{base_url}/chat/completions"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': model,
                'messages': [
                    {
                        'role': 'user',
                        'content': self.prompt
                    }
                ],
                'temperature': 0.7
            }
            
            response = requests.post(
                chat_url,
                headers=headers,
                json=payload,
                timeout=120,  # 2 minutes for complex reasoning
                verify=True
            )
            
            if response.status_code != 200:
                self.error.emit(f"API call failed: HTTP {response.status_code} - {response.text}")
                return
                
            result_data = response.json()
            
            if 'choices' in result_data and result_data['choices']:
                result_text = result_data['choices'][0].get('message', {}).get('content', '')
                if result_text:
                    self.finished.emit(result_text)
                else:
                    self.error.emit("No content received from API")
            else:
                self.error.emit("Invalid response format from API")
                
        except requests.exceptions.Timeout:
            self.error.emit("Request timed out after 2 minutes")
        except requests.exceptions.ConnectionError:
            self.error.emit("Could not connect to LLM endpoint")
        except requests.exceptions.SSLError:
            self.error.emit("SSL certificate verification failed")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")


class SelfDiscoverWizardDialog(QDialog):
    """Self-Discover 3단계 위저드 다이얼로그"""
    
    # Signal: 최종 개선된 프롬프트
    improvement_completed = pyqtSignal(str)
    
    def __init__(self, original_prompt: str, endpoint: Dict[str, Any], parent=None):
        super().__init__(parent)
        
        self.original_prompt = original_prompt
        self.endpoint = endpoint
        self.db_client = DatabaseClient()
        self.improvement_manager = PromptImprovementManager()
        
        # Stage results storage
        self.selected_modules = ""
        self.adapted_modules = ""
        self.reasoning_structure = ""
        self.final_improved_prompt = ""
        
        # Current stage (0=SELECT, 1=ADAPT, 2=IMPLEMENT, 3=STAGE2)
        self.current_stage = 0
        
        # Stage completion tracking
        self.stage_completed = [False, False, False, False]  # SELECT, ADAPT, IMPLEMENT, STAGE2
        
        # LLM thread
        self.llm_thread: Optional[LLMProcessThread] = None
        
        self.setWindowTitle("Self-Discover 프롬프트 개선 위저드")
        self.setModal(True)
        self.resize(900, 700)
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 헤더
        header_label = QLabel("🔍 Self-Discover 프롬프트 개선")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(header_label)
        
        # 설명
        desc_label = QLabel("3단계 reasoning 구조화를 통해 체계적으로 프롬프트를 개선합니다.")
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # 진행 표시
        self.progress_frame = self.create_progress_indicator()
        layout.addWidget(self.progress_frame)
        
        # 스택 위젯 (각 단계별 화면)
        self.stacked_widget = QStackedWidget()
        
        # Stage 1: SELECT
        self.stage_select = self.create_stage_widget(
            "Step 1: SELECT",
            "39개의 reasoning modules 중 이 프롬프트 개선에 적합한 것들을 선택합니다.",
            "선택 중..."
        )
        self.stacked_widget.addWidget(self.stage_select)
        
        # Stage 1: ADAPT
        self.stage_adapt = self.create_stage_widget(
            "Step 2: ADAPT",
            "선택된 modules를 프롬프트 개선에 특화되도록 구체화합니다.",
            "구체화 중..."
        )
        self.stacked_widget.addWidget(self.stage_adapt)
        
        # Stage 1: IMPLEMENT
        self.stage_implement = self.create_stage_widget(
            "Step 3: IMPLEMENT",
            "구체화된 modules를 JSON 형식의 reasoning structure로 변환합니다.",
            "구조화 중..."
        )
        self.stacked_widget.addWidget(self.stage_implement)
        
        # Stage 2: SOLVE
        self.stage_solve = self.create_stage_widget(
            "Stage 2: 최종 개선",
            "생성된 reasoning structure를 사용하여 최종 프롬프트를 개선합니다.",
            "개선 중..."
        )
        self.stacked_widget.addWidget(self.stage_solve)
        
        layout.addWidget(self.stacked_widget, 1)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setFixedSize(100, 40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.prev_button = QPushButton("◀ 이전")
        self.prev_button.setFixedSize(100, 40)
        self.prev_button.setEnabled(False)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover:enabled {
                background-color: #5a6268;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #adb5bd;
            }
        """)
        self.prev_button.clicked.connect(self.go_previous_stage)
        button_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("시작 ▶")
        self.next_button.setFixedSize(100, 40)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover:enabled {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.next_button.clicked.connect(self.go_next_stage)
        button_layout.addWidget(self.next_button)
        
        layout.addLayout(button_layout)
        
    def create_progress_indicator(self) -> QWidget:
        """진행 표시 인디케이터 생성"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        stages = [
            ("1", "SELECT"),
            ("2", "ADAPT"),
            ("3", "IMPLEMENT"),
            ("4", "STAGE 2")
        ]
        
        self.stage_labels = []
        
        for i, (num, name) in enumerate(stages):
            if i > 0:
                # 화살표
                arrow_label = QLabel("→")
                arrow_label.setStyleSheet("color: #ced4da; font-size: 16px; font-weight: bold;")
                layout.addWidget(arrow_label)
            
            # 단계 라벨
            stage_label = QLabel(f"{num}. {name}")
            stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stage_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    border: 2px solid #dee2e6;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 11px;
                    font-weight: 600;
                    color: #6c757d;
                    min-width: 80px;
                }
            """)
            self.stage_labels.append(stage_label)
            layout.addWidget(stage_label)
        
        # 첫 단계 활성화
        self.update_progress_indicator()
        
        return frame
        
    def update_progress_indicator(self):
        """진행 표시 업데이트"""
        stages = [
            ("1", "SELECT"),
            ("2", "ADAPT"),
            ("3", "IMPLEMENT"),
            ("4", "STAGE 2")
        ]
        
        for i, label in enumerate(self.stage_labels):
            if i < len(stages):
                num, name = stages[i]
                
                if i < len(self.stage_completed) and self.stage_completed[i]:
                    # 완료된 단계 - 체크마크 표시
                    label.setText(f"✓ {name}")
                    label.setStyleSheet("""
                        QLabel {
                            background-color: #28a745;
                            border: 2px solid #28a745;
                            border-radius: 6px;
                            padding: 8px 12px;
                            font-size: 11px;
                            font-weight: 600;
                            color: white;
                            min-width: 80px;
                        }
                    """)
                elif i == self.current_stage:
                    # 현재 단계
                    label.setText(f"{num}. {name}")
                    label.setStyleSheet("""
                        QLabel {
                            background-color: #3498db;
                            border: 2px solid #3498db;
                            border-radius: 6px;
                            padding: 8px 12px;
                            font-size: 11px;
                            font-weight: 600;
                            color: white;
                            min-width: 80px;
                        }
                    """)
                else:
                    # 대기 단계
                    label.setText(f"{num}. {name}")
                    label.setStyleSheet("""
                        QLabel {
                            background-color: white;
                            border: 2px solid #dee2e6;
                            border-radius: 6px;
                            padding: 8px 12px;
                            font-size: 11px;
                            font-weight: 600;
                            color: #6c757d;
                            min-width: 80px;
                        }
                    """)
                
    def create_stage_widget(self, title: str, description: str, loading_text: str) -> QWidget:
        """단계별 위젯 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 제목
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        layout.addWidget(title_label)
        
        # 설명
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(desc_label)
        
        # 결과 텍스트 영역
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlaceholderText("AI가 분석을 완료하면 결과가 여기에 표시됩니다...")
        text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 10px;
                background-color: white;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(text_edit, 1)
        
        # 로딩 인디케이터
        loading_frame = QFrame()
        loading_frame.setVisible(False)
        loading_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        loading_layout = QHBoxLayout(loading_frame)
        loading_layout.setContentsMargins(10, 10, 10, 10)
        
        loading_label = QLabel(loading_text)
        loading_label.setStyleSheet("color: #856404; font-weight: 500;")
        loading_layout.addWidget(loading_label)
        
        layout.addWidget(loading_frame)
        
        # Store references
        widget.text_edit = text_edit
        widget.loading_frame = loading_frame
        
        return widget
        
    def go_next_stage(self):
        """다음 단계로 이동"""
        # 현재 단계가 이미 완료되었는지 확인
        if self.current_stage < len(self.stage_completed) and self.stage_completed[self.current_stage]:
            # 이미 완료된 단계 - 바로 다음 화면으로 이동
            self.current_stage += 1
            self.stacked_widget.setCurrentIndex(self.current_stage)
            self.update_progress_indicator()
            self.update_buttons()
            return
        
        # 새로운 단계 - LLM 호출
        if self.current_stage == 0:
            # SELECT 단계 시작
            self.start_select_stage()
        elif self.current_stage == 1:
            # ADAPT 단계 시작
            self.start_adapt_stage()
        elif self.current_stage == 2:
            # IMPLEMENT 단계 시작
            self.start_implement_stage()
        elif self.current_stage == 3:
            # STAGE 2 시작
            self.start_stage2()
        elif self.current_stage == 4:
            # 완료 - 결과 적용
            self.complete_wizard()
            
    def go_previous_stage(self):
        """이전 단계로 이동"""
        if self.current_stage > 0:
            self.current_stage -= 1
            self.stacked_widget.setCurrentIndex(self.current_stage)
            self.update_progress_indicator()
            self.update_buttons()
            
    def start_select_stage(self):
        """SELECT 단계 시작"""
        # 버튼 비활성화
        self.next_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        # 로딩 표시
        self.stage_select.loading_frame.setVisible(True)
        
        # 템플릿 준비
        select_prompt = self.improvement_manager.apply_self_discover_template(
            'stage1_select',
            main_prompt=self.original_prompt
        )
        
        if not select_prompt:
            QMessageBox.critical(self, "오류", "SELECT 템플릿을 로드할 수 없습니다.")
            self.reject()
            return
        
        # LLM 호출
        self.call_llm(select_prompt, self.on_select_completed, self.on_stage_error)
        
    def start_adapt_stage(self):
        """ADAPT 단계 시작"""
        self.next_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        self.stage_adapt.loading_frame.setVisible(True)
        
        adapt_prompt = self.improvement_manager.apply_self_discover_template(
            'stage1_adapt',
            main_prompt=self.original_prompt,
            selected_modules=self.selected_modules
        )
        
        if not adapt_prompt:
            QMessageBox.critical(self, "오류", "ADAPT 템플릿을 로드할 수 없습니다.")
            self.reject()
            return
        
        self.call_llm(adapt_prompt, self.on_adapt_completed, self.on_stage_error)
        
    def start_implement_stage(self):
        """IMPLEMENT 단계 시작"""
        self.next_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        self.stage_implement.loading_frame.setVisible(True)
        
        implement_prompt = self.improvement_manager.apply_self_discover_template(
            'stage1_implement',
            main_prompt=self.original_prompt,
            adapted_modules=self.adapted_modules
        )
        
        if not implement_prompt:
            QMessageBox.critical(self, "오류", "IMPLEMENT 템플릿을 로드할 수 없습니다.")
            self.reject()
            return
        
        self.call_llm(implement_prompt, self.on_implement_completed, self.on_stage_error)
        
    def start_stage2(self):
        """STAGE 2 시작"""
        self.next_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        self.stage_solve.loading_frame.setVisible(True)
        
        stage2_prompt = self.improvement_manager.apply_self_discover_template(
            'stage2_solve',
            main_prompt=self.original_prompt,
            reasoning_structure=self.reasoning_structure
        )
        
        if not stage2_prompt:
            QMessageBox.critical(self, "오류", "STAGE 2 템플릿을 로드할 수 없습니다.")
            self.reject()
            return
        
        self.call_llm(stage2_prompt, self.on_stage2_completed, self.on_stage_error)
        
    def call_llm(self, prompt: str, success_callback, error_callback):
        """LLM 호출"""
        self.llm_thread = LLMProcessThread(self.db_client, prompt, self.endpoint)
        self.llm_thread.finished.connect(success_callback)
        self.llm_thread.error.connect(error_callback)
        self.llm_thread.start()
        
    def on_select_completed(self, result: str):
        """SELECT 단계 완료"""
        self.selected_modules = result
        self.stage_select.text_edit.setPlainText(result)
        self.stage_select.loading_frame.setVisible(False)
        
        # 완료 플래그 설정
        self.stage_completed[0] = True
        
        self.current_stage = 1
        self.stacked_widget.setCurrentIndex(self.current_stage)
        self.update_progress_indicator()
        self.update_buttons()
        
        self.next_button.setText("다음 ▶")
        
    def on_adapt_completed(self, result: str):
        """ADAPT 단계 완료"""
        self.adapted_modules = result
        self.stage_adapt.text_edit.setPlainText(result)
        self.stage_adapt.loading_frame.setVisible(False)
        
        # 완료 플래그 설정
        self.stage_completed[1] = True
        
        self.current_stage = 2
        self.stacked_widget.setCurrentIndex(self.current_stage)
        self.update_progress_indicator()
        self.update_buttons()
        
    def on_implement_completed(self, result: str):
        """IMPLEMENT 단계 완료"""
        self.reasoning_structure = result
        self.stage_implement.text_edit.setPlainText(result)
        self.stage_implement.loading_frame.setVisible(False)
        
        # 완료 플래그 설정
        self.stage_completed[2] = True
        
        self.current_stage = 3
        self.stacked_widget.setCurrentIndex(self.current_stage)
        self.update_progress_indicator()
        self.update_buttons()
        
    def on_stage2_completed(self, result: str):
        """STAGE 2 완료"""
        self.final_improved_prompt = result
        self.stage_solve.text_edit.setPlainText(result)
        self.stage_solve.loading_frame.setVisible(False)
        
        # 완료 플래그 설정
        self.stage_completed[3] = True
        
        self.current_stage = 4
        self.update_buttons()
        
        self.next_button.setText("완료 ✓")
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
    def on_stage_error(self, error_message: str):
        """단계 오류 처리"""
        current_widget = self.stacked_widget.currentWidget()
        if hasattr(current_widget, 'loading_frame'):
            current_widget.loading_frame.setVisible(False)
        if hasattr(current_widget, 'text_edit'):
            current_widget.text_edit.setPlainText(f"오류 발생:\n{error_message}")
        
        QMessageBox.critical(self, "오류", f"처리 중 오류가 발생했습니다:\n{error_message}")
        
        self.update_buttons()
        
    def complete_wizard(self):
        """위저드 완료"""
        if self.final_improved_prompt:
            self.improvement_completed.emit(self.final_improved_prompt)
            self.accept()
        else:
            QMessageBox.warning(self, "오류", "개선된 프롬프트가 생성되지 않았습니다.")
            
    def update_buttons(self):
        """버튼 상태 업데이트"""
        self.next_button.setEnabled(True)
        self.prev_button.setEnabled(self.current_stage > 0 and self.current_stage < 4)
        self.cancel_button.setEnabled(True)
        
        # 버튼 텍스트 및 스타일 업데이트
        if self.current_stage < len(self.stage_completed):
            if self.stage_completed[self.current_stage]:
                # 이미 완료된 단계 - 회색 버튼
                self.next_button.setText("다음으로 이동 ▶")
                self.next_button.setStyleSheet("""
                    QPushButton {
                        background-color: #6c757d;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 13px;
                        font-weight: 600;
                    }
                    QPushButton:hover:enabled {
                        background-color: #5a6268;
                    }
                    QPushButton:disabled {
                        background-color: #bdc3c7;
                    }
                """)
            else:
                # 미완료 단계 - 파란색 버튼
                if self.current_stage == 0:
                    self.next_button.setText("시작 ▶")
                else:
                    self.next_button.setText("다음 단계 실행 ▶")
                
                self.next_button.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 13px;
                        font-weight: 600;
                    }
                    QPushButton:hover:enabled {
                        background-color: #2980b9;
                    }
                    QPushButton:disabled {
                        background-color: #bdc3c7;
                    }
                """)
