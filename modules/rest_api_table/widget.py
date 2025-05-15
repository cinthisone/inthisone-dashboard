from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QTableView, QHeaderView,
    QComboBox, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from PySide6.QtGui import QColor

import json

class JsonTableModel(QAbstractTableModel):
    """Table model for displaying JSON data"""
    
    def __init__(self, data=None):
        super().__init__()
        self._data = []
        self._headers = []
        
        if data:
            self.update_data(data)
    
    def update_data(self, data):
        """Update the model with new data"""
        self.beginResetModel()
        
        if isinstance(data, list) and len(data) > 0:
            # Use the first item to determine headers
            self._headers = list(data[0].keys())
            self._data = data
        elif isinstance(data, dict):
            # If it's a dictionary, convert to a list of dictionaries
            self._headers = list(data.keys())
            self._data = [data]
        else:
            # Empty or invalid data
            self._headers = []
            self._data = []
        
        self.endResetModel()
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None
        
        row = index.row()
        col = index.column()
        column_name = self._headers[col]
        
        if role == Qt.DisplayRole:
            # Get the value for the cell
            value = self._data[row].get(column_name)
            
            # Convert value to string for display
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)
            elif value is None:
                return ""
            else:
                return str(value)
        
        elif role == Qt.BackgroundRole:
            # Alternate row colors
            if row % 2 == 0:
                return QColor(245, 245, 245)
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal and section < len(self._headers):
                return self._headers[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        
        return None

class RestApiTableWidget(QWidget):
    """A widget for displaying data from a REST API in a table"""
    
    def __init__(self, db_manager, ingest_manager):
        super().__init__()
        
        self.db_manager = db_manager
        self.ingest_manager = ingest_manager
        self.widget_id = "rest_api_table"
        
        # Connect to ingest manager signals
        self.ingest_manager.api_data_ready.connect(self._on_api_data_ready)
        
        # Initialize variables
        self.current_url = self.db_manager.get_widget_setting(
            self.widget_id, "url", "https://jsonplaceholder.typicode.com/todos"
        )
        self.auto_refresh = self.db_manager.get_widget_setting(
            self.widget_id, "auto_refresh", False
        )
        self.refresh_interval = int(self.db_manager.get_widget_setting(
            self.widget_id, "refresh_interval", 60
        ))
        
        # Set up the UI
        self._init_ui()
        
        # Set up auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self._update_refresh_timer()
        
        # Initial data fetch
        self.refresh()
    
    def _init_ui(self):
        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create settings group
        settings_group = QGroupBox("API Settings")
        settings_layout = QFormLayout()
        
        # URL input
        self.url_input = QLineEdit(self.current_url)
        self.url_input.setPlaceholderText("Enter API URL")
        self.url_input.editingFinished.connect(self._url_changed)
        settings_layout.addRow("URL:", self.url_input)
        
        # Auto-refresh settings
        refresh_layout = QHBoxLayout()
        
        self.auto_refresh_combo = QComboBox()
        self.auto_refresh_combo.addItem("Manual Refresh", False)
        self.auto_refresh_combo.addItem("Auto Refresh", True)
        self.auto_refresh_combo.setCurrentIndex(1 if self.auto_refresh else 0)
        self.auto_refresh_combo.currentIndexChanged.connect(self._auto_refresh_changed)
        
        self.refresh_interval_combo = QComboBox()
        self.refresh_interval_combo.addItem("30 seconds", 30)
        self.refresh_interval_combo.addItem("1 minute", 60)
        self.refresh_interval_combo.addItem("5 minutes", 300)
        self.refresh_interval_combo.addItem("15 minutes", 900)
        self.refresh_interval_combo.addItem("30 minutes", 1800)
        
        # Set current interval
        index = self.refresh_interval_combo.findData(self.refresh_interval)
        if index >= 0:
            self.refresh_interval_combo.setCurrentIndex(index)
        self.refresh_interval_combo.currentIndexChanged.connect(self._refresh_interval_changed)
        
        refresh_layout.addWidget(self.auto_refresh_combo)
        refresh_layout.addWidget(self.refresh_interval_combo)
        
        settings_layout.addRow("Refresh:", refresh_layout)
        
        # Set layout for settings group
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Create toolbar
        toolbar = QHBoxLayout()
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh Now")
        self.refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(self.refresh_button)
        
        # Add spacer
        toolbar.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready")
        toolbar.addWidget(self.status_label)
        
        # Add toolbar to layout
        layout.addLayout(toolbar)
        
        # Create table view
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.verticalHeader().setVisible(True)
        
        # Create and set model
        self.table_model = JsonTableModel()
        self.table_view.setModel(self.table_model)
        
        # Add table to layout
        layout.addWidget(self.table_view)
        
        # Set layout
        self.setLayout(layout)
        
        # Set minimum size
        self.setMinimumSize(500, 400)
    
    def _url_changed(self):
        """Handle URL input changes"""
        new_url = self.url_input.text().strip()
        if new_url and new_url != self.current_url:
            self.current_url = new_url
            self.db_manager.set_widget_setting(self.widget_id, "url", self.current_url)
            self.refresh()
    
    def _auto_refresh_changed(self, index):
        """Handle auto-refresh setting changes"""
        self.auto_refresh = self.auto_refresh_combo.currentData()
        self.db_manager.set_widget_setting(self.widget_id, "auto_refresh", self.auto_refresh)
        self._update_refresh_timer()
    
    def _refresh_interval_changed(self, index):
        """Handle refresh interval changes"""
        self.refresh_interval = self.refresh_interval_combo.currentData()
        self.db_manager.set_widget_setting(self.widget_id, "refresh_interval", self.refresh_interval)
        self._update_refresh_timer()
    
    def _update_refresh_timer(self):
        """Update the refresh timer based on current settings"""
        if self.auto_refresh and self.refresh_interval > 0:
            self.refresh_timer.start(self.refresh_interval * 1000)
            self.refresh_interval_combo.setEnabled(True)
        else:
            self.refresh_timer.stop()
            self.refresh_interval_combo.setEnabled(self.auto_refresh)
    
    def refresh(self):
        """Refresh data from the API"""
        if not self.current_url:
            return
        
        # Update status
        self.status_label.setText("Fetching data...")
        
        # Request data through the ingest manager
        source_id = f"rest_api_table_{id(self)}"
        self.ingest_manager.ingest_api(source_id, self.current_url)
    
    def _on_api_data_ready(self, source_id, data):
        """Handle API data received from ingest manager"""
        # Check if this data is for us
        if source_id.startswith(f"rest_api_table_{id(self)}"):
            # Update the table model
            self.table_model.update_data(data)
            
            # Update status
            self.status_label.setText(f"Data updated: {len(data)} records")
            
            # Resize columns to content
            self.table_view.resizeColumnsToContents()

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "REST API Table",
        "title": "REST API Table",
        "description": "Display data from a REST API in a table",
        "widget_class": RestApiTableWidget
    }