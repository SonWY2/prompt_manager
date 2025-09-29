"""
Task Navigator Widget - PyQt GUI equivalent of TaskNavigator.jsx
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QListWidgetItem, QTabWidget, QInputDialog,
    QMessageBox, QFrame, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime, timedelta

from ..utils.db_client import DatabaseClient


class TaskItem(QFrame):
    """Custom task item widget"""
    
    clicked = pyqtSignal(str)  # task_id
    favorite_toggled = pyqtSignal(str, bool)  # task_id, is_favorite
    
    def __init__(self, task_data: Dict[str, Any]):
        super().__init__()
        self.task_data = task_data
        self.task_id = task_data.get('id', '')
        
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setContentsMargins(2, 2, 2, 2)
        
        self.setup_ui()
        self.setup_styles()
        
    def setup_ui(self):
        """Setup the task item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Main content area
        content_layout = QVBoxLayout()
        
        # Title row
        title_layout = QHBoxLayout()
        
        # Task icon
        icon_label = QLabel("📄")
        icon_label.setFixedSize(16, 16)
        title_layout.addWidget(icon_label)
        
        # Task name
        name_label = QLabel(self.task_data.get('name', 'Untitled Task'))
        name_label.setFont(QFont("", 10, QFont.Weight.Medium))
        title_layout.addWidget(name_label)
        title_layout.addStretch()
        
        content_layout.addLayout(title_layout)
        
        # Info row
        info_text = self._get_info_text()
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        content_layout.addWidget(info_label)
        
        layout.addLayout(content_layout, 1)
        
        # Favorite button
        self.favorite_btn = QPushButton()
        self.favorite_btn.setFixedSize(24, 24)
        self.favorite_btn.setStyleSheet("border: none; background: transparent;")
        self.update_favorite_button()
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        
        layout.addWidget(self.favorite_btn)
        
    def setup_styles(self):
        """Setup widget styles"""
        self.setStyleSheet("""
            TaskItem {
                background-color: transparent;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
            TaskItem:hover {
                background-color: #f8f9fa;
                border-color: #bbb;
            }
            TaskItem[selected="true"] {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
        
    def _get_info_text(self) -> str:
        """Get task info text"""
        versions = self.task_data.get('versions', [])
        version_count = len(versions) if isinstance(versions, list) else 0
        
        # Format time
        updated_at = self.task_data.get('updatedAt')
        time_text = self._format_time_ago(updated_at) if updated_at else "Unknown"
        
        return f"{version_count} versions • Modified {time_text}"
        
    def _format_time_ago(self, updated_at: str) -> str:
        """Format time ago text"""
        try:
            updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            now = datetime.now(updated.tzinfo)
            diff = now - updated
            
            if diff < timedelta(hours=1):
                return "Just now"
            elif diff < timedelta(days=1):
                hours = int(diff.seconds / 3600)
                return f"{hours}h ago"
            elif diff < timedelta(days=2):
                return "Yesterday"
            else:
                days = diff.days
                return f"{days} days ago"
        except:
            return "Unknown"
            
    def update_favorite_button(self):
        """Update favorite button appearance"""
        is_favorite = self.task_data.get('isFavorite', False)
        self.favorite_btn.setText("★" if is_favorite else "☆")
        self.favorite_btn.setToolTip(
            "Remove from favorites" if is_favorite else "Add to favorites"
        )
        
    def toggle_favorite(self):
        """Toggle favorite status"""
        current_status = self.task_data.get('isFavorite', False)
        new_status = not current_status
        self.task_data['isFavorite'] = new_status
        self.update_favorite_button()
        self.favorite_toggled.emit(self.task_id, new_status)
        
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.setProperty("selected", selected)
        self.style().polish(self)
        
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.task_id)
        super().mousePressEvent(event)


class TaskNavigator(QWidget):
    """Task navigation widget"""
    
    # Signals
    task_selected = pyqtSignal(str)  # task_id
    task_created = pyqtSignal(str)   # task_id
    task_deleted = pyqtSignal(str)   # task_id
    
    def __init__(self):
        super().__init__()
        
        self.db_client = DatabaseClient()
        self.tasks: Dict[str, Any] = {}
        self.current_task_id: Optional[str] = None
        self.current_filter = "all"  # all, recent, favorites
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f8f9fa; border-bottom: 1px solid #dee2e6;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        # Title
        title_label = QLabel("Tasks")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Filter tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                padding: 6px 12px;
                margin-right: 2px;
                background-color: transparent;
                border: none;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                color: white;
                border-radius: 4px;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
                border-radius: 4px;
            }
        """)
        
        # Create filter tabs (empty widgets - just for navigation)
        self.tab_widget.addTab(QWidget(), "All")
        self.tab_widget.addTab(QWidget(), "Recent")
        self.tab_widget.addTab(QWidget(), "Favorites")
        
        header_layout.addWidget(self.tab_widget)
        layout.addWidget(header_frame)
        
        # Task list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.task_list_widget = QWidget()
        self.task_list_layout = QVBoxLayout(self.task_list_widget)
        self.task_list_layout.setContentsMargins(8, 8, 8, 8)
        self.task_list_layout.setSpacing(4)
        self.task_list_layout.addStretch()
        
        scroll_area.setWidget(self.task_list_widget)
        layout.addWidget(scroll_area, 1)
        
        # Footer with action buttons
        footer_frame = QFrame()
        footer_frame.setStyleSheet("background-color: #f8f9fa; border-top: 1px solid #dee2e6;")
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(12, 8, 12, 8)
        
        button_layout = QHBoxLayout()
        
        # New task button
        self.new_task_btn = QPushButton("+ New Task")
        self.new_task_btn.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        
        # Delete task button
        self.delete_task_btn = QPushButton("Delete Task")
        self.delete_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #a71e2a;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.delete_task_btn.setEnabled(False)
        
        button_layout.addWidget(self.new_task_btn)
        button_layout.addWidget(self.delete_task_btn)
        footer_layout.addLayout(button_layout)
        
        layout.addWidget(footer_frame)
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        self.tab_widget.currentChanged.connect(self.on_filter_changed)
        self.new_task_btn.clicked.connect(self.create_new_task)
        self.delete_task_btn.clicked.connect(self.delete_current_task)
        
    def on_filter_changed(self, index: int):
        """Handle filter tab change"""
        filters = ["all", "recent", "favorites"]
        if 0 <= index < len(filters):
            self.current_filter = filters[index]
            self.refresh_task_list()
            
    def load_tasks(self):
        """Load tasks from API"""
        try:
            response = self.db_client.get_tasks()
            if response:
                # Convert list to dict
                self.tasks = {task['id']: task for task in response}
                self.refresh_task_list()
            else:
                self.tasks = {}
                self.refresh_task_list()
        except Exception as e:
            QMessageBox.warning(self, "Loading Error", f"Failed to load tasks: {str(e)}")
            
    def refresh_task_list(self):
        """Refresh the task list display"""
        # Clear existing items
        for i in reversed(range(self.task_list_layout.count() - 1)):  # Keep stretch
            child = self.task_list_layout.itemAt(i)
            if child and child.widget():
                child.widget().deleteLater()
                
        # Get filtered tasks
        filtered_tasks = self._get_filtered_tasks()
        
        # Show empty state if no tasks
        if not filtered_tasks:
            self._show_empty_state()
            return
            
        # Create task items
        for task in filtered_tasks:
            task_item = TaskItem(task)
            task_item.clicked.connect(self.on_task_clicked)
            task_item.favorite_toggled.connect(self.on_favorite_toggled)
            
            # Set selection state
            if self.current_task_id == task['id']:
                task_item.set_selected(True)
                
            self.task_list_layout.insertWidget(
                self.task_list_layout.count() - 1,  # Before stretch
                task_item
            )
            
    def _get_filtered_tasks(self) -> List[Dict[str, Any]]:
        """Get filtered and sorted task list"""
        tasks_list = list(self.tasks.values())
        
        if self.current_filter == "recent":
            # Sort by updated time
            tasks_list.sort(key=lambda t: t.get('updatedAt', ''), reverse=True)
        elif self.current_filter == "favorites":
            # Filter favorites and sort by name
            tasks_list = [t for t in tasks_list if t.get('isFavorite', False)]
            tasks_list.sort(key=lambda t: t.get('name', ''))
        else:  # all
            # Sort by name
            tasks_list.sort(key=lambda t: t.get('name', ''))
            
        return tasks_list
        
    def _show_empty_state(self):
        """Show empty state message"""
        empty_widget = QFrame()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon
        icon_label = QLabel("📝")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; margin: 20px;")
        empty_layout.addWidget(icon_label)
        
        # Message
        if self.current_filter == "favorites":
            message = "No favorite tasks\nStar some tasks to see them here."
        else:
            message = "No tasks in this view\nCreate a new task to get started."
            
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("color: #666; font-size: 14px; line-height: 1.4;")
        empty_layout.addWidget(message_label)
        
        self.task_list_layout.insertWidget(
            self.task_list_layout.count() - 1,
            empty_widget
        )
        
    def on_task_clicked(self, task_id: str):
        """Handle task selection"""
        # Update selection state
        old_task_id = self.current_task_id
        self.current_task_id = task_id
        
        # Update UI
        self.refresh_task_list()
        self.delete_task_btn.setEnabled(True)
        
        # Emit signal
        self.task_selected.emit(task_id)
        
    def on_favorite_toggled(self, task_id: str, is_favorite: bool):
        """Handle favorite toggle"""
        try:
            # Update local state
            if task_id in self.tasks:
                self.tasks[task_id]['isFavorite'] = is_favorite
                
            # Update server
            self.db_client.update_task(task_id, {'isFavorite': is_favorite})
            
            # Refresh list if in favorites view
            if self.current_filter == "favorites":
                self.refresh_task_list()
                
        except Exception as e:
            # Revert local state on error
            if task_id in self.tasks:
                self.tasks[task_id]['isFavorite'] = not is_favorite
            QMessageBox.warning(self, "Update Error", f"Failed to update favorite: {str(e)}")
            self.refresh_task_list()
            
    def create_new_task(self):
        """Create a new task"""
        task_name, ok = QInputDialog.getText(
            self, 
            "New Task", 
            "Enter a name for the new task:"
        )
        
        if ok and task_name.strip():
            try:
                task_id = f'task-{int(datetime.now().timestamp() * 1000)}'
                response = self.db_client.create_task(task_id, task_name.strip())
                
                if response:
                    self.tasks[response['id']] = response
                    self.refresh_task_list()
                    
                    # Select the new task
                    self.on_task_clicked(response['id'])
                    self.task_created.emit(response['id'])
                    
            except Exception as e:
                QMessageBox.critical(self, "Creation Error", f"Failed to create task: {str(e)}")
                
    def delete_current_task(self):
        """Delete the currently selected task"""
        if not self.current_task_id:
            return
            
        task_name = self.tasks.get(self.current_task_id, {}).get('name', 'Unknown Task')
        
        reply = QMessageBox.question(
            self,
            "Delete Task",
            f'Are you sure you want to delete the task "{task_name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_client.delete_task(self.current_task_id)
                
                # Remove from local state
                deleted_task_id = self.current_task_id
                del self.tasks[self.current_task_id]
                self.current_task_id = None
                
                # Update UI
                self.delete_task_btn.setEnabled(False)
                self.refresh_task_list()
                
                # Emit signal
                self.task_deleted.emit(deleted_task_id)
                
            except Exception as e:
                QMessageBox.critical(self, "Deletion Error", f"Failed to delete task: {str(e)}")
                
    def get_task_name(self, task_id: str) -> Optional[str]:
        """Get task name by ID"""
        return self.tasks.get(task_id, {}).get('name')
        
    def apply_theme(self, is_dark: bool):
        """Apply theme to the widget"""
        if is_dark:
            self.setStyleSheet("""
                TaskNavigator {
                    background-color: #2b2b2b;
                    color: white;
                }
                QFrame {
                    background-color: #3c3c3c;
                    border-color: #555;
                }
                QLabel {
                    color: white;
                }
            """)
        else:
            self.setStyleSheet("""
                TaskNavigator {
                    background-color: white;
                    color: black;
                }
                QFrame {
                    background-color: #f8f9fa;
                    border-color: #dee2e6;
                }
            """)
