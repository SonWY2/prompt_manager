"""
Version Comparison Dialog - Compare two prompt versions with diff highlighting
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QTabWidget, QMessageBox, QInputDialog, QComboBox, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor
from typing import Dict, Any
import difflib
from datetime import datetime


class VersionComparisonDialog(QDialog):
    """Dialog for comparing two prompt versions with highlighting"""
    
    def __init__(self, version_a: Dict[str, Any], version_b: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.version_a = version_a
        self.version_b = version_b
        self.parent_editor = parent
        self.available_versions = []
        
        # Get all available versions from parent
        if parent and hasattr(parent, 'versions'):
            self.available_versions = parent.versions
        
        self.setup_ui()
        self.setup_version_dropdowns()
        self.apply_diff_highlighting()
        
    def setup_ui(self):
        """Setup the comparison dialog UI"""
        self.setWindowTitle("⚖️ Compare Versions")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header section
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Back button and title
        back_btn = QPushButton("← Back to Editor")
        back_btn.clicked.connect(self.accept)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        
        # Title
        title_label = QLabel("📊 Compare Versions")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333;
                margin: 0 20px;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Apply button
        apply_btn = QPushButton("Apply Changes →")
        apply_btn.clicked.connect(self.show_apply_options)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        header_layout.addWidget(apply_btn)
        
        layout.addWidget(header_widget)
        
        # Version selection section
        selection_widget = QWidget()
        selection_layout = QHBoxLayout(selection_widget)
        selection_layout.setContentsMargins(0, 10, 0, 10)
        
        # Base Version dropdown
        base_section = QVBoxLayout()
        base_label = QLabel("Base Version:")
        base_label.setStyleSheet("font-weight: bold; color: #007bff; font-size: 14px;")
        self.base_combo = QComboBox()
        self.base_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 2px solid #007bff;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
                font-weight: bold;
                color: #007bff;
                min-width: 200px;
            }
        """)
        base_section.addWidget(base_label)
        base_section.addWidget(self.base_combo)
        
        # Compare With dropdown
        compare_section = QVBoxLayout()
        compare_label = QLabel("Compare With:")
        compare_label.setStyleSheet("font-weight: bold; color: #28a745; font-size: 14px;")
        self.compare_combo = QComboBox()
        self.compare_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 2px solid #28a745;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
                font-weight: bold;
                color: #28a745;
                min-width: 200px;
            }
        """)
        compare_section.addWidget(compare_label)
        compare_section.addWidget(self.compare_combo)
        
        selection_layout.addLayout(base_section)
        selection_layout.addStretch()
        selection_layout.addLayout(compare_section)
        
        # Legend
        legend_widget = self.create_legend()
        selection_layout.addWidget(legend_widget)
        
        layout.addWidget(selection_widget)
        
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
        from PyQt6.QtWidgets import QWidget
        
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
        from PyQt6.QtWidgets import QWidget
        
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
        from PyQt6.QtWidgets import QWidget
        
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
                
                # Schedule UI refresh and dialog close to avoid widget conflicts
                from PyQt6.QtCore import QTimer
                
                def delayed_refresh_and_close():
                    try:
                        # Refresh parent editor data after a short delay
                        if self.parent_editor:
                            self.parent_editor.load_task_data()
                        # Close dialog after refresh
                        self.accept()
                    except Exception as e:
                        print(f"Error during delayed refresh: {e}")
                        # Still close the dialog even if refresh fails
                        self.accept()
                
                # Delay the refresh to allow Qt to finish current operations
                QTimer.singleShot(150, delayed_refresh_and_close)
                
            else:
                QMessageBox.warning(self, "Save Error", "Failed to create new version")
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to create version: {str(e)}")
    
    def setup_version_dropdowns(self):
        """Setup version selection dropdowns"""
        try:
            # Clear existing items
            self.base_combo.clear()
            self.compare_combo.clear()
            
            # Add versions to dropdowns
            for version in self.available_versions:
                version_name = version.get('name', 'Untitled Version')
                version_id = version.get('id', '')
                
                # Create display text
                display_text = f"{version_name}"
                created_at = version.get('createdAt', '')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%m/%d %H:%M")
                        display_text = f"{version_name} ({formatted_date})"
                    except:
                        pass
                
                self.base_combo.addItem(display_text, version_id)
                self.compare_combo.addItem(display_text, version_id)
            
            # Set current selections to the versions being compared
            self.set_dropdown_selection(self.base_combo, self.version_a.get('id', ''))
            self.set_dropdown_selection(self.compare_combo, self.version_b.get('id', ''))
            
            # Connect change handlers
            self.base_combo.currentIndexChanged.connect(self.on_version_selection_changed)
            self.compare_combo.currentIndexChanged.connect(self.on_version_selection_changed)
            
        except Exception as e:
            print(f"Error setting up version dropdowns: {e}")
    
    def set_dropdown_selection(self, combo: QComboBox, version_id: str):
        """Set dropdown selection to specific version"""
        try:
            for i in range(combo.count()):
                if combo.itemData(i) == version_id:
                    combo.setCurrentIndex(i)
                    break
        except Exception as e:
            print(f"Error setting dropdown selection: {e}")
    
    def on_version_selection_changed(self):
        """Handle version selection change from dropdowns"""
        try:
            # Get selected version IDs
            base_version_id = self.base_combo.currentData()
            compare_version_id = self.compare_combo.currentData()
            
            if not base_version_id or not compare_version_id:
                return
            
            # Find version data
            new_version_a = None
            new_version_b = None
            
            for version in self.available_versions:
                if version.get('id') == base_version_id:
                    new_version_a = version
                elif version.get('id') == compare_version_id:
                    new_version_b = version
            
            if new_version_a and new_version_b:
                # Update versions and refresh comparison
                self.version_a = new_version_a
                self.version_b = new_version_b
                
                # Update text edits with new content
                self.update_text_edits()
                
                # Re-apply diff highlighting
                self.apply_diff_highlighting()
                
                # Update version labels
                self.update_version_labels()
                
        except Exception as e:
            print(f"Error handling version selection change: {e}")
    
    def update_text_edits(self):
        """Update text edits with new version content"""
        try:
            # Update description
            self.desc_a_edit.setPlainText(self.version_a.get('description', ''))
            self.desc_b_edit.setPlainText(self.version_b.get('description', ''))
            
            # Update system prompt
            self.system_a_edit.setPlainText(self.version_a.get('system_prompt', ''))
            self.system_b_edit.setPlainText(self.version_b.get('system_prompt', ''))
            
            # Update main prompt
            self.main_a_edit.setPlainText(self.version_a.get('content', ''))
            self.main_b_edit.setPlainText(self.version_b.get('content', ''))
            
        except Exception as e:
            print(f"Error updating text edits: {e}")
    
    def update_version_labels(self):
        """Update version labels"""
        try:
            # This would need to find and update the labels in the UI
            # For now, this is a placeholder - could be enhanced to update labels dynamically
            pass
        except Exception as e:
            print(f"Error updating version labels: {e}")
    
    def show_apply_options(self):
        """Show options for applying changes"""
        try:
            # Create simple dialog with options
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Apply Changes")
            dialog.setMinimumSize(400, 200)
            
            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            
            # Title
            title_label = QLabel("Choose how to apply the changes:")
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(title_label)
            
            # Option buttons
            save_a_as_new_btn = QPushButton("💾 Save Version A as New Version")
            save_a_as_new_btn.clicked.connect(lambda: (dialog.accept(), self.save_as_new_version('a')))
            save_a_as_new_btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            
            save_b_as_new_btn = QPushButton("💾 Save Version B as New Version")
            save_b_as_new_btn.clicked.connect(lambda: (dialog.accept(), self.save_as_new_version('b')))
            save_b_as_new_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            
            layout.addWidget(save_a_as_new_btn)
            layout.addWidget(save_b_as_new_btn)
            
            # Cancel button
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)
            
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            dialog.exec()
            
        except Exception as e:
            print(f"Error showing apply options: {e}")
            QMessageBox.warning(self, "Error", f"Failed to show apply options: {str(e)}")
