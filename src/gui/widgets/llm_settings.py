"""
LLM Settings Widget - PyQt GUI equivalent of LLMEndpointSettings.jsx
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QSplitter,
    QFormLayout, QGroupBox, QMessageBox, QInputDialog, QTabWidget,
    QScrollArea, QFrame, QSpinBox, QCheckBox, QComboBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QIcon
from typing import Dict, List, Optional, Any
import json
import uuid
from datetime import datetime

from ..utils.db_client import DatabaseClient


class EndpointTestThread(QThread):
    """Thread for testing endpoints"""
    
    finished = pyqtSignal(dict)  # result
    error = pyqtSignal(str)      # error message
    
    def __init__(self, db_client: DatabaseClient, test_type: str, endpoint_data: Dict[str, Any], message: str = ""):
        super().__init__()
        self.db_client = db_client
        self.test_type = test_type  # "models" or "chat"
        self.endpoint_data = endpoint_data
        self.message = message
        
    def run(self):
        """Run the test"""
        try:
            if self.test_type == "models":
                result = self.db_client.test_llm_models(
                    self.endpoint_data['baseUrl'],
                    self.endpoint_data['apiKey']
                )
            elif self.test_type == "chat":
                result = self.db_client.test_llm_chat(
                    self.endpoint_data['baseUrl'],
                    self.endpoint_data['apiKey'],
                    self.endpoint_data.get('defaultModel', 'gpt-3.5-turbo'),
                    self.message
                )
            else:
                raise ValueError(f"Unknown test type: {self.test_type}")
                
            if result:
                self.finished.emit(result)
            else:
                self.error.emit("No response from endpoint")
                
        except Exception as e:
            self.error.emit(str(e))


class EndpointListItem(QFrame):
    """Custom endpoint list item widget"""
    
    clicked = pyqtSignal(str)  # endpoint_id
    edit_requested = pyqtSignal(str)  # endpoint_id
    delete_requested = pyqtSignal(str)  # endpoint_id
    activate_requested = pyqtSignal(str)  # endpoint_id
    set_default_requested = pyqtSignal(str)  # endpoint_id
    
    def __init__(self, endpoint_data: Dict[str, Any], is_active: bool = False, is_default: bool = False):
        super().__init__()
        self.endpoint_data = endpoint_data
        self.endpoint_id = endpoint_data.get('id', '')
        self.is_active = is_active
        self.is_default = is_default
        
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setContentsMargins(2, 2, 2, 2)
        
        self.setup_ui()
        self.update_styles()
        
    def setup_ui(self):
        """Setup the endpoint item UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Header with name and badges
        header_layout = QHBoxLayout()
        
        # Name
        name_label = QLabel(self.endpoint_data.get('name', 'Unnamed Endpoint'))
        name_label.setFont(QFont("", 11, QFont.Weight.Medium))
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        # Badges
        if self.is_active:
            active_badge = QLabel("Active")
            active_badge.setStyleSheet("""
                QLabel {
                    background-color: rgba(16, 185, 129, 0.2);
                    color: #10b981;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 9px;
                    font-weight: bold;
                }
            """)
            header_layout.addWidget(active_badge)
            
        if self.is_default:
            default_badge = QLabel("Default")
            default_badge.setStyleSheet("""
                QLabel {
                    background-color: rgba(139, 92, 246, 0.2);
                    color: #8b5cf6;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 9px;
                    font-weight: bold;
                }
            """)
            header_layout.addWidget(default_badge)
            
        layout.addLayout(header_layout)
        
        # Info
        base_url = self.endpoint_data.get('baseUrl', 'No URL')
        if len(base_url) > 40:
            base_url = base_url[:37] + "..."
            
        url_label = QLabel(base_url)
        url_label.setStyleSheet("color: #6c757d; font-size: 10px; font-family: monospace;")
        layout.addWidget(url_label)
        
        # Model info
        model = self.endpoint_data.get('defaultModel', '')
        if model:
            model_label = QLabel(f"Model: {model}")
            model_label.setStyleSheet("color: #6c757d; font-size: 10px;")
            layout.addWidget(model_label)
            
    def update_styles(self):
        """Update item styles based on state"""
        if self.is_active:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 123, 255, 0.05);
                    border: 2px solid #007bff;
                    border-radius: 6px;
                }
            """)
        else:
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
            
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.endpoint_id)
        super().mousePressEvent(event)
        
    def contextMenuEvent(self, event):
        """Handle context menu"""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.endpoint_id))
        
        if not self.is_active:
            activate_action = menu.addAction("Activate")
            activate_action.triggered.connect(lambda: self.activate_requested.emit(self.endpoint_id))
            
        if not self.is_default:
            default_action = menu.addAction("Set as Default")
            default_action.triggered.connect(lambda: self.set_default_requested.emit(self.endpoint_id))
            
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.endpoint_id))
        
        menu.exec(event.globalPos())


class EndpointForm(QWidget):
    """Form for creating/editing endpoints"""
    
    saved = pyqtSignal(dict)  # endpoint data
    cancelled = pyqtSignal()
    
    def __init__(self, endpoint_data: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.endpoint_data = endpoint_data
        self.is_editing = endpoint_data is not None
        
        self.setup_ui()
        
        if endpoint_data:
            self.load_data(endpoint_data)
            
    def setup_ui(self):
        """Setup the form UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = "Edit Endpoint" if self.is_editing else "Add New Endpoint"
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(cancel_btn)
        
        layout.addLayout(header_layout)
        
        # Form
        form_group = QGroupBox("Endpoint Configuration")
        form_layout = QFormLayout(form_group)
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., OpenAI GPT-4")
        form_layout.addRow("Name:", self.name_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        self.description_input.setPlaceholderText("Optional description")
        form_layout.addRow("Description:", self.description_input)
        
        # Base URL
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.openai.com/v1")
        form_layout.addRow("Base URL:", self.base_url_input)
        
        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Your API key")
        form_layout.addRow("API Key:", self.api_key_input)
        
        # Default Model
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("gpt-4o")
        form_layout.addRow("Default Model:", self.model_input)
        
        # Context Size
        self.context_size_input = QSpinBox()
        self.context_size_input.setRange(1000, 200000)
        self.context_size_input.setValue(8192)
        self.context_size_input.setSuffix(" tokens")
        form_layout.addRow("Context Size:", self.context_size_input)
        
        # Default checkbox
        self.is_default_checkbox = QCheckBox("Set as default endpoint")
        form_layout.addRow("", self.is_default_checkbox)
        
        layout.addWidget(form_group)
        
        # Test section
        test_group = QGroupBox("Connection Test")
        test_layout = QVBoxLayout(test_group)
        
        # Test message input
        test_message_layout = QFormLayout()
        self.test_message_input = QTextEdit()
        self.test_message_input.setMaximumHeight(80)
        self.test_message_input.setPlainText("Hello, this is a test message. Can you respond with a simple greeting?")
        test_message_layout.addRow("Test Message:", self.test_message_input)
        test_layout.addLayout(test_message_layout)
        
        # Test buttons
        test_buttons_layout = QHBoxLayout()
        
        self.test_models_btn = QPushButton("Test /v1/models")
        self.test_models_btn.clicked.connect(self.test_models)
        
        self.test_chat_btn = QPushButton("Test /v1/chat/completions")
        self.test_chat_btn.clicked.connect(self.test_chat)
        
        test_buttons_layout.addWidget(self.test_models_btn)
        test_buttons_layout.addWidget(self.test_chat_btn)
        test_layout.addLayout(test_buttons_layout)
        
        # Test progress
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        self.test_progress.setRange(0, 0)  # Indeterminate
        test_layout.addWidget(self.test_progress)
        
        # Test results
        self.test_results = QTextEdit()
        self.test_results.setMaximumHeight(200)
        self.test_results.setVisible(False)
        test_layout.addWidget(self.test_results)
        
        layout.addWidget(test_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.save_btn = QPushButton("Save Endpoint")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.save_btn.clicked.connect(self.save_endpoint)
        
        action_layout.addWidget(self.save_btn)
        layout.addLayout(action_layout)
        
        layout.addStretch()
        
    def load_data(self, data: Dict[str, Any]):
        """Load endpoint data into form"""
        self.name_input.setText(data.get('name', ''))
        self.description_input.setPlainText(data.get('description', ''))
        self.base_url_input.setText(data.get('baseUrl', ''))
        self.api_key_input.setText(data.get('apiKey', ''))
        self.model_input.setText(data.get('defaultModel', ''))
        self.context_size_input.setValue(data.get('contextSize', 8192))
        self.is_default_checkbox.setChecked(data.get('isDefault', False))
        
    def get_form_data(self) -> Dict[str, Any]:
        """Get form data as dictionary"""
        return {
            'name': self.name_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'baseUrl': self.base_url_input.text().strip(),
            'apiKey': self.api_key_input.text().strip(),
            'defaultModel': self.model_input.text().strip(),
            'contextSize': self.context_size_input.value(),
            'isDefault': self.is_default_checkbox.isChecked()
        }
        
    def validate_form(self) -> bool:
        """Validate form data"""
        data = self.get_form_data()
        
        if not data['name']:
            QMessageBox.warning(self, "Validation Error", "Name is required")
            return False
            
        if not data['baseUrl']:
            QMessageBox.warning(self, "Validation Error", "Base URL is required")
            return False
            
        if not data['baseUrl'].startswith(('http://', 'https://')):
            QMessageBox.warning(self, "Validation Error", "Base URL must start with http:// or https://")
            return False
            
        return True
        
    def save_endpoint(self):
        """Save the endpoint"""
        if not self.validate_form():
            return
            
        data = self.get_form_data()
        
        # Add ID and timestamps for new endpoints
        if not self.is_editing:
            data['id'] = str(uuid.uuid4())
            data['createdAt'] = datetime.now().isoformat()
        else:
            data['id'] = self.endpoint_data['id']
            data['updatedAt'] = datetime.now().isoformat()
            
        self.saved.emit(data)
        
    def test_models(self):
        """Test models endpoint"""
        if not self.validate_form():
            return
            
        data = self.get_form_data()
        
        self.test_models_btn.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_results.setVisible(False)
        
        self.test_thread = EndpointTestThread(DatabaseClient(), "models", data)
        self.test_thread.finished.connect(self.on_test_finished)
        self.test_thread.error.connect(self.on_test_error)
        self.test_thread.start()
        
    def test_chat(self):
        """Test chat endpoint"""
        if not self.validate_form():
            return
            
        data = self.get_form_data()
        message = self.test_message_input.toPlainText().strip()
        
        if not message:
            QMessageBox.warning(self, "Test Error", "Test message is required")
            return
            
        self.test_chat_btn.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_results.setVisible(False)
        
        self.test_thread = EndpointTestThread(DatabaseClient(), "chat", data, message)
        self.test_thread.finished.connect(self.on_test_finished)
        self.test_thread.error.connect(self.on_test_error)
        self.test_thread.start()
        
    def on_test_finished(self, result: Dict[str, Any]):
        """Handle test completion"""
        self.test_models_btn.setEnabled(True)
        self.test_chat_btn.setEnabled(True)
        self.test_progress.setVisible(False)
        
        self.test_results.setPlainText(json.dumps(result, indent=2))
        self.test_results.setVisible(True)
        
    def on_test_error(self, error: str):
        """Handle test error"""
        self.test_models_btn.setEnabled(True)
        self.test_chat_btn.setEnabled(True)
        self.test_progress.setVisible(False)
        
        self.test_results.setPlainText(f"Test failed: {error}")
        self.test_results.setStyleSheet("color: #dc3545;")
        self.test_results.setVisible(True)


class LLMSettingsWidget(QWidget):
    """Main LLM settings widget"""
    
    def __init__(self):
        super().__init__()
        
        self.db_client = DatabaseClient()
        self.endpoints: List[Dict[str, Any]] = []
        self.active_endpoint_id: Optional[str] = None
        self.default_endpoint_id: Optional[str] = None
        self.selected_endpoint_id: Optional[str] = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the LLM settings UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - endpoint list
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - details/form
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        splitter.addWidget(self.right_panel)
        
        # Set splitter proportions
        splitter.setSizes([320, 800])
        
        layout.addWidget(splitter)
        
        # Show initial state
        self.show_welcome_state()
        
    def create_left_panel(self) -> QWidget:
        """Create the left panel with endpoint list"""
        panel = QWidget()
        panel.setStyleSheet("background-color: #f8f9fa; border-right: 1px solid #dee2e6;")
        panel.setFixedWidth(320)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #e9ecef; border-bottom: 1px solid #dee2e6;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        # Title
        title_label = QLabel("LLM Providers")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Manage API endpoints")
        subtitle_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)
        
        # Endpoint list
        self.endpoint_list_scroll = QScrollArea()
        self.endpoint_list_scroll.setWidgetResizable(True)
        self.endpoint_list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.endpoint_list_widget = QWidget()
        self.endpoint_list_layout = QVBoxLayout(self.endpoint_list_widget)
        self.endpoint_list_layout.setContentsMargins(8, 8, 8, 8)
        self.endpoint_list_layout.setSpacing(4)
        self.endpoint_list_layout.addStretch()
        
        self.endpoint_list_scroll.setWidget(self.endpoint_list_widget)
        layout.addWidget(self.endpoint_list_scroll, 1)
        
        # Footer
        footer_frame = QFrame()
        footer_frame.setStyleSheet("background-color: #e9ecef; border-top: 1px solid #dee2e6;")
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(12, 8, 12, 8)
        
        self.add_endpoint_btn = QPushButton("+ Add Provider")
        self.add_endpoint_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.add_endpoint_btn.clicked.connect(self.add_endpoint)
        
        footer_layout.addWidget(self.add_endpoint_btn)
        layout.addWidget(footer_frame)
        
        return panel
        
    def load_endpoints(self):
        """Load endpoints from API"""
        try:
            data = self.db_client.get_llm_endpoints()
            self.endpoints = data.get('endpoints', [])
            self.active_endpoint_id = data.get('activeEndpointId')
            self.default_endpoint_id = data.get('defaultEndpointId')
            
            self.refresh_endpoint_list()
            
        except Exception as e:
            QMessageBox.warning(self, "Loading Error", f"Failed to load endpoints: {str(e)}")
            
    def refresh_endpoint_list(self):
        """Refresh the endpoint list display"""
        # Clear existing items
        for i in reversed(range(self.endpoint_list_layout.count() - 1)):  # Keep stretch
            child = self.endpoint_list_layout.itemAt(i)
            if child and child.widget():
                child.widget().deleteLater()
                
        # Add endpoint items
        if self.endpoints:
            for endpoint in self.endpoints:
                is_active = endpoint['id'] == self.active_endpoint_id
                is_default = endpoint['id'] == self.default_endpoint_id
                
                item = EndpointListItem(endpoint, is_active, is_default)
                item.clicked.connect(self.select_endpoint)
                item.edit_requested.connect(self.edit_endpoint)
                item.delete_requested.connect(self.delete_endpoint)
                item.activate_requested.connect(self.activate_endpoint)
                item.set_default_requested.connect(self.set_default_endpoint)
                
                self.endpoint_list_layout.insertWidget(
                    self.endpoint_list_layout.count() - 1,
                    item
                )
        else:
            # Show empty state
            empty_label = QLabel("No endpoints configured")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #666; font-style: italic; padding: 40px;")
            self.endpoint_list_layout.insertWidget(0, empty_label)
            
    def select_endpoint(self, endpoint_id: str):
        """Select an endpoint for viewing"""
        self.selected_endpoint_id = endpoint_id
        
        # Find endpoint data
        endpoint_data = None
        for endpoint in self.endpoints:
            if endpoint['id'] == endpoint_id:
                endpoint_data = endpoint
                break
                
        if endpoint_data:
            self.show_endpoint_detail(endpoint_data)
            
    def show_endpoint_detail(self, endpoint_data: Dict[str, Any]):
        """Show endpoint details"""
        self.clear_right_panel()
        
        # Create detail widget
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title and badges
        title_layout = QVBoxLayout()
        
        name_label = QLabel(endpoint_data.get('name', 'Unnamed Endpoint'))
        name_font = QFont()
        name_font.setPointSize(18)
        name_font.setBold(True)
        name_label.setFont(name_font)
        
        badges_layout = QHBoxLayout()
        
        if endpoint_data['id'] == self.active_endpoint_id:
            active_badge = QLabel("Active")
            active_badge.setStyleSheet("""
                QLabel {
                    background-color: rgba(16, 185, 129, 0.2);
                    color: #10b981;
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            badges_layout.addWidget(active_badge)
            
        if endpoint_data['id'] == self.default_endpoint_id:
            default_badge = QLabel("Default")
            default_badge.setStyleSheet("""
                QLabel {
                    background-color: rgba(139, 92, 246, 0.2);
                    color: #8b5cf6;
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            badges_layout.addWidget(default_badge)
            
        badges_layout.addStretch()
        
        title_layout.addWidget(name_label)
        title_layout.addLayout(badges_layout)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Action buttons
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self.edit_endpoint(endpoint_data['id']))
        header_layout.addWidget(edit_btn)
        
        if endpoint_data['id'] != self.active_endpoint_id:
            activate_btn = QPushButton("Activate")
            activate_btn.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
            activate_btn.clicked.connect(lambda: self.activate_endpoint(endpoint_data['id']))
            header_layout.addWidget(activate_btn)
            
        if endpoint_data['id'] != self.default_endpoint_id:
            default_btn = QPushButton("Set Default")
            default_btn.setStyleSheet("""
                QPushButton {
                    background-color: #8b5cf6;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #7c3aed;
                }
            """)
            default_btn.clicked.connect(lambda: self.set_default_endpoint(endpoint_data['id']))
            header_layout.addWidget(default_btn)
            
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_endpoint(endpoint_data['id']))
        header_layout.addWidget(delete_btn)
            
        detail_layout.addLayout(header_layout)
        
        # Details
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Configuration section
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout(config_group)
        
        # Base URL
        base_url_label = QLabel(endpoint_data.get('baseUrl', 'Not specified'))
        base_url_label.setStyleSheet("font-family: monospace; background-color: #f8f9fa; padding: 4px; border-radius: 4px;")
        config_layout.addRow("Base URL:", base_url_label)
        
        # Model
        model_label = QLabel(endpoint_data.get('defaultModel', 'Not specified'))
        model_label.setStyleSheet("font-family: monospace; background-color: #f8f9fa; padding: 4px; border-radius: 4px;")
        config_layout.addRow("Default Model:", model_label)
        
        # Authentication
        has_key = bool(endpoint_data.get('apiKey', ''))
        auth_label = QLabel("🟢 Configured" if has_key else "🔴 Not configured")
        config_layout.addRow("Authentication:", auth_label)
        
        # Context size
        context_size = endpoint_data.get('contextSize', 0)
        context_label = QLabel(f"{context_size:,} tokens" if context_size else "Not specified")
        config_layout.addRow("Context Size:", context_label)
        
        details_layout.addWidget(config_group)
        
        # Description
        description = endpoint_data.get('description', '').strip()
        if description:
            desc_group = QGroupBox("Description")
            desc_layout = QVBoxLayout(desc_group)
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_layout.addWidget(desc_label)
            details_layout.addWidget(desc_group)
            
        # Metadata
        meta_group = QGroupBox("Metadata")
        meta_layout = QFormLayout(meta_group)
        
        created_at = endpoint_data.get('createdAt', '')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                created_str = created_at
            meta_layout.addRow("Created:", QLabel(created_str))
            
        updated_at = endpoint_data.get('updatedAt', '')
        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                updated_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                updated_str = updated_at
            meta_layout.addRow("Updated:", QLabel(updated_str))
            
        details_layout.addWidget(meta_group)
        details_layout.addStretch()
        
        scroll_area.setWidget(details_widget)
        detail_layout.addWidget(scroll_area, 1)
        
        self.right_layout.addWidget(detail_widget)
        
    def add_endpoint(self):
        """Add a new endpoint"""
        self.show_endpoint_form()
        
    def edit_endpoint(self, endpoint_id: str):
        """Edit an endpoint"""
        endpoint_data = None
        for endpoint in self.endpoints:
            if endpoint['id'] == endpoint_id:
                endpoint_data = endpoint
                break
                
        if endpoint_data:
            self.show_endpoint_form(endpoint_data)
            
    def show_endpoint_form(self, endpoint_data: Optional[Dict[str, Any]] = None):
        """Show the endpoint form"""
        self.clear_right_panel()
        
        form = EndpointForm(endpoint_data)
        form.saved.connect(self.save_endpoint)
        form.cancelled.connect(self.cancel_form)
        
        self.right_layout.addWidget(form)
        
    def save_endpoint(self, endpoint_data: Dict[str, Any]):
        """Save endpoint data"""
        try:
            if 'createdAt' in endpoint_data:  # New endpoint
                self.db_client.add_llm_endpoint(endpoint_data)
            else:  # Existing endpoint
                endpoint_id = endpoint_data['id']
                self.db_client.update_llm_endpoint(endpoint_id, endpoint_data)
                
            # Reload data
            self.load_endpoints()
            
            # Select the saved endpoint
            self.select_endpoint(endpoint_data['id'])
            
            QMessageBox.information(self, "Success", "Endpoint saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save endpoint: {str(e)}")
            
    def cancel_form(self):
        """Cancel form editing"""
        if self.selected_endpoint_id:
            self.select_endpoint(self.selected_endpoint_id)
        else:
            self.show_welcome_state()
            
    def delete_endpoint(self, endpoint_id: str):
        """Delete an endpoint"""
        endpoint_data = None
        for endpoint in self.endpoints:
            if endpoint['id'] == endpoint_id:
                endpoint_data = endpoint
                break
                
        if not endpoint_data:
            return
            
        reply = QMessageBox.question(
            self,
            "Delete Endpoint",
            f'Are you sure you want to delete "{endpoint_data.get("name", "Unknown")}"?\n\nThis action cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_client.delete_llm_endpoint(endpoint_id)
                
                # Clear selection if deleted endpoint was selected
                if self.selected_endpoint_id == endpoint_id:
                    self.selected_endpoint_id = None
                    
                # Reload data
                self.load_endpoints()
                self.show_welcome_state()
                
                QMessageBox.information(self, "Success", "Endpoint deleted successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Failed to delete endpoint: {str(e)}")
                
    def activate_endpoint(self, endpoint_id: str):
        """Activate an endpoint"""
        try:
            self.db_client.set_active_endpoint(endpoint_id)
            
            # Update local state
            self.active_endpoint_id = endpoint_id
            
            # Refresh displays
            self.refresh_endpoint_list()
            
            if self.selected_endpoint_id == endpoint_id:
                self.select_endpoint(endpoint_id)
                
            QMessageBox.information(self, "Success", "Endpoint activated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Activation Error", f"Failed to activate endpoint: {str(e)}")
            
    def set_default_endpoint(self, endpoint_id: str):
        """Set default endpoint"""
        try:
            self.db_client.set_default_endpoint(endpoint_id)
            
            # Update local state
            self.default_endpoint_id = endpoint_id
            
            # Refresh displays
            self.refresh_endpoint_list()
            
            if self.selected_endpoint_id == endpoint_id:
                self.select_endpoint(endpoint_id)
                
            QMessageBox.information(self, "Success", "Default endpoint set successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Default Error", f"Failed to set default endpoint: {str(e)}")
            
    def show_welcome_state(self):
        """Show welcome state when no endpoint is selected"""
        self.clear_right_panel()
        
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon
        icon_label = QLabel("⚙️")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 64px; margin: 20px;")
        
        # Title
        title_label = QLabel("LLM Provider Settings")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 8px;")
        
        # Description
        desc_label = QLabel("Select a provider from the sidebar to view its configuration,\nor create a new one to get started with your AI workflows.")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 14px; line-height: 1.4; max-width: 400px;")
        
        # Add provider button
        add_btn = QPushButton("Add Your First Provider")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        add_btn.clicked.connect(self.add_endpoint)
        
        welcome_layout.addWidget(icon_label)
        welcome_layout.addWidget(title_label)
        welcome_layout.addWidget(desc_label)
        welcome_layout.addWidget(add_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.right_layout.addWidget(welcome_widget)
        
    def clear_right_panel(self):
        """Clear the right panel"""
        for i in reversed(range(self.right_layout.count())):
            child = self.right_layout.itemAt(i)
            if child and child.widget():
                child.widget().deleteLater()
                
    def apply_theme(self, is_dark: bool):
        """Apply theme to the widget"""
        # Theme will be applied through stylesheets
        pass
