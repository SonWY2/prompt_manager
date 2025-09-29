"""
Theme Manager for PyQt GUI Application
"""

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from typing import Optional


class ThemeManager:
    """Manages application themes and styling"""
    
    def __init__(self):
        self.light_stylesheet = self._get_light_stylesheet()
        self.dark_stylesheet = self._get_dark_stylesheet()
        
    def apply_theme(self, widget: QWidget, is_dark: bool = False):
        """Apply theme to a widget"""
        if is_dark:
            widget.setStyleSheet(self.dark_stylesheet)
            self._set_dark_palette()
        else:
            widget.setStyleSheet(self.light_stylesheet)
            self._set_light_palette()
            
    def _set_light_palette(self):
        """Set light theme palette"""
        app = QApplication.instance()
        if app:
            palette = QPalette()
            
            # Window colors
            palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
            
            # Base colors
            palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
            
            # Button colors
            palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
            
            # Highlight colors
            palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 123, 255))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
            
            app.setPalette(palette)
            
    def _set_dark_palette(self):
        """Set dark theme palette"""
        app = QApplication.instance()
        if app:
            palette = QPalette()
            
            # Window colors
            palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            
            # Base colors
            palette.setColor(QPalette.ColorRole.Base, QColor(60, 60, 60))
            palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
            
            # Button colors
            palette.setColor(QPalette.ColorRole.Button, QColor(85, 85, 85))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            
            # Highlight colors
            palette.setColor(QPalette.ColorRole.Highlight, QColor(139, 92, 246))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
            
            app.setPalette(palette)
            
    def _get_light_stylesheet(self) -> str:
        """Get light theme stylesheet"""
        return """
            /* Main Window */
            QMainWindow {
                background-color: #ffffff;
                color: #000000;
            }
            
            /* Menu Bar */
            QMenuBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 4px;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
                border-radius: 4px;
            }
            
            QMenuBar::item:selected {
                background-color: #e9ecef;
            }
            
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
            }
            
            QMenu::item {
                padding: 6px 12px;
                border-radius: 4px;
            }
            
            QMenu::item:selected {
                background-color: #007bff;
                color: white;
            }
            
            /* Status Bar */
            QStatusBar {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                padding: 4px;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: #ffffff;
            }
            
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
            
            QPushButton:disabled {
                background-color: #6c757d;
                color: #ffffff;
            }
            
            /* Secondary Button */
            QPushButton[class="secondary"] {
                background-color: #6c757d;
            }
            
            QPushButton[class="secondary"]:hover {
                background-color: #545b62;
            }
            
            /* Danger Button */
            QPushButton[class="danger"] {
                background-color: #dc3545;
            }
            
            QPushButton[class="danger"]:hover {
                background-color: #c82333;
            }
            
            /* Input Fields */
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
            }
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #007bff;
                outline: none;
            }
            
            /* List Widget */
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #000000;
            }
            
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
            
            /* Splitter */
            QSplitter::handle {
                background-color: #dee2e6;
                width: 2px;
                height: 2px;
            }
            
            QSplitter::handle:hover {
                background-color: #007bff;
            }
            
            /* Scroll Bar */
            QScrollBar:vertical {
                border: none;
                background-color: #f8f9fa;
                width: 8px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #ced4da;
                border-radius: 4px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            
            /* Label */
            QLabel {
                color: #000000;
            }
            
            QLabel[class="muted"] {
                color: #6c757d;
            }
            
            QLabel[class="primary"] {
                color: #007bff;
                font-weight: bold;
            }
        """
        
    def _get_dark_stylesheet(self) -> str:
        """Get dark theme stylesheet"""
        return """
            /* Main Window */
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            /* Menu Bar */
            QMenuBar {
                background-color: #2d2d2d;
                border-bottom: 1px solid #404040;
                padding: 4px;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
                border-radius: 4px;
                color: #ffffff;
            }
            
            QMenuBar::item:selected {
                background-color: #404040;
            }
            
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px;
                color: #ffffff;
            }
            
            QMenu::item {
                padding: 6px 12px;
                border-radius: 4px;
            }
            
            QMenu::item:selected {
                background-color: #8b5cf6;
                color: white;
            }
            
            /* Status Bar */
            QStatusBar {
                background-color: #2d2d2d;
                border-top: 1px solid #404040;
                padding: 4px;
                color: #ffffff;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1e1e1e;
            }
            
            QTabBar::tab {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
                color: #ffffff;
            }
            
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                border-bottom: 1px solid #1e1e1e;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #404040;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #8b5cf6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #7c3aed;
            }
            
            QPushButton:pressed {
                background-color: #6d28d9;
            }
            
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
            
            /* Secondary Button */
            QPushButton[class="secondary"] {
                background-color: #6c757d;
            }
            
            QPushButton[class="secondary"]:hover {
                background-color: #5a6268;
            }
            
            /* Danger Button */
            QPushButton[class="danger"] {
                background-color: #dc3545;
            }
            
            QPushButton[class="danger"]:hover {
                background-color: #c82333;
            }
            
            /* Input Fields */
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                color: #ffffff;
            }
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #8b5cf6;
                outline: none;
            }
            
            /* List Widget */
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2d2d2d;
                color: #ffffff;
            }
            
            QListWidget::item:selected {
                background-color: #3d4ed8;
                color: #ffffff;
            }
            
            QListWidget::item:hover {
                background-color: #2d2d2d;
            }
            
            /* Splitter */
            QSplitter::handle {
                background-color: #404040;
                width: 2px;
                height: 2px;
            }
            
            QSplitter::handle:hover {
                background-color: #8b5cf6;
            }
            
            /* Scroll Bar */
            QScrollBar:vertical {
                border: none;
                background-color: #2d2d2d;
                width: 8px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 4px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #555555;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            
            /* Label */
            QLabel {
                color: #ffffff;
            }
            
            QLabel[class="muted"] {
                color: #adb5bd;
            }
            
            QLabel[class="primary"] {
                color: #8b5cf6;
                font-weight: bold;
            }
        """

