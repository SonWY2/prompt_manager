"""
Variable Editor Widget - Template variable management
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QScrollArea, QFrame,
    QMessageBox, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from typing import Dict, Optional
import re

from ..utils.db_client import DatabaseClient


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
