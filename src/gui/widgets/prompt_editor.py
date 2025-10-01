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
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter, QTextDocument
from typing import Dict, List, Optional, Any
import re
import json
from datetime import datetime

from ..utils.db_client import DatabaseClient


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
                
            except Exception as e:
                # 오류 발생 시 기본 높이로 설정
                print(f"Error calculating height: {e}")
                edit.setFixedHeight(50)
        
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
        
        # Task title and actions
        title_layout = QHBoxLayout()
        
        self.task_title_label = QLabel("No Task Selected")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.task_title_label.setFont(title_font)
        title_layout.addWidget(self.task_title_label)
        
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
        
        # Version timeline
        self.version_timeline = VersionTimeline()
        self.version_timeline.version_selected.connect(self.select_version)
        header_layout.addWidget(self.version_timeline)
        
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
        self.description_edit.textChanged.connect(self.schedule_auto_save)
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
        self.system_prompt_edit.textChanged.connect(self.schedule_auto_save)
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
        self.main_prompt_edit.textChanged.connect(self.schedule_auto_save)
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
        
        # Add stretch to push buttons to the right
        actions_layout.addStretch()
        
        self.preview_btn = QPushButton("👁️ Preview")
        self.preview_btn.setCheckable(True)
        self.preview_btn.clicked.connect(self.toggle_preview)
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 12px;
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
        
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_current_version)
        self.save_btn.setStyleSheet("""
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
        
        actions_layout.addWidget(self.preview_btn)
        actions_layout.addWidget(self.save_btn)
        
        layout.addLayout(actions_layout)
        
        return widget
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Tab functionality removed - using single content area now
        
    def set_task_id(self, task_id: str):
        """Set the current task"""
        self.current_task_id = task_id
        self.current_version_id = None
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
            self.task_title_label.setText(self.task_data.get('name', 'Untitled Task'))
        else:
            self.task_title_label.setText("No Task Selected")
            
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
        """Create a version selection item (like variables editor)"""
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
        item_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        item_layout = QVBoxLayout(item_frame)
        item_layout.setSpacing(8)
        
        # Header with version name and actions
        header_layout = QHBoxLayout()
        
        # Version icon and name
        version_icon = QLabel("📄")
        version_icon.setFixedSize(20, 20)
        version_icon.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(version_icon)
        
        # Version name (like variable name)
        version_name = version.get('name', 'Untitled Version')
        name_label = QLabel(version_name)
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

    def go_back_to_version_selection(self):
        """Go back to version selection screen"""
        try:
            # Exit preview mode if active
            self._exit_preview_mode()
            
            # Clear current version selection
            self.current_version_id = None
            self.version_timeline.set_current_version(None)
            
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
            if not widget.layout():
                content_layout = QVBoxLayout()
                content_layout.setContentsMargins(0, 0, 0, 0)
                widget.setLayout(content_layout)
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
                print("Switched to Preview mode")
            else:
                # Edit 모드로 전환
                self.apply_edit_mode()
                preview_btn.setText("👁️ Preview")
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
        
    def apply_theme(self, is_dark: bool):
        """Apply theme to the widget"""
        # Theme will be applied through stylesheets
        pass
