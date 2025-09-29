"""
Main Window for Prompt Manager PyQt GUI Application
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QTabWidget, QStatusBar, QMenuBar, QToolBar, QMessageBox,
    QApplication, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap

# Import custom widgets
from .widgets.task_navigator import TaskNavigator
from .widgets.prompt_editor import PromptEditor
from .widgets.result_viewer import ResultViewer
from .widgets.llm_settings import LLMSettingsWidget
from .utils.db_client import DatabaseClient
from .utils.theme_manager import ThemeManager


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    task_selected = pyqtSignal(str)  # task_id
    
    def __init__(self):
        super().__init__()
        
        # Initialize state
        self.current_task_id: Optional[str] = None
        self.current_version_id: Optional[str] = None
        
        # Initialize managers
        self.db_client = DatabaseClient()
        self.theme_manager = ThemeManager()
        
        # Initialize UI
        self.init_ui()
        self.setup_connections()
        self.load_initial_data()
        
        # Setup periodic server status check
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_server_status)
        self.status_timer.start(30000)  # Check every 30 seconds
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Prompt Manager")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set window icon
        self.setWindowIcon(QIcon("public/logo.svg"))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Create content area
        self.create_navigation_panel()
        self.create_content_area()
        
        # Set splitter proportions
        self.main_splitter.setSizes([300, 1100])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
        
        # Apply light theme (fixed)
        self.theme_manager.apply_theme(self, False)
        
    def create_navigation_panel(self):
        """Create the left navigation panel"""
        self.task_navigator = TaskNavigator()
        self.main_splitter.addWidget(self.task_navigator)
        
    def create_content_area(self):
        """Create the main content area with tabs"""
        # Create tab widget for main content
        self.main_tabs = QTabWidget()
        self.main_tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # Create content splitter for editor and right sidebar
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create prompt editor (left side)
        self.prompt_editor = PromptEditor()
        content_splitter.addWidget(self.prompt_editor)
        
        # Create right sidebar with Variables and LLM Result tabs
        self.right_sidebar = QTabWidget()
        self.right_sidebar.setTabPosition(QTabWidget.TabPosition.North)
        
        # Variables tab (using PromptEditor's variables editor)
        variables_tab = self.prompt_editor.variables_editor
        self.right_sidebar.addTab(variables_tab, "📝 Variables")
        
        # Create result viewer (without Variables tab)
        self.result_viewer = ResultViewer()
        self.right_sidebar.addTab(self.result_viewer, "🤖 LLM Result")
        
        # Add right sidebar to content splitter
        content_splitter.addWidget(self.right_sidebar)
        
        # Set content splitter proportions (left: editor, right: sidebar)
        content_splitter.setSizes([700, 400])
        
        # Add content to main tabs
        self.main_tabs.addTab(content_splitter, "📝 Editor")
        
        # Create LLM settings widget
        self.llm_settings = LLMSettingsWidget()
        self.main_tabs.addTab(self.llm_settings, "⚙️ LLM Provider")
        
        # Create welcome tab
        welcome_widget = self.create_welcome_widget()
        self.main_tabs.insertTab(0, welcome_widget, "🏠 Welcome")
        self.main_tabs.setCurrentIndex(0)
        
        self.main_splitter.addWidget(self.main_tabs)
        
    def create_welcome_widget(self) -> QWidget:
        """Create welcome screen widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Welcome content
        title = QLabel("✨ Prompt Manager")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        title.setFont(font)
        
        subtitle = QLabel("Select a task to start editing prompts")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 14px;")
        
        description = QLabel("Create or select from the sidebar")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("color: #999; font-size: 12px;")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(description)
        
        return widget
        
    def setup_connections(self):
        """Setup signal-slot connections between widgets"""
        try:
            # Connect task navigator signals
            self.task_navigator.task_selected.connect(self.on_task_selected)
            self.task_navigator.task_created.connect(self.on_task_created)
            self.task_navigator.task_deleted.connect(self.on_task_deleted)
            
        except Exception as e:
            print(f"Error setting up connections: {e}")
        
    def on_task_selected(self, task_id: str):
        """Handle task selection"""
        try:
            self.current_task_id = task_id
            
            # Update prompt editor
            self.prompt_editor.set_task(task_id)
            
            # Update result viewer
            self.result_viewer.set_task(task_id)
            
            # Update current task display
            print(f"Selected task: {task_id}")
            
        except Exception as e:
            print(f"Error handling task selection: {e}")
            
    def on_task_created(self, task_id: str):
        """Handle task creation"""
        try:
            # Automatically select the new task
            self.on_task_selected(task_id)
            
        except Exception as e:
            print(f"Error handling task creation: {e}")
            
    def on_task_deleted(self, task_id: str):
        """Handle task deletion"""
        try:
            if self.current_task_id == task_id:
                self.current_task_id = None
                
                # Clear prompt editor
                self.prompt_editor.clear()
                
                # Clear result viewer  
                self.result_viewer.clear()
                
        except Exception as e:
            print(f"Error handling task deletion: {e}")
        
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_task_action = QAction("&New Task", self)
        new_task_action.setShortcut("Ctrl+N")
        new_task_action.triggered.connect(self.task_navigator.create_new_task)
        file_menu.addAction(new_task_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Server status indicator
        self.server_status_label = QLabel("🔴 Disconnected")
        self.status_bar.addPermanentWidget(self.server_status_label)
        
        # LLM provider status
        self.llm_status_label = QLabel("No LLM Provider")
        self.status_bar.addPermanentWidget(self.llm_status_label)
        
        # Show ready message
        self.status_bar.showMessage("Ready")
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Task navigator connections
        self.task_navigator.task_selected.connect(self.on_task_selected)
        self.task_navigator.task_created.connect(self.on_task_created)
        self.task_navigator.task_deleted.connect(self.on_task_deleted)
        
        # Tab change connections
        self.main_tabs.currentChanged.connect(self.on_tab_changed)
        
        
    def load_initial_data(self):
        """Load initial data from API"""
        try:
            # Load tasks
            self.task_navigator.load_tasks()
            
            # Check server status
            self.check_server_status()
            
            # Load LLM endpoints
            self.llm_settings.load_endpoints()
            
        except Exception as e:
            QMessageBox.warning(self, "Loading Error", f"Failed to load initial data: {str(e)}")
            
    def check_server_status(self):
        """Check and update server status"""
        try:
            is_connected = self.db_client.check_connection()
            if is_connected:
                self.server_status_label.setText("🟢 Connected")
                self.server_status_label.setToolTip("Backend server is running")
            else:
                self.server_status_label.setText("🔴 Disconnected")
                self.server_status_label.setToolTip("Backend server is not accessible")
                
        except Exception as e:
            self.server_status_label.setText("🔴 Error")
            self.server_status_label.setToolTip(f"Connection error: {str(e)}")
            
    def on_task_selected(self, task_id: str):
        """Handle task selection"""
        self.current_task_id = task_id
        self.current_version_id = None
        
        # Switch to editor tab if not already there
        if self.main_tabs.currentIndex() == 0:  # Welcome tab
            self.main_tabs.setCurrentIndex(1)  # Editor tab
            
        # Update editor and result viewer
        self.prompt_editor.set_task_id(task_id)
        self.result_viewer.set_task_id(task_id)
        
        # Update variables tab if it exists
        if hasattr(self, 'right_sidebar') and self.right_sidebar.count() > 0:
            variables_editor = self.right_sidebar.widget(0)  # Variables tab is at index 0
            if hasattr(variables_editor, 'load_variables'):
                variables_editor.load_variables()
        
        # Update status bar
        task_name = self.task_navigator.get_task_name(task_id)
        self.status_bar.showMessage(f"Task: {task_name}" if task_name else "Task selected")
        
        # Emit signal for other components
        self.task_selected.emit(task_id)
        
    def on_task_created(self, task_id: str):
        """Handle task creation"""
        self.status_bar.showMessage("New task created", 2000)
        self.on_task_selected(task_id)
        
    def on_task_deleted(self, task_id: str):
        """Handle task deletion"""
        if self.current_task_id == task_id:
            self.current_task_id = None
            self.current_version_id = None
            self.prompt_editor.clear()
            self.result_viewer.clear()
            self.main_tabs.setCurrentIndex(0)  # Return to welcome tab
            
        self.status_bar.showMessage("Task deleted", 2000)
        
    def on_tab_changed(self, index: int):
        """Handle tab change"""
        tab_names = ["Welcome", "Editor", "LLM Provider"]
        if 0 <= index < len(tab_names):
            self.status_bar.showMessage(f"Switched to {tab_names[index]}", 2000)
            
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Prompt Manager",
            "Prompt Manager v1.0\n\n"
            "A powerful tool for managing and testing AI prompts\n"
            "with support for multiple LLM providers and version control.\n\n"
            "Built with PyQt6 and Python."
        )
        
    def closeEvent(self, event):
        """Handle application close event"""
        # Save window state
        self.save_window_state()
        
        # Clean up timers
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
            
        event.accept()
        
    def save_window_state(self):
        """Save window state to settings"""
        try:
            settings_path = Path("src/gui/settings.json")
            settings_path.parent.mkdir(exist_ok=True)
            
            settings = {
                "window_geometry": {
                    "x": self.x(),
                    "y": self.y(),
                    "width": self.width(),
                    "height": self.height()
                },
                "splitter_sizes": self.main_splitter.sizes(),
                "current_tab": self.main_tabs.currentIndex()
            }
            
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save window state: {e}")
            
    def load_window_state(self):
        """Load window state from settings"""
        try:
            settings_path = Path("src/gui/settings.json")
            if not settings_path.exists():
                return
                
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                
            # Restore window geometry
            if "window_geometry" in settings:
                geom = settings["window_geometry"]
                self.setGeometry(geom["x"], geom["y"], geom["width"], geom["height"])
                
            # Restore splitter sizes
            if "splitter_sizes" in settings:
                self.main_splitter.setSizes(settings["splitter_sizes"])
                
                
            # Restore current tab
            if "current_tab" in settings:
                self.main_tabs.setCurrentIndex(settings["current_tab"])
                
        except Exception as e:
            print(f"Failed to load window state: {e}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Prompt Manager")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Prompt Manager")
    
    # Create and show main window
    window = MainWindow()
    window.load_window_state()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
