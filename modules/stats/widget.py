from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QTableView, QHeaderView,
    QFormLayout, QGroupBox, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
import random
import numpy as np
import sys
import os

# Add the cpp_example directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cpp_example"))

# Try to import the stats wrapper
try:
    from cpp_example.stats_wrapper import stats
    STATS_LIB_AVAILABLE = True
except ImportError:
    STATS_LIB_AVAILABLE = False

class StatsWidget(QWidget):
    """A widget for demonstrating the C++ stats library"""
    
    def __init__(self, db_manager, ingest_manager):
        super().__init__()
        
        self.db_manager = db_manager
        self.ingest_manager = ingest_manager
        self.widget_id = "stats"
        
        # Initialize data
        self.data = []
        
        # Set up the UI
        self._init_ui()
        
        # Generate some initial data
        self._generate_random_data()
    
    def _init_ui(self):
        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create status label
        if not STATS_LIB_AVAILABLE:
            status_label = QLabel("C++ Stats Library Not Available")
            status_label.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(status_label)
        
        # Create data input group
        data_group = QGroupBox("Data")
        data_layout = QVBoxLayout()
        
        # Data input
        self.data_input = QTextEdit()
        self.data_input.setPlaceholderText("Enter numbers separated by commas, spaces, or new lines")
        data_layout.addWidget(self.data_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.generate_button = QPushButton("Generate Random Data")
        self.generate_button.clicked.connect(self._generate_random_data)
        button_layout.addWidget(self.generate_button)
        
        self.calculate_button = QPushButton("Calculate Statistics")
        self.calculate_button.clicked.connect(self._calculate_statistics)
        button_layout.addWidget(self.calculate_button)
        
        data_layout.addLayout(button_layout)
        
        # Set layout for data group
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Create results group
        results_group = QGroupBox("Results")
        results_layout = QFormLayout()
        
        # Results labels
        self.count_label = QLabel("0")
        results_layout.addRow("Count:", self.count_label)
        
        self.mean_label = QLabel("0.0")
        results_layout.addRow("Mean:", self.mean_label)
        
        self.median_label = QLabel("0.0")
        results_layout.addRow("Median:", self.median_label)
        
        self.stddev_label = QLabel("0.0")
        results_layout.addRow("Standard Deviation:", self.stddev_label)
        
        self.min_label = QLabel("0.0")
        results_layout.addRow("Minimum:", self.min_label)
        
        self.max_label = QLabel("0.0")
        results_layout.addRow("Maximum:", self.max_label)
        
        # Set layout for results group
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Set layout
        self.setLayout(layout)
        
        # Set minimum size
        self.setMinimumSize(300, 400)
    
    def _generate_random_data(self):
        """Generate random data for demonstration"""
        # Generate 100 random numbers
        self.data = [random.normalvariate(50, 15) for _ in range(100)]
        
        # Update the data input
        self.data_input.setText(", ".join(f"{x:.2f}" for x in self.data))
        
        # Calculate statistics
        self._calculate_statistics()
    
    def _parse_data_input(self):
        """Parse the data input text into a list of numbers"""
        text = self.data_input.toPlainText()
        
        # Replace commas with spaces
        text = text.replace(",", " ")
        
        # Split by whitespace
        parts = text.split()
        
        # Convert to numbers
        data = []
        for part in parts:
            try:
                value = float(part)
                data.append(value)
            except ValueError:
                pass
        
        return data
    
    def _calculate_statistics(self):
        """Calculate statistics using the C++ library"""
        # Parse data from input
        self.data = self._parse_data_input()
        
        if not self.data:
            QMessageBox.warning(self, "No Data", "Please enter or generate some data first.")
            return
        
        # Update count
        self.count_label.setText(str(len(self.data)))
        
        if STATS_LIB_AVAILABLE:
            # Use C++ library for calculations
            mean = stats.mean(self.data)
            median = stats.median(self.data)
            stddev = stats.stddev(self.data)
        else:
            # Fall back to numpy
            mean = np.mean(self.data)
            median = np.median(self.data)
            stddev = np.std(self.data, ddof=1)  # ddof=1 for sample standard deviation
        
        # Calculate min and max using Python
        min_val = min(self.data)
        max_val = max(self.data)
        
        # Update labels
        self.mean_label.setText(f"{mean:.4f}")
        self.median_label.setText(f"{median:.4f}")
        self.stddev_label.setText(f"{stddev:.4f}")
        self.min_label.setText(f"{min_val:.4f}")
        self.max_label.setText(f"{max_val:.4f}")
    
    def refresh(self):
        """Refresh the widget"""
        self._calculate_statistics()

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "Statistics",
        "title": "Statistics",
        "description": "Calculate statistics using C++ library",
        "widget_class": StatsWidget
    }