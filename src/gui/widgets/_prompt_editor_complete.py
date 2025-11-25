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
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter, QTextDocument, QTextCursor
from typing import Dict, List, Optional, Any
import re
import json
import difflib
from datetime import datetime

from ..utils.db_client import DatabaseClient


class VersionComparisonDialog(QDialog):
    """Dialog for comparing two prompt versions with highlighting"""
    
    def __init__(self, version_a: Dict[str, Any], version_b: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.version_a = version_a
        self.version_b = version_b
        self.parent_editor = parent
        
        self.setup_ui()
        self.apply_diff_highlighting()
        
    def setup_ui(self):
        """Setup the comparison dialog UI"""
        self.setWindowTitle("🔄 Version Comparison")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("📊 Prompt Version Comparison")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Legend
        legend_widget = self.create_legend()
        header_layout.addWidget(legend_widget)
        
        layout.addWidget(header_widget)
        
        # Version labels
        labels_layout = QHBoxLayout()
        
        version_a_label = QLabel(f"Version A: {self.version_a.get('name', 'Untitled')}")
        version_a_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #007bff;
                padding: 8px 12px;
                background-color: rgba(0, 123, 255, 0.1);
                border-radius: 6px;
                border-left: 4px solid #007bff;
            }
        """)
        
        version_b_label = QLabel(f"Version B: {self.version_b.get('name', 'Untitled')}")
        version_b_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #28a745;
                padding: 8px 12px;
                background-color: rgba(40, 167, 69, 0.1);
                border-radius: 6px;
                border-left: 4px solid #28a745;
            }
        """)
        
        labels_layout.addWidget(version_a_label)
        labels_layout.addWidget(version_b_label)
        
        layout.addLayout(labels_layout)
        
        # Main comparison area with tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                color: #495057;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #007bff;
                border-bottom: 2px solid #007bff;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)
        
        # Create tabs for different sections
        self.create_description_tab()
        self.create_system_prompt_tab()
        self.create_main_prompt_tab()
        
        layout.addWidget(self.tab_widget, 1)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        save_a_btn = QPushButton("💾 Save Version A as New")
        save_a_btn.clicked.connect(lambda: self.save_as_new_version('a'))
        save_a_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        save_b_btn = QPushButton("💾 Save Version B as New")
        save_b_btn.clicked.connect(lambda: self.save_as_new_version('b'))
        save_b_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        close_btn = QPushButton("✕ Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        
        buttons_layout.addWidget(save_a_btn)
        buttons_layout.addWidget(save_b_btn)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def create_legend(self):
        """Create legend for diff colors"""
        legend_widget = QWidget()
        legend_layout = QHBoxLayout(legend_widget)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(15)
        
        # Added text legend
        added_label = QLabel("Added")
        added_label.setStyleSheet("""
            QLabel {
                background-color: #d4edda;
                color: #155724;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        
        # Deleted text legend
        deleted_label = QLabel("Deleted")
        deleted_label.setStyleSheet("""
            QLabel {
                background-color: #f8d7da;
                color: #721c24;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        
        legend_layout.addWidget(QLabel("Legend:"))
        legend_layout.addWidget(added_label)
        legend_layout.addWidget(deleted_label)
        
        return legend_widget
    
    def create_description_tab(self):
        """Create description comparison tab"""
        tab_widget = QWidget()
        layout = QHBoxLayout(tab_widget)
        layout.setSpacing(10)
        
        # Version A
        self.desc_a_edit = self.create_text_edit(
            self.version_a.get('description', ''),
            "Version A Description"
        )
        
        # Version B
        self.desc_b_edit = self.create_text_edit(
            self.version_b.get('description', ''),
            "Version B Description"
        )
        
        layout.addWidget(self.desc_a_edit)
        layout.addWidget(self.desc_b_edit)
        
        self.tab_widget.addTab(tab_widget, "📝 Description")
    
    def create_system_prompt_tab(self):
        """Create system prompt comparison tab"""
        tab_widget = QWidget()
        layout = QHBoxLayout(tab_widget)
        layout.setSpacing(10)
        
        # Version A
        self.system_a_edit = self.create_text_edit(
            self.version_a.get('system_prompt', ''),
            "Version A System Prompt"
        )
        
        # Version B
        self.system_b_edit = self.create_text_edit(
            self.version_b.get('system_prompt', ''),
            "Version B System Prompt"
        )
        
        layout.addWidget(self.system_a_edit)
        layout.addWidget(self.system_b_edit)
        
        self.tab_widget.addTab(tab_widget, "🤖 System Prompt")
    
    def create_main_prompt_tab(self):
        """Create main prompt comparison tab"""
        tab_widget = QWidget()
        layout = QHBoxLayout(tab_widget)
        layout.setSpacing(10)
        
        # Version A
        self.main_a_edit = self.create_text_edit(
            self.version_a.get('content', ''),
            "Version A Main Prompt"
        )
        
        # Version B
        self.main_b_edit = self.create_text_edit(
            self.version_b.get('content', ''),
            "Version B Main Prompt"
        )
        
        layout.addWidget(self.main_a_edit)
        layout.addWidget(self.main_b_edit)
        
        self.tab_widget.addTab(tab_widget, "💬 Main Prompt")
    
    def create_text_edit(self, content: str, placeholder: str) -> QTextEdit:
        """Create a styled text edit widget"""
        text_edit = QTextEdit()
        text_edit.setPlainText(content)
        text_edit.setPlaceholderText(placeholder)
        text_edit.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                font-family: 'Consolas', 'Courier New', monospace;
                color: #495057;
                padding: 12px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #80bdff;
                outline: none;
            }
        """)
        return text_edit
    
    def apply_diff_highlighting(self):
        """Apply diff highlighting to all text edits"""
        # Description diff
        self.apply_diff_to_editors(
            self.version_a.get('description', ''),
            self.version_b.get('description', ''),
            self.desc_a_edit,
            self.desc_b_edit
        )
        
        # System prompt diff
        self.apply_diff_to_editors(
            self.version_a.get('system_prompt', ''),
            self.version_b.get('system_prompt', ''),
            self.system_a_edit,
            self.system_b_edit
        )
        
        # Main prompt diff
        self.apply_diff_to_editors(
            self.version_a.get('content', ''),
            self.version_b.get('content', ''),
            self.main_a_edit,
            self.main_b_edit
        )
    
    def apply_diff_to_editors(self, text_a: str, text_b: str, edit_a: QTextEdit, edit_b: QTextEdit):
        """Apply diff highlighting to a pair of text editors"""
        # Create diff using difflib
        matcher = difflib.SequenceMatcher(None, text_a, text_b)
        opcodes = matcher.get_opcodes()
        
        # Create formats for highlighting
        add_format = QTextCharFormat()
        add_format.setBackground(QColor("#d4edda"))  # Light green
        
        del_format = QTextCharFormat()
        del_format.setBackground(QColor("#f8d7da"))  # Light red
        
        # Apply highlighting to Version A (deleted parts)
        cursor_a = edit_a.textCursor()
        for tag, i1, i2, j1, j2 in opcodes:
            if tag in ['replace', 'delete']:
                cursor_a.setPosition(i1)
                cursor_a.setPosition(i2, QTextCursor.MoveMode.KeepAnchor)
                cursor_a.mergeCharFormat(del_format)
        
        # Apply highlighting to Version B (added parts)
        cursor_b = edit_b.textCursor()
        for tag, i1, i2, j1, j2 in opcodes:
            if tag in ['replace', 'insert']:
                cursor_b.setPosition(j1)
                cursor_b.setPosition(j2, QTextCursor.MoveMode.KeepAnchor)
                cursor_b.mergeCharFormat(add_format)
    
    def save_as_new_version(self, version: str):
        """Save the selected version as a new version"""
        if not self.parent_editor or not self.parent_editor.current_task_id:
            QMessageBox.warning(self, "Save Error", "No task selected")
            return
        
        # Get content from the appropriate text edits
        if version == 'a':
            version_name = f"{self.version_a.get('name', 'Version')} (Modified)"
            content = self.main_a_edit.toPlainText()
            system_prompt = self.system_a_edit.toPlainText()
            description = self.desc_a_edit.toPlainText()
        else:
            version_name = f"{self.version_b.get('name', 'Version')} (Modified)"
            content = self.main_b_edit.toPlainText()
            system_prompt = self.system_b_edit.toPlainText()
            description = self.desc_b_edit.toPlainText()
        
        # Ask for version name
        new_name, ok = QInputDialog.getText(
            self,
            "Save as New Version",
            "Enter name for the new version:",
            text=version_name
        )
        
        if not ok or not new_name.strip():
            return
        
        try:
            version_data = {
                'versionId': f'v{int(datetime.now().timestamp() * 1000)}',
                'name': new_name.strip(),
                'content': content,
                'system_prompt': system_prompt,
                'description': description
            }
            
            response = self.parent_editor.db_client.create_version(
                self.parent_editor.current_task_id, 
                version_data
            )
            
            if response:
                QMessageBox.information(self, "Success", f"New version '{new_name.strip()}' created successfully!")
                
                # Refresh parent editor data
                self.parent_editor.load_task_data()
                
                # Close dialog
                self.accept()
            else:
                QMessageBox.warning(self, "Save Error", "Failed to create new version")
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to create version: {str(e)}")


class VariableEditor(QWidget):
    """Widget for editing template variables"""
    
    variables_changed = pyqtSignal(dict)  # variables dict
    
    def __init__(self):
        super().__init__()
        self.variables: Dict[str, str] = {}
        self.current_task_id: Optional[str] = None
        self.db_client = DatabaseClient()
        self.setup_ui()
    
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
        
        # Variables list
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
        self.variables_layout.setContentsMargins(8, 8, 8, 8)
        self.variables_layout.setSpacing(4)
        self.variables_layout.addStretch()
        
        self.variables_scroll.setWidget(self.variables_widget)
        
        layout.addWidget(self.variables_scroll, 1)
        
    def set_task_id(self, task_id: str):
        """Set the current task and load variables"""
        self.current_task_id = task_id
        self.load_variables()
        
    def load_variables(self):
        """Load variables for the current task"""
        if not self.current_task_id:
            return
            
        try:
            variables = self.db_client.get_variables(self.current_task_id)
            self.set_variables(variables)
        except Exception as e:
            print(f"Error loading variables: {e}")
        
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
        self.save_variables()
        
    def remove_variable(self, name: str):
        """Remove a variable"""
        if name in self.variables:
            del self.variables[name]
            self.refresh_variables_list()
            self.save_variables()
            
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
        
    def get_variables(self) -> Dict[str, str]:
        """Get current variables"""
        return self.variables.copy()
        
    def save_variables(self):
        """Save variables to database"""
        if not self.current_task_id:
            return
            
        try:
            self.db_client.update_variables(self.current_task_id, self.variables)
            self.variables_changed.emit(self.variables)
        except Exception as e:
            print(f"Error saving variables: {e}")
        
    def refresh_variables_list(self):
        """Refresh the variables list display"""
        # Clear existing items
        for i in reversed(range(self.variables_layout.count() - 1)):  # Keep stretch
            child = self.variables_layout.itemAt(i)
            if child and child.widget():
                child.widget().deleteLater()
                
        # Add variable items
        for name, value in self.variables.items():
            var_card = self.create_variable_card(name, value)
            self.variables_layout.insertWidget(
                self.variables_layout.count() - 1,  # Before stretch
                var_card
            )
            
        # Show empty message if no variables
        if not self.variables:
            empty_label = QLabel("No variables defined.\nAdd variables that can be used in prompts with {{variable_name}} syntax.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #666; font-style: italic; padding: 40px;")
            self.variables_layout.insertWidget(0, empty_label)
            
    def create_variable_card(self, name: str, value: str) -> QWidget:
        """Create a variable card with edit functionality"""
        card = QWidget()
        card.setFixedHeight(120)
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(6)
        
        # Header with variable name and buttons
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        
        # Variable name label
        var_name_label = QLabel(f"{{{{{name}}}}}")
        var_name_label.setFixedHeight(24)
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
        
        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setFixedSize(70, 28)
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
        header_layout.addStretch()
        header_layout.addWidget(delete_button)
        
        # Value edit area
        value_edit = QTextEdit()
        value_edit.setPlainText(value)
        value_edit.setStyleSheet("""
            QTextEdit {
                font-size: 12px;
                color: #495057;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        value_edit.textChanged.connect(
            lambda: self.update_variable_value(name, value_edit.toPlainText())
        )
        
        card_layout.addLayout(header_layout)
        card_layout.addWidget(value_edit)
        
        return card
        
    def update_variable_value(self, name: str, value: str):
        """Update variable value"""
        self.variables[name] = value
        # Auto-save after short delay to avoid too many saves
        if not hasattr(self, '_save_timer'):
            self._save_timer = QTimer()
            self._save_timer.timeout.connect(self.save_variables)
            self._save_timer.setSingleShot(True)
        
        self._save_timer.stop()
        self._save_timer.start(1000)  # Save after 1 second of inactivity


class PromptEditor(QWidget):
    """Main prompt editor widget for version selection and comparison"""
    
    # Signals
    version_changed = pyqtSignal(str, str)  # task_id, version_id
    content_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.db_client = DatabaseClient()
        self.current_task_id: Optional[str] = None
        self.current_version_id: Optional[str] = None
        self.task_data: Optional[Dict[str, Any]] = None
        self.versions: List[Dict[str, Any]] = []
        
        # 버전 비교 기능
        self.selected_versions = []  # 선택된 버전들 (최대 2개)
        self.version_checkboxes = {}  # 체크박스 참조 저장
        
        # Create variables editor for main window access
        self.variables_editor = VariableEditor()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the prompt editor UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main content - just the prompt editor (no tabs)
        self.prompt_content_widget = QWidget()
        layout.addWidget(self.prompt_content_widget, 1)
        
        # Initial empty state
        self.show_empty_state()
        
    def set_task_id(self, task_id: str):
        """Set the current task"""
        self.current_task_id = task_id
        self.current_version_id = None
        
        # Update variables editor
        self.variables_editor.set_task_id(task_id)
        
        self.load_task_data()
        
    def set_task(self, task_id: str):
        """Alias for set_task_id for compatibility"""
        self.set_task_id(task_id)
        
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
            
            # Show version selection screen
            if self.versions:
                self.show_version_selection_state()
            else:
                self.show_no_versions_state()
                
        except Exception as e:
            QMessageBox.warning(self, "Loading Error", f"Failed to load task data: {str(e)}")
    
    def show_version_selection_state(self):
        """Show version selection state when versions are available"""
        try:
            # Clear existing content
            self.clear_widget_completely(self.prompt_content_widget)
            
            # Reset selection state
            self.selected_versions = []
            self.version_checkboxes = {}
                
            selection_widget = QWidget()
            selection_layout = QVBoxLayout(selection_widget)
            selection_layout.setContentsMargins(20, 20, 20, 20)
            
            # Header section with compare button
            header_widget = QWidget()
            header_layout = QVBoxLayout(header_widget)
            header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Icon
            icon_label = QLabel("📚")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("font-size: 48px; margin:
