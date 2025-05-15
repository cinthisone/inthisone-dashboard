from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton,
    QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

class CalculatorWidget(QWidget):
    """A basic calculator widget"""
    
    def __init__(self, db_manager, ingest_manager):
        super().__init__()
        self.db_manager = db_manager
        self.widget_id = None  # Will be set when added to dashboard
        
        # Initialize variables
        self.current_number = ""
        self.stored_number = None
        self.last_operation = None
        self.new_number = True
        
        # Set up the UI
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Display
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setText("0")
        self.display.setMinimumHeight(50)
        font = QFont("Arial", 20)
        self.display.setFont(font)
        layout.addWidget(self.display)
        
        # Buttons grid
        button_grid = QGridLayout()
        
        # Button labels
        buttons = [
            ['7', '8', '9', '/'],
            ['4', '5', '6', '*'],
            ['1', '2', '3', '-'],
            ['0', '.', '=', '+']
        ]
        
        # Create and add buttons
        for i, row in enumerate(buttons):
            for j, label in enumerate(row):
                button = QPushButton(label)
                button.setMinimumSize(50, 50)
                button.clicked.connect(self.button_clicked)
                if label.isdigit() or label == '.':
                    button.setStyleSheet("""
                        QPushButton {
                            background-color: palette(button);
                            border: 1px solid palette(mid);
                            border-radius: 5px;
                            color: palette(text);
                        }
                        QPushButton:hover {
                            background-color: palette(highlight);
                            color: palette(highlighted-text);
                        }
                    """)
                else:
                    button.setStyleSheet("""
                        QPushButton {
                            background-color: palette(dark);
                            color: palette(bright-text);
                            border: 1px solid palette(mid);
                            border-radius: 5px;
                        }
                        QPushButton:hover {
                            background-color: palette(highlight);
                            color: palette(highlighted-text);
                        }
                    """)
                button_grid.addWidget(button, i, j)
        
        # Additional row for clear buttons
        clear_button = QPushButton("C")
        clear_button.setMinimumSize(50, 50)
        clear_button.clicked.connect(self.clear)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: 1px solid #ff5252;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        button_grid.addWidget(clear_button, 4, 0, 1, 2)
        
        backspace_button = QPushButton("⌫")
        backspace_button.setMinimumSize(50, 50)
        backspace_button.clicked.connect(self.backspace)
        backspace_button.setStyleSheet("""
            QPushButton {
                background-color: palette(dark);
                color: palette(bright-text);
                border: 1px solid palette(mid);
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: palette(shadow);
            }
        """)
        button_grid.addWidget(backspace_button, 4, 2, 1, 2)
        
        layout.addLayout(button_grid)
        self.setLayout(layout)
        
        # Set size policies
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    
    def sizeHint(self):
        """Provide size hint for the widget"""
        return QSize(250, 350)
    
    def save_state(self):
        """Save calculator state"""
        if not self.widget_id:
            return
            
        state = {
            "display": self.display.text(),
            "stored_number": self.stored_number,
            "last_operation": self.last_operation,
            "new_number": self.new_number
        }
        
        self.db_manager.set_widget_data(self.widget_id, state)
    
    def restore_state(self, widget_id, state):
        """Restore calculator state"""
        self.widget_id = widget_id
        
        if not state:
            return
            
        self.display.setText(state.get("display", "0"))
        self.stored_number = state.get("stored_number")
        self.last_operation = state.get("last_operation")
        self.new_number = state.get("new_number", True)
    
    def button_clicked(self):
        """Handle button clicks"""
        button = self.sender()
        text = button.text()
        
        if text.isdigit() or text == '.':
            if self.new_number:
                self.display.setText(text)
                self.new_number = False
            else:
                current = self.display.text()
                if text == '.' and '.' in current:
                    return
                self.display.setText(current + text)
            self.save_state()
        else:
            self.handle_operation(text)
    
    def handle_operation(self, operation):
        """Handle mathematical operations"""
        try:
            current = float(self.display.text())
            
            if operation == '=':
                if self.stored_number is not None and self.last_operation:
                    if self.last_operation == '+':
                        result = self.stored_number + current
                    elif self.last_operation == '-':
                        result = self.stored_number - current
                    elif self.last_operation == '*':
                        result = self.stored_number * current
                    elif self.last_operation == '/':
                        if current == 0:
                            self.display.setText("Error")
                            self.new_number = True
                            return
                        result = self.stored_number / current
                    
                    # Format result
                    if result.is_integer():
                        self.display.setText(str(int(result)))
                    else:
                        self.display.setText(str(result))
                    
                    self.stored_number = None
                    self.last_operation = None
            else:
                self.stored_number = current
                self.last_operation = operation
                # Show the current number followed by the operator
                display_text = str(current) if current.is_integer() else str(float(current))
                self.display.setText(f"{display_text} {operation}")
                self.new_number = True
            
            self.save_state()
                
        except ValueError:
            self.display.setText("Error")
            self.new_number = True
            self.save_state()
    
    def clear(self):
        """Clear the calculator"""
        self.display.setText("0")
        self.stored_number = None
        self.last_operation = None
        self.new_number = True
        self.save_state()
    
    def backspace(self):
        """Handle backspace button"""
        current = self.display.text()
        if len(current) > 1:
            self.display.setText(current[:-1])
        else:
            self.display.setText("0")
            self.new_number = True
        self.save_state()

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "Calculator",
        "title": "Calculator",
        "description": "Basic calculator widget",
        "widget_class": CalculatorWidget,
        "module_name": "calculator"
    } 