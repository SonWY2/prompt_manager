"""
Result Viewer Widget - PyQt GUI equivalent of ResultViewer.jsx
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QTabWidget, QScrollArea, QFrame, QListWidget,
    QListWidgetItem, QSplitter, QMessageBox, QProgressBar,
    QGroupBox, QFormLayout, QTextBrowser, QComboBox, QSlider,
    QDoubleSpinBox, QDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon
from typing import Dict, List, Optional, Any
import json
import math
from datetime import datetime

from ..utils.db_client import DatabaseClient
from .prompt_editor import VariableEditor


class LLMCallThread(QThread):
    """Thread for calling LLM API"""
    
    finished = pyqtSignal(dict)  # result
    error = pyqtSignal(str)      # error message
    
    def __init__(self, db_client: DatabaseClient, task_id: str, version_id: str, 
                 input_data: Dict[str, Any], system_prompt: str, endpoint: Optional[Dict[str, Any]], 
                 temperature: float = 0.7):
        super().__init__()
        self.db_client = db_client
        self.task_id = task_id
        self.version_id = version_id
        self.input_data = input_data
        self.system_prompt = system_prompt
        self.endpoint = endpoint
        self.temperature = temperature
        
    def run(self):
        """Run the LLM call"""
        try:
            result = self.db_client.call_llm(
                self.task_id, 
                self.version_id, 
                self.input_data, 
                self.system_prompt,
                self.endpoint,
                temperature=self.temperature
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class TranslateThread(QThread):
    """Thread for translating response content to Korean"""
    
    finished = pyqtSignal(str)  # translated text
    error = pyqtSignal(str)     # error message
    
    def __init__(self, db_client: DatabaseClient, content_to_translate: str, endpoint: Optional[Dict[str, Any]]):
        super().__init__()
        self.db_client = db_client
        self.content_to_translate = content_to_translate
        self.endpoint = endpoint
        
    def run(self):
        """Run the translation call"""
        try:
            if not self.endpoint:
                self.error.emit("No LLM endpoint available for translation")
                return
                
            # Prepare translation prompt
            system_prompt = "You are a professional translator. Translate the given text to Korean while maintaining the original meaning, tone, and context. Provide only the translated text without any additional comments or explanations."
            user_prompt = f"아래 내용을 요약이나 생략없이 있는 그대로 `한국어`로만 번역해주세요:\n\n{self.content_to_translate}"
            
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
                        'content': user_prompt
                    }
                ],
                'temperature': 0.3  # Lower temperature for consistent translation
            }
            
            response = requests.post(
                chat_url,
                headers=headers,
                json=payload,
                timeout=60,  # 1 minute timeout
                verify=True
            )
            
            if response.status_code != 200:
                self.error.emit(f"Translation API call failed: HTTP {response.status_code} - {response.text}")
                return
                
            result_data = response.json()
            
            # Extract translated content
            if 'choices' in result_data and result_data['choices']:
                translated_text = result_data['choices'][0].get('message', {}).get('content', '')
                if translated_text:
                    self.finished.emit(translated_text)
                else:
                    self.error.emit("No translated content received from API")
            else:
                self.error.emit("Invalid response format from translation API")
                
        except requests.exceptions.Timeout:
            self.error.emit("Translation request timed out after 1 minute")
        except requests.exceptions.ConnectionError:
            self.error.emit("Could not connect to LLM endpoint for translation")
        except requests.exceptions.SSLError:
            self.error.emit("SSL certificate verification failed")
        except Exception as e:
            self.error.emit(f"Translation error: {str(e)}")


class TranslatePopup(QDialog):
    """Popup dialog for showing translation results"""
    
    def __init__(self, original_text: str, parent=None):
        super().__init__(parent)
        self.original_text = original_text
        self.translated_text = ""
        
        self.setWindowTitle("한국어 번역")
        self.setModal(True)
        self.resize(700, 500)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the translation popup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("AI 응답 번역 결과")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Original text section
        original_group = QGroupBox("원본 텍스트 (Original)")
        original_layout = QVBoxLayout(original_group)
        
        self.original_text_widget = QTextBrowser()
        self.original_text_widget.setPlainText(self.original_text)
        self.original_text_widget.setMaximumHeight(150)
        self.original_text_widget.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        original_layout.addWidget(self.original_text_widget)
        layout.addWidget(original_group)
        
        # Translation result section
        translation_group = QGroupBox("번역 결과 (Korean Translation)")
        translation_layout = QVBoxLayout(translation_group)
        
        self.translation_text_widget = QTextBrowser()
        self.translation_text_widget.setPlainText("번역 중...")
        self.translation_text_widget.setMinimumHeight(200)
        self.translation_text_widget.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #3498db;
                border-radius: 5px;
                padding: 15px;
                background-color: white;
                font-family: 'Malgun Gothic', 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #2c3e50;
            }
        """)
        translation_layout.addWidget(self.translation_text_widget)
        layout.addWidget(translation_group)
        
        # Progress indicator
        self.progress_widget = QWidget()
        progress_layout = QHBoxLayout(self.progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("번역 중...")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(self.progress_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Copy button
        self.copy_button = QPushButton("📋 번역 결과 복사")
        self.copy_button.setEnabled(False)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: 500;
                min-width: 120px;
            }
            QPushButton:hover:enabled {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.copy_button.clicked.connect(self.copy_translation)
        button_layout.addWidget(self.copy_button)
        
        # Close button
        close_button = QPushButton("닫기")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
    def show_translation_progress(self):
        """Show translation in progress"""
        self.progress_widget.setVisible(True)
        self.translation_text_widget.setPlainText("번역 중... 잠시만 기다려 주세요.")
        self.status_label.setText("AI가 텍스트를 번역하고 있습니다...")
        self.copy_button.setEnabled(False)
        
    def show_translation_result(self, translated_text: str):
        """Show translation result"""
        self.translated_text = translated_text
        self.translation_text_widget.setPlainText(translated_text)
        self.progress_widget.setVisible(False)
        self.copy_button.setEnabled(True)
        
    def show_translation_error(self, error_message: str):
        """Show translation error"""
        error_text = f"번역 중 오류가 발생했습니다:\n\n{error_message}\n\n다시 시도하거나 나중에 다시 시도해 주세요."
        self.translation_text_widget.setPlainText(error_text)
        self.translation_text_widget.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #e74c3c;
                border-radius: 5px;
                padding: 15px;
                background-color: #fdf2f2;
                font-family: 'Malgun Gothic', 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #c0392b;
            }
        """)
        self.progress_widget.setVisible(False)
        self.copy_button.setEnabled(False)
        
    def copy_translation(self):
        """Copy translation result to clipboard"""
        if self.translated_text:
            try:
                clipboard = QApplication.clipboard()
                clipboard.setText(self.translated_text)
                self.status_label.setText("번역 결과가 클립보드에 복사되었습니다!")
                
                # Hide status message after 3 seconds
                QTimer.singleShot(3000, lambda: self.status_label.setText(""))
                
            except Exception as e:
                self.status_label.setText(f"복사 실패: {str(e)}")


class ResultHistoryItem(QFrame):
    """Custom history item widget"""
    
    clicked = pyqtSignal(dict)  # result data
    double_clicked = pyqtSignal(dict)  # result data for double click
    delete_requested = pyqtSignal(str)  # timestamp
    
    def __init__(self, result_data: Dict[str, Any], index: int):
        super().__init__()
        self.result_data = result_data
        self.index = index
        
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setContentsMargins(2, 2, 2, 2)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border-color: #007bff;
            }
        """)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the history item UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Index badge
        index_label = QLabel(str(self.index))
        index_label.setStyleSheet("""
            QLabel {
                background-color: #6c757d;
                color: white;
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 6px;
                min-width: 16px;
            }
        """)
        index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(index_label)
        
        # Title
        title_label = QLabel(f"Run #{self.index}")
        title_label.setFont(QFont("", 10, QFont.Weight.Medium))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Timestamp
        timestamp = self.result_data.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%m/%d %H:%M')
            except:
                time_str = timestamp[:16] if len(timestamp) >= 16 else timestamp
        else:
            time_str = 'Unknown'
            
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #6c757d; font-size: 10px;")
        header_layout.addWidget(time_label)
        
        # Delete button
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(20, 20)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #dc3545;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
                border-radius: 10px;
            }
        """)
        delete_btn.setToolTip("Delete this result")
        delete_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.result_data.get('timestamp', ''))
        )
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        # Preview content
        content = self._get_preview_content()
        preview_label = QLabel(content)
        preview_label.setStyleSheet("color: #495057; font-size: 11px; line-height: 1.4;")
        preview_label.setWordWrap(True)
        layout.addWidget(preview_label)
        
        # Footer info
        footer_layout = QHBoxLayout()
        
        # Token count
        tokens = self._calculate_tokens()
        token_label = QLabel(f"{tokens:,} tokens")
        token_label.setStyleSheet("color: #6c757d; font-size: 10px;")
        footer_layout.addWidget(token_label)
        
        # Model info
        model = self._get_model_info()
        if model:
            model_label = QLabel(model)
            model_label.setStyleSheet("""
                QLabel {
                    background-color: #e9ecef;
                    color: #495057;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 9px;
                    font-family: monospace;
                }
            """)
            footer_layout.addWidget(model_label)
            
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
    def _get_preview_content(self) -> str:
        """Get preview content"""
        output = self.result_data.get('output', {})
        
        # Try different response formats
        content = ""
        if isinstance(output, dict):
            if 'choices' in output and output['choices']:
                content = output['choices'][0].get('message', {}).get('content', '')
            elif 'content' in output:
                content = output['content']
        elif isinstance(output, str):
            content = output
            
        # Truncate for preview
        if len(content) > 120:
            content = content[:120] + "..."
            
        return content if content else "No response content"
        
    def _calculate_tokens(self) -> int:
        """Estimate token count"""
        input_data = self.result_data.get('inputData', {})
        output = self.result_data.get('output', {})
        
        # Simple estimation: ~4 characters per token
        input_text = json.dumps(input_data)
        output_text = str(output)
        total_chars = len(input_text) + len(output_text)
        
        return math.ceil(total_chars / 4)
        
    def _get_model_info(self) -> Optional[str]:
        """Get model information with temperature - improved version"""
        endpoint = self.result_data.get('endpoint', {})
        model_name = None
        
        # Priority-based model name extraction
        if endpoint:
            # Priority 1: usedModel (actual model used in API call)
            model_name = endpoint.get('usedModel')
            
            # Priority 2: defaultModel field
            if not model_name:
                model_name = endpoint.get('defaultModel')
            
            # Priority 3: model field (alternative naming)
            if not model_name:
                model_name = endpoint.get('model')
            
            # Priority 4: modelName field
            if not model_name:
                model_name = endpoint.get('modelName')
            
            # Priority 5: Extract from API response
            if not model_name:
                output = self.result_data.get('output', {})
                if isinstance(output, dict) and output.get('model'):
                    model_name = output['model']
            
            # Priority 6: Use provider name as fallback
            if not model_name:
                model_name = endpoint.get('name') or endpoint.get('provider')
        
        if model_name:
            # Get temperature from result data (now stored properly)
            temperature = self.result_data.get('temperature', 0.7)
            return f"{model_name} • T:{temperature:.1f}"
        
        return "Unknown Model • T:0.7"
        
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.result_data)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double click events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.result_data)
        super().mouseDoubleClickEvent(event)


class ResultDetailDialog(QDialog):
    """Popup dialog for showing detailed result information"""
    
    def __init__(self, result_data: Dict[str, Any], version_data: Optional[Dict[str, Any]] = None, 
                 db_client: Optional[DatabaseClient] = None, active_endpoint: Optional[Dict[str, Any]] = None, 
                 parent=None):
        super().__init__(parent)
        self.result_data = result_data
        self.version_data = version_data
        self.db_client = db_client
        self.active_endpoint = active_endpoint
        
        # Translation state tracking
        self.system_prompt_translated = False
        self.system_prompt_translation = ""
        self.user_prompt_translated = False
        self.user_prompt_translation = ""
        self.response_translated = False
        self.response_translation = ""
        
        # UI references for translation
        self.system_prompt_browser = None
        self.system_translate_btn = None
        self.user_prompt_browser = None
        self.user_translate_btn = None
        self.response_browser = None
        self.response_translate_btn = None
        
        self.setWindowTitle("Result Details")
        self.setModal(True)
        self.resize(900, 700)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title with timestamp
        title_layout = QHBoxLayout()
        title_label = QLabel("📊 Result Details")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Timestamp
        timestamp = self.result_data.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = timestamp
        else:
            time_str = 'Unknown'
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        title_layout.addWidget(time_label)
        
        layout.addLayout(title_layout)
        
        # Tab widget for organized content
        tab_widget = QTabWidget()
        
        # Request tab
        tab_widget.addTab(self.create_request_tab(), "📝 Request")
        
        # Response tab
        tab_widget.addTab(self.create_response_tab(), "💬 Response")
        
        # Details tab
        tab_widget.addTab(self.create_details_tab(), "📈 Details")
        
        layout.addWidget(tab_widget, 1)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 500;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
    def create_request_tab(self) -> QWidget:
        """Create request information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # System Prompt
        system_group = QGroupBox()
        system_group_layout = QVBoxLayout(system_group)
        
        # Header with title and translate button
        system_header = QHBoxLayout()
        system_label = QLabel("System Prompt")
        system_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        system_header.addWidget(system_label)
        system_header.addStretch()
        
        self.system_translate_btn = QPushButton("🌐 Translate")
        self.system_translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.system_translate_btn.clicked.connect(lambda: self.toggle_system_translation())
        if not self.db_client or not self.active_endpoint:
            self.system_translate_btn.setEnabled(False)
        system_header.addWidget(self.system_translate_btn)
        
        system_group_layout.addLayout(system_header)
        
        # System prompt text
        stored_system = self.result_data.get('systemPromptTemplate')
        if stored_system:
            system_text = stored_system
        else:
            system_text = self.version_data.get('system_prompt', 'N/A') if self.version_data else 'N/A'
        
        self.system_prompt_browser = QTextBrowser()
        self.system_prompt_browser.setPlainText(system_text)
        self.system_prompt_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 10px;
                background-color: #f9f9f9;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        system_group_layout.addWidget(self.system_prompt_browser)
        layout.addWidget(system_group)
        
        # User Prompt
        user_group = QGroupBox()
        user_group_layout = QVBoxLayout(user_group)
        
        # Header with title and translate button
        user_header = QHBoxLayout()
        user_label = QLabel("User Prompt")
        user_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        user_header.addWidget(user_label)
        user_header.addStretch()
        
        self.user_translate_btn = QPushButton("🌐 Translate")
        self.user_translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.user_translate_btn.clicked.connect(lambda: self.toggle_user_translation())
        if not self.db_client or not self.active_endpoint:
            self.user_translate_btn.setEnabled(False)
        user_header.addWidget(self.user_translate_btn)
        
        user_group_layout.addLayout(user_header)
        
        # User prompt text
        stored_user = self.result_data.get('userPromptTemplate')
        if stored_user:
            user_text = stored_user
        else:
            content = self.version_data.get('content', '') if self.version_data else ''
            input_data = self.result_data.get('inputData', {})
            user_text = self._render_prompt(content, input_data)
        
        self.user_prompt_browser = QTextBrowser()
        self.user_prompt_browser.setPlainText(user_text)
        self.user_prompt_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 10px;
                background-color: #f9f9f9;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        user_group_layout.addWidget(self.user_prompt_browser)
        layout.addWidget(user_group)
        
        return widget
        
    def create_response_tab(self) -> QWidget:
        """Create response information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Response content
        response_group = QGroupBox()
        response_layout = QVBoxLayout(response_group)
        
        # Header with title and buttons
        header_layout = QHBoxLayout()
        
        response_title = QLabel("AI Response")
        response_title.setStyleSheet("font-weight: bold; font-size: 13px;")
        header_layout.addWidget(response_title)
        
        header_layout.addStretch()
        
        copy_button = QPushButton("📋 Copy")
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        copy_button.clicked.connect(self.copy_response)
        header_layout.addWidget(copy_button)
        
        self.response_translate_btn = QPushButton("🌐 Translate")
        self.response_translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.response_translate_btn.clicked.connect(lambda: self.toggle_response_translation())
        if not self.db_client or not self.active_endpoint:
            self.response_translate_btn.setEnabled(False)
        header_layout.addWidget(self.response_translate_btn)
        
        response_layout.addLayout(header_layout)
        
        # Response text
        response_content = self._extract_response_content(self.result_data.get('output', {}))
        self.response_browser = QTextBrowser()
        self.response_browser.setPlainText(response_content)
        self.response_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 15px;
                background-color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        response_layout.addWidget(self.response_browser)
        layout.addWidget(response_group)
        
        return widget
        
    def create_details_tab(self) -> QWidget:
        """Create details information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Metrics
        metrics_group = QGroupBox("Metrics")
        metrics_layout = QFormLayout(metrics_group)
        
        endpoint = self.result_data.get('endpoint', {})
        model = endpoint.get('defaultModel') or endpoint.get('name', 'Unknown')
        temperature = self.result_data.get('temperature', 0.7)
        
        metrics_layout.addRow("Model:", QLabel(model))
        metrics_layout.addRow("Temperature:", QLabel(f"{temperature:.1f}"))
        
        # Calculate tokens
        input_data = self.result_data.get('inputData', {})
        output = self.result_data.get('output', {})
        if isinstance(output, dict) and 'usage' in output:
            usage = output['usage']
            metrics_layout.addRow("Input Tokens:", QLabel(f"{usage.get('prompt_tokens', 'N/A'):,}"))
            metrics_layout.addRow("Output Tokens:", QLabel(f"{usage.get('completion_tokens', 'N/A'):,}"))
            metrics_layout.addRow("Total Tokens:", QLabel(f"{usage.get('total_tokens', 'N/A'):,}"))
        
        layout.addWidget(metrics_group)
        
        # Variables
        if input_data:
            variables_group = QGroupBox("Input Variables")
            variables_layout = QVBoxLayout(variables_group)
            
            variables_browser = QTextBrowser()
            variables_browser.setPlainText(json.dumps(input_data, indent=2, ensure_ascii=False))
            variables_browser.setMaximumHeight(200)
            variables_browser.setStyleSheet("""
                QTextBrowser {
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 10px;
                    background-color: #f9f9f9;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                }
            """)
            variables_layout.addWidget(variables_browser)
            layout.addWidget(variables_group)
        
        layout.addStretch()
        
        return widget
        
    def _render_prompt(self, template: str, variables: Dict[str, Any]) -> str:
        """Render prompt template with variables"""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
        
    def _extract_response_content(self, output: Any) -> str:
        """Extract response content from output"""
        if isinstance(output, dict):
            if 'choices' in output and output['choices']:
                return output['choices'][0].get('message', {}).get('content', 'No content')
            elif 'content' in output:
                return output['content']
        elif isinstance(output, str):
            return output
        return 'No content available'
        
    def copy_response(self):
        """Copy response content to clipboard"""
        try:
            content = self._extract_response_content(self.result_data.get('output', {}))
            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            
            # Show temporary feedback
            sender = self.sender()
            if sender:
                original_text = sender.text()
                sender.setText("✓ Copied!")
                QTimer.singleShot(2000, lambda: sender.setText(original_text))
        except Exception as e:
            QMessageBox.warning(self, "Copy Error", f"Failed to copy: {str(e)}")
    
    def toggle_system_translation(self):
        """Toggle system prompt translation"""
        if not self.db_client or not self.active_endpoint:
            QMessageBox.warning(self, "No LLM Provider", "번역을 위해서는 활성화된 LLM 공급자가 필요합니다.")
            return
        
        if self.system_prompt_translated:
            # Show original
            stored_system = self.result_data.get('systemPromptTemplate')
            if stored_system:
                system_text = stored_system
            else:
                system_text = self.version_data.get('system_prompt', 'N/A') if self.version_data else 'N/A'
            self.system_prompt_browser.setPlainText(system_text)
            self.system_translate_btn.setText("🌐 Translate")
            self.system_prompt_translated = False
        else:
            # Check if we already have translation
            if self.system_prompt_translation:
                self.system_prompt_browser.setPlainText(self.system_prompt_translation)
                self.system_translate_btn.setText("🔄 Show Original")
                self.system_prompt_translated = True
            else:
                # Need to translate
                self.translate_system_prompt()
    
    def toggle_user_translation(self):
        """Toggle user prompt translation"""
        if not self.db_client or not self.active_endpoint:
            QMessageBox.warning(self, "No LLM Provider", "번역을 위해서는 활성화된 LLM 공급자가 필요합니다.")
            return
        
        if self.user_prompt_translated:
            # Show original
            stored_user = self.result_data.get('userPromptTemplate')
            if stored_user:
                user_text = stored_user
            else:
                content = self.version_data.get('content', '') if self.version_data else ''
                input_data = self.result_data.get('inputData', {})
                user_text = self._render_prompt(content, input_data)
            self.user_prompt_browser.setPlainText(user_text)
            self.user_translate_btn.setText("🌐 Translate")
            self.user_prompt_translated = False
        else:
            # Check if we already have translation
            if self.user_prompt_translation:
                self.user_prompt_browser.setPlainText(self.user_prompt_translation)
                self.user_translate_btn.setText("🔄 Show Original")
                self.user_prompt_translated = True
            else:
                # Need to translate
                self.translate_user_prompt()
    
    def toggle_response_translation(self):
        """Toggle response translation"""
        if not self.db_client or not self.active_endpoint:
            QMessageBox.warning(self, "No LLM Provider", "번역을 위해서는 활성화된 LLM 공급자가 필요합니다.")
            return
        
        if self.response_translated:
            # Show original
            response_content = self._extract_response_content(self.result_data.get('output', {}))
            self.response_browser.setPlainText(response_content)
            self.response_translate_btn.setText("🌐 Translate")
            self.response_translated = False
        else:
            # Check if we already have translation
            if self.response_translation:
                self.response_browser.setPlainText(self.response_translation)
                self.response_translate_btn.setText("🔄 Show Original")
                self.response_translated = True
            else:
                # Need to translate
                self.translate_response()
    
    def translate_system_prompt(self):
        """Translate system prompt"""
        stored_system = self.result_data.get('systemPromptTemplate')
        if stored_system:
            system_text = stored_system
        else:
            system_text = self.version_data.get('system_prompt', 'N/A') if self.version_data else 'N/A'
        
        if not system_text or system_text == 'N/A':
            QMessageBox.warning(self, "No Content", "번역할 내용이 없습니다.")
            return
        
        # Disable button and show loading
        self.system_translate_btn.setEnabled(False)
        self.system_translate_btn.setText("번역 중...")
        self.system_prompt_browser.setPlainText("번역 중... 잠시만 기다려 주세요.")
        
        # Start translation thread
        self.system_translate_thread = TranslateThread(
            self.db_client,
            system_text,
            self.active_endpoint
        )
        self.system_translate_thread.finished.connect(self.on_system_translation_finished)
        self.system_translate_thread.error.connect(self.on_system_translation_error)
        self.system_translate_thread.start()
    
    def translate_user_prompt(self):
        """Translate user prompt"""
        stored_user = self.result_data.get('userPromptTemplate')
        if stored_user:
            user_text = stored_user
        else:
            content = self.version_data.get('content', '') if self.version_data else ''
            input_data = self.result_data.get('inputData', {})
            user_text = self._render_prompt(content, input_data)
        
        if not user_text or user_text == 'N/A':
            QMessageBox.warning(self, "No Content", "번역할 내용이 없습니다.")
            return
        
        # Disable button and show loading
        self.user_translate_btn.setEnabled(False)
        self.user_translate_btn.setText("번역 중...")
        self.user_prompt_browser.setPlainText("번역 중... 잠시만 기다려 주세요.")
        
        # Start translation thread
        self.user_translate_thread = TranslateThread(
            self.db_client,
            user_text,
            self.active_endpoint
        )
        self.user_translate_thread.finished.connect(self.on_user_translation_finished)
        self.user_translate_thread.error.connect(self.on_user_translation_error)
        self.user_translate_thread.start()
    
    def translate_response(self):
        """Translate response"""
        response_content = self._extract_response_content(self.result_data.get('output', {}))
        
        if not response_content or response_content == 'No content':
            QMessageBox.warning(self, "No Content", "번역할 내용이 없습니다.")
            return
        
        # Disable button and show loading
        self.response_translate_btn.setEnabled(False)
        self.response_translate_btn.setText("번역 중...")
        self.response_browser.setPlainText("번역 중... 잠시만 기다려 주세요.")
        
        # Start translation thread
        self.response_translate_thread = TranslateThread(
            self.db_client,
            response_content,
            self.active_endpoint
        )
        self.response_translate_thread.finished.connect(self.on_response_translation_finished)
        self.response_translate_thread.error.connect(self.on_response_translation_error)
        self.response_translate_thread.start()
    
    def on_system_translation_finished(self, translated_text: str):
        """Handle system prompt translation completion"""
        self.system_prompt_translation = translated_text
        self.system_prompt_browser.setPlainText(translated_text)
        self.system_translate_btn.setText("🔄 Show Original")
        self.system_translate_btn.setEnabled(True)
        self.system_prompt_translated = True
    
    def on_system_translation_error(self, error_message: str):
        """Handle system prompt translation error"""
        QMessageBox.warning(self, "Translation Error", f"번역 중 오류가 발생했습니다:\n{error_message}")
        # Restore original text
        stored_system = self.result_data.get('systemPromptTemplate')
        if stored_system:
            system_text = stored_system
        else:
            system_text = self.version_data.get('system_prompt', 'N/A') if self.version_data else 'N/A'
        self.system_prompt_browser.setPlainText(system_text)
        self.system_translate_btn.setText("🌐 Translate")
        self.system_translate_btn.setEnabled(True)
    
    def on_user_translation_finished(self, translated_text: str):
        """Handle user prompt translation completion"""
        self.user_prompt_translation = translated_text
        self.user_prompt_browser.setPlainText(translated_text)
        self.user_translate_btn.setText("🔄 Show Original")
        self.user_translate_btn.setEnabled(True)
        self.user_prompt_translated = True
    
    def on_user_translation_error(self, error_message: str):
        """Handle user prompt translation error"""
        QMessageBox.warning(self, "Translation Error", f"번역 중 오류가 발생했습니다:\n{error_message}")
        # Restore original text
        stored_user = self.result_data.get('userPromptTemplate')
        if stored_user:
            user_text = stored_user
        else:
            content = self.version_data.get('content', '') if self.version_data else ''
            input_data = self.result_data.get('inputData', {})
            user_text = self._render_prompt(content, input_data)
        self.user_prompt_browser.setPlainText(user_text)
        self.user_translate_btn.setText("🌐 Translate")
        self.user_translate_btn.setEnabled(True)
    
    def on_response_translation_finished(self, translated_text: str):
        """Handle response translation completion"""
        self.response_translation = translated_text
        self.response_browser.setPlainText(translated_text)
        self.response_translate_btn.setText("🔄 Show Original")
        self.response_translate_btn.setEnabled(True)
        self.response_translated = True
    
    def on_response_translation_error(self, error_message: str):
        """Handle response translation error"""
        QMessageBox.warning(self, "Translation Error", f"번역 중 오류가 발생했습니다:\n{error_message}")
        # Restore original text
        response_content = self._extract_response_content(self.result_data.get('output', {}))
        self.response_browser.setPlainText(response_content)
        self.response_translate_btn.setText("🌐 Translate")
        self.response_translate_btn.setEnabled(True)


