"""
Prompt Editor Widget - PyQt GUI equivalent of PromptEditor.jsx
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QTabWidget, QScrollArea, QFrame,
    QSplitter, QMessageBox, QInputDialog, QCheckBox, QComboBox,
    QFormLayout, QGroupBox, QSpacerItem, QSizePolicy, QStackedWidget,
    QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter, QTextDocument
from typing import Dict, List, Optional, Any
import re
import json
import hashlib
from datetime import datetime

from ..utils.db_client import DatabaseClient
from ..utils.prompt_improvement import PromptImprovementManager
from .version_comparison_dialog import VersionComparisonDialog
from .prompt_improvement_dialog import PromptImprovementDialog


class TokenCalculationThread(QThread):
    """Thread for calculating token count asynchronously"""
    
    finished = pyqtSignal(dict)  # Emits result dictionary
    
    def __init__(self, db_client: DatabaseClient, model: str, system_prompt: str, user_prompt: str):
        super().__init__()
        self.db_client = db_client
        self.model = model
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        
    def run(self):
        """Run token calculation in background"""
        try:
            result = self.db_client.calculate_tokens(
                model=self.model,
                system_prompt=self.system_prompt,
                user_prompt=self.user_prompt
            )
            self.finished.emit(result or {'success': False, 'error': 'Unknown error'})
        except Exception as e:
            self.finished.emit({
                'success': False,
                'error': str(e),
                'message': f'Error: {str(e)}'
            })


class ImprovePromptThread(QThread):
    """Thread for improving prompt using LLM"""
    
    finished = pyqtSignal(str)  # improved text
    error = pyqtSignal(str)     # error message
    
    def __init__(self, db_client: DatabaseClient, improvement_prompt: str, endpoint: Optional[Dict[str, Any]]):
        super().__init__()
        self.db_client = db_client
        self.improvement_prompt = improvement_prompt
        self.endpoint = endpoint
        
    def run(self):
        """Run the improvement call"""
        try:
            if not self.endpoint:
                self.error.emit("No LLM endpoint available for improvement")
                return
                
            # Prepare improvement prompt
            system_prompt = "You are an expert prompt engineer. Your task is to improve prompts to make them clearer, more effective, and better structured for LLMs. Provide only the improved prompt without any additional explanations or comments."
            
            # Prepare API request
            base_url = self.endpoint.get('baseUrl', '').rstrip('/')
            api_key = self.endpoint.get('apiKey', '')
            model = self.endpoint.get('defaultModel', 'gpt-3.5-turbo')
            
            if not base_url or not api_key:
                self.error.emit("Missing endpoint URL or API key")
                return
                
            # Make API call
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
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user', 
                        'content': self.improvement_prompt
                    }
                ],
                'temperature': 0.7
            }
            
            response = requests.post(
                chat_url,
                headers=headers,
                json=payload,
                timeout=60,
                verify=True
            )
            
            if response.status_code != 200:
                self.error.emit(f"Improvement API call failed: HTTP {response.status_code} - {response.text}")
                return
                
            result_data = response.json()
            
            # Extract improved content
            if 'choices' in result_data and result_data['choices']:
                improved_text = result_data['choices'][0].get('message', {}).get('content', '')
                if improved_text:
                    self.finished.emit(improved_text)
                else:
                    self.error.emit("No improved content received from API")
            else:
                self.error.emit("Invalid response format from improvement API")
                
        except requests.exceptions.Timeout:
            self.error.emit("Improvement request timed out after 1 minute")
        except requests.exceptions.ConnectionError:
            self.error.emit("Could not connect to LLM endpoint for improvement")
        except requests.exceptions.SSLError:
            self.error.emit("SSL certificate verification failed")
        except Exception as e:
            self.error.emit(f"Improvement error: {str(e)}")


class VariableHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for template variables"""
    
    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        
        # Variable format
        self.variable_format = QTextCharFormat()
        self.variable_format.setBackground(QColor(139, 92, 246, 60))  # Purple with transparency
        self.variable_format.setForeground(QColor(139, 92, 246))
        self.variable_format.setFontWeight(QFont.Weight.Bold)
        
    def highlightBlock(self, text: str):
        """Highlight template variables in the text"""
        # Pattern for {{variable_name}}
        pattern = r'\{\{([a-zA-Z_][a-zA-Z0-9_-]*)\}\}'
        
        for match in re.finditer(pattern, text):
            start = match.start()
            length = match.end() - start
            self.setFormat(start, length, self.variable_format)


