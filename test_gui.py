#!/usr/bin/env python3
"""
Simple test to verify the GUI layout improvements
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtWidgets import QApplication
    from gui.main_window import MainWindow
    from utils.config import AppConfig
    
    def test_gui():
        app = QApplication(sys.argv)
        config = AppConfig()
        
        # Create main window
        window = MainWindow(config)
        window.show()
        
        print("GUI test launched successfully!")
        print("Check the Test Configuration section in the 'Test & Metrics' tab")
        print("The dropdown menus should now display text properly")
        
        return app.exec()
    
    if __name__ == "__main__":
        sys.exit(test_gui())
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure PyQt6 is installed: pip install PyQt6")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