class ResultDetail(QWidget):
    """Widget for displaying detailed result information"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the result detail UI"""
        layout = QVBoxLayout(self)
        
        # Scroll area for content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
        
        # Initial empty state
        self.show_empty_state()
        
    def show_empty_state(self):
        """Show empty state"""
        self.clear_content()
        
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel("🔍")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; margin: 20px;")
        
        message_label = QLabel("Select a history item to see details")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("color: #666; font-size: 14px;")
        
        empty_layout.addWidget(icon_label)
        empty_layout.addWidget(message_label)
        
        self.content_layout.addWidget(empty_widget)
        
    def show_result(self, result_data: Dict[str, Any], version_data: Optional[Dict[str, Any]] = None):
        """Show detailed result information with guaranteed scroll to top"""
        # STEP 1: Immediately force scroll to top before any changes
        self.force_scroll_to_absolute_top()

        # STEP 2: Completely recreate the scroll widget to avoid accumulation
        self.recreate_scroll_widget()

        # STEP 3: Build new content in the fresh widget
        self.build_result_content(result_data, version_data)

        # STEP 4: Final scroll to top with multiple guarantees
        QTimer.singleShot(50, self.force_scroll_to_absolute_top)
        QTimer.singleShot(150, self.force_scroll_to_absolute_top)
        QTimer.singleShot(300, self.force_scroll_to_absolute_top)
    
    def recreate_scroll_widget(self):
        """Completely recreate the scroll widget to avoid content accumulation"""
        try:
            # Remove old scroll area completely
            layout = self.layout()
            if layout:
                for i in reversed(range(layout.count())):
                    item = layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        widget.setParent(None)
                        widget.deleteLater()
            
            # Create completely new scroll area
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            # Create new content widget
            self.content_widget = QWidget()
            self.content_layout = QVBoxLayout(self.content_widget)
            
            # Set up scroll area
            self.scroll_area.setWidget(self.content_widget)
            
            # Add to main layout
            layout.addWidget(self.scroll_area)
            
        except Exception as e:
            pass
    
    def force_scroll_to_absolute_top(self):
        """Force scroll to absolute top with maximum certainty"""
        try:
            if not hasattr(self, 'scroll_area') or not self.scroll_area:
                return
            
            # Get vertical scrollbar
            scrollbar = self.scroll_area.verticalScrollBar()
            
            # Method 1: Set value to 0 multiple times
            scrollbar.setValue(0)
            scrollbar.setSliderPosition(0)
            
            # Method 2: Update geometry first, then scroll
            if hasattr(self, 'content_widget') and self.content_widget:
                self.content_widget.updateGeometry()
                self.content_widget.adjustSize()
                
            self.scroll_area.updateGeometry()
            
            # Method 3: Force immediate scroll
            scrollbar.setValue(0)
            
            # Method 4: Use ensureVisible for top-left corner
            self.scroll_area.ensureVisible(0, 0, 0, 0)
            
            # Method 5: Final value setting
            scrollbar.setValue(0)
            
        except Exception as e:
            pass
    
    def build_result_content(self, result_data: Dict[str, Any], version_data: Optional[Dict[str, Any]] = None):
        """Build the result content"""
        # Request section
        request_group = QGroupBox("Request Message")
        request_layout = QVBoxLayout(request_group)
        
        # Build request message using stored templates first (fixes timing issue)
        stored_system_template = result_data.get('systemPromptTemplate')
        stored_user_template = result_data.get('userPromptTemplate')

        if stored_system_template and stored_user_template:
            # Use stored templates from execution time (accurate)
            system_prompt = stored_system_template
            user_prompt = stored_user_template
        else:
            # Fallback to current version templates (may be inaccurate for old results)
            system_prompt = version_data.get('system_prompt', '') if version_data else ''
            user_prompt = self._render_prompt(
                version_data.get('content', '') if version_data else '',
                result_data.get('inputData', {})
            )
        
        request_text = f"---------- System Prompt ----------\n{system_prompt}\n\n---------- User Prompt ----------\n{user_prompt}"
        
        request_edit = QTextBrowser()
        request_edit.setPlainText(request_text)
        request_edit.setMaximumHeight(200)
        request_layout.addWidget(request_edit)
        
        self.content_layout.addWidget(request_group)
        
        # Response section
        response_group = QGroupBox("Response")
        response_layout = QVBoxLayout(response_group)
        
        response_content = self._extract_response_content(result_data.get('output', {}))
        response_edit = QTextBrowser()
        response_edit.setPlainText(response_content)
        response_edit.setMaximumHeight(300)
        response_layout.addWidget(response_edit)
        
        self.content_layout.addWidget(response_group)
        
        # Metrics section
        metrics_group = QGroupBox("Metrics")
        metrics_layout = QFormLayout(metrics_group)
        
        # Model
        endpoint = result_data.get('endpoint', {})
        model = endpoint.get('defaultModel') or endpoint.get('name', 'Unknown')
        metrics_layout.addRow("Model:", QLabel(model))
        
        # Temperature
        temperature = result_data.get('temperature', 0.7)
        metrics_layout.addRow("Temperature:", QLabel(f"{temperature:.1f}"))
        
        # Token calculation
        input_tokens = self._calculate_tokens(request_text)
        output_tokens = self._calculate_tokens(response_content)
        total_tokens = input_tokens + output_tokens
        
        metrics_layout.addRow("Tokens Used:", QLabel(f"{total_tokens:,}"))
        metrics_layout.addRow("Token Breakdown:", QLabel(f"{input_tokens:,} in, {output_tokens:,} out"))
        
        # Cost estimation
        estimated_cost = self._calculate_cost(input_tokens, output_tokens, model)
        metrics_layout.addRow("Estimated Cost:", QLabel(estimated_cost))
        
        self.content_layout.addWidget(metrics_group)
        
        # Variables section
        input_data = result_data.get('inputData', {})
        if input_data:
            variables_group = QGroupBox("Input Variables")
            variables_layout = QVBoxLayout(variables_group)
            
            variables_edit = QTextBrowser()
            variables_edit.setPlainText(json.dumps(input_data, indent=2, ensure_ascii=False))
            variables_edit.setMaximumHeight(150)
            variables_layout.addWidget(variables_edit)
            
            self.content_layout.addWidget(variables_group)
            
        # Raw output section
        raw_group = QGroupBox("Raw Output")
        raw_layout = QVBoxLayout(raw_group)
        
        raw_edit = QTextBrowser()
        raw_edit.setPlainText(json.dumps(result_data.get('output', {}), indent=2, ensure_ascii=False))
        raw_edit.setMaximumHeight(200)
        raw_layout.addWidget(raw_edit)
        
        self.content_layout.addWidget(raw_group)
        
        # Add stretch
        self.content_layout.addStretch()
    
    def force_scroll_to_top(self):
        """Force scroll to top with aggressive methods"""
        try:
            if hasattr(self, 'scroll_area') and self.scroll_area:
                scrollbar = self.scroll_area.verticalScrollBar()
                
                # Reset scroll position to absolute top
                scrollbar.setValue(0)
                scrollbar.setSliderPosition(0)
                
                # Force scroll area update
                self.scroll_area.verticalScrollBar().setValue(0)
                
                # Ensure widget is positioned at top
                if hasattr(self, 'content_widget') and self.content_widget:
                    self.scroll_area.ensureWidgetVisible(self.content_widget, 0, 0)
                
                # Update geometry
                self.content_widget.updateGeometry()
                self.scroll_area.updateGeometry()
                
                print(f"FORCE scrolled to top - final value: {scrollbar.value()}")
        except Exception as e:
            print(f"Error in force_scroll_to_top: {e}")
        
    def clear_content_immediately(self):
        """Clear content immediately without deleteLater"""
        try:
            # Hide all widgets first
            for i in range(self.content_layout.count()):
                item = self.content_layout.itemAt(i)
                if item and item.widget():
                    item.widget().hide()
            
            # Remove all widgets immediately
            while self.content_layout.count():
                item = self.content_layout.takeAt(0)
                if item and item.widget():
                    widget = item.widget()
                    widget.setParent(None)
                    widget.deleteLater()
            
            print("Content cleared immediately")
            
        except Exception as e:
            print(f"Error clearing content: {e}")
        
    def clear_content(self):
        """Clear the content - fallback method"""
        self.clear_content_immediately()
                
    def _render_prompt(self, template: str, variables: Dict[str, Any]) -> str:
        """Render prompt template with variables"""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
        
    def _extract_response_content(self, output: Any) -> str:
        """Extract response content from output"""
        if isinstance(output, dict):
            if 'choices' in output and output['choices']:
                return output['choices'][0].get('message', {}).get('content', 'No content')
            elif 'content' in output:
                return output['content']
        elif isinstance(output, str):
            return output
        return 'No content available'
        
    def _calculate_tokens(self, text: str) -> int:
        """Estimate token count (simple approximation)"""
        return math.ceil(len(text) / 4)
        
    def _calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> str:
        """Calculate estimated cost"""
        # Cost per 1K tokens (approximate)
        costs = {
            'gpt-4o': {'input': 0.0025, 'output': 0.01},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
            'claude-3-opus': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
            'claude-3-haiku': {'input': 0.00025, 'output': 0.00125}
        }
        
        model_cost = costs.get(model, costs['gpt-3.5-turbo'])
        total_cost = (input_tokens / 1000 * model_cost['input']) + (output_tokens / 1000 * model_cost['output'])
        
        return f"${total_cost:.4f}"