class VariableEditor(QWidget):
    """Widget for editing template variables"""
    
    variables_changed = pyqtSignal(dict)  # variables dict
    
    def __init__(self):
        super().__init__()
        self.variables: Dict[str, str] = {}
        self.setup_ui()
    
    def create_edit_dialog(self, name: str, current_value: str) -> QDialog:
        """팝업 편집 다이얼로그 생성"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Variable: {{{{{name}}}}}")
        dialog.setMinimumSize(600, 400)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 헤더
        header_label = QLabel(f"Editing: {{{{{name}}}}}")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #212529;
                margin-bottom: 10px;
            }
        """)
        
        # 큰 텍스트 편집 영역
        text_edit = QTextEdit()
        text_edit.setPlainText(current_value)
        text_edit.setStyleSheet("""
            QTextEdit {
                font-size: 14px;
                color: #495057;
                padding: 12px;
                background-color: white;
                border: 2px solid #ced4da;
                border-radius: 6px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border-color: #80bdff;
            }
        """)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedSize(100, 36)
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        save_button = QPushButton("Save")
        save_button.setFixedSize(100, 36)
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        layout.addWidget(header_label)
        layout.addWidget(text_edit)
        layout.addLayout(button_layout)
        
        # 버튼 이벤트
        cancel_button.clicked.connect(dialog.reject)
        save_button.clicked.connect(dialog.accept)
        
        # 값 반환 메서드
        dialog.get_value = lambda: text_edit.toPlainText()
        
        return dialog
        
    def setup_ui(self):
        """Setup the variable editor UI"""
        layout = QVBoxLayout(self)
        
        # Add new variable section
        add_group = QGroupBox("Add Variable")
        add_layout = QFormLayout(add_group)
        
        self.var_name_input = QLineEdit()
        self.var_name_input.setPlaceholderText("Variable Name (e.g., topic, tone, audience)")
        
        self.var_value_input = QTextEdit()
        self.var_value_input.setPlaceholderText("Variable Value (supports multiline text)")
        self.var_value_input.setMaximumHeight(80)
        
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_variable)
        
        add_layout.addRow("Name:", self.var_name_input)
        add_layout.addRow("Value:", self.var_value_input)
        add_layout.addRow("", add_button)
        
        layout.addWidget(add_group)
        
        # Variables list - 밀도 개선을 위한 최적화된 스크롤 영역
        self.variables_scroll = QScrollArea()
        self.variables_scroll.setWidgetResizable(True)
        self.variables_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.variables_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
            }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #ced4da;
                border-radius: 3px;
                min-height: 20px;
            }
        """)
        
        self.variables_widget = QWidget()
        self.variables_layout = QVBoxLayout(self.variables_widget)
        self.variables_layout.setContentsMargins(8, 8, 8, 8)  # 최소 여백
        self.variables_layout.setSpacing(4)  # 카드 간 4px (6→4px 감소)
        self.variables_layout.addStretch()
        
        self.variables_scroll.setWidget(self.variables_widget)
        
        layout.addWidget(self.variables_scroll, 1)
        
    def add_variable(self):
        """Add a new variable"""
        name = self.var_name_input.text().strip()
        value = self.var_value_input.toPlainText()
        
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Variable name cannot be empty")
            return
            
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', name):
            QMessageBox.warning(self, "Invalid Input", 
                              "Variable name must start with a letter or underscore and contain only letters, numbers, underscores, and hyphens")
            return
            
        self.variables[name] = value
        self.var_name_input.clear()
        self.var_value_input.clear()
        
        self.refresh_variables_list()
        self.variables_changed.emit(self.variables)
        
    def remove_variable(self, name: str):
        """Remove a variable"""
        if name in self.variables:
            del self.variables[name]
            self.refresh_variables_list()
            self.variables_changed.emit(self.variables)
            
    def set_variables(self, variables):
        """Set the variables dictionary"""
        # Ensure variables is always a dictionary
        if isinstance(variables, dict):
            self.variables = variables.copy()
        elif isinstance(variables, list):
            # Convert list to empty dict - list format not supported
            print(f"Warning: Expected dict for variables, got list: {variables}")
            self.variables = {}
        else:
            print(f"Warning: Expected dict for variables, got {type(variables)}: {variables}")
            self.variables = {}
        self.refresh_variables_list()
        
    def refresh_variables_list(self):
        """Refresh the variables list display"""
        # Clear existing items
        for i in reversed(range(self.variables_layout.count() - 1)):  # Keep stretch
            child = self.variables_layout.itemAt(i)
            if child and child.widget():
                child.widget().deleteLater()
                
        # Add variable items - 밀도 개선된 카드 생성
        for name, value in self.variables.items():
            var_card = self.create_variable_card(name, value)
            self.variables_layout.insertWidget(
                self.variables_layout.count() - 1,  # Before stretch
                var_card
            )
            
        # Show empty message if no variables
        if not self.variables:
            empty_label = QLabel("No variables in prompt.\nUse {{variable_name}} format in your prompt.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #666; font-style: italic; padding: 40px;")
            self.variables_layout.insertWidget(0, empty_label)
            
    def create_variable_card(self, name: str, value: str) -> QWidget:
        """팝업 편집 기능이 있는 변수 카드"""
        # 카드 컨테이너 - 높이 고정
        card = QWidget()
        card.setFixedHeight(130)  # 110px → 130px로 증가 (Edit 버튼 공간)
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)  # 상하좌우 여백
        card_layout.setSpacing(6)  # 헤더와 텍스트 간 간격
        
        # ===== 헤더 영역 (변수명 + Edit + Delete 버튼) =====
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)  # 버튼 간 간격 줄임
        
        # 변수명 라벨
        var_name_label = QLabel(f"{{{{{name}}}}}")
        var_name_label.setFixedHeight(24)  # 라벨 높이 고정
        var_name_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: 600;
                color: #6f42c1;
                background-color: #f3e5ff;
                padding: 3px 8px;
                border-radius: 3px;
            }
        """)
        
        # Edit 버튼 추가
        edit_button = QPushButton("Edit")
        edit_button.setFixedSize(50, 28)  # 24 → 28px로 증가 (글씨 깨짐 방지)
        edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        # Delete 버튼 - 크기 증가로 글자 깨짐 방지
        delete_button = QPushButton("Delete")
        delete_button.setFixedSize(70, 28)  # 24 → 28px로 증가 (글씨 깨짐 방지)
        delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        delete_button.clicked.connect(lambda checked, n=name: self.remove_variable(n))
        
        header_layout.addWidget(var_name_label)
        header_layout.addStretch()  # 중간 공백
        header_layout.addWidget(edit_button)
        header_layout.addWidget(delete_button)
        
        # ===== Edit 버튼 클릭 이벤트 연결 =====
        def open_edit_dialog():
            dialog = self.create_edit_dialog(name, value_edit.toPlainText())
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_value = dialog.get_value()
                value_edit.setPlainText(new_value)
                # 변수 값 업데이트
                self.variables[name] = new_value
                self.variables_changed.emit(self.variables)
        
        edit_button.clicked.connect(open_edit_dialog)
        
        # ===== 값 입력 영역 - 카드 크기에 맞춰 조정 =====
        value_edit = QTextEdit()
        value_edit.setPlainText(value)
        
        # 카드 높이가 130px이므로 텍스트 영역은 80px 정도로 조정
        def adjust_text_height():
            # QTimer로 다음 이벤트 루프에서 실행 (정확한 크기 계산을 위해)
            QTimer.singleShot(10, lambda: calculate_and_set_height(value_edit))
        
        def calculate_and_set_height(edit):
            try:
                # 위젯 유효성 검사
                if not edit or not hasattr(edit, 'toPlainText'):
                    return
                
                # 위젯이 삭제되었는지 확인
                try:
                    test_access = edit.isVisible()  # 위젯 접근 테스트
                except RuntimeError:
                    # 위젯이 이미 삭제된 경우
                    # print("Widget was deleted, skipping height calculation")
                    return
                
                # 부모 위젯이 존재하는지 확인
                if not edit.parent():
                    # print("Widget has no parent, skipping height calculation")
                    return
                
                text = edit.toPlainText()
                
                # FontMetrics를 사용한 정확한 높이 계산
                font_metrics = edit.fontMetrics()
                line_height = font_metrics.height()
                
                # 줄 수 계산 (개행 문자 기준)
                lines = max(1, text.count('\n') + 1) if text else 1
                
                # 텍스트 래핑 고려 (위젯 너비 기반)
                if text and edit.width() > 0:
                    avg_char_width = font_metrics.averageCharWidth()
                    chars_per_line = max(1, (edit.width() - 20) // avg_char_width)  # 패딩 고려
                    
                    wrapped_lines = 0
                    for line in text.split('\n'):
                        wrapped_lines += max(1, len(line) // chars_per_line + (1 if len(line) % chars_per_line else 0))
                    
                    lines = max(lines, wrapped_lines)
                
                # 패딩과 여백을 고려한 총 높이 계산
                content_height = lines * line_height + 16  # 상하 패딩 16px
                
                # 카드 높이 130px에 맞춰 최소 50px, 최대 80px로 제한
                new_height = min(max(content_height, 50), 80)
                edit.setFixedHeight(int(new_height))
                
            except (RuntimeError, AttributeError) as e:
                # 위젯이 삭제되었거나 접근할 수 없는 경우
                print(f"Widget access error (likely deleted): {e}")
                return
            except Exception as e:
                # 기타 오류 발생 시 기본 높이로 설정 (안전 검사 추가)
                # print(f"Error calculating height: {e}")
                try:
                    if edit and hasattr(edit, 'setFixedHeight'):
                        edit.setFixedHeight(50)
                except (RuntimeError, AttributeError):
                    print("Could not set default height - widget deleted")
        
        # 텍스트 변경 시 높이 재조정
        value_edit.textChanged.connect(adjust_text_height)
        
        # 초기 로드 시 높이 설정 (위젯이 완전히 초기화된 후)
        QTimer.singleShot(50, lambda: calculate_and_set_height(value_edit))
        
        # 스크롤바는 필요할 때만 표시
        value_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        value_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        value_edit.setStyleSheet("""
            QTextEdit {
                font-size: 12px;
                color: #495057;
                padding: 6px 8px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 3px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #80bdff;
                background-color: white;
            }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #ced4da;
                border-radius: 3px;
            }
        """)
        
        # 값 변경 감지 및 업데이트
        value_edit.textChanged.connect(
            lambda n=name, edit=value_edit: self.on_variable_changed(n, edit.toPlainText())
        )
        
        # 레이아웃 조립
        card_layout.addLayout(header_layout)
        card_layout.addWidget(value_edit)
        
        return card
            
    def on_variable_changed(self, name: str, value: str):
        """Handle variable value change"""
        if name in self.variables:
            self.variables[name] = value
            self.variables_changed.emit(self.variables)


class VersionTimeline(QWidget):
    """Version timeline widget"""
    
    version_selected = pyqtSignal(str)  # version_id
    
    def __init__(self):
        super().__init__()
        self.versions: List[Dict[str, Any]] = []
        self.current_version_id: Optional[str] = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the version timeline UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Force main layout left alignment
        
        # Create scroll area for horizontal scrolling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setMaximumHeight(60)  # Fixed height to prevent vertical expansion
        self.scroll_area.setMinimumHeight(60)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Force scroll area left alignment
        
        # Apply modern scroll bar styling
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: rgba(0, 0, 0, 0.05);
                height: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background: rgba(0, 123, 255, 0.6);
                border-radius: 4px;
                min-width: 20px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: rgba(0, 123, 255, 0.8);
            }
            
            QScrollBar::handle:horizontal:pressed {
                background: rgba(0, 123, 255, 1.0);
            }
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
                height: 0px;
                background: none;
            }
            
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        # Create content widget for the timeline
        self.timeline_widget = QWidget()
        self.timeline_layout = QHBoxLayout(self.timeline_widget)
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_layout.setSpacing(4)
        self.timeline_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Force left alignment
        
        # Set the content widget in the scroll area
        self.scroll_area.setWidget(self.timeline_widget)
        
        # Add scroll area to main layout
        layout.addWidget(self.scroll_area)
        
    def set_versions(self, versions: List[Dict[str, Any]]):
        """Set the versions list"""
        self.versions = versions
        self.refresh_timeline()
        
    def set_current_version(self, version_id: Optional[str]):
        """Set the current version"""
        self.current_version_id = version_id
        self.refresh_timeline()
        
    def refresh_timeline(self):
        """Refresh the timeline display"""
        # Clear existing items from timeline layout
        for i in reversed(range(self.timeline_layout.count())):
            child = self.timeline_layout.itemAt(i)
            if child and child.widget():
                child.widget().deleteLater()
                
        if not self.versions:
            # Show empty message when no versions
            empty_label = QLabel("No versions available")
            empty_label.setStyleSheet("color: #999; font-style: italic; padding: 8px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.timeline_layout.addWidget(empty_label)
            
            # Set the timeline widget to minimum size when empty
            self.timeline_widget.setMinimumWidth(200)
            self.timeline_widget.setMaximumWidth(200)
            return
            
        # Calculate total width needed for all buttons and connectors
        total_width = 0
        button_count = len(self.versions)
        connector_count = max(0, button_count - 1)
        
        # Add version buttons with fixed width to prevent overflow
        for i, version in enumerate(self.versions):
            version_btn = QPushButton(version.get('name', f'v{i+1}'))
            version_btn.setCheckable(True)
            version_btn.setChecked(version['id'] == self.current_version_id)
            version_btn.setToolTip(f"Version: {version.get('name', '')}\nCreated: {version.get('createdAt', 'Unknown')}")
            
            # Set fixed size to prevent buttons from growing too large
            version_btn.setMinimumWidth(80)
            version_btn.setMaximumWidth(120)
            version_btn.setFixedHeight(28)
            total_width += 120  # Use max width for calculation
            
            if version['id'] == self.current_version_id:
                version_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #007bff;
                        color: white;
                        border: 2px solid #007bff;
                        border-radius: 6px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: bold;
                        text-align: left;
                    }
                """)
            else:
                version_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f8f9fa;
                        color: #495057;
                        border: 1px solid #dee2e6;
                        border-radius: 6px;
                        padding: 4px 8px;
                        font-size: 11px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #e9ecef;
                    }
                """)
                
            version_btn.clicked.connect(
                lambda checked, v_id=version['id']: self.version_selected.emit(v_id)
            )
            
            self.timeline_layout.addWidget(version_btn)
            
            # Add connector line (except for last item)
            if i < len(self.versions) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.VLine)  # Changed to VLine for horizontal layout
                line.setFrameShadow(QFrame.Shadow.Sunken)
                line.setStyleSheet("color: #dee2e6;")
                line.setFixedWidth(8)  # Fixed width for vertical line
                line.setMaximumHeight(20)
                self.timeline_layout.addWidget(line)
                total_width += 8
        
        # Set timeline widget to exact size needed - this prevents right alignment
        total_width += 20  # Add some padding
        self.timeline_widget.setMinimumWidth(total_width)
        self.timeline_widget.setMaximumWidth(total_width)
        
        # Force the layout to be compact and left-aligned
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_layout.setSpacing(4)
        
        # Update the timeline widget size immediately
        self.timeline_widget.updateGeometry()
        self.timeline_widget.adjustSize()


