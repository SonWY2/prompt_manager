"""
Prompt Improvement Dialog
프롬프트 개선 방법론 선택 다이얼로그
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QTextEdit, QScrollArea, QWidget,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional, Dict

from ..utils.prompt_improvement import PromptImprovementManager


class PromptImprovementDialog(QDialog):
    """프롬프트 개선 방법론을 선택하는 다이얼로그"""
    
    # Signal: 선택된 메서드와 커스텀 템플릿(선택 시)
    improvement_selected = pyqtSignal(str, str)  # method_id, template_or_custom
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.improvement_manager = PromptImprovementManager()
        self.selected_method_id: Optional[str] = None
        self.custom_template_text: str = ""
        
        self.setWindowTitle("프롬프트 개선 방법 선택")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 제목
        title_label = QLabel("🔧 프롬프트 개선 방법 선택")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 4px;
            }
        """)
        layout.addWidget(title_label)
        
        # 설명
        desc_label = QLabel("개선할 방법을 선택하거나 커스텀 개선 지침을 입력하세요.")
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 4px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # 메서드 선택 영역
        methods_widget = QWidget()
        methods_layout = QVBoxLayout(methods_widget)
        methods_layout.setContentsMargins(0, 0, 0, 0)
        methods_layout.setSpacing(4)
        
        # 버튼 그룹 (라디오 버튼들)
        self.button_group = QButtonGroup(self)
        
        # 디폴트 개선 방법론들
        methods = self.improvement_manager.get_all_methods()
        for i, method in enumerate(methods):
            method_card = self.create_method_card(method, i)
            methods_layout.addWidget(method_card)
            
        # 커스텀 옵션
        custom_info = self.improvement_manager.get_custom_template()
        custom_card = self.create_custom_card(custom_info, len(methods))
        methods_layout.addWidget(custom_card)
        
        methods_layout.addStretch()
        
        scroll_area.setWidget(methods_widget)
        layout.addWidget(scroll_area, 1)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 취소 버튼
        cancel_button = QPushButton("취소")
        cancel_button.setFixedSize(100, 40)
        cancel_button.setStyleSheet("""
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
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # 적용 버튼
        self.apply_button = QPushButton("적용")
        self.apply_button.setFixedSize(100, 40)
        self.apply_button.setEnabled(False)  # 처음에는 비활성화
        self.apply_button.setStyleSheet("""
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
        self.apply_button.clicked.connect(self.on_apply)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
        
    def create_method_card(self, method: Dict, index: int) -> QWidget:
        """개선 방법론 카드 생성"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.NoFrame)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(3)
        
        # 헤더 (라디오 버튼 + 아이콘 + 이름)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        
        # 라디오 버튼
        radio_button = QRadioButton()
        radio_button.setStyleSheet("""
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #3498db;
                border-radius: 8px;
                background-color: #3498db;
            }
        """)
        self.button_group.addButton(radio_button, index)
        radio_button.toggled.connect(lambda checked, m=method: self.on_method_selected(checked, m))
        header_layout.addWidget(radio_button)
        
        # 아이콘 + 이름을 함께 표시
        title_text = f"{method.get('icon', '🔧')} {method.get('name', 'Unknown')}"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #2c3e50;
                border: none;
                background: transparent;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        card_layout.addLayout(header_layout)
        
        # 설명
        desc_label = QLabel(method.get('description', ''))
        desc_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 11px;
                line-height: 1.3;
                margin-left: 20px;
            }
        """)
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)
        
        # 카드 클릭 시 라디오 버튼 선택
        def card_clicked(event):
            radio_button.setChecked(True)
        
        card.mousePressEvent = card_clicked
        
        return card
        
    def create_custom_card(self, custom_info: Dict, index: int) -> QWidget:
        """커스텀 옵션 카드 생성"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.NoFrame)
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
            }
            QFrame:hover {
                border-color: #3498db;
            }
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(5)
        
        # 헤더
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        
        # 라디오 버튼
        self.custom_radio = QRadioButton()
        self.custom_radio.setStyleSheet("""
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #3498db;
                border-radius: 8px;
                background-color: #3498db;
            }
        """)
        self.button_group.addButton(self.custom_radio, index)
        self.custom_radio.toggled.connect(self.on_custom_selected)
        header_layout.addWidget(self.custom_radio)
        
        # 아이콘 + 이름을 함께 표시
        title_text = f"{custom_info.get('icon', '✏️')} {custom_info.get('name', '커스텀 개선')}"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #2c3e50;
                border: none;
                background: transparent;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        card_layout.addLayout(header_layout)
        
        # 설명
        desc_label = QLabel(custom_info.get('description', ''))
        desc_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 11px;
                margin-left: 20px;
            }
        """)
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)
        
        # 커스텀 프롬프트 입력 영역
        self.custom_text_edit = QTextEdit()
        self.custom_text_edit.setPlaceholderText(custom_info.get('placeholder', '커스텀 개선 지침을 입력하세요...'))
        self.custom_text_edit.setMaximumHeight(120)
        self.custom_text_edit.setEnabled(False)  # 처음에는 비활성화
        self.custom_text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
            QTextEdit:focus {
                border-color: #3498db;
            }
            QTextEdit:disabled {
                background-color: #e9ecef;
            }
        """)
        self.custom_text_edit.textChanged.connect(self.on_custom_text_changed)
        card_layout.addWidget(self.custom_text_edit)
        
        # 카드 클릭 시 라디오 버튼 선택 (텍스트 영역 제외)
        def card_clicked(event):
            # 텍스트 입력 영역을 클릭한 경우 선택만 하고 포커스 이동 안함
            if self.custom_text_edit.geometry().contains(event.pos()):
                if not self.custom_radio.isChecked():
                    self.custom_radio.setChecked(True)
            else:
                self.custom_radio.setChecked(True)
        
        card.mousePressEvent = card_clicked
        
        return card
        
    def on_method_selected(self, checked: bool, method: Dict):
        """디폴트 방법론 선택 시"""
        if checked:
            self.selected_method_id = method.get('id', '')
            self.custom_template_text = ""
            self.custom_text_edit.setEnabled(False)
            self.apply_button.setEnabled(True)
            
    def on_custom_selected(self, checked: bool):
        """커스텀 옵션 선택 시"""
        if checked:
            self.selected_method_id = "custom"
            self.custom_text_edit.setEnabled(True)
            self.custom_text_edit.setFocus()
            
            # 텍스트가 있으면 적용 버튼 활성화
            self.apply_button.setEnabled(bool(self.custom_text_edit.toPlainText().strip()))
            
    def on_custom_text_changed(self):
        """커스텀 텍스트 변경 시"""
        if self.custom_radio.isChecked():
            self.custom_template_text = self.custom_text_edit.toPlainText()
            # 텍스트가 있으면 적용 버튼 활성화
            self.apply_button.setEnabled(bool(self.custom_template_text.strip()))
            
    def on_apply(self):
        """적용 버튼 클릭 시"""
        if not self.selected_method_id:
            return
            
        if self.selected_method_id == "custom":
            # 커스텀 템플릿 전송
            template = self.custom_text_edit.toPlainText().strip()
            if template:
                self.improvement_selected.emit(self.selected_method_id, template)
                self.accept()
        else:
            # 디폴트 템플릿 ID 전송
            method = self.improvement_manager.get_method_by_id(self.selected_method_id)
            if method:
                template = method.get('template', '')
                self.improvement_selected.emit(self.selected_method_id, template)
                self.accept()
