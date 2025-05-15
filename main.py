#!/usr/bin/env python3
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from app.main_window import MainWindow
from app.data_ingest import DataIngestManager
from app.db import DatabaseManager

def main():
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Inthisone Dashboard")
    app.setOrganizationName("Inthisone")
    
    # Initialize database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_data.db")
    db_manager = DatabaseManager(db_path)
    db_manager.initialize()
    
    # Initialize data ingest manager
    ingest_manager = DataIngestManager()
    
    # Create and show main window
    window = MainWindow(db_manager, ingest_manager)
    window.show()
    
    # Start the data ingest manager in a separate thread
    ingest_manager.start()
    
    # Execute application
    exit_code = app.exec()
    
    # Clean up before exit
    ingest_manager.stop()
    window.save_layout()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()