class PromptEditor(QWidget):
    """Main prompt editor widget"""
    
    # Signals
    version_changed = pyqtSignal(str, str)  # task_id, version_id
    content_changed = pyqtSignal()
    task_name_updated = pyqtSignal(str, str)  # task_id, new_name
    
    # 스타일 상수 정의
    EDIT_MODE_STYLES = {
        'description': """
            QTextEdit {
                font-size: 12px;
                color: #495057;
                padding: 8px;
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QTextEdit:focus {
                border-color: #80bdff;
                background-color: white;
            }
        """,
        'system': """
            QTextEdit {
                font-size: 12px;
                color: #495057;
                padding: 8px;
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QTextEdit:focus {
                border-color: #80bdff;
                background-color: white;
            }
        """,
        'main': """
            QTextEdit {
                font-size: 14px;
                color: #495057;
                padding: 12px;
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QTextEdit:focus {
                border-color: #80bdff;
                background-color: white;
            }
        """
    }
    
    PREVIEW_MODE_STYLES = {
        'description': """
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #007bff;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                color: #495057;
                padding: 8px;
                font-size: 12px;
            }
        """,
        'system': """
            QTextEdit {
                background-color: rgba(16, 185, 129, 0.1);
                border: 2px solid #10b981;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                color: #047857;
                padding: 8px;
                font-size: 12px;
            }
        """,
        'main': """
            QTextEdit {
                background-color: #fff8e1;
                border: 2px solid #ffc107;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                color: #856404;
                padding: 12px;
                font-size: 14px;
            }
        """
    }
    
    def __init__(self):
        super().__init__()
        
        self.db_client = DatabaseClient()
        self.current_task_id: Optional[str] = None
        self.current_version_id: Optional[str] = None
        self.task_data: Optional[Dict[str, Any]] = None
        self.versions: List[Dict[str, Any]] = []
        self.auto_save_timer = QTimer()
        self.original_splitter_sizes: List[int] = []  # Store original sizes
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self.auto_save)
        
        # Preview 모드 상태 관리
        self.is_preview_mode = False
        self.text_edits = {}  # QTextEdit 참조 저장
        self.original_contents = {}  # 원본 텍스트 내용 저장
        
        # 버전 비교 기능 추가
        self.selected_versions = []  # 선택된 버전들 (최대 2개)
        self.version_checkboxes = {}  # 체크박스 참조 저장
        self.compare_btn = None  # Compare 버튼 참조
        
        # 토큰 카운팅 기능
        self.token_cache = {}  # {cache_key: {"model": str, "count": int}}
        self.token_label = None  # 토큰 카운트 표시 라벨
        self.token_thread = None  # 토큰 계산 스레드
        
        # 번역 기능
        self.translation_cache = {}  # {cache_key: translated_text}
        self.translate_thread = None  # 번역 스레드
        
        # 변경사항 추적을 위한 원본 데이터 저장
        self.original_version_data: Optional[Dict[str, Any]] = None
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup the prompt editor UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header section
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f8f9fa; border-bottom: 1px solid #dee2e6;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        # Task title and actions - IMPROVED: Editable task name
        title_layout = QHBoxLayout()
        
        # Task name section with label and editable field
        task_name_section = QVBoxLayout()
        task_name_section.setSpacing(4)
        
        # Task name label
        task_name_label = QLabel("태스크 이름:")
        task_name_label.setStyleSheet("font-size: 12px; color: #666; font-weight: 500;")
        task_name_section.addWidget(task_name_label)
        
        # Editable task name field
        self.task_title_edit = QLineEdit("No Task Selected")
        self.task_title_edit.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                font-weight: bold;
                border: 1px solid transparent;
                background-color: transparent;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QLineEdit:hover {
                border: 1px solid #d0d0d0;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border: 1px solid #1a73e8;
                background-color: white;
            }
        """)
        self.task_title_edit.editingFinished.connect(self.on_task_name_changed)
        
        task_name_section.addWidget(self.task_title_edit)
        title_layout.addLayout(task_name_section)
        
        title_layout.addStretch()
        
        # Action buttons
        self.copy_version_btn = QPushButton("📋 Copy")
        self.copy_version_btn.clicked.connect(self.copy_version)
        self.copy_version_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
            QPushButton:pressed {
                background-color: #3c4043;
            }
        """)
        
        self.new_version_btn = QPushButton("🌿 New Version") 
        self.new_version_btn.clicked.connect(self.create_new_version)
        self.new_version_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        
        title_layout.addWidget(self.copy_version_btn)
        title_layout.addWidget(self.new_version_btn)
        
        header_layout.addLayout(title_layout)
        
        # Version selection - IMPROVED: Clean dropdown instead of timeline
        version_section = QVBoxLayout()
        version_section.setSpacing(4)
        
        # Version selection label
        version_label = QLabel("버전 선택:")
        version_label.setStyleSheet("font-size: 12px; color: #666; font-weight: 500;")
        version_section.addWidget(version_label)
        
        # Version dropdown
        self.version_selector = QComboBox()
        self.version_selector.setMinimumWidth(250)
        self.version_selector.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 14px;
                color: #333;
            }
            QComboBox:hover {
                border-color: #999;
            }
            QComboBox:focus {
                border-color: #1a73e8;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ccc;
                background-color: white;
                selection-background-color: #e3f2fd;
            }
        """)
        self.version_selector.currentTextChanged.connect(self.on_version_selection_changed)
        
        version_section.addWidget(self.version_selector)
        
        # Keep reference to original timeline for compatibility, but don't display it
        self.version_timeline = VersionTimeline()  # Hidden - for compatibility
        self.version_timeline.version_selected.connect(self.select_version)
        
        header_layout.addLayout(version_section)
        
        layout.addWidget(header_frame)
        
        # Main content - just the prompt editor (no tabs)
        self.prompt_content_widget = QWidget()
        
        layout.addWidget(self.prompt_content_widget, 1)
        
        # Store variables editor reference (will be moved to result viewer)
        self.variables_editor = VariableEditor()
        self.variables_editor.variables_changed.connect(self.on_variables_changed)
        
        # Initial empty state
        self.show_empty_state()
        
    def create_prompt_content(self, version_data: Dict[str, Any]) -> QWidget:
        """Create the prompt editing content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Back button header
        back_header = QFrame()
        back_header.setStyleSheet("background-color: #f8f9fa; border-bottom: 1px solid #dee2e6; padding: 8px;")
        back_layout = QHBoxLayout(back_header)
        back_layout.setContentsMargins(12, 8, 12, 8)
        
        # Back button
        back_btn = QPushButton("← Back to Versions")
        back_btn.clicked.connect(self.go_back_to_version_selection)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
            QPushButton:pressed {
                background-color: #3c4043;
            }
        """)
        
        # Current version info with editable name
        version_name = version_data.get('name', 'Untitled Version')
        
        # Create container for version info
        version_info_widget = QWidget()
        version_info_layout = QHBoxLayout(version_info_widget)
        version_info_layout.setContentsMargins(0, 0, 0, 0)
        version_info_layout.setSpacing(8)
        
        # Version label
        self.current_version_label = QLabel(f"Editing: {version_name}")
        self.current_version_label.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        version_info_layout.addWidget(self.current_version_label)
        
        # Edit name button
        edit_name_btn = QPushButton("📝")
        edit_name_btn.setToolTip("Edit version name")
        edit_name_btn.setMaximumSize(24, 24)
        edit_name_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 12px;
                font-size: 12px;
                color: #6c757d;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
                color: #495057;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        edit_name_btn.clicked.connect(self.edit_version_name)
        version_info_layout.addWidget(edit_name_btn)
        
        back_layout.addWidget(back_btn)
        back_layout.addStretch()
        back_layout.addWidget(version_info_widget)
        
        layout.addWidget(back_header)
        
        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Description section
        desc_group = QGroupBox("📝 Prompt Description")
        desc_group.setCheckable(True)
        desc_group.setChecked(True)
        desc_group.toggled.connect(lambda checked: self.toggle_group_content(desc_group, checked))
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(version_data.get('description', ''))
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Describe the purpose and usage of this prompt...")
        # 자동저장 비활성화: self.description_edit.textChanged.connect(self.schedule_auto_save)
        # 초기 Edit 모드 스타일 적용
        self.description_edit.setStyleSheet(self.EDIT_MODE_STYLES['description'])
        desc_layout.addWidget(self.description_edit)
        
        splitter.addWidget(desc_group)
        
        # System prompt section  
        system_group = QGroupBox("🤖 System Prompt")
        system_group.setCheckable(True)
        system_group.setChecked(True)
        system_group.toggled.connect(lambda checked: self.toggle_group_content(system_group, checked))
        system_layout = QVBoxLayout(system_group)
        
        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setPlainText(version_data.get('system_prompt', 'You are a helpful AI Assistant'))
        self.system_prompt_edit.setMaximumHeight(120)
        self.system_prompt_edit.setPlaceholderText("Define AI role and instructions...")
        # 자동저장 비활성화: self.system_prompt_edit.textChanged.connect(self.schedule_auto_save)
        # 초기 Edit 모드 스타일 적용
        self.system_prompt_edit.setStyleSheet(self.EDIT_MODE_STYLES['system'])
        system_layout.addWidget(self.system_prompt_edit)
        
        splitter.addWidget(system_group)
        
        # Main prompt section
        main_group = QGroupBox("💬 Main Prompt")
        main_group.setCheckable(True) 
        main_group.setChecked(True)
        main_group.toggled.connect(lambda checked: self.toggle_group_content(main_group, checked))
        main_layout = QVBoxLayout(main_group)
        
        self.main_prompt_edit = QTextEdit()
        self.main_prompt_edit.setPlainText(version_data.get('content', ''))
        self.main_prompt_edit.setPlaceholderText("Enter prompt... (Use {{variable_name}} for variables)")
        # 자동저장 비활성화: self.main_prompt_edit.textChanged.connect(self.schedule_auto_save)
        # 초기 Edit 모드 스타일 적용
        self.main_prompt_edit.setStyleSheet(self.EDIT_MODE_STYLES['main'])
        
        # Add syntax highlighting
        self.highlighter = VariableHighlighter(self.main_prompt_edit.document())
        
        main_layout.addWidget(self.main_prompt_edit)
        
        # QTextEdit 참조 저장 (새로운 preview 시스템용)
        self.text_edits = {
            'description': self.description_edit,
            'system': self.system_prompt_edit, 
            'main': self.main_prompt_edit
        }
        
        # Preview 모드 상태 초기화
        self.is_preview_mode = False
        self.original_contents = {}
        
        splitter.addWidget(main_group)
        
        # Set splitter proportions
        initial_sizes = [100, 120, 300]
        splitter.setSizes(initial_sizes)
        self.original_splitter_sizes = initial_sizes.copy()  # Store original sizes
        
        # Store reference to splitter for size management
        self.current_splitter = splitter
        
        layout.addWidget(splitter)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        # Token counter label (left side)
        self.token_label = QLabel("")
        self.token_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 12px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        self.token_label.setMinimumWidth(300)
        self.token_label.hide()  # Hidden initially
        actions_layout.addWidget(self.token_label)
        
        # Add stretch to push buttons to the right
        actions_layout.addStretch()
        
        self.preview_btn = QPushButton("👁️ Preview")
        self.preview_btn.setCheckable(True)
        self.preview_btn.clicked.connect(self.toggle_preview)
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: 2px solid transparent;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:checked {
                background-color: #0056b3;
                border: 2px solid #004085;
            }
        """)
        
        self.improve_btn = QPushButton("🔧 Improve")
        self.improve_btn.clicked.connect(self.improve_prompt)
        self.improve_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: 2px solid transparent;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        
        self.translate_btn = QPushButton("🌐 Translate")
        self.translate_btn.clicked.connect(self.translate_prompts)
        self.translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: 2px solid transparent;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_current_version)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: 2px solid transparent;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        
        actions_layout.addWidget(self.preview_btn)
        actions_layout.addWidget(self.improve_btn)
        actions_layout.addWidget(self.translate_btn)
        actions_layout.addWidget(self.save_btn)
        
        layout.addLayout(actions_layout)
        
        return widget
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Tab functionality removed - using single content area now
        
    def set_task_id(self, task_id: str):
        """Set the current task"""
        # Check for unsaved changes before switching tasks
        if self.has_unsaved_changes():
            reply = self.show_unsaved_changes_dialog()
            
            if reply == QMessageBox.StandardButton.Save:
                # Save current version before switching
                self.save_version(show_message=False)
            elif reply == QMessageBox.StandardButton.Cancel:
                # Don't switch tasks
                return
            # If Discard, proceed without saving
        
        self.current_task_id = task_id
        self.current_version_id = None
        
        # Clear original version data when switching tasks
        self.original_version_data = None
        
        self.load_task_data()
        
    def load_task_data(self):
        """Load task data from API"""
        if not self.current_task_id:
            return
            
        try:
            # Load task info
            tasks_response = self.db_client.get_tasks()
            if tasks_response:
                tasks = {t['id']: t for t in tasks_response}
                self.task_data = tasks.get(self.current_task_id)
                
            # Load versions
            versions_response = self.db_client.get_versions(self.current_task_id)
            self.versions = versions_response if versions_response else []
            
            # Update UI
            self.update_header()
            self.version_timeline.set_versions(self.versions)
            
            # Show version selection screen instead of auto-selecting first version
            if self.versions:
                self.show_version_selection_state()
            else:
                self.show_no_versions_state()
                
            # Load variables
            self.load_variables()
            
        except Exception as e:
            QMessageBox.warning(self, "Loading Error", f"Failed to load task data: {str(e)}")
            
    def load_variables(self):
        """Load template variables"""
        if not self.current_task_id:
            return
            
        try:
            variables = self.db_client.get_variables(self.current_task_id)
            self.variables_editor.set_variables(variables)
        except Exception as e:
            print(f"Failed to load variables: {e}")
            
    def update_header(self):
        """Update the header with task information"""
        if self.task_data:
            self.task_title_edit.setText(self.task_data.get('name', 'Untitled Task'))
        else:
            self.task_title_edit.setText("No Task Selected")
        
        # Update version selector
        self.update_version_selector()
    
    def update_version_selector(self):
        """Update the version selector dropdown"""
        # Clear existing items
        self.version_selector.blockSignals(True)  # Prevent triggering change events
        self.version_selector.clear()
        
        if not self.versions:
            self.version_selector.addItem("No versions available")
            self.version_selector.setEnabled(False)
        else:
            self.version_selector.setEnabled(True)
            
            # Add versions to combo box
            for version in self.versions:
                version_name = version.get('name', 'Untitled Version')
                version_id = version.get('id', '')
                
                # Create display text with name and creation date
                display_text = version_name
                created_at = version.get('createdAt', '')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                        display_text = f"{version_name} ({formatted_date})"
                    except:
                        pass
                
                self.version_selector.addItem(display_text, version_id)
        
        # Set current selection
        if self.current_version_id and self.versions:
            for i, version in enumerate(self.versions):
                if version.get('id') == self.current_version_id:
                    self.version_selector.setCurrentIndex(i)
                    break
        
        self.version_selector.blockSignals(False)
    
    def on_task_name_changed(self):
        """Handle task name change"""
        if not self.current_task_id or not self.task_data:
            return
            
        new_name = self.task_title_edit.text().strip()
        current_name = self.task_data.get('name', '')
        
        # Clear focus to unfocus the field when Enter is pressed
        self.task_title_edit.clearFocus()
        
        if new_name and new_name != current_name:
            try:
                # Update task name in database
                success = self.db_client.update_task(self.current_task_id, {'name': new_name})
                
                if success:
                    # Update local task data
                    self.task_data['name'] = new_name
                    print(f"Task name updated to: {new_name}")
                    
                    # Emit signal to notify other components (like task navigator)
                    self.task_name_updated.emit(self.current_task_id, new_name)
                else:
                    # Revert to original name if update failed
                    self.task_title_edit.setText(current_name)
                    print("Failed to update task name in database")
                    
            except Exception as e:
                print(f"Error updating task name: {e}")
                # Revert to original name
                self.task_title_edit.setText(current_name)
    
    def on_version_selection_changed(self, text):
        """Handle version selection change from dropdown"""
        if not text or text == "No versions available":
            return
            
        # Find the version ID for the selected item
        current_index = self.version_selector.currentIndex()
        if current_index >= 0 and current_index < len(self.versions):
            version_id = self.versions[current_index].get('id')
            if version_id and version_id != self.current_version_id:
                self.select_version(version_id)
            
    def select_version(self, version_id: str):
        """Select a version for editing"""
        # Exit preview mode if active
        self._exit_preview_mode()
        
        self.current_version_id = version_id
        self.version_timeline.set_current_version(version_id)
        
        # Find version data
        version_data = None
        for version in self.versions:
            if version['id'] == version_id:
                version_data = version
                break
                
        if version_data:
            self.show_version_editor(version_data)
        else:
            self.show_empty_state()
            
        # Emit version_changed signal to notify other components
        if self.current_task_id:
            self.version_changed.emit(self.current_task_id, version_id)
            
    def show_version_editor(self, version_data: Dict[str, Any]):
        """Show the version editor"""
        try:
            # Clear existing content from prompt content widget
            self.clear_widget_completely(self.prompt_content_widget)
            
            # Wait for deletion to complete
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            
            # 원본 버전 데이터 저장 (변경사항 감지용)
            self.original_version_data = {
                'description': version_data.get('description', ''),
                'system_prompt': version_data.get('system_prompt', 'You are a helpful AI Assistant'),
                'content': version_data.get('content', '')
            }
            
            # Create new prompt content
            prompt_content = self.create_prompt_content(version_data)
            
            # Add content to widget using safe layout setting
            self._ensure_widget_layout(self.prompt_content_widget)
            self.prompt_content_widget.layout().addWidget(prompt_content)
            
            # Show the content widget
            self.prompt_content_widget.setVisible(True)
            
            # Enable preview functionality since we now have editor widgets
            self._enable_preview_button()
            
        except Exception as e:
            print(f"Error in show_version_editor: {e}")
            # Fallback: create minimal content
            self.show_empty_state()
        
    def show_version_selection_state(self):
        """Show version selection state when versions are available"""
        try:
            # Reset version selection state when entering this screen
            self.reset_version_selection()
            
            # Disable updates to prevent flickering
            self.prompt_content_widget.setUpdatesEnabled(False)
            
            # Show the content widget (but with version selection state)
            self.prompt_content_widget.setVisible(True)
            
            # Clear existing content
            self.clear_widget_completely(self.prompt_content_widget)
                
            selection_widget = QWidget()
            selection_layout = QVBoxLayout(selection_widget)
            selection_layout.setContentsMargins(20, 20, 20, 20)
            
            # Header section
            header_widget = QWidget()
            header_layout = QVBoxLayout(header_widget)
            header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Icon
            icon_label = QLabel("📚")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("font-size: 48px; margin: 10px;")
            
            # Title
            title_label = QLabel("Select a Version")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("color: #333; font-size: 18px; font-weight: bold; margin-bottom: 8px;")
            
            # Message
            message_label = QLabel("Choose a version below to start editing your prompt.")
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet("color: #666; font-size: 14px; margin-bottom: 20px;")
            
            header_layout.addWidget(icon_label)
            header_layout.addWidget(title_label)
            header_layout.addWidget(message_label)
            
            selection_layout.addWidget(header_widget)
            
            # Compare button section
            compare_section = QWidget()
            compare_layout = QHBoxLayout(compare_section)
            compare_layout.setContentsMargins(0, 10, 0, 10)
            
            # Info label
            compare_info_label = QLabel("Select 2 versions to compare:")
            compare_info_label.setStyleSheet("color: #666; font-size: 12px;")
            compare_layout.addWidget(compare_info_label)
            
            compare_layout.addStretch()
            
            # Compare versions button
            self.compare_btn = QPushButton("⚖️ Compare Versions")
            self.compare_btn.setEnabled(False)  # Disabled initially
            self.compare_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover:enabled {
                    background-color: #5a6268;
                }
                QPushButton:pressed:enabled {
                    background-color: #545b62;
                }
                QPushButton:enabled {
                    background-color: #007bff;
                }
                QPushButton:enabled:hover {
                    background-color: #0056b3;
                }
                QPushButton:disabled {
                    background-color: #e9ecef;
                    color: #adb5bd;
                }
            """)
            self.compare_btn.clicked.connect(self.open_version_comparison)
            compare_layout.addWidget(self.compare_btn)
            
            selection_layout.addWidget(compare_section)
            
            # Version list (like variables editor)
            versions_scroll = QScrollArea()
            versions_scroll.setWidgetResizable(True)
            versions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            versions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            
            versions_widget = QWidget()
            versions_layout = QVBoxLayout(versions_widget)
            versions_layout.setContentsMargins(10, 10, 10, 10)
            versions_layout.setSpacing(8)
            versions_layout.addStretch()  # Add stretch at the end
            
            # Create version items (stacked vertically)
            for version in self.versions:
                version_item = self.create_version_item(version)
                versions_layout.insertWidget(
                    versions_layout.count() - 1,  # Before stretch
                    version_item
                )
            
            versions_scroll.setWidget(versions_widget)
            selection_layout.addWidget(versions_scroll, 1)
            
            # Add content to widget using safe layout setting
            self._ensure_widget_layout(self.prompt_content_widget)
            self.prompt_content_widget.layout().addWidget(selection_widget)
            
            # Re-enable updates and show content
            self.prompt_content_widget.setUpdatesEnabled(True)
            
            # Disable preview functionality in selection mode
            self._disable_preview_button()
            
        except Exception as e:
            print(f"Error in show_version_selection_state: {e}")
            # Ensure updates are re-enabled even if error occurs
            try:
                self.prompt_content_widget.setUpdatesEnabled(True)
            except:
                pass

    def create_version_item(self, version: Dict[str, Any]) -> QWidget:
        """Create a version selection item with checkbox for comparison"""
        item_frame = QFrame()
        item_frame.setFrameStyle(QFrame.Shape.Box)
        item_frame.setStyleSheet("""
            QFrame { 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                padding: 8px;
                background-color: white;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border-color: #007bff;
            }
        """)
        
        item_layout = QVBoxLayout(item_frame)
        item_layout.setSpacing(8)
        
        # Header with version name and actions
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        # Checkbox for comparison selection
        version_checkbox = QCheckBox()
        version_checkbox.setToolTip("Select for comparison")
        
        # Fix closure issue by using default parameter to capture version_id
        version_id = version['id']  # Capture the ID in local variable
        
        # Ensure checkbox is properly initialized
        version_checkbox.setChecked(False)  # Explicitly set to unchecked
        version_checkbox.setTristate(False)  # Disable tristate
        
        # Debug: Log checkbox creation
        # print(f"🏗️ Created checkbox for {version_id}: initial_state={version_checkbox.isChecked()}")
        
        # Use toggled signal instead of stateChanged for better reliability
        version_checkbox.toggled.connect(
            lambda checked, v_id=version_id: self.on_version_checkbox_changed(v_id, checked)
        )
        
        # Store checkbox reference
        self.version_checkboxes[version_id] = version_checkbox
        header_layout.addWidget(version_checkbox)
        
        # Version name with icon (combined to avoid extra widgets)
        version_name = version.get('name', 'Untitled Version')
        name_label = QLabel(f"📄 {version_name}")
        name_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 123, 255, 0.2);
                color: #007bff;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-family: monospace;
            }
        """)
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        
        # Select button
        select_btn = QPushButton("Select")
        select_btn.setProperty("class", "primary")
        select_btn.setMaximumWidth(80)
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        select_btn.clicked.connect(lambda: self.select_version(version['id']))
        header_layout.addWidget(select_btn)
        
        item_layout.addLayout(header_layout)
        
        # Version details
        details_layout = QHBoxLayout()
        
        # Version ID
        version_id = version.get('id', '')
        if len(version_id) > 20:
            version_id = version_id[:17] + "..."
        id_label = QLabel(f"ID: {version_id}")
        id_label.setStyleSheet("font-size: 11px; color: #6c757d; font-family: monospace;")
        details_layout.addWidget(id_label)
        
        details_layout.addStretch()
        
        # Created date
        created_at = version.get('createdAt', '')
        if created_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_date = "Unknown date"
        else:
            formatted_date = "Unknown date"
            
        date_label = QLabel(f"📅 {formatted_date}")
        date_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        details_layout.addWidget(date_label)
        
        item_layout.addLayout(details_layout)
        
        # Content preview (like variable value)
        content = version.get('content', '')
        if content:
            if len(content) > 100:
                content = content[:97] + "..."
        else:
            content = "No content"
            
        content_edit = QLabel(content)
        content_edit.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                color: #495057;
                font-family: monospace;
            }
        """)
        content_edit.setWordWrap(True)
        content_edit.setMaximumHeight(60)
        item_layout.addWidget(content_edit)
        
        # Store version data
        item_frame.version_data = version
        
        # Make entire item clickable
        def item_clicked(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.select_version(version['id'])
        
        item_frame.mousePressEvent = item_clicked
        
        return item_frame

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        if not self.original_version_data:
            return False
        
        try:
            # Get current content from editors
            current_description = getattr(self, 'description_edit', None)
            current_system = getattr(self, 'system_prompt_edit', None)
            current_main = getattr(self, 'main_prompt_edit', None)
            
            if not all([current_description, current_system, current_main]):
                return False
            
            # Compare with original
            return (
                current_description.toPlainText() != self.original_version_data.get('description', '') or
                current_system.toPlainText() != self.original_version_data.get('system_prompt', '') or
                current_main.toPlainText() != self.original_version_data.get('content', '')
            )
        except Exception as e:
            print(f"Error checking unsaved changes: {e}")
            return False
    
    def show_unsaved_changes_dialog(self) -> QMessageBox.StandardButton:
        """Show dialog asking user about unsaved changes"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("저장하지 않은 변경사항")
        msg_box.setText("저장하지 않은 변경사항이 있습니다.")
        msg_box.setInformativeText("변경사항을 저장하시겠습니까?")
        
        # Add buttons
        save_button = msg_box.addButton("저장", QMessageBox.ButtonRole.AcceptRole)
        discard_button = msg_box.addButton("저장하지 않음", QMessageBox.ButtonRole.DestructiveRole)
        cancel_button = msg_box.addButton("취소", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.setDefaultButton(save_button)
        msg_box.exec()
        
        # Return the clicked button
        clicked = msg_box.clickedButton()
        if clicked == save_button:
            return QMessageBox.StandardButton.Save
        elif clicked == discard_button:
            return QMessageBox.StandardButton.Discard
        else:
            return QMessageBox.StandardButton.Cancel
    
    def go_back_to_version_selection(self):
        """Go back to version selection screen"""
        try:
            # 변경사항 확인
            if self.has_unsaved_changes():
                reply = self.show_unsaved_changes_dialog()
                
                if reply == QMessageBox.StandardButton.Save:
                    # 저장 후 이동
                    self.save_version(show_message=False)
                elif reply == QMessageBox.StandardButton.Discard:
                    # 저장하지 않고 이동
                    pass
                else:  # Cancel
                    # 현재 화면 유지
                    return
            
            # Exit preview mode if active
            self._exit_preview_mode()
            
            # Clear current version selection
            self.current_version_id = None
            self.version_timeline.set_current_version(None)
            
            # 원본 데이터 클리어
            self.original_version_data = None
            
            # Show version selection state
            if self.versions:
                self.show_version_selection_state()
            else:
                self.show_no_versions_state()
                
        except Exception as e:
            print(f"Error in go_back_to_version_selection: {e}")

    def show_no_versions_state(self):
        """Show state when no versions exist - prompt to create new version"""
        try:
            # Show the content widget (but with no versions state)
            self.prompt_content_widget.setVisible(True)
            
            # Clear existing content
            self.clear_widget_completely(self.prompt_content_widget)
            
            # Wait for deletion to complete
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
                
            no_versions_widget = QWidget()
            no_versions_layout = QVBoxLayout(no_versions_widget)
            no_versions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Icon
            icon_label = QLabel("📝")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("font-size: 48px; margin: 20px;")
            
            # Title
            title_label = QLabel("No Prompt Versions Found")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("color: #333; font-size: 18px; font-weight: bold; margin-bottom: 8px;")
            
            # Message
            message_label = QLabel("This task doesn't have any prompt versions yet.\nCreate a new version to get started!")
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet("color: #666; font-size: 14px; line-height: 1.5; margin-bottom: 20px;")
            
            # Create version button
            create_version_btn = QPushButton("🌿 Create New Version")
            create_version_btn.clicked.connect(self.create_new_version)
            create_version_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 160px;
                }
                QPushButton:hover {
                    background-color: #218838;
                    transform: translateY(-1px);
                }
                QPushButton:pressed {
                    background-color: #1e7e34;
                }
            """)
            
            no_versions_layout.addWidget(icon_label)
            no_versions_layout.addWidget(title_label)
            no_versions_layout.addWidget(message_label)
            no_versions_layout.addWidget(create_version_btn)
            
            # Add content to widget using safe layout setting
            self._ensure_widget_layout(self.prompt_content_widget)
            self.prompt_content_widget.layout().addWidget(no_versions_widget)
            
            # Disable preview functionality when no versions exist
            self._disable_preview_button()
            
        except Exception as e:
            print(f"Error in show_no_versions_state: {e}")

    def show_empty_state(self):
        """Show empty state when no version is selected"""
        try:
            # Show the content widget (but with empty state)
            self.prompt_content_widget.setVisible(True)
            
            # Clear existing content
            self.clear_widget_completely(self.prompt_content_widget)
            
            # Wait for deletion to complete
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
                
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            icon_label = QLabel("☝️")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("font-size: 48px; margin: 20px;")
            
            message_label = QLabel("Select a version from the timeline above to start editing.")
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet("color: #666; font-size: 14px;")
            
            empty_layout.addWidget(icon_label)
            empty_layout.addWidget(message_label)
            
            # Add content to widget using safe layout setting
            self._ensure_widget_layout(self.prompt_content_widget)
            self.prompt_content_widget.layout().addWidget(empty_widget)
            
            # Disable preview functionality in empty state
            self._disable_preview_button()
            
        except Exception as e:
            print(f"Error in show_empty_state: {e}")
        
    def clear_widget_completely(self, widget):
        """Completely clear a widget of all content with minimal flickering"""
        try:
            # Disable updates to prevent flickering during cleanup
            widget.setUpdatesEnabled(False)
            
            # Clear layout contents but keep the layout object
            if widget.layout():
                layout = widget.layout()
                # Remove all items from the layout
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().hide()
                        child.widget().deleteLater()
                    elif child.layout():
                        self._clear_layout_recursive(child.layout())
            
            # Re-enable updates after cleanup is complete
            widget.setUpdatesEnabled(True)
            
        except Exception as e:
            print(f"Error in clear_widget_completely: {e}")
            # Ensure updates are re-enabled even if error occurs
            try:
                widget.setUpdatesEnabled(True)
            except:
                pass
    
    def _ensure_widget_layout(self, widget):
        """Ensure widget has a layout, create if needed"""
        try:
            if widget.layout() is None:  # More precise check for None
                content_layout = QVBoxLayout()
                content_layout.setContentsMargins(0, 0, 0, 0)
                widget.setLayout(content_layout)
            # If layout already exists, don't try to set it again
        except Exception as e:
            print(f"Error in _ensure_widget_layout: {e}")
    
    def _enable_preview_button(self):
        """Enable preview button when editing widgets are available"""
        try:
            if hasattr(self, 'preview_btn'):
                # Find preview button in header timeline section
                self.preview_btn = self._find_preview_button_in_header()
                if self.preview_btn:
                    self.preview_btn.setEnabled(True)
                    self.preview_btn.setToolTip("Preview the prompt with current values")
        except Exception as e:
            print(f"Error enabling preview button: {e}")
    
    def _disable_preview_button(self):
        """Disable preview button when no editing widgets are available"""
        try:
            if hasattr(self, 'preview_btn'):
                # Find preview button in header timeline section
                self.preview_btn = self._find_preview_button_in_header()
                if self.preview_btn:
                    self.preview_btn.setEnabled(False)
                    self.preview_btn.setChecked(False)  # Reset state
                    self.preview_btn.setText("👁️ Preview")
                    self.preview_btn.setToolTip("Preview not available - select a version to edit")
        except Exception as e:
            print(f"Error disabling preview button: {e}")
    
    def _find_preview_button_in_header(self):
        """Find the preview button in the current editor content"""
        try:
            # Search for preview button in the current prompt content
            if hasattr(self, 'prompt_content_widget') and self.prompt_content_widget:
                for child in self.prompt_content_widget.findChildren(QPushButton):
                    if "Preview" in child.text() or "Edit Mode" in child.text():
                        return child
            return None
        except Exception as e:
            print(f"Error finding preview button: {e}")
            return None
    
    def _clear_layout_recursive(self, layout):
        """Recursively clear a layout"""
        try:
            if not layout:
                return
                
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().hide()
                    child.widget().deleteLater()
                elif child.layout():
                    self._clear_layout_recursive(child.layout())
            
            # Don't delete the layout itself, just clear its contents
            # Deleting layouts can cause Qt errors
            
        except Exception as e:
            print(f"Error in recursive layout clear: {e}")
    
    def toggle_group_content(self, group_box, checked):
        """Toggle visibility of group box content"""
        try:
            # Get the layout of the group box
            layout = group_box.layout()
            if not layout:
                return
            
            # Use stored splitter reference if available
            splitter = getattr(self, 'current_splitter', None)
            
            # Find group index in splitter
            group_index = -1
            if splitter:
                for i in range(splitter.count()):
                    if splitter.widget(i) == group_box:
                        group_index = i
                        break
            
            # Toggle visibility of all child widgets
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    widget.setVisible(checked)
            
            # Update the group box properties
            if checked:
                # When expanding, restore normal size policy
                group_box.setSizePolicy(
                    QSizePolicy.Policy.Preferred,
                    QSizePolicy.Policy.Expanding
                )
                group_box.setMinimumHeight(0)
                group_box.setMaximumHeight(16777215)  # Default max height
            else:
                # When collapsing, set fixed height to title bar only
                group_box.setSizePolicy(
                    QSizePolicy.Policy.Preferred,
                    QSizePolicy.Policy.Fixed
                )
                # Set height to just show the title (approximately 35px for better visibility)
                group_box.setFixedHeight(35)
            
            # Control splitter sizes to prevent other sections from expanding
            if splitter and group_index >= 0 and hasattr(self, 'original_splitter_sizes'):
                def adjust_splitter_sizes():
                    try:
                        if not checked:
                            # When collapsing: set collapsed size to minimum, keep others at original ratio
                            current_sizes = splitter.sizes()
                            total_available = sum(current_sizes)
                            collapsed_size = 35
                            
                            # Calculate remaining space for other sections
                            remaining_space = total_available - collapsed_size
                            
                            # Distribute remaining space to other sections based on original ratios
                            original_total = sum(self.original_splitter_sizes)
                            other_original_total = original_total - self.original_splitter_sizes[group_index]
                            
                            new_sizes = []
                            for i in range(len(current_sizes)):
                                if i == group_index:
                                    new_sizes.append(collapsed_size)
                                else:
                                    if other_original_total > 0:
                                        ratio = self.original_splitter_sizes[i] / other_original_total
                                        new_sizes.append(max(50, int(remaining_space * ratio)))  # Minimum 50px
                                    else:
                                        new_sizes.append(max(50, remaining_space // (len(current_sizes) - 1)))
                            
                            splitter.setSizes(new_sizes)
                        else:
                            # When expanding: restore original proportions
                            splitter.setSizes(self.original_splitter_sizes.copy())
                    except Exception as e:
                        print(f"Error adjusting splitter sizes: {e}")
                
                # Apply size changes after layout update
                QTimer.singleShot(50, adjust_splitter_sizes)
                
            # Force layout update
            group_box.updateGeometry()
            if splitter:
                splitter.updateGeometry()
            
        except Exception as e:
            print(f"Error toggling group content: {e}")
    
    def clear_widget_layout(self, widget):
        """Clear all children from a widget's layout"""
        if widget.layout():
            while widget.layout().count():
                child = widget.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    self._clear_layout(child.layout())
                    
    def _clear_layout(self, layout):
        """Recursively clear a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
        
    def toggle_preview(self):
        """새로운 개선된 Preview 모드 토글"""
        try:
            # QTextEdit 위젯들이 사용 가능한지 확인
            if not self.text_edits or not all(self.text_edits.values()):
                print("QTextEdit widgets not available - cannot toggle preview")
                return
            
            # Preview 버튼 찾기
            preview_btn = self._find_preview_button_in_header()
            if not preview_btn:
                print("Preview button not found - cannot toggle preview")
                return
                
            # Preview 모드 상태 토글
            self.is_preview_mode = not self.is_preview_mode
            
            if self.is_preview_mode:
                # Preview 모드로 전환
                self.apply_preview_mode()
                preview_btn.setText("✏️ Edit Mode")
                
                # 토큰 계산 시작
                self.calculate_token_count()
                
                print("Switched to Preview mode")
            else:
                # Edit 모드로 전환
                self.apply_edit_mode()
                preview_btn.setText("👁️ Preview")
                
                # 토큰 라벨 숨기기
                if self.token_label:
                    self.token_label.hide()
                
                print("Switched to Edit mode")
                
            # 버튼 체크 상태 업데이트
            preview_btn.setChecked(self.is_preview_mode)
                
        except Exception as e:
            print(f"Error in toggle_preview: {e}")
            # 오류 발생 시 안전한 상태로 복구
            self.is_preview_mode = False
            if preview_btn:
                try:
                    preview_btn.setChecked(False)
                    preview_btn.setText("👁️ Preview")
                except:
                    pass
    
    def calculate_token_count(self):
        """Calculate token count for current prompt"""
        try:
            if not self.token_label:
                return
            
            # Get current prompts
            system_prompt = self.text_edits['system'].toPlainText() if 'system' in self.text_edits else ""
            user_prompt = self.text_edits['main'].toPlainText() if 'main' in self.text_edits else ""
            
            # Get active endpoint and model
            endpoints_data = self.db_client.get_llm_endpoints()
            active_endpoint_id = endpoints_data.get('activeEndpointId')
            
            if not active_endpoint_id:
                self.token_label.setText("⚠️ No active LLM endpoint configured")
                self.token_label.show()
                return
            
            # Find active endpoint
            active_endpoint = None
            for ep in endpoints_data.get('endpoints', []):
                if ep.get('id') == active_endpoint_id:
                    active_endpoint = ep
                    break
            
            if not active_endpoint:
                self.token_label.setText("⚠️ Active endpoint not found")
                self.token_label.show()
                return
            
            model = active_endpoint.get('defaultModel', 'unknown')
            
            # Generate cache key
            cache_key = self._get_cache_key(model, system_prompt, user_prompt)
            
            # Check cache
            if cache_key in self.token_cache:
                cached_data = self.token_cache[cache_key]
                self._display_token_count(cached_data['model'], cached_data['count'])
                return
            
            # Show loading state
            self.token_label.setText("⏳ Calculating tokens...")
            self.token_label.show()
            
            # Start token calculation thread
            self.token_thread = TokenCalculationThread(
                self.db_client,
                model,
                system_prompt,
                user_prompt
            )
            self.token_thread.finished.connect(
                lambda result: self.on_token_calculation_finished(result, cache_key)
            )
            self.token_thread.start()
            
        except Exception as e:
            print(f"Error calculating token count: {e}")
            if self.token_label:
                error_msg = str(e).lower()
                if 'connection' in error_msg or 'connect' in error_msg:
                    self.token_label.setText("❌ Backend server not running (port 8000)")
                else:
                    self.token_label.setText(f"❌ Error: {str(e)}")
                self.token_label.show()
    
    def _get_cache_key(self, model: str, system_prompt: str, user_prompt: str) -> str:
        """Generate cache key for token count"""
        content = f"{model}|{system_prompt}|{user_prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def on_token_calculation_finished(self, result: dict, cache_key: str):
        """Handle token calculation result"""
        try:
            if result.get('success'):
                token_count = result.get('token_count', 0)
                model = result.get('model', 'unknown')
                
                # Cache the result
                self.token_cache[cache_key] = {
                    'model': model,
                    'count': token_count
                }
                
                # Display result
                self._display_token_count(model, token_count)
                
            else:
                error_msg = result.get('message', result.get('error', 'Unknown error'))
                self.token_label.setText(f"❌ {error_msg}")
                self.token_label.show()
                
        except Exception as e:
            print(f"Error handling token calculation result: {e}")
            if self.token_label:
                self.token_label.setText(f"❌ Error: {str(e)}")
                self.token_label.show()
    
    def _display_token_count(self, model: str, token_count: int):
        """Display token count in label"""
        try:
            if not self.token_label:
                return
            
            # Format number with commas
            formatted_count = f"{token_count:,}"
            
            # Display format: model: xxx / total token count: xxx,xxx
            display_text = f"model: {model} / total token count: {formatted_count}"
            
            self.token_label.setText(display_text)
            self.token_label.show()
            
        except Exception as e:
            print(f"Error displaying token count: {e}")
    
    def _protect_placeholders(self, text: str) -> tuple[str, dict]:
        """
        Placeholder를 임시 토큰으로 치환하여 보호
        Returns: (protected_text, placeholder_map)
        """
        placeholder_map = {}
        protected_text = text
        
        # {{변수명}} 패턴 추출
        pattern = r'\{\{([a-zA-Z_][a-zA-Z0-9_-]*)\}\}'
        matches = list(re.finditer(pattern, text))
        
        # 역순으로 치환 (인덱스 유지를 위해)
        for i, match in enumerate(reversed(matches)):
            placeholder = match.group(0)  # {{변수명}}
            token = f"PLACEHOLDER_TOKEN_{len(matches)-1-i}_END"
            placeholder_map[token] = placeholder
            
            # 텍스트에서 placeholder를 토큰으로 치환
            protected_text = protected_text[:match.start()] + token + protected_text[match.end():]
        
        return protected_text, placeholder_map
    
    def _restore_placeholders(self, text: str, placeholder_map: dict) -> str:
        """
        임시 토큰을 원래 placeholder로 복원
        """
        restored_text = text
        
        for token, placeholder in placeholder_map.items():
            restored_text = restored_text.replace(token, placeholder)
        
        return restored_text
    
    def apply_preview_mode(self):
        """Preview 모드 스타일과 내용 적용"""
        try:
            # 원본 내용 저장 (한 번만)
            if not self.original_contents:
                self.original_contents = {
                    'description': self.text_edits['description'].toPlainText(),
                    'system': self.text_edits['system'].toPlainText(),
                    'main': self.text_edits['main'].toPlainText()
                }
            
            # 각 QTextEdit에 Preview 모드 적용
            for edit_type, text_edit in self.text_edits.items():
                if text_edit and edit_type in self.original_contents:
                    # 변수가 적용된 내용으로 렌더링
                    rendered_content = self.render_prompt_with_variables(
                        self.original_contents[edit_type]
                    )
                    
                    # Preview 스타일과 내용 적용
                    text_edit.setPlainText(rendered_content)
                    text_edit.setReadOnly(True)
                    text_edit.setStyleSheet(self.PREVIEW_MODE_STYLES[edit_type])
                    
            print("Preview mode applied successfully")
            
        except Exception as e:
            print(f"Error applying preview mode: {e}")
    
    def apply_edit_mode(self):
        """Edit 모드 스타일과 내용 복원"""
        try:
            # 각 QTextEdit에 Edit 모드 복원
            for edit_type, text_edit in self.text_edits.items():
                if text_edit and edit_type in self.original_contents:
                    # 원본 내용과 스타일 복원
                    text_edit.setReadOnly(False)
                    text_edit.setPlainText(self.original_contents[edit_type])
                    text_edit.setStyleSheet(self.EDIT_MODE_STYLES[edit_type])
            
            # 원본 내용 캐시 클리어
            self.original_contents = {}
            
            print("Edit mode applied successfully")
            
        except Exception as e:
            print(f"Error applying edit mode: {e}")
    
    def _exit_preview_mode(self):
        """Exit preview mode if currently active"""
        try:
            if hasattr(self, 'preview_btn') and self.preview_btn and self.preview_btn.isChecked():
                self.preview_btn.setChecked(False)
                self.switch_to_edit_mode()
                self.preview_btn.setText("👁️ Preview")
        except Exception as e:
            print(f"Error exiting preview mode: {e}")
            
    def show_preview(self):
        """Show the preview content (deprecated - now using inline preview)"""
        print("show_preview called - now using inline preview mode")
        pass
        
    def render_prompt_with_variables(self, template: str) -> str:
        """Render prompt template with current variable values"""
        if not self.current_task_id:
            return template
            
        try:
            # Get current variables from the variables tab
            variables = {}
            if hasattr(self, 'variables_editor') and self.variables_editor:
                variables = self.variables_editor.variables
            
            # If no variables from editor, try to get from database
            if not variables:
                variables = self.db_client.get_variables(self.current_task_id)
            
            print(f"Rendering template with variables: {variables}")
            
            # Replace variables in template
            rendered = template
            if variables and isinstance(variables, dict):
                for key, value in variables.items():
                    placeholder = f"{{{{{key}}}}}"
                    if placeholder in rendered:
                        replacement = str(value) if value else f"[Missing: {key}]"
                        rendered = rendered.replace(placeholder, replacement)
                        print(f"Replaced {placeholder} with {replacement}")
            
            return rendered
        except Exception as e:
            print(f"Error rendering prompt: {e}")
            return template
                
    def schedule_auto_save(self):
        """Schedule auto-save"""
        self.auto_save_timer.start(2000)  # 2 seconds delay
        
    def auto_save(self):
        """Auto-save current content"""
        self.save_version()
        
    def force_save(self):
        """Force save current content (deprecated - use save_current_version)"""
        self.save_current_version()
        
    def save_version(self, show_message: bool = False):
        """Save the current version"""
        if not self.current_task_id or not self.current_version_id:
            return
            
        try:
            # Get current version data to preserve name
            current_version = None
            for version in self.versions:
                if version['id'] == self.current_version_id:
                    current_version = version
                    break
            
            if not current_version:
                if show_message:
                    QMessageBox.warning(self, "Save Error", "Current version not found")
                print("Error: Current version not found in versions list")
                return
            
            updates = {
                'name': current_version.get('name', 'Untitled Version'),  # Preserve name
                'content': getattr(self, 'main_prompt_edit', QTextEdit()).toPlainText(),
                'system_prompt': getattr(self, 'system_prompt_edit', QTextEdit()).toPlainText(),
                'description': getattr(self, 'description_edit', QTextEdit()).toPlainText()
            }
            
            # Call the database client's update_version method correctly
            success = self.db_client.update_version(self.current_version_id, **updates)
            
            if success:
                if show_message:
                    QMessageBox.information(self, "Saved", "Version saved successfully!")
                print(f"Version {self.current_version_id} saved successfully")
                # Update the current version data in memory (without reloading UI)
                self._update_current_version_data()
                
                # 저장 성공 시 원본 데이터도 업데이트 (자동저장 후 변경사항 감지 초기화)
                if self.original_version_data:
                    self.original_version_data = {
                        'description': updates['description'],
                        'system_prompt': updates['system_prompt'],
                        'content': updates['content']
                    }
            else:
                if show_message:
                    QMessageBox.warning(self, "Save Error", "Failed to save version to database")
                print("Error: Failed to save version to database")
                
        except Exception as e:
            error_msg = f"Failed to save version: {str(e)}"
            if show_message:
                QMessageBox.warning(self, "Save Error", error_msg)
            print(f"Error updating version: {e}")

    def save_current_version(self):
        """Save current version and show success message"""
        self.save_version(show_message=True)
        
    def _update_current_version_data(self):
        """Update current version data in memory without UI reload"""
        try:
            if not self.current_version_id:
                return
                
            # Update the version data in the versions list
            for i, version in enumerate(self.versions):
                if version['id'] == self.current_version_id:
                    # Update with current editor content
                    self.versions[i]['content'] = getattr(self, 'main_prompt_edit', QTextEdit()).toPlainText()
                    self.versions[i]['system_prompt'] = getattr(self, 'system_prompt_edit', QTextEdit()).toPlainText()
                    self.versions[i]['description'] = getattr(self, 'description_edit', QTextEdit()).toPlainText()
                    self.versions[i]['updated_at'] = datetime.now().isoformat()
                    break
                    
        except Exception as e:
            print(f"Error updating version data: {e}")
                
    def create_new_version(self):
        """Create a new version"""
        if not self.current_task_id:
            QMessageBox.warning(self, "No Task", "Please select a task first")
            return
            
        name, ok = QInputDialog.getText(self, "New Version", "Enter version name:")
        if ok and name.strip():
            try:
                version_data = {
                    'versionId': f'v{int(datetime.now().timestamp() * 1000)}',
                    'name': name.strip(),
                    'content': '',
                    'system_prompt': 'You are a helpful AI Assistant',
                    'description': ''
                }
                
                response = self.db_client.create_version(self.current_task_id, version_data)
                
                # Refresh data first
                self.load_task_data()
                
                # Then automatically select the new version
                if response and 'id' in response:
                    # Give the UI time to update, then select the new version
                    QTimer.singleShot(100, lambda: self.select_version(response['id']))
                elif self.versions:
                    # Fallback: select the last version (most recently created)
                    QTimer.singleShot(100, lambda: self.select_version(self.versions[-1]['id']))
                
            except Exception as e:
                QMessageBox.critical(self, "Creation Error", f"Failed to create version: {str(e)}")
                
    def copy_version(self):
        """Copy the current version"""
        if not self.current_task_id or not self.current_version_id:
            return
            
        # Find current version data
        current_version = None
        for version in self.versions:
            if version['id'] == self.current_version_id:
                current_version = version
                break
                
        if not current_version:
            return
            
        name, ok = QInputDialog.getText(
            self, 
            "Copy Version", 
            "Enter name for copied version:", 
            text=f"{current_version.get('name', 'Version')} (Copy)"
        )
        
        if ok and name.strip():
            try:
                version_data = {
                    'versionId': f'v{int(datetime.now().timestamp() * 1000)}',
                    'name': name.strip(),
                    'content': current_version.get('content', ''),
                    'system_prompt': current_version.get('system_prompt', ''),
                    'description': current_version.get('description', '')
                }
                
                response = self.db_client.create_version(self.current_task_id, version_data)
                
                # Refresh data first
                self.load_task_data()
                
                # Then automatically select the new version
                if response and 'id' in response:
                    # Give the UI time to update, then select the new version
                    QTimer.singleShot(100, lambda: self.select_version(response['id']))
                elif self.versions:
                    # Fallback: select the last version (most recently created)
                    QTimer.singleShot(100, lambda: self.select_version(self.versions[-1]['id']))
                
            except Exception as e:
                QMessageBox.critical(self, "Copy Error", f"Failed to copy version: {str(e)}")

    def edit_version_name(self):
        """Edit the name of the current version"""
        if not self.current_task_id or not self.current_version_id:
            QMessageBox.warning(self, "No Version Selected", "Please select a version to edit its name")
            return
            
        # Find current version data
        current_version = None
        for version in self.versions:
            if version['id'] == self.current_version_id:
                current_version = version
                break
                
        if not current_version:
            QMessageBox.warning(self, "Version Not Found", "Current version data not found")
            return
            
        current_name = current_version.get('name', 'Untitled Version')
        
        # Show input dialog for new name
        new_name, ok = QInputDialog.getText(
            self, 
            "Edit Version Name", 
            "Enter new version name:", 
            text=current_name
        )
        
        if ok and new_name.strip() and new_name.strip() != current_name:
            try:
                # Update version name in database
                success = self.db_client.update_version(
                    self.current_version_id, 
                    name=new_name.strip(),
                    content=current_version.get('content', ''),
                    system_prompt=current_version.get('system_prompt', ''),
                    description=current_version.get('description', '')
                )
                
                if success:
                    # Update local data
                    for i, version in enumerate(self.versions):
                        if version['id'] == self.current_version_id:
                            self.versions[i]['name'] = new_name.strip()
                            break
                    
                    # Update UI elements
                    self._update_version_name_in_ui(new_name.strip())
                    
                    # Refresh version timeline to show updated name
                    self.version_timeline.set_versions(self.versions)
                    self.version_timeline.set_current_version(self.current_version_id)
                    
                    QMessageBox.information(self, "Success", "Version name updated successfully!")
                    print(f"Version name updated to: {new_name.strip()}")
                    
                else:
                    QMessageBox.warning(self, "Update Error", "Failed to update version name in database")
                    
            except Exception as e:
                error_msg = f"Failed to update version name: {str(e)}"
                QMessageBox.critical(self, "Update Error", error_msg)
                print(f"Error updating version name: {e}")
                
    def _update_version_name_in_ui(self, new_name: str):
        """Update version name in the UI elements"""
        try:
            # Update the current version label if it exists
            if hasattr(self, 'current_version_label') and self.current_version_label:
                try:
                    self.current_version_label.setText(f"Editing: {new_name}")
                except RuntimeError:
                    print("Could not update version name label - label was deleted")
            
            # The version timeline will be updated separately in edit_version_name
            
        except Exception as e:
            print(f"Error updating version name in UI: {e}")
                
        
    # Tab functionality removed - Variables moved to Result viewer
            
    def extract_and_update_variables(self):
        """Extract variables from current prompt and update variables editor"""
        try:
            # Check if the text edit widgets exist and are valid
            if not (hasattr(self, 'main_prompt_edit') and 
                   self.main_prompt_edit is not None):
                return
                
            # Check if the widget is still valid (not deleted)
            try:
                content = self.main_prompt_edit.toPlainText()
            except RuntimeError:
                # Widget has been deleted
                return
                
            # Get system prompt content safely
            system_content = ""
            if (hasattr(self, 'system_prompt_edit') and 
                self.system_prompt_edit is not None):
                try:
                    system_content = self.system_prompt_edit.toPlainText()
                except RuntimeError:
                    # Widget has been deleted
                    system_content = ""
            
            # Extract variables
            all_content = content + "\n" + system_content
            matches = re.findall(r'\{\{([a-zA-Z_][a-zA-Z0-9_-]*)\}\}', all_content)
            extracted_vars = list(set(matches))
            
            # Add any missing variables to the editor
            current_vars = self.variables_editor.variables
            
            # Ensure current_vars is a dictionary
            if not isinstance(current_vars, dict):
                print(f"Warning: variables_editor.variables is not a dict: {type(current_vars)}")
                current_vars = {}
                
            # Add missing variables
            for var in extracted_vars:
                if var not in current_vars:
                    current_vars[var] = ""
                    
            self.variables_editor.set_variables(current_vars)
            
        except Exception as e:
            print(f"Error in extract_and_update_variables: {e}")
            # Continue silently to avoid breaking the UI
            
    def on_variables_changed(self, variables: Dict[str, str]):
        """Handle variables change"""
        if self.current_task_id:
            try:
                self.db_client.update_variables(self.current_task_id, variables)
            except Exception as e:
                print(f"Failed to save variables: {e}")
                
    def clear(self):
        """Clear the editor"""
        self.current_task_id = None
        self.current_version_id = None
        self.task_data = None
        self.versions = []
        
        self.update_header()
        self.version_timeline.set_versions([])
        
        # Clear variables tab
        self.variables_editor.set_variables({})
        
        self.show_empty_state()
        
    def on_version_checkbox_changed(self, version_id: str, is_checked: bool):
        """Handle version checkbox state change for comparison"""
        try:
            print(f"🔄 Checkbox changed: version_id={version_id}, is_checked={is_checked}")
            print(f"📋 Current selected_versions before: {self.selected_versions}")
            
            if is_checked:
                # Add to selected versions if not already there and limit to 2
                if version_id not in self.selected_versions:
                    if len(self.selected_versions) >= 2:
                        # Uncheck the first selected version and remove it
                        first_selected = self.selected_versions[0]
                        print(f"🔄 Unchecking first selected: {first_selected}")
                        if first_selected in self.version_checkboxes:
                            self.version_checkboxes[first_selected].setChecked(False)
                        self.selected_versions.remove(first_selected)
                    
                    self.selected_versions.append(version_id)
                    # print(f"➕ Added version to selection: {version_id}")
                else:
                    print(f"⚠️ Version already in selection: {version_id}")
            else:
                # Remove from selected versions
                if version_id in self.selected_versions:
                    self.selected_versions.remove(version_id)
                    # print(f"➖ Removed version from selection: {version_id}")
                else:
                    print(f"⚠️ Version not in selection: {version_id}")
            
            # print(f"📋 Selected versions after: {self.selected_versions}")
            
            # Update compare button state
            self.update_compare_button_state()
            
            # print(f"✅ Final selected versions for comparison: {self.selected_versions}")
            
        except Exception as e:
            print(f"❌ Error handling version checkbox change: {e}")
            import traceback
            traceback.print_exc()
    
    def update_compare_button_state(self):
        """Update the state of the compare button based on selected versions"""
        try:
            if self.compare_btn:
                # Enable button only when exactly 2 versions are selected
                can_compare = len(self.selected_versions) == 2
                self.compare_btn.setEnabled(can_compare)
                
                # Update button text and style based on selection count
                if len(self.selected_versions) == 0:
                    self.compare_btn.setText("⚖️ Compare Versions")
                    self.compare_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #e9ecef;
                            color: #adb5bd;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 14px;
                        }
                    """)
                elif len(self.selected_versions) == 1:
                    self.compare_btn.setText("⚖️ Compare Versions (1/2)")
                    self.compare_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #e9ecef;
                            color: #adb5bd;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 14px;
                        }
                    """)
                else:  # exactly 2 selected
                    self.compare_btn.setText("⚖️ Compare Versions (2/2)")
                    self.compare_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #007bff;
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background-color: #0056b3;
                        }
                        QPushButton:pressed {
                            background-color: #004085;
                        }
                    """)
                    
        except Exception as e:
            print(f"Error updating compare button state: {e}")
    
    def open_version_comparison(self):
        """Open version comparison dialog"""
        try:
            if len(self.selected_versions) != 2:
                QMessageBox.warning(
                    self, 
                    "Invalid Selection", 
                    "Please select exactly 2 versions to compare."
                )
                return
            
            # Find version data for the selected versions
            version_a = None
            version_b = None
            
            for version in self.versions:
                if version['id'] == self.selected_versions[0]:
                    version_a = version
                elif version['id'] == self.selected_versions[1]:
                    version_b = version
            
            if not version_a or not version_b:
                QMessageBox.warning(
                    self,
                    "Version Not Found",
                    "Could not find the selected versions for comparison."
                )
                return
            
            # Open comparison dialog
            dialog = VersionComparisonDialog(version_a, version_b, self)
            dialog.exec()
            
            # Refresh data after dialog closes (in case user saved a new version)
            self.load_task_data()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Comparison Error", 
                f"Failed to open version comparison: {str(e)}"
            )
            print(f"Error opening version comparison: {e}")
    
    def reset_version_selection(self):
        """Reset version selection state"""
        try:
            # Clear selected versions
            self.selected_versions = []
            
            # Uncheck all checkboxes
            for checkbox in self.version_checkboxes.values():
                checkbox.setChecked(False)
            
            # Clear checkbox references
            self.version_checkboxes = {}
            
            # Update compare button
            self.update_compare_button_state()
            
        except Exception as e:
            print(f"Error resetting version selection: {e}")
    
    def improve_prompt(self):
        """프롬프트 개선 기능"""
        try:
            # Main Prompt 텍스트 가져오기
            if not hasattr(self, 'main_prompt_edit') or not self.main_prompt_edit:
                QMessageBox.warning(self, "No Content", "프롬프트가 없습니다. 버전을 선택해주세요.")
                return
            
            main_prompt_text = self.main_prompt_edit.toPlainText()
            
            if not main_prompt_text or not main_prompt_text.strip():
                QMessageBox.warning(self, "No Content", "개선할 프롬프트 내용이 없습니다.")
                return
            
            # Active endpoint 확인
            endpoints_data = self.db_client.get_llm_endpoints()
            active_endpoint_id = endpoints_data.get('activeEndpointId')
            
            if not active_endpoint_id:
                QMessageBox.warning(
                    self,
                    "No LLM Provider",
                    "프롬프트 개선을 위해서는 활성화된 LLM 공급자가 필요합니다.\n설정에서 LLM 공급자를 설정해주세요."
                )
                return
            
            # Active endpoint 찾기
            active_endpoint = None
            for ep in endpoints_data.get('endpoints', []):
                if ep.get('id') == active_endpoint_id:
                    active_endpoint = ep
                    break
            
            if not active_endpoint:
                QMessageBox.warning(
                    self,
                    "Endpoint Not Found",
                    "활성화된 LLM 엔드포인트를 찾을 수 없습니다."
                )
                return
            
            # 개선 방법론 선택 다이얼로그 표시
            improvement_dialog = PromptImprovementDialog(self)
            improvement_dialog.improvement_selected.connect(
                lambda method_id, template: self.start_improvement(
                    method_id, template, main_prompt_text, active_endpoint
                )
            )
            improvement_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Improvement Error",
                f"프롬프트 개선 중 예상치 못한 오류가 발생했습니다:\n{str(e)}"
            )
    
    def start_improvement(self, method_id: str, template: str, main_prompt: str, endpoint: Dict[str, Any]):
        """개선 프로세스 시작"""
        try:
            # 지연 import로 순환 참조 방지
            from .result_viewer import TranslatePopup
            
            # PromptImprovementManager를 사용하여 템플릿에 main_prompt 적용
            improvement_manager = PromptImprovementManager()
            improvement_prompt = improvement_manager.apply_template(template, main_prompt)
            
            # TranslatePopup 재사용 (개선 결과 표시용)
            self.improvement_popup = TranslatePopup(main_prompt, self)
            self.improvement_popup.setWindowTitle("프롬프트 개선 결과")
            
            # 팝업 레이아웃 수정 함수
            def update_popup_labels():
                try:
                    # 1. 타이틀 라벨 변경 ("AI 응답 번역 결과" -> "AI 응답 개선 결과")
                    for label in self.improvement_popup.findChildren(QLabel):
                        label_text = label.text()
                        if "AI 응답 번역 결과" in label_text or "번역 결과" in label_text:
                            label.setText("AI 응답 개선 결과")
                            print(f"✅ Changed title label: '{label_text}' -> 'AI 응답 개선 결과'")
                            break
                    
                    # 2. 원본 텍스트 그룹 박스 제목 변경
                    if hasattr(self.improvement_popup, 'original_text_widget'):
                        for widget in self.improvement_popup.findChildren(QGroupBox):
                            if "원본" in widget.title() or "Original" in widget.title():
                                widget.setTitle("원본 프롬프트 (Original Prompt)")
                                break
                    
                    # 3. 개선 결과 그룹 박스 제목 변경
                    if hasattr(self.improvement_popup, 'translation_text_widget'):
                        for widget in self.improvement_popup.findChildren(QGroupBox):
                            if "번역" in widget.title() or "Translation" in widget.title():
                                widget.setTitle("개선된 프롬프트 (Improved Prompt)")
                                break
                        
                        # 초기 텍스트를 "개선 중..."으로 변경
                        self.improvement_popup.translation_text_widget.setPlainText("개선 중...")
                    
                    # 4. 복사 버튼 텍스트 변경
                    if hasattr(self.improvement_popup, 'copy_button'):
                        self.improvement_popup.copy_button.setText("📋 개선 결과 복사")
                except Exception as e:
                    print(f"Error updating popup labels: {e}")
            
            # QTimer로 지연 실행 (팝업이 완전히 생성된 후 실행)
            QTimer.singleShot(100, update_popup_labels)
            
            # 모든 텍스트 변경 후 팝업 표시
            self.improvement_popup.show_translation_progress()
            self.improvement_popup.show()
            
            # 상태 메시지 업데이트
            if hasattr(self.improvement_popup, 'status_label'):
                self.improvement_popup.status_label.setText("AI가 프롬프트를 개선하고 있습니다...")
            
            # ImprovePromptThread 시작
            self.improvement_thread = ImprovePromptThread(
                self.db_client,
                improvement_prompt,
                endpoint
            )
            
            # 시그널 연결
            self.improvement_thread.finished.connect(self.on_improvement_finished)
            self.improvement_thread.error.connect(self.on_improvement_error)
            
            # 개선 시작
            self.improvement_thread.start()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Improvement Error",
                f"개선 시작 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def on_improvement_finished(self, improved_text: str):
        """프롬프트 개선 완료 처리"""
        try:
            if hasattr(self, 'improvement_popup') and self.improvement_popup:
                self.improvement_popup.show_translation_result(improved_text)
                
                # 개선된 프롬프트를 에디터에 적용하는 버튼 추가
                if hasattr(self.improvement_popup, 'copy_button'):
                    # 기존 복사 버튼 옆에 적용 버튼 추가
                    apply_button = QPushButton("✅ 적용하기")
                    apply_button.setStyleSheet("""
                        QPushButton {
                            background-color: #28a745;
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 5px;
                            font-size: 12px;
                            font-weight: 500;
                            min-width: 120px;
                        }
                        QPushButton:hover {
                            background-color: #218838;
                        }
                    """)
                    
                    # 적용 버튼 클릭 시 개선된 텍스트를 에디터에 적용
                    apply_button.clicked.connect(
                        lambda: self.apply_improved_prompt(improved_text)
                    )
                    
                    # 버튼 레이아웃에 추가
                    button_layout = self.improvement_popup.copy_button.parent().layout()
                    if button_layout:
                        # 복사 버튼 앞에 적용 버튼 추가
                        button_layout.insertWidget(
                            button_layout.indexOf(self.improvement_popup.copy_button),
                            apply_button
                        )
                
        except Exception as e:
            print(f"Error handling improvement completion: {e}")
            if hasattr(self, 'improvement_popup') and self.improvement_popup:
                self.improvement_popup.show_translation_error(str(e))
    
    def on_improvement_error(self, error_message: str):
        """프롬프트 개선 오류 처리"""
        try:
            if hasattr(self, 'improvement_popup') and self.improvement_popup:
                self.improvement_popup.show_translation_error(error_message)
        except Exception as e:
            print(f"Error handling improvement error: {e}")
    
    def apply_improved_prompt(self, improved_text: str):
        """개선된 프롬프트를 에디터에 적용"""
        try:
            if hasattr(self, 'main_prompt_edit') and self.main_prompt_edit:
                self.main_prompt_edit.setPlainText(improved_text)
                
                # 팝업 닫기
                if hasattr(self, 'improvement_popup') and self.improvement_popup:
                    self.improvement_popup.close()
                
                QMessageBox.information(
                    self,
                    "적용 완료",
                    "개선된 프롬프트가 에디터에 적용되었습니다.\n변경사항을 저장하려면 '💾 Save' 버튼을 클릭하세요."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "적용 오류",
                f"개선된 프롬프트를 적용하는 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def translate_prompts(self):
        """System Prompt와 Main Prompt를 한국어로 번역"""
        try:
            # 지연 import로 순환 참조 방지
            from .result_viewer import TranslateThread, TranslatePopup
            
            # System Prompt와 Main Prompt 텍스트 가져오기
            if not hasattr(self, 'system_prompt_edit') or not self.system_prompt_edit:
                QMessageBox.warning(self, "No Content", "프롬프트가 없습니다. 버전을 선택해주세요.")
                return
            
            if not hasattr(self, 'main_prompt_edit') or not self.main_prompt_edit:
                QMessageBox.warning(self, "No Content", "프롬프트가 없습니다. 버전을 선택해주세요.")
                return
            
            system_prompt_text = self.system_prompt_edit.toPlainText()
            main_prompt_text = self.main_prompt_edit.toPlainText()
            
            # 둘 다 비어있으면 경고
            if (not system_prompt_text or not system_prompt_text.strip()) and \
               (not main_prompt_text or not main_prompt_text.strip()):
                QMessageBox.warning(self, "No Content", "번역할 프롬프트 내용이 없습니다.")
                return
            
            # Active endpoint 확인
            endpoints_data = self.db_client.get_llm_endpoints()
            active_endpoint_id = endpoints_data.get('activeEndpointId')
            
            if not active_endpoint_id:
                QMessageBox.warning(
                    self,
                    "No LLM Provider",
                    "번역을 위해서는 활성화된 LLM 공급자가 필요합니다.\n설정에서 LLM 공급자를 설정해주세요."
                )
                return
            
            # Active endpoint 찾기
            active_endpoint = None
            for ep in endpoints_data.get('endpoints', []):
                if ep.get('id') == active_endpoint_id:
                    active_endpoint = ep
                    break
            
            if not active_endpoint:
                QMessageBox.warning(
                    self,
                    "Endpoint Not Found",
                    "활성화된 LLM 엔드포인트를 찾을 수 없습니다."
                )
                return
            
            # 각 프롬프트의 Placeholder 보호
            protected_system, system_placeholder_map = self._protect_placeholders(system_prompt_text)
            protected_main, main_placeholder_map = self._protect_placeholders(main_prompt_text)
            
            # 합쳐진 텍스트 생성 (구분선 포함)
            separator = "\n\n====================\n\n"
            combined_original = f"[System Prompt]\n{system_prompt_text}{separator}[Main Prompt]\n{main_prompt_text}"
            combined_protected = f"[System Prompt]\n{protected_system}{separator}[Main Prompt]\n{protected_main}"
            
            # 캐시 키 생성
            import hashlib
            cache_key = hashlib.md5(combined_protected.encode()).hexdigest()
            
            # 캐시 확인
            if cache_key in self.translation_cache:
                # 캐시에서 번역 결과 가져오기
                cached_translation = self.translation_cache[cache_key]
                # Placeholder 복원 (두 부분으로 나누어)
                final_translation = self._restore_combined_placeholders(
                    cached_translation, 
                    system_placeholder_map, 
                    main_placeholder_map,
                    separator
                )
                
                # TranslatePopup으로 결과 표시
                self.translate_popup = TranslatePopup(combined_original, self)
                self.translate_popup.show_translation_result(final_translation)
                self.translate_popup.show()
                return
            
            # 캐시가 없으면 번역 실행
            # TranslatePopup 생성 및 표시
            self.translate_popup = TranslatePopup(combined_original, self)
            self.translate_popup.show_translation_progress()
            self.translate_popup.show()
            
            # 번역 프롬프트에 placeholder 보호 지시 추가
            translation_instructions = (
                "아래 내용을 요약이나 생략없이 있는 그대로 `한국어`로만 번역해주세요.\n"
                "중요: 'PLACEHOLDER_TOKEN_'로 시작하는 특수 토큰들과 [System Prompt], [Main Prompt], '====================' 구분선은 절대 번역하지 말고 원문 그대로 유지해주세요.\n\n"
                f"{combined_protected}"
            )
            
            translation_instructions = f"""
# 번역 지시사항

아래 제공된 텍스트를 **한국어로 정확하게 번역**해주세요.

## 핵심 원칙

1. **완전성**: 모든 내용을 빠짐없이 번역하세요. 어떤 문장, 단어, 구두점도 생략하거나 요약하지 마세요.

2. **정확성**: 원문의 의미, 뉘앙스, 어조를 정확하게 보존하세요.

3. **자연스러움**: 한국어로 자연스럽게 읽히도록 번역하되, 원문의 구조와 의미를 유지하세요.

## 절대 번역하지 말아야 할 요소

다음 요소들은 **반드시 원문 그대로** 유지해주세요:

- `PLACEHOLDER_TOKEN_`로 시작하는 모든 특수 토큰
- `[System Prompt]`, `[Main Prompt]` 등의 대괄호 표기
- `====================` 형태의 구분선
- 코드 블록 내의 변수명, 함수명, 키워드

## 예시

**입력:**
```
[System Prompt]
This is a sample text with PLACEHOLDER_TOKEN_123.
====================
```

**올바른 출력:**
```
[System Prompt]
이것은 PLACEHOLDER_TOKEN_123이 포함된 샘플 텍스트입니다.
====================
```

---
  
# 입력:
{combined_protected}           
            """.strip()
            print(translation_instructions)
            
            # TranslateThread 시작
            self.translate_thread = TranslateThread(
                self.db_client,
                translation_instructions,
                active_endpoint
            )
            
            # 시그널 연결 (placeholder_map들을 클로저로 캡처)
            self.translate_thread.finished.connect(
                lambda translated: self.on_prompts_translation_finished(
                    translated, system_placeholder_map, main_placeholder_map, separator, cache_key
                )
            )
            self.translate_thread.error.connect(self.on_prompts_translation_error)
            
            # 번역 시작
            self.translate_thread.start()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Translation Error",
                f"번역 중 예상치 못한 오류가 발생했습니다:\n{str(e)}"
            )
    
    def _restore_combined_placeholders(self, text: str, system_map: dict, main_map: dict, separator: str) -> str:
        """
        합쳐진 번역 결과에서 각 부분의 placeholder 복원
        """
        try:
            # 구분선으로 두 부분으로 나누기
            parts = text.split(separator)
            
            if len(parts) >= 2:
                # 각 부분에서 placeholder 복원
                system_part = self._restore_placeholders(parts[0], system_map)
                main_part = self._restore_placeholders(parts[1], main_map)
                return f"{system_part}{separator}{main_part}"
            else:
                # 구분선이 없으면 전체에 대해 모든 placeholder 복원 시도
                combined_map = {**system_map, **main_map}
                return self._restore_placeholders(text, combined_map)
        except Exception as e:
            print(f"Error restoring combined placeholders: {e}")
            # 오류 발생 시 모든 placeholder 복원 시도
            combined_map = {**system_map, **main_map}
            return self._restore_placeholders(text, combined_map)
    
    def on_prompts_translation_finished(self, translated_text: str, system_map: dict, main_map: dict, separator: str, cache_key: str):
        """프롬프트들 번역 완료 처리"""
        try:
            # Placeholder 복원
            final_translation = self._restore_combined_placeholders(
                translated_text, 
                system_map, 
                main_map,
                separator
            )
            
            # 캐시에 저장 (placeholder 복원 전 상태로)
            self.translation_cache[cache_key] = translated_text
            
            # TranslatePopup에 결과 표시
            if hasattr(self, 'translate_popup') and self.translate_popup:
                self.translate_popup.show_translation_result(final_translation)
                
        except Exception as e:
            print(f"Error handling prompts translation completion: {e}")
            if hasattr(self, 'translate_popup') and self.translate_popup:
                self.translate_popup.show_translation_error(str(e))
    
    def on_prompts_translation_error(self, error_message: str):
        """프롬프트들 번역 오류 처리"""
        try:
            if hasattr(self, 'translate_popup') and self.translate_popup:
                self.translate_popup.show_translation_error(error_message)
        except Exception as e:
            print(f"Error handling prompts translation error: {e}")
    
    def apply_theme(self, is_dark: bool):
        """Apply theme to the widget"""
        # Theme will be applied through stylesheets
        pass
