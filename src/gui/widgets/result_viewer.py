"""
Result Viewer Widget - PyQt GUI equivalent of ResultViewer.jsx
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QTabWidget, QScrollArea, QFrame, QListWidget,
    QListWidgetItem, QSplitter, QMessageBox, QProgressBar,
    QGroupBox, QFormLayout, QTextBrowser
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
                 input_data: Dict[str, Any], system_prompt: str, endpoint: Optional[Dict[str, Any]]):
        super().__init__()
        self.db_client = db_client
        self.task_id = task_id
        self.version_id = version_id
        self.input_data = input_data
        self.system_prompt = system_prompt
        self.endpoint = endpoint
        
    def run(self):
        """Run the LLM call"""
        try:
            result = self.db_client.call_llm(
                self.task_id, 
                self.version_id, 
                self.input_data, 
                self.system_prompt,
                self.endpoint
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ResultHistoryItem(QFrame):
    """Custom history item widget"""
    
    clicked = pyqtSignal(dict)  # result data
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
        """Get model information"""
        endpoint = self.result_data.get('endpoint', {})
        if endpoint and endpoint.get('defaultModel'):
            return endpoint['defaultModel']
        elif endpoint and endpoint.get('name'):
            return endpoint['name']
        return None
        
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.result_data)
        super().mousePressEvent(event)


class ResultDetail(QWidget):
    """Widget for displaying detailed result information"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the result detail UI"""
        layout = QVBoxLayout(self)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
        
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
        """Show detailed result information"""
        self.clear_content()
        
        # Request section
        request_group = QGroupBox("Request Message")
        request_layout = QVBoxLayout(request_group)
        
        # Build request message
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
            variables_edit.setPlainText(json.dumps(input_data, indent=2))
            variables_edit.setMaximumHeight(150)
            variables_layout.addWidget(variables_edit)
            
            self.content_layout.addWidget(variables_group)
            
        # Raw output section
        raw_group = QGroupBox("Raw Output")
        raw_layout = QVBoxLayout(raw_group)
        
        raw_edit = QTextBrowser()
        raw_edit.setPlainText(json.dumps(result_data.get('output', {}), indent=2))
        raw_edit.setMaximumHeight(200)
        raw_layout.addWidget(raw_edit)
        
        self.content_layout.addWidget(raw_group)
        
        # Add stretch
        self.content_layout.addStretch()
        
    def clear_content(self):
        """Clear the content"""
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i)
            if child and child.widget():
                child.widget().deleteLater()
                
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
        
        # LLM Provider info
        self.provider_frame = QFrame()
        self.provider_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(139, 92, 246, 0.1);
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 6px;
                padding: 8px;
            }
        """)
        provider_layout = QHBoxLayout(self.provider_frame)
        provider_layout.setContentsMargins(8, 4, 8, 4)
        
        self.provider_status_dot = QLabel("🔴")
        self.provider_name_label = QLabel("No LLM Provider")
        self.provider_model_label = QLabel("")
        
        provider_layout.addWidget(self.provider_status_dot)
        provider_layout.addWidget(self.provider_name_label)
        provider_layout.addWidget(self.provider_model_label)
        provider_layout.addStretch()
        
        header_layout.addWidget(self.provider_frame)
        
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
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
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
                    
            self.update_provider_info()
            
        except Exception as e:
            print(f"Failed to load endpoints: {e}")
            
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
        """Set the current task"""
        self.current_task_id = task_id
        self.current_version_id = None
        self.load_task_data()
        
    def set_version_id(self, version_id: str):
        """Set the current version"""
        self.current_version_id = version_id
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
                history_item.clicked.connect(
                    lambda data: self.result_detail.show_result(data, self.version_data)
                )
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
                
        # Show loading state
        self.run_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Running...")
        
        # Start LLM call thread
        self.llm_thread = LLMCallThread(
            self.db_client,
            self.current_task_id,
            self.current_version_id,
            variables,
            system_prompt,
            self.active_endpoint
        )
        self.llm_thread.finished.connect(self.on_llm_finished)
        self.llm_thread.error.connect(self.on_llm_error)
        self.llm_thread.start()
        
    def on_llm_finished(self, result: Dict[str, Any]):
        """Handle LLM call completion"""
        # Hide loading state
        self.run_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Completed at {datetime.now().strftime('%H:%M:%S')}")
        
        # Create result data
        result_data = {
            'inputData': getattr(self.llm_thread, 'input_data', {}),
            'output': result,
            'timestamp': datetime.now().isoformat(),
            'endpoint': self.active_endpoint
        }
        
        # Add to results
        self.results.insert(0, result_data)  # Add at beginning
        
        # Refresh displays
        self.refresh_history()
        self.show_latest_result(result_data)
        
    def on_llm_error(self, error: str):
        """Handle LLM call error"""
        # Hide loading state
        self.run_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Error")
        
        QMessageBox.critical(self, "LLM Error", f"Failed to call LLM: {error}")
        
    def show_latest_result(self, result_data: Dict[str, Any]):
        """Show the latest result in the response tab"""
        # Switch to response tab
        self.tab_widget.setCurrentIndex(0)
        
        # Clear existing result display
        for i in reversed(range(self.result_display.layout().count())):
            child = self.result_display.layout().itemAt(i)
            if child and child.widget() and child.widget() != self.run_button and child.widget() != self.progress_bar:
                child.widget().deleteLater()
                
        # Show result
        result_frame = QFrame()
        result_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 16px;
                margin: 8px 0;
            }
        """)
        result_layout = QVBoxLayout(result_frame)
        
        # Header
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("🤖")
        header_layout.addWidget(icon_label)
        
        response_label = QLabel(f"{self.active_endpoint.get('name', 'AI')} Response")
        response_label.setFont(QFont("", 12, QFont.Weight.Medium))
        header_layout.addWidget(response_label)
        
        header_layout.addStretch()
        
        timestamp_label = QLabel(datetime.now().strftime('%H:%M:%S'))
        timestamp_label.setStyleSheet("color: #666; font-size: 10px;")
        header_layout.addWidget(timestamp_label)
        
        result_layout.addLayout(header_layout)
        
        # Response content
        content = self._extract_response_content(result_data.get('output', {}))
        response_edit = QTextBrowser()
        response_edit.setPlainText(content)
        response_edit.setMaximumHeight(300)
        result_layout.addWidget(response_edit)
        
        # Add to display
        self.result_display.layout().addWidget(result_frame)
        
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
        self.provider_name_label.setText("No LLM Provider")
        self.provider_status_dot.setText("🔴")
        
    def show_task_selected_state(self):
        """Show state when task is selected but no version"""
        # Update status  
        task_name = self.task_data.get('name', 'Unknown') if self.task_data else 'Unknown'
        self.status_label.setText(f"Task: {task_name}")
        
        # Update provider info if available
        if self.active_endpoint:
            self.provider_name_label.setText(self.active_endpoint.get('name', 'Unknown'))
            self.provider_status_dot.setText("🟢")
        else:
            self.provider_name_label.setText("No LLM Provider")
            self.provider_status_dot.setText("🔴")
        
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
        
        
        self.refresh_history()
        self.result_detail.show_empty_state()
        self.show_no_task_state()
        
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