class ResultViewer(QWidget):
    """Main result viewer widget"""
    
    def __init__(self):
        super().__init__()
        
        self.db_client = DatabaseClient()
        self.current_task_id: Optional[str] = None
        self.current_version_id: Optional[str] = None
        self.task_data: Optional[Dict[str, Any]] = None
        self.version_data: Optional[Dict[str, Any]] = None
        self.results: List[Dict[str, Any]] = []
        self.active_endpoints: List[Dict[str, Any]] = []
        self.active_endpoint: Optional[Dict[str, Any]] = None
        
        
        self.setup_ui()
        self.load_endpoints()
        
    def setup_ui(self):
        """Setup the result viewer UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f8f9fa; border-bottom: 1px solid #dee2e6;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        # Title and status
        title_layout = QHBoxLayout()
        
        title_label = QLabel("Result")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        title_layout.addWidget(self.status_label)
        
        header_layout.addLayout(title_layout)
        
        # LLM Provider 선택 영역
        self.provider_container = QWidget()
        self.provider_container.setFixedHeight(90)  # 더 여유있게
        self.provider_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-bottom: 1px solid #dee2e6;
            }
        """)

        provider_layout = QVBoxLayout(self.provider_container)
        provider_layout.setContentsMargins(15, 15, 15, 15)  # 모든 방향 여유있게
        provider_layout.setSpacing(8)

        # 라벨
        provider_label = QLabel("LLM Provider")
        provider_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #6c757d;
                font-weight: 500;
            }
        """)

        # 드롭박스 - 핵심 수정
        self.provider_combo = QComboBox()
        self.provider_combo.setFixedHeight(45)  # 40 → 45로 증가
        self.provider_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 10px 12px;  /* 상하 패딩 증가 */
                padding-right: 35px;
                background-color: white;
                font-size: 14px;
                line-height: 20px;  /* line-height 명시 */
            }
            QComboBox:hover {
                border-color: #80bdff;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ced4da;
                background-color: white;
                selection-background-color: #e3f2fd;
                padding: 5px;
            }
            QComboBox QAbstractItemView::item {
                height: 40px;  /* 드롭다운 아이템 높이 */
                padding: 8px 12px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)

        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_combo)
        
        # Connect ComboBox signal
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        
        header_layout.addWidget(self.provider_container)
        
        # Temperature 설정 영역
        self.temperature_container = QWidget()
        self.temperature_container.setFixedHeight(90)
        self.temperature_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-bottom: 1px solid #dee2e6;
            }
        """)

        temp_layout = QVBoxLayout(self.temperature_container)
        temp_layout.setContentsMargins(15, 15, 15, 15)
        temp_layout.setSpacing(8)

        # Temperature 라벨
        temp_label = QLabel("Temperature")
        temp_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #6c757d;
                font-weight: 500;
            }
        """)
        temp_layout.addWidget(temp_label)

        # Temperature 설정 컨트롤들
        temp_control_layout = QHBoxLayout()
        temp_control_layout.setSpacing(10)

        # Temperature 슬라이더
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 20)  # 0.0 ~ 2.0 (x10, 0.1 단위)
        self.temperature_slider.setValue(7)  # 기본값 0.7
        self.temperature_slider.setFixedHeight(30)
        self.temperature_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #f0f0f0;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #007bff;
                border: 1px solid #777;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #007bff;
                border: 1px solid #5c6bc0;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #0056b3;
            }
        """)

        # Temperature 값 표시 및 입력
        self.temperature_spinbox = QDoubleSpinBox()
        self.temperature_spinbox.setRange(0.0, 2.0)
        self.temperature_spinbox.setDecimals(1)  # 소수점 1자리로 변경
        self.temperature_spinbox.setSingleStep(0.1)  # 0.1 단위로 변경
        self.temperature_spinbox.setValue(0.7)  # 0.7로 변경
        self.temperature_spinbox.setFixedWidth(70)
        self.temperature_spinbox.setFixedHeight(30)
        self.temperature_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px 6px;
                background-color: white;
                font-size: 12px;
                font-weight: 600;
            }
            QDoubleSpinBox:hover {
                border-color: #80bdff;
            }
        """)

        temp_control_layout.addWidget(self.temperature_slider, 1)
        temp_control_layout.addWidget(self.temperature_spinbox)

        temp_layout.addLayout(temp_control_layout)

        # Connect signals for synchronization
        self.temperature_slider.valueChanged.connect(self.on_temperature_slider_changed)
        self.temperature_spinbox.valueChanged.connect(self.on_temperature_spinbox_changed)
        
        header_layout.addWidget(self.temperature_container)
        
        layout.addWidget(header_frame)
        
        # Main tabs - without Variables tab (moved to main sidebar)
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_response_tab(), "Response")
        self.tab_widget.addTab(self.create_history_tab(), "History (0)")
        self.tab_widget.addTab(self.create_comparison_tab(), "Comparison")
        self.tab_widget.addTab(self.create_metrics_tab(), "Metrics")
        
        layout.addWidget(self.tab_widget, 1)
        
        # Initial state
        self.show_no_task_state()

    def on_temperature_slider_changed(self, value: int):
        """Handle temperature slider change"""
        # Convert slider value (0-20) to temperature (0.0-2.0) - 0.1 단위
        temperature = value / 10.0
        # Update spinbox without triggering its signal
        self.temperature_spinbox.blockSignals(True)
        self.temperature_spinbox.setValue(temperature)
        self.temperature_spinbox.blockSignals(False)

    def on_temperature_spinbox_changed(self, value: float):
        """Handle temperature spinbox change"""
        # Convert temperature (0.0-2.0) to slider value (0-20) - 0.1 단위
        slider_value = int(value * 10)
        # Update slider without triggering its signal
        self.temperature_slider.blockSignals(True)
        self.temperature_slider.setValue(slider_value)
        self.temperature_slider.blockSignals(False)

    def get_temperature(self) -> float:
        """Get current temperature value"""
        return self.temperature_spinbox.value()
        
    def finish_setup_ui(self, layout):
        """Complete the setup_ui method"""
        # Main tabs - without Variables tab (moved to main sidebar)
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_response_tab(), "Response")
        self.tab_widget.addTab(self.create_history_tab(), "History (0)")
        self.tab_widget.addTab(self.create_comparison_tab(), "Comparison")
        self.tab_widget.addTab(self.create_metrics_tab(), "Metrics")
        
        layout.addWidget(self.tab_widget, 1)
        
        # Initial state
        self.show_no_task_state()
        
    def create_response_tab(self) -> QWidget:
        """Create the response tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Run button
        self.run_button = QPushButton("🚀 Run Prompt")
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.run_button.clicked.connect(self.run_prompt)
        layout.addWidget(self.run_button)
        
        # Progress bar (hidden by default) - 높이 0으로 시작하여 레이아웃 영향 제거
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(0)  # 초기 높이 0
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #007bff;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007bff;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Result display area
        self.result_display = QWidget()
        result_layout = QVBoxLayout(self.result_display)
        
        # This will be populated dynamically
        layout.addWidget(self.result_display, 1)
        
        return widget
        
        
    def create_history_tab(self) -> QWidget:
        """Create the history tab"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # History list
        history_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: History list
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.history_list_widget = QWidget()
        self.history_list_layout = QVBoxLayout(self.history_list_widget)
        self.history_list_layout.addStretch()
        
        self.history_scroll.setWidget(self.history_list_widget)
        history_layout.addWidget(self.history_scroll)
        
        history_splitter.addWidget(history_widget)
        
        # Right: Result detail
        self.result_detail = ResultDetail()
        history_splitter.addWidget(self.result_detail)
        
        # Set splitter proportions
        history_splitter.setSizes([300, 500])
        
        layout.addWidget(history_splitter)
        
        return widget
        
    def create_comparison_tab(self) -> QWidget:
        """Create the comparison tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Placeholder for comparison functionality
        placeholder = QLabel("Comparison functionality coming soon...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #666; font-size: 14px; font-style: italic;")
        layout.addWidget(placeholder)
        
        return widget
        
    def create_metrics_tab(self) -> QWidget:
        """Create the metrics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Placeholder for metrics functionality  
        placeholder = QLabel("Metrics dashboard coming soon...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #666; font-size: 14px; font-style: italic;")
        layout.addWidget(placeholder)
        
        return widget
        
    def load_endpoints(self):
        """Load LLM endpoints"""
        try:
            endpoints_data = self.db_client.get_llm_endpoints()
            self.active_endpoints = endpoints_data.get('endpoints', [])
            active_id = endpoints_data.get('activeEndpointId')
            
            # Find active endpoint
            self.active_endpoint = None
            for endpoint in self.active_endpoints:
                if endpoint['id'] == active_id:
                    self.active_endpoint = endpoint
                    break
                    
            # Load providers into ComboBox
            self.load_llm_providers()
            
        except Exception as e:
            print(f"Failed to load endpoints: {e}")
            
    def load_llm_providers(self):
        """Load LLM Provider 목록을 ComboBox에 로드"""
        self.provider_combo.clear()
        
        if not self.active_endpoints:
            self.provider_combo.addItem("🔴 No LLM Provider", userData=None)
            self.run_button.setEnabled(False)
            return
            
        # 각 endpoint에 대해 ComboBox 아이템 추가
        default_index = 0
        for i, provider in enumerate(self.active_endpoints):
            # 연결 상태 아이콘
            status_icon = "🟢"  # 기본적으로 연결된 것으로 표시
            
            # 표시 텍스트 생성
            provider_name = provider.get('name', 'Unknown')
            model_name = provider.get('defaultModel', '')
            
            if model_name:
                display_text = f"{status_icon} {provider_name} • {model_name}"
            else:
                display_text = f"{status_icon} {provider_name}"
                
            # ComboBox에 아이템 추가
            self.provider_combo.addItem(display_text, userData=provider)
            
            # 현재 active endpoint인 경우 기본 선택으로 설정
            if self.active_endpoint and provider['id'] == self.active_endpoint['id']:
                default_index = i
                
        # 기본 선택 설정
        self.provider_combo.setCurrentIndex(default_index)
        self.run_button.setEnabled(True)
        
    def on_provider_changed(self, index: int):
        """Provider 선택 변경 이벤트 핸들러"""
        if index < 0:
            return
            
        # 선택된 provider 데이터 가져오기
        selected_provider = self.provider_combo.itemData(index)
        
        if selected_provider:
            # Active endpoint 업데이트
            self.active_endpoint = selected_provider
            
            # 데이터베이스에 active endpoint 설정
            try:
                self.db_client.set_active_endpoint(selected_provider['id'])
                self.run_button.setEnabled(True)
                
                # 상태 업데이트
                self.status_label.setText(f"Provider changed to {selected_provider.get('name', 'Unknown')}")
                
            except Exception as e:
                print(f"Failed to set active endpoint: {e}")
        else:
            self.active_endpoint = None
            self.run_button.setEnabled(False)
            
    def update_provider_info(self):
        """Update provider information display"""
        if self.active_endpoint:
            self.provider_status_dot.setText("🟢")
            self.provider_name_label.setText(self.active_endpoint.get('name', 'Unknown'))
            
            model = self.active_endpoint.get('defaultModel', '')
            self.provider_model_label.setText(f"• {model}" if model else "")
            
            # Enable run button
            self.run_button.setEnabled(True)
        else:
            self.provider_status_dot.setText("🔴")
            self.provider_name_label.setText("No LLM Provider")
            self.provider_model_label.setText("")
            
            # Disable run button
            self.run_button.setEnabled(False)
            
    def set_task_id(self, task_id: str):
        """Set the current task and completely refresh sidebar"""
        print(f"ResultViewer: Setting task ID to {task_id}")
        
        # Store new task ID
        self.current_task_id = task_id
        self.current_version_id = None
        
        # Complete data reset
        self.task_data = None
        self.version_data = None
        self.results = []
        
        # Clear all UI components
        self.clear_all_content()
        
        # Load new task data
        self.load_task_data()
        
    def set_version_id(self, version_id: str):
        """Set the current version and refresh results"""
        print(f"ResultViewer: Setting version ID to {version_id}")
        
        # Store new version ID
        self.current_version_id = version_id
        
        # Clear version-specific data
        self.version_data = None
        self.results = []
        
        # Clear result detail area
        self.result_detail.show_empty_state()
        
        # Load new version data
        self.load_version_data()
        
    def load_task_data(self):
        """Load task data"""
        if not self.current_task_id:
            self.show_no_task_state()
            return
            
        try:
            # Load task info
            tasks_response = self.db_client.get_tasks()
            if tasks_response:
                tasks = {t['id']: t for t in tasks_response}
                self.task_data = tasks.get(self.current_task_id)
            
                
            self.show_task_selected_state()
            
        except Exception as e:
            QMessageBox.warning(self, "Loading Error", f"Failed to load task data: {str(e)}")
            
    def load_version_data(self):
        """Load version data and results"""
        if not self.current_task_id or not self.current_version_id:
            return
            
        try:
            # Load versions to get version data
            versions = self.db_client.get_versions(self.current_task_id)
            self.version_data = None
            
            for version in versions:
                if version['id'] == self.current_version_id:
                    self.version_data = version
                    break
                    
            # Load results from version data
            if self.version_data and 'results' in self.version_data:
                self.results = self.version_data['results']
            else:
                self.results = []
                
            self.refresh_history()
            
        except Exception as e:
            print(f"Failed to load version data: {e}")
            
    def refresh_history(self):
        """Refresh the history display"""
        # Update history tab title
        history_count = len(self.results)
        self.tab_widget.setTabText(1, f"History ({history_count})")
        
        # Clear existing history items
        for i in reversed(range(self.history_list_layout.count() - 1)):  # Keep stretch
            child = self.history_list_layout.itemAt(i)
            if child and child.widget():
                child.widget().deleteLater()
                
        # Add history items
        if self.results:
            for i, result in enumerate(self.results):
                history_item = ResultHistoryItem(result, len(self.results) - i)

                # 시그널에서 emit된 데이터를 직접 받아서 처리
                history_item.clicked.connect(self.on_history_item_clicked)
                history_item.double_clicked.connect(self.on_history_item_double_clicked)
                history_item.delete_requested.connect(self.delete_history_item)

                self.history_list_layout.insertWidget(
                    self.history_list_layout.count() - 1,
                    history_item
                )
        else:
            # Show empty state
            empty_label = QLabel("No execution history")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #666; font-style: italic; padding: 40px;")
            self.history_list_layout.insertWidget(0, empty_label)
    
    def on_history_item_clicked(self, result_data: Dict[str, Any]):
        """Handle history item click - receives data directly from signal"""
        # Pass the result data to the detail view
        self.result_detail.show_result(result_data, self.version_data)
    
    def on_history_item_double_clicked(self, result_data: Dict[str, Any]):
        """Handle history item double click - show detailed popup"""
        dialog = ResultDetailDialog(
            result_data, 
            self.version_data, 
            self.db_client,
            self.active_endpoint,
            self
        )
        dialog.exec()
            
    def run_prompt(self):
        """Run the current prompt"""
        if not self.current_task_id or not self.current_version_id or not self.active_endpoint:
            return
            
        if not self.version_data:
            QMessageBox.warning(self, "No Version", "Please select a version to run")
            return
            
        # Extract variables from prompt
        content = self.version_data.get('content', '')
        system_prompt = self.version_data.get('system_prompt', '')
        
        # Simple variable extraction (could be more sophisticated)
        import re
        variables = {}
        matches = re.findall(r'\{\{([a-zA-Z_][a-zA-Z0-9_-]*)\}\}', content + system_prompt)
        
        # Get variables from task data (this should come from variable editor)
        if self.task_data and 'variables' in self.task_data:
            task_variables = self.task_data['variables']
            for var in set(matches):
                variables[var] = task_variables.get(var, f"[{var}]")
        else:
            for var in set(matches):
                variables[var] = f"[{var}]"
                
        # Show loading state - 높이를 명시적으로 설정
        self.run_button.setEnabled(False)
        self.progress_bar.setFixedHeight(4)  # 보일 때 높이 설정
        self.progress_bar.setVisible(True)
        self.status_label.setText("Running...")
        
        # Get current temperature setting
        temperature = self.get_temperature()
        
        # Start LLM call thread
        self.llm_thread = LLMCallThread(
            self.db_client,
            self.current_task_id,
            self.current_version_id,
            variables,
            system_prompt,
            self.active_endpoint,
            temperature  # Pass temperature value
        )
        self.llm_thread.finished.connect(self.on_llm_finished)
        self.llm_thread.error.connect(self.on_llm_error)
        self.llm_thread.start()
        
    def on_llm_finished(self, result: Dict[str, Any]):
        """Handle LLM call completion"""
        # Hide loading state - 높이를 0으로 설정
        self.run_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(0)  # 숨길 때 높이 0
        self.status_label.setText(f"Completed at {datetime.now().strftime('%H:%M:%S')}")
        
        # Reload version data from DB to get the newly saved result with templates
        self.load_version_data()
        
        # Get the latest result (first in list since they're sorted by timestamp DESC)
        if self.results:
            latest_result = self.results[0]
            self.show_latest_result(latest_result)
        
    def on_llm_error(self, error: str):
        """Handle LLM call error"""
        # Hide loading state - 높이를 0으로 설정
        self.run_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(0)  # 숨길 때 높이 0
        self.status_label.setText("Error")
        
        QMessageBox.critical(self, "LLM Error", f"Failed to call LLM: {error}")
        
    def show_latest_result(self, result_data: Dict[str, Any]):
        """Show the latest result with optimized layout (10-75-5-5-5%)"""
        # Switch to response tab
        self.tab_widget.setCurrentIndex(0)
        
        # 핵심 수정: 레이아웃 업데이트를 일시 차단하고 완전히 정리 후 재구축
        # 레이아웃 업데이트 차단
        self.result_display.setUpdatesEnabled(False)
        
        try:
            # 기존 컨테이너를 완전히 제거
            if self.result_display.layout():
                layout = self.result_display.layout()
                # 모든 아이템을 즉시 제거
                while layout.count():
                    item = layout.takeAt(0)
                    if item and item.widget():
                        widget = item.widget()
                        # run_button과 progress_bar는 유지
                        if widget not in [self.run_button, self.progress_bar]:
                            widget.hide()
                            widget.setParent(None)
                            widget.deleteLater()
            
            # 레이아웃 강제 처리 - 삭제 완료 보장
            self.result_display.layout().update()
            QApplication.processEvents()
            
            # Create main result container - 간격 0으로 겹침 방지
            result_container = QWidget()
            container_layout = QVBoxLayout(result_container)
            container_layout.setContentsMargins(0, 0, 0, 0)  # 외부 여백 제거
            container_layout.setSpacing(0)  # 위젯 간 간격 제거로 겹침 방지
            
            # 1. 메타 정보 영역 (고정 높이)
            meta_widget = self.create_meta_info_widget(result_data)
            container_layout.addWidget(meta_widget, 0)  # 고정 크기
            
            # 2. 메인 콘텐츠 영역 (최대 공간 사용)  
            main_response_widget = self.create_main_response_widget(result_data)
            container_layout.addWidget(main_response_widget, 1)  # 모든 남은 공간 사용
            
            # 3. 액션 버튼 영역 (고정 높이)
            action_buttons_widget = self.create_action_buttons_widget(result_data)
            container_layout.addWidget(action_buttons_widget, 0)  # 고정 크기
            
            # 4. 상세 정보 영역 (고정 높이)
            detail_info_widget = self.create_detail_info_widget(result_data)
            container_layout.addWidget(detail_info_widget, 0)  # 고정 크기
            
            # 5. 상태바 (고정 높이)
            status_bar_widget = self.create_status_bar_widget(result_data)
            container_layout.addWidget(status_bar_widget, 0)  # 고정 크기
            
            # Add to display
            self.result_display.layout().addWidget(result_container)
            
        finally:
            # 레이아웃 업데이트 재개
            self.result_display.setUpdatesEnabled(True)
            # 강제 리프레시
            self.result_display.update()
        
    def create_summary_card(self, result_data: Dict[str, Any]) -> QWidget:
        """Create simple summary info"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Model info
        model_name = self.active_endpoint.get('defaultModel', 'Unknown Model')
        provider_name = self.active_endpoint.get('name', 'AI')
        model_label = QLabel(f"✅ {provider_name} • {model_name}")
        model_label.setStyleSheet("font-weight: 500; font-size: 12px; color: #495057;")
        layout.addWidget(model_label)
        
        layout.addStretch()
        
        # Simple metrics
        input_data = result_data.get('inputData', {})
        output = result_data.get('output', {})
        
        # Estimate tokens
        input_text = json.dumps(input_data) if input_data else ""
        if isinstance(output, dict) and 'choices' in output and output['choices']:
            output_text = output['choices'][0].get('message', {}).get('content', '')
        else:
            output_text = str(output)
            
        input_tokens = max(1, len(input_text) // 4)
        output_tokens = max(1, len(output_text) // 4)
        total_tokens = input_tokens + output_tokens
        
        tokens_label = QLabel(f"{total_tokens:,} tokens")
        tokens_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        layout.addWidget(tokens_label)
        
        return card
        
    def create_response_card(self, result_data: Dict[str, Any]) -> QWidget:
        """Create main response display card"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header with copy button
        header_layout = QHBoxLayout()
        
        response_title = QLabel("AI Response")
        response_title.setFont(QFont("", 11, QFont.Weight.Medium))
        response_title.setStyleSheet("color: #495057;")
        header_layout.addWidget(response_title)
        
        header_layout.addStretch()
        
        # Copy button - more visible
        copy_button = QPushButton("📋 Copy")
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        copy_button.clicked.connect(lambda: self.copy_response_content(result_data))
        header_layout.addWidget(copy_button)
        
        layout.addLayout(header_layout)
        
        # Response content
        content = self._extract_response_content(result_data.get('output', {}))
        response_text = QTextBrowser()
        response_text.setPlainText(content)
        response_text.setStyleSheet("""
            QTextBrowser {
                border: none;
                background-color: #f8f9fa;
                border-radius: 4px;
                padding: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        response_text.setMaximumHeight(300)  # Reduced height
        layout.addWidget(response_text)
        
        return card

    def create_meta_info_widget(self, result_data: Dict[str, Any]) -> QWidget:
        """1️⃣ 메타 정보 영역 - 고정 높이로 겹침 방지"""
        widget = QWidget()
        widget.setFixedHeight(50)  # 고정 높이로 겹침 방지
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 10, 15, 10)  # 상하 여백 충분히
        layout.setSpacing(20)
        
        # 실행 상태 + 모델 정보
        model_name = self.active_endpoint.get('defaultModel', 'Unknown Model')
        provider_name = self.active_endpoint.get('name', 'AI')
        model_label = QLabel(f"✅ {provider_name} • {model_name}")
        model_label.setStyleSheet("font-weight: 600; font-size: 12px; color: #495057;")
        layout.addWidget(model_label)
        
        layout.addStretch()
        
        # 토큰 수
        total_tokens = self._calculate_total_tokens(result_data)
        tokens_label = QLabel(f"{total_tokens} tokens")
        tokens_label.setStyleSheet("font-size: 11px; color: #6c757d; font-weight: 500;")
        layout.addWidget(tokens_label)
        
        # 응답 시간 (추정)
        time_label = QLabel("⏱ 2.3s")
        time_label.setStyleSheet("font-size: 11px; color: #6c757d; font-weight: 500;")
        layout.addWidget(time_label)
        
        return widget

    def create_main_response_widget(self, result_data: Dict[str, Any]) -> QWidget:
        """2️⃣ 메인 콘텐츠 영역 (75%) - AI 응답을 위한 최대 공간"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # 헤더: 제목 + Copy 버튼
        header_layout = QHBoxLayout()
        
        title_label = QLabel("AI Response")
        title_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #495057;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Copy 버튼
        copy_btn = QPushButton("📋 Copy")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        copy_btn.clicked.connect(lambda: self.copy_response_content(result_data))
        header_layout.addWidget(copy_btn)
        
        layout.addLayout(header_layout)
        
        # 메인 응답 영역 - 스크롤 가능, 마크다운 렌더링 가능
        response_content = self._extract_response_content(result_data.get('output', {}))
        
        response_text = QTextBrowser()
        response_text.setPlainText(response_content)
        response_text.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #e9ecef;
                background-color: #fdfdfd;
                border-radius: 4px;
                padding: 16px;
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #333;
            }
        """)
        
        # 최소 높이 제거 - stretch factor로만 크기 관리하여 일관성 유지
        # 높이는 전적으로 부모 레이아웃의 stretch factor에 의존
        
        layout.addWidget(response_text, 1)  # stretch factor로 최대 공간 사용
        
        return widget

    def create_action_buttons_widget(self, result_data: Dict[str, Any]) -> QWidget:
        """3️⃣ 액션 버튼 영역 - Retry & Translate 버튼을 가로로 나란히 배치"""
        from PyQt6.QtWidgets import QSizePolicy
        
        # 버튼 컨테이너
        button_container = QWidget()
        button_container.setFixedHeight(60)
        button_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-top: 1px solid #dee2e6;
                border-bottom: 1px solid #dee2e6;
            }
        """)

        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(15, 10, 15, 10)  # 좌우 여백
        button_layout.setSpacing(10)  # 버튼 사이 간격

        # Retry 버튼 - 50% 너비
        retry_btn = QPushButton("🔄  Retry")
        retry_btn.setFixedHeight(40)  # 높이는 고정
        retry_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # 가로로 확장
            QSizePolicy.Policy.Fixed       # 세로는 고정
        )

        retry_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: 600;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        
        retry_btn.clicked.connect(self.run_prompt)

        # Translate 버튼 - 50% 너비
        translate_btn = QPushButton("🌐  Translate")
        translate_btn.setFixedHeight(40)  # 높이는 고정
        translate_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # 가로로 확장
            QSizePolicy.Policy.Fixed       # 세로는 고정
        )

        translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: 600;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        translate_btn.clicked.connect(lambda: self.translate_response(result_data))

        # 버튼들을 나란히 배치
        button_layout.addWidget(retry_btn)
        button_layout.addWidget(translate_btn)
        
        return button_container

    def create_detail_info_widget(self, result_data: Dict[str, Any]) -> QWidget:
        """4️⃣ 상세 정보 영역 - 고정 높이로 겹침 방지"""
        widget = QWidget()
        widget.setFixedHeight(60)  # 고정 높이로 겹침 방지
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(3)
        
        # 첫 번째 줄: 토큰 사용량 / 비용
        first_line = QHBoxLayout()
        
        total_tokens = self._calculate_total_tokens(result_data)
        estimated_cost = self._estimate_cost(result_data)
        
        usage_label = QLabel(f"📊 Token Usage: {total_tokens} / Cost: {estimated_cost}")
        usage_label.setStyleSheet("font-size: 11px; color: #495057; font-weight: 500;")
        first_line.addWidget(usage_label)
        first_line.addStretch()
        
        layout.addLayout(first_line)
        
        # 두 번째 줄: 모델 정보 / 설정
        second_line = QHBoxLayout()
        
        model_name = self.active_endpoint.get('defaultModel', 'Unknown')
        current_temp = self.get_temperature()
        model_info_label = QLabel(f"Model: {model_name} | Temp: {current_temp:.2f}")
        model_info_label.setStyleSheet("font-size: 10px; color: #6c757d;")
        second_line.addWidget(model_info_label)
        second_line.addStretch()
        
        layout.addLayout(second_line)
        
        return widget

    def create_status_bar_widget(self, result_data: Dict[str, Any]) -> QWidget:
        """5️⃣ 상태바 - 고정 높이로 겹침 방지"""
        widget = QWidget()
        widget.setFixedHeight(35)  # 고정 높이로 겹침 방지
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 5, 15, 5)
        
        # 연결 상태
        if self.active_endpoint:
            status_label = QLabel("🟢 Connected")
            status_label.setStyleSheet("font-size: 11px; color: #28a745; font-weight: 500;")
        else:
            status_label = QLabel("🔴 No LLM Provider")
            status_label.setStyleSheet("font-size: 11px; color: #dc3545; font-weight: 500;")
            
        layout.addWidget(status_label)
        layout.addStretch()
        
        # 완료 시간
        completed_time = datetime.now().strftime("%H:%M:%S")
        time_label = QLabel(f"Completed at {completed_time}")
        time_label.setStyleSheet("font-size: 10px; color: #6c757d;")
        layout.addWidget(time_label)
        
        return widget

    def _calculate_total_tokens(self, result_data: Dict[str, Any]) -> int:
        """토큰 수 계산"""
        input_data = result_data.get('inputData', {})
        output = result_data.get('output', {})
        
        # API 응답에서 직접 토큰 정보 확인
        if isinstance(output, dict) and 'usage' in output:
            usage = output['usage']
            return usage.get('total_tokens', 0)
        
        # 추정 계산
        input_text = json.dumps(input_data) if input_data else ""
        if isinstance(output, dict) and 'choices' in output and output['choices']:
            output_text = output['choices'][0].get('message', {}).get('content', '')
        else:
            output_text = str(output)
            
        total_chars = len(input_text) + len(output_text)
        return max(1, total_chars // 4)  # 대략적인 토큰 추정

    def _estimate_cost(self, result_data: Dict[str, Any]) -> str:
        """비용 추정"""
        total_tokens = self._calculate_total_tokens(result_data)
        model_name = self.active_endpoint.get('defaultModel', 'gpt-3.5-turbo')
        
        # 간단한 비용 추정 (실제로는 모델별로 다름)
        cost_per_1k_tokens = {
            'gpt-4o': 0.005,
            'gpt-4': 0.03,
            'gpt-3.5-turbo': 0.002,
            'claude-3-opus': 0.045,
            'claude-3-sonnet': 0.009,
        }
        
        cost_rate = cost_per_1k_tokens.get(model_name, 0.002)
        estimated_cost = (total_tokens / 1000) * cost_rate
        
        return f"${estimated_cost:.3f}"
        
    def create_action_buttons(self, result_data: Dict[str, Any]) -> QWidget:
        """Create simple action buttons row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Only essential buttons
        retry_btn = QPushButton("🔄 Retry")
        retry_btn.setStyleSheet(self.get_action_button_style("#007bff"))
        retry_btn.clicked.connect(self.run_prompt)
        layout.addWidget(retry_btn)
        
        layout.addStretch()
        
        return widget
        
    def create_expandable_details(self, result_data: Dict[str, Any]) -> QWidget:
        """Create expandable details section"""
        # Create a simple collapsible widget
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toggle button for details
        toggle_button = QPushButton("▼ Show Details")
        toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px 16px;
                border-radius: 4px;
                text-align: left;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        details_layout.addWidget(toggle_button)
        
        # Details content (initially hidden)
        details_content = QWidget()
        details_content_layout = QVBoxLayout(details_content)
        details_content.setVisible(False)
        
        # Request details
        request_group = QGroupBox("Request Details")
        request_layout = QVBoxLayout(request_group)
        
        # Show system prompt and user prompt if available
        if self.version_data:
            system_prompt = self.version_data.get('system_prompt', '')
            content = self.version_data.get('content', '')
            
            if system_prompt:
                sys_prompt_text = QTextBrowser()
                sys_prompt_text.setPlainText(f"System: {system_prompt}")
                sys_prompt_text.setMaximumHeight(80)
                sys_prompt_text.setStyleSheet("font-size: 11px; background-color: #f8f9fa;")
                request_layout.addWidget(sys_prompt_text)
                
            if content:
                user_prompt_text = QTextBrowser()
                rendered_content = self._render_prompt_with_variables(content, result_data.get('inputData', {}))
                user_prompt_text.setPlainText(f"User: {rendered_content}")
                user_prompt_text.setMaximumHeight(80)
                user_prompt_text.setStyleSheet("font-size: 11px; background-color: #f8f9fa;")
                request_layout.addWidget(user_prompt_text)
        
        details_content_layout.addWidget(request_group)
        
        # Metrics details
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QFormLayout(metrics_group)
        
        # Add detailed metrics here
        input_data = result_data.get('inputData', {})
        output = result_data.get('output', {})
        
        if isinstance(output, dict) and 'usage' in output:
            usage = output['usage']
            metrics_layout.addRow("Prompt tokens:", QLabel(str(usage.get('prompt_tokens', 'N/A'))))
            metrics_layout.addRow("Completion tokens:", QLabel(str(usage.get('completion_tokens', 'N/A'))))
            metrics_layout.addRow("Total tokens:", QLabel(str(usage.get('total_tokens', 'N/A'))))
        
        details_content_layout.addWidget(metrics_group)
        details_layout.addWidget(details_content)
        
        # Toggle functionality
        def toggle_details():
            visible = details_content.isVisible()
            details_content.setVisible(not visible)
            toggle_button.setText("▲ Hide Details" if not visible else "▼ Show Details")
            
        toggle_button.clicked.connect(toggle_details)
        
        return details_widget
        
    def get_action_button_style(self, color: str) -> str:
        """Get consistent button style"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:disabled {{
                background-color: #6c757d;
            }}
        """
        
    def darken_color(self, color: str) -> str:
        """Darken a color for hover state"""
        color_map = {
            "#007bff": "#0056b3",
            "#28a745": "#218838",
            "#6c757d": "#545b62"
        }
        return color_map.get(color, "#495057")
        
    def copy_response_content(self, result_data: Dict[str, Any]):
        """Copy response content to clipboard"""
        try:
            from PyQt6.QtWidgets import QApplication
            content = self._extract_response_content(result_data.get('output', {}))
            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            
            # Show temporary message
            self.status_label.setText("Response copied to clipboard!")
            QTimer.singleShot(3000, lambda: self.status_label.setText(""))
            
        except Exception as e:
            print(f"Failed to copy to clipboard: {e}")
            
    def _render_prompt_with_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Render prompt template with variables"""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
        
    def delete_history_item(self, timestamp: str):
        """Delete a history item"""
        reply = QMessageBox.question(
            self,
            "Delete History",
            "Are you sure you want to delete this history item?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove from local list
                self.results = [r for r in self.results if r.get('timestamp') != timestamp]
                
                # TODO: Call API to delete from server
                # self.api_client.delete(f'/api/tasks/{self.current_task_id}/versions/{self.current_version_id}/results/{timestamp}')
                
                self.refresh_history()
                
            except Exception as e:
                QMessageBox.warning(self, "Delete Error", f"Failed to delete history item: {str(e)}")
                
    def show_no_task_state(self):
        """Show state when no task is selected"""
        # Update status
        self.status_label.setText("No task selected")
        
    def show_task_selected_state(self):
        """Show state when task is selected but no version"""
        # Update status  
        task_name = self.task_data.get('name', 'Unknown') if self.task_data else 'Unknown'
        self.status_label.setText(f"Task: {task_name}")
        
    def clear_all_content(self):
        """Completely clear all content areas for task/version refresh"""
        print("ResultViewer: Clearing all content areas")
        
        # Clear result detail area
        self.result_detail.show_empty_state()
        
        # Clear history list
        for i in reversed(range(self.history_list_layout.count())):
            child = self.history_list_layout.itemAt(i)
            if child and child.widget():
                child.widget().deleteLater()
        
        # Re-add the stretch item to history list
        self.history_list_layout.addStretch()
        
        # Clear result display area
        if hasattr(self, 'result_display') and self.result_display.layout():
            for i in reversed(range(self.result_display.layout().count())):
                child = self.result_display.layout().itemAt(i)
                if child and child.widget() and child.widget() not in [self.run_button, self.progress_bar]:
                    child.widget().deleteLater()
        
        # Reset tab titles
        self.tab_widget.setTabText(1, "History (0)")
        
        print("ResultViewer: All content areas cleared")

    def clear_content(self):
        """Clear the content area"""
        # Content is now managed by tab widget, no need to clear manually
        pass
                
    def clear(self):
        """Clear the viewer"""
        self.current_task_id = None
        self.current_version_id = None
        self.task_data = None
        self.version_data = None
        self.results = []
        
        self.clear_all_content()
        self.refresh_history()
        self.result_detail.show_empty_state()
        self.show_no_task_state()
        
    def translate_response(self, result_data: Dict[str, Any]):
        """Translate the response content to Korean"""
        try:
            # Check if we have an active endpoint for translation
            if not self.active_endpoint:
                QMessageBox.warning(
                    self, 
                    "No LLM Provider", 
                    "번역을 위해서는 활성화된 LLM 공급자가 필요합니다.\n설정에서 LLM 공급자를 설정해 주세요."
                )
                return
                
            # Extract response content to translate
            response_content = self._extract_response_content(result_data.get('output', {}))
            
            if not response_content or response_content == 'No response content available':
                QMessageBox.warning(
                    self, 
                    "No Content", 
                    "번역할 내용이 없습니다."
                )
                return
                
            # Create and show translation popup
            self.translate_popup = TranslatePopup(response_content, self)
            self.translate_popup.show_translation_progress()
            self.translate_popup.show()
            
            # Start translation thread
            self.translate_thread = TranslateThread(
                self.db_client,
                response_content,
                self.active_endpoint
            )
            
            # Connect signals
            self.translate_thread.finished.connect(self.on_translate_finished)
            self.translate_thread.error.connect(self.on_translate_error)
            
            # Start translation
            self.translate_thread.start()
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Translation Error", 
                f"번역 중 예상치 못한 오류가 발생했습니다:\n{str(e)}"
            )
            
    def on_translate_finished(self, translated_text: str):
        """Handle translation completion"""
        try:
            if hasattr(self, 'translate_popup') and self.translate_popup:
                self.translate_popup.show_translation_result(translated_text)
        except Exception as e:
            print(f"Error handling translation completion: {e}")
            
    def on_translate_error(self, error_message: str):
        """Handle translation error"""
        try:
            if hasattr(self, 'translate_popup') and self.translate_popup:
                self.translate_popup.show_translation_error(error_message)
        except Exception as e:
            print(f"Error handling translation error: {e}")
            
    def _extract_response_content(self, output: Any) -> str:
        """Extract response content from output"""
        if isinstance(output, dict):
            if 'choices' in output and output['choices']:
                return output['choices'][0].get('message', {}).get('content', 'No content')
            elif 'content' in output:
                return output['content']
        elif isinstance(output, str):
            return output
        return 'No response content available'
        
    
    def apply_theme(self, is_dark: bool):
        """Apply theme to the widget"""
        # Theme will be applied through stylesheets
        pass
