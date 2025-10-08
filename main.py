#!/usr/bin/env python3
"""
Serial Communication Performance Testing Tool
Main application entry point
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from gui.main_window import MainWindow
from utils.config import AppConfig

def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('serial_tester.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Serial Communication Performance Tester")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SerialTester")
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Serial Communication Performance Tester")
    
    # Load configuration
    config = AppConfig()
    
    # Create and show main window
    main_window = MainWindow(config)
    main_window.show()
    
    # Setup periodic cleanup timer
    cleanup_timer = QTimer()
    cleanup_timer.timeout.connect(lambda: None)  # Placeholder for cleanup tasks
    cleanup_timer.start(60000)  # Every minute
    
    try:
        exit_code = app.exec()
        logger.info("Application closing normally")
        return exit_code
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
