from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton,
    QLineEdit, QSizePolicy, QTabWidget, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
import math

class ScientificCalculatorWidget(QWidget):
    """A scientific calculator widget with advanced mathematical functions"""
    
    def __init__(self, db_manager, ingest_manager):
        super().__init__()
        self.db_manager = db_manager
        self.widget_id = None  # Will be set when added to dashboard
        
        # Initialize variables
        self.current_number = ""
        self.stored_number = None
        self.last_operation = None
        self.new_number = True
        self.memory = 0
        self.angle_mode = "DEG"  # DEG or RAD
        
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
        
        # Create tab widget for different button sets
        tab_widget = QTabWidget()
        
        # Basic calculator tab
        basic_tab = QFrame()
        basic_layout = QGridLayout()
        
        # Basic buttons
        basic_buttons = [
            ['7', '8', '9', '/'],
            ['4', '5', '6', '*'],
            ['1', '2', '3', '-'],
            ['0', '.', '=', '+']
        ]
        
        for i, row in enumerate(basic_buttons):
            for j, label in enumerate(row):
                button = QPushButton(label)
                button.setMinimumSize(40, 40)
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
                            background-color: palette(shadow);
                        }
                    """)
                basic_layout.addWidget(button, i, j)
        
        # Clear and backspace buttons
        clear_button = QPushButton("C")
        clear_button.setMinimumSize(40, 40)
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
        basic_layout.addWidget(clear_button, 4, 0, 1, 2)
        
        backspace_button = QPushButton("⌫")
        backspace_button.setMinimumSize(40, 40)
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
        basic_layout.addWidget(backspace_button, 4, 2, 1, 2)
        
        basic_tab.setLayout(basic_layout)
        tab_widget.addTab(basic_tab, "Basic")
        
        # Scientific tab
        scientific_tab = QFrame()
        scientific_layout = QGridLayout()
        
        # Scientific buttons
        scientific_buttons = [
            ['sin', 'cos', 'tan', 'π'],
            ['asin', 'acos', 'atan', 'e'],
            ['log', 'ln', 'x²', '√'],
            ['x^y', '1/x', '(', ')'],
            ['DEG', 'RAD', 'M+', 'MR']
        ]
        
        for i, row in enumerate(scientific_buttons):
            for j, label in enumerate(row):
                button = QPushButton(label)
                button.setMinimumSize(40, 40)
                button.clicked.connect(self.scientific_button_clicked)
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
                scientific_layout.addWidget(button, i, j)
        
        scientific_tab.setLayout(scientific_layout)
        tab_widget.addTab(scientific_tab, "Scientific")
        
        layout.addWidget(tab_widget)
        self.setLayout(layout)
        
        # Set size policies
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    
    def sizeHint(self):
        """Provide size hint for the widget"""
        return QSize(300, 450)
    
    def save_state(self):
        """Save calculator state"""
        if not self.widget_id:
            return
            
        state = {
            "display": self.display.text(),
            "stored_number": self.stored_number,
            "last_operation": self.last_operation,
            "new_number": self.new_number,
            "memory": self.memory,
            "angle_mode": self.angle_mode
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
        self.memory = state.get("memory", 0)
        self.angle_mode = state.get("angle_mode", "DEG")
    
    def button_clicked(self):
        """Handle basic button clicks"""
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
    
    def scientific_button_clicked(self):
        """Handle scientific button clicks"""
        button = self.sender()
        operation = button.text()
        
        try:
            current = float(self.display.text())
            
            if operation in ['sin', 'cos', 'tan']:
                if self.angle_mode == "DEG":
                    current = math.radians(current)
                if operation == 'sin':
                    result = math.sin(current)
                elif operation == 'cos':
                    result = math.cos(current)
                else:
                    result = math.tan(current)
            
            elif operation in ['asin', 'acos', 'atan']:
                if operation == 'asin':
                    result = math.asin(current)
                elif operation == 'acos':
                    result = math.acos(current)
                else:
                    result = math.atan(current)
                if self.angle_mode == "DEG":
                    result = math.degrees(result)
            
            elif operation == 'log':
                result = math.log10(current)
            elif operation == 'ln':
                result = math.log(current)
            elif operation == 'x²':
                result = current * current
            elif operation == '√':
                result = math.sqrt(current)
            elif operation == '1/x':
                if current == 0:
                    self.display.setText("Error")
                    self.save_state()
                    return
                result = 1 / current
            elif operation == 'π':
                result = math.pi
            elif operation == 'e':
                result = math.e
            elif operation == 'DEG':
                self.angle_mode = "DEG"
                self.save_state()
                return
            elif operation == 'RAD':
                self.angle_mode = "RAD"
                self.save_state()
                return
            elif operation == 'M+':
                self.memory += current
                self.save_state()
                return
            elif operation == 'MR':
                result = self.memory
            else:
                return
            
            # Format and display result
            if abs(result) < 1e-10:
                result = 0
            if float(result).is_integer():
                self.display.setText(str(int(result)))
            else:
                self.display.setText(str(result))
            
            self.new_number = True
            self.save_state()
            
        except Exception as e:
            self.display.setText("Error")
            self.new_number = True
            self.save_state()
    
    def handle_operation(self, operation):
        """Handle basic mathematical operations"""
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
                            self.save_state()
                            return
                        result = self.stored_number / current
                    elif self.last_operation == '^':
                        result = math.pow(self.stored_number, current)
                    
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
                op_symbol = '^' if operation == 'x^y' else operation
                self.display.setText(f"{display_text} {op_symbol}")
                self.new_number = True
            
            self.save_state()
                
        except Exception as e:
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
        "name": "Scientific Calculator",
        "title": "Scientific Calculator",
        "description": "Advanced scientific calculator with trigonometric and logarithmic functions",
        "widget_class": ScientificCalculatorWidget,
        "module_name": "scientific_calculator"
    } 