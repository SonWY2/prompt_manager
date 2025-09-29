#!/usr/bin/env python3
"""
Prompt Manager GUI Launcher

이 스크립트는 Prompt Manager의 PyQt GUI 버전을 실행합니다.
웹 프론트엔드 대신 네이티브 GUI 환경에서 동일한 기능을 사용할 수 있습니다.

사용법:
    python run_gui.py

요구사항:
    - Python 3.8+
    - PyQt6
    - requests
    - 백엔드 서버가 실행 중이어야 함 (http://localhost:8000)
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
except ImportError as e:
    print("❌ PyQt6 is not installed.")
    print("Please install PyQt6 using: pip install PyQt6")
    print(f"Error details: {e}")
    sys.exit(1)

try:
    import requests
except ImportError as e:
    print("❌ requests library is not installed.")
    print("Please install requests using: pip install requests")
    print(f"Error details: {e}")
    sys.exit(1)

# Import GUI application
try:
    from gui.main_window import MainWindow
except ImportError as e:
    print("❌ Failed to import GUI components.")
    print("Please make sure all GUI files are in the src/gui directory.")
    print(f"Error details: {e}")
    sys.exit(1)


def check_backend_server(url="http://localhost:8000"):
    """Check if backend server is running"""
    try:
        response = requests.get(f"{url}/api/tasks", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def start_backend_server():
    """Start the backend server"""
    try:
        backend_script = Path(__file__).parent / "src" / "backend" / "main.py"
        if not backend_script.exists():
            print("❌ Backend server script not found.")
            print(f"Expected location: {backend_script}")
            return None
            
        print("🚀 Starting backend server...")
        print(f"🐍 Using Python: {sys.executable}")
        print(f"📁 Backend script: {backend_script}")
        
        # Start server with visible output for debugging
        process = subprocess.Popen([
            sys.executable, str(backend_script)
        ], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,  # Redirect stderr to stdout
        universal_newlines=True,
        bufsize=1
        )
        
        # Wait for server to start with better feedback
        print("⏳ Waiting for backend server to start...")
        for i in range(30):  # Wait up to 30 seconds
            # Check if process is still running
            if process.poll() is not None:
                # Process has terminated
                stdout, _ = process.communicate()
                print("❌ Backend server process terminated unexpectedly!")
                if stdout:
                    print("📝 Server output:")
                    print(stdout)
                return None
                
            if check_backend_server():
                print("✅ Backend server is running!")
                return process
                
            # Show progress every 5 seconds
            if (i + 1) % 5 == 0:
                print(f"⏳ Still waiting... ({i+1}/30 seconds)")
            
            time.sleep(1)
            
        print("❌ Backend server failed to start within 30 seconds")
        
        # Get any output before terminating
        try:
            stdout, _ = process.communicate(timeout=2)
            if stdout:
                print("📝 Server output before termination:")
                print(stdout)
        except subprocess.TimeoutExpired:
            pass
            
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Failed to start backend server: {e}")
        import traceback
        traceback.print_exc()
        return None


def show_server_error_dialog():
    """Show error dialog for server connection issues"""
    app = QApplication.instance()
    if not app:
        app = QApplication([])
        
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Backend Server Error")
    msg.setText("Cannot connect to backend server")
    msg.setInformativeText(
        "The Prompt Manager GUI requires a backend server to function.\n\n"
        "Please ensure that:\n"
        "1. The backend server is running on http://localhost:8000\n"
        "2. You have the required dependencies installed\n"
        "3. The database is properly initialized\n\n"
        "You can start the backend server manually by running:\n"
        "python src/backend/main.py"
    )
    msg.setStandardButtons(
        QMessageBox.StandardButton.Retry | 
        QMessageBox.StandardButton.Ignore | 
        QMessageBox.StandardButton.Close
    )
    msg.setDefaultButton(QMessageBox.StandardButton.Retry)
    
    return msg.exec()


def main():
    """Main application entry point"""
    print("🎨 Prompt Manager GUI")
    print("=" * 50)
    
    # Using direct SQLite connection - no backend server needed
    print("🔍 Initializing database connection...")
    print("✅ Using direct SQLite connection!")
    backend_process = None
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Prompt Manager")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Prompt Manager")
    app.setApplicationDisplayName("Prompt Manager GUI")
    
    # Set application icon if available
    icon_path = Path(__file__).parent / "public" / "logo.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Enable high DPI scaling for PyQt6
    # Note: AA_EnableHighDpiScaling is deprecated in PyQt6
    # High DPI scaling is enabled by default in PyQt6
    try:
        # Try to set AA_UseHighDpiPixmaps if available
        if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
            app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # Ignore if not available - PyQt6 handles High DPI automatically
        pass
    
    try:
        # Create and show main window
        print("🖥️  Initializing GUI...")
        window = MainWindow()
        
        # Load window state from settings
        window.load_window_state()
        
        # Show window
        window.show()
        print("✅ GUI initialized successfully!")
        
        # Show welcome message
        print("\n" + "=" * 50)
        print("🎉 Prompt Manager GUI is now running!")
        print("📝 You can now manage prompts, test with LLMs, and more.")
        print("🔧 Use the File menu to create tasks and manage settings.")
        print("🌙 Toggle dark mode with Ctrl+D")
        print("❓ Use Help > About for more information")
        print("=" * 50)
        
        # Run application
        exit_code = app.exec()
        
        # Cleanup
        print("\n👋 Shutting down...")
        if backend_process:
            print("🛑 Stopping backend server...")
            backend_process.terminate()
            backend_process.wait()
            
        return exit_code
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        if 'backend_process' in locals() and backend_process:
            backend_process.terminate()
            
        return 1


if __name__ == "__main__":
    sys.exit(main())
