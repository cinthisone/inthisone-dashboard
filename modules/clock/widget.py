from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, 
    QPushButton, QHBoxLayout, QFrame, QGridLayout,
    QApplication, QSizePolicy
)
from PySide6.QtCore import (
    QTimer, Qt, QDateTime, QMimeData, QPoint,
    QSize
)
from PySide6.QtGui import QDrag
import pytz

class TimeZoneDisplay(QFrame):
    """A draggable widget to display time in a specific timezone"""
    def __init__(self, timezone="UTC", parent=None):
        super().__init__(parent)
        
        # Ensure timezone is valid
        try:
            if not isinstance(timezone, str):
                timezone = str(timezone)
            if timezone not in pytz.all_timezones:
                timezone = "UTC"
            self.timezone = timezone
            
        except Exception as e:
            print(f"Error setting timezone: {e}, falling back to UTC")
            self.timezone = "UTC"
        
        self._init_ui()
        
        # Enable mouse tracking for drag and drop
        self.setMouseTracking(True)
        self.drag_start_position = None
        
        # Set size policies
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
    
    def sizeHint(self):
        """Provide size hint for the widget"""
        return QSize(200, 120)
    
    def minimumSizeHint(self):
        """Provide minimum size hint for the widget"""
        return QSize(150, 100)
    
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        # Adjust font sizes based on widget width
        width = event.size().width()
        if width < 180:
            self.time_label.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                color: palette(text);
            """)
            self.date_label.setStyleSheet("""
                font-size: 10px;
                color: palette(text);
            """)
        else:
            self.time_label.setStyleSheet("""
                font-size: 24px;
                font-weight: bold;
                color: palette(text);
            """)
            self.date_label.setStyleSheet("""
                font-size: 12px;
                color: palette(text);
            """)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for drag and drop"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for drag and drop"""
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self.drag_start_position:
            return
        
        # Check if the mouse has moved far enough to start a drag
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        
        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.timezone)  # Store timezone as drag data
        drag.setMimeData(mime_data)
        
        # Execute drag
        drag.exec_(Qt.MoveAction)
    
    def _init_ui(self):
        try:
            # Main layout
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(10, 5, 10, 5)
            main_layout.setSpacing(2)
            
            # Header layout with timezone and remove button
            header_layout = QHBoxLayout()
            header_layout.setSpacing(5)
            
            # Timezone label
            self.tz_label = QLabel()
            self.tz_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.tz_label.setStyleSheet("""
                font-size: 10px;
                color: palette(text);
            """)
            self.tz_label.setText(self.timezone)
            header_layout.addWidget(self.tz_label, stretch=1)
            
            # Remove button
            remove_button = QPushButton("×")
            remove_button.setFixedSize(16, 16)
            remove_button.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    color: palette(text);
                    font-size: 14px;
                    padding: 0px;
                }
                QPushButton:hover {
                    color: palette(highlight);
                }
            """)
            remove_button.clicked.connect(self.remove_timezone)
            header_layout.addWidget(remove_button)
            
            main_layout.addLayout(header_layout)
            
            # Time label
            self.time_label = QLabel()
            self.time_label.setAlignment(Qt.AlignCenter)
            self.time_label.setStyleSheet("""
                font-size: 24px;
                font-weight: bold;
                color: palette(text);
            """)
            main_layout.addWidget(self.time_label)
            
            # Date label
            self.date_label = QLabel()
            self.date_label.setAlignment(Qt.AlignCenter)
            self.date_label.setStyleSheet("""
                font-size: 12px;
                color: palette(text);
            """)
            main_layout.addWidget(self.date_label)
            
            self.setLayout(main_layout)
            self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
            self.setStyleSheet("""
                TimeZoneDisplay {
                    border: 1px solid palette(mid);
                    border-radius: 5px;
                    background-color: palette(base);
                }
            """)
            
            # Initial time update
            self.update_time()
            
        except Exception as e:
            print(f"Error initializing TimeZoneDisplay UI: {e}")
            import traceback
            traceback.print_exc()
    
    def update_time(self):
        """Update the time display"""
        try:
            tz = pytz.timezone(self.timezone)
            now = QDateTime.currentDateTime().toPython().astimezone(tz)
            
            self.time_label.setText(now.strftime("%I:%M:%S %p"))
            self.date_label.setText(now.strftime("%A, %B %d"))
            self.tz_label.setText(f"{self.timezone} ({now.strftime('%Z')})")
            
        except Exception as e:
            print(f"Error updating time display: {e}")
            self.time_label.setText("Error")
            self.date_label.setText("")
    
    def set_timezone(self, timezone):
        """Set the timezone for this display"""
        try:
            if not isinstance(timezone, str):
                timezone = str(timezone)
            if timezone in pytz.all_timezones:
                self.timezone = timezone
                self.update_time()
            else:
                print(f"Invalid timezone: {timezone}")
        except Exception as e:
            print(f"Error setting timezone: {e}")
    
    def remove_timezone(self):
        """Remove this timezone display"""
        try:
            if isinstance(self.parent(), ClockWidget):
                self.parent().remove_timezone(self)
        except Exception as e:
            print(f"Error removing timezone: {e}")

class ClockWidget(QWidget):
    """A widget displaying multiple time zones in a grid"""
    
    def __init__(self, db_manager, ingest_manager):
        super().__init__()
        self.db_manager = db_manager
        self.widget_id = "clock"  # Set default widget_id
        self.displays = []
        
        self._init_ui()
        self.load_timezones()  # Load saved timezones
    
    def sizeHint(self):
        """Provide size hint for the widget"""
        return QSize(450, 300)
    
    def minimumSizeHint(self):
        """Provide minimum size hint for the widget"""
        return QSize(400, 200)
    
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        self._update_grid_layout()
    
    def _init_ui(self):
        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create controls layout
        controls = QHBoxLayout()
        
        # Timezone selector
        self.tz_combo = QComboBox()
        self.tz_combo.addItems(sorted(pytz.all_timezones))
        self.tz_combo.setCurrentText("UTC")
        self.tz_combo.setMinimumWidth(200)
        controls.addWidget(self.tz_combo)
        
        # Add timezone button
        add_button = QPushButton("Add Timezone")
        add_button.clicked.connect(self._on_add_clicked)
        add_button.setMinimumWidth(100)
        controls.addWidget(add_button)
        
        layout.addLayout(controls)
        
        # Create grid layout for displays
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        layout.addLayout(self.grid_layout)
        
        # Add stretch at the bottom
        layout.addStretch()
        
        self.setLayout(layout)
    
    def _on_add_clicked(self):
        """Handle add button click"""
        timezone = self.tz_combo.currentText()
        print(f"Adding timezone: {timezone}")  # Debug print
        self.add_timezone(timezone)
    
    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop events to rearrange timezone displays"""
        try:
            source = event.source()
            if not isinstance(source, TimeZoneDisplay):
                return
            
            # Get drop position
            pos = event.pos()
            
            # Find the target position in the grid
            for i in range(self.grid_layout.count()):
                item = self.grid_layout.itemAt(i)
                if item and item.widget():
                    widget_rect = item.widget().geometry()
                    if widget_rect.contains(pos):
                        # Found the target position, swap widgets
                        self._reorder_displays(source, item.widget())
                        break
            
            event.acceptProposedAction()
            
        except Exception as e:
            print(f"Error handling drop event: {e}")
    
    def _reorder_displays(self, source, target):
        """Reorder displays in the grid"""
        try:
            if source == target:
                return
            
            # Get current positions
            source_idx = self.displays.index(source)
            target_idx = self.displays.index(target)
            
            # Swap positions in the list
            self.displays[source_idx], self.displays[target_idx] = self.displays[target_idx], self.displays[source_idx]
            
            # Rearrange grid
            self._update_grid_layout()
            
            # Save the new order
            self.save_state()
            
        except Exception as e:
            print(f"Error reordering displays: {e}")
    
    def _update_grid_layout(self):
        """Update the grid layout with current displays"""
        try:
            # Calculate number of columns based on width
            width = self.width()
            num_columns = max(1, min(4, width // 200))  # Adjust number of columns based on width
            
            # Clear current layout
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            
            # Add displays back in current order
            for i, display in enumerate(self.displays):
                row = i // num_columns
                col = i % num_columns
                self.grid_layout.addWidget(display, row, col)
            
        except Exception as e:
            print(f"Error updating grid layout: {e}")
    
    def add_timezone(self, timezone=None):
        """Add a new timezone display"""
        try:
            if timezone is None:
                timezone = self.tz_combo.currentText()
            
            # Debug print
            print(f"Attempting to add timezone: {timezone}, type: {type(timezone)}")
            
            # Validate timezone
            if not isinstance(timezone, str):
                timezone = str(timezone)
            
            if not timezone or timezone not in pytz.all_timezones:
                print(f"Invalid timezone: {timezone}")
                return
            
            # Check if timezone already exists
            for display in self.displays:
                if display.timezone == timezone:
                    print(f"Timezone {timezone} already exists")
                    return
            
            # Create display
            display = TimeZoneDisplay(timezone, self)
            self.displays.append(display)
            
            # Update grid layout
            self._update_grid_layout()
            
            # Save timezone list
            self.save_state()
            
        except Exception as e:
            print(f"Error adding timezone: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_time(self):
        """Update all timezone displays"""
        for display in self.displays:
            try:
                display.update_time()
            except Exception as e:
                print(f"Error updating time for {display.timezone}: {str(e)}")
    
    def save_state(self):
        """Save current timezones"""
        if not self.widget_id:
            return
            
        state = {
            "timezones": [display.timezone for display in self.displays]
        }
        self.db_manager.set_widget_setting(self.widget_id, "state", str(state))
    
    def restore_state(self, widget_id, state):
        """Restore saved timezones"""
        self.widget_id = widget_id
        try:
            if state and "timezones" in state:
                # Clear existing timezones first
                for display in self.displays[:]:
                    self.remove_timezone(display)
                
                # Add saved timezones
                for timezone in state["timezones"]:
                    self.add_timezone(timezone)
            else:
                # Try loading from widget settings
                saved_state = self.db_manager.get_widget_setting(self.widget_id, "state")
                if saved_state:
                    try:
                        state = eval(saved_state)
                        if state and "timezones" in state:
                            for timezone in state["timezones"]:
                                self.add_timezone(timezone)
                            return
                    except Exception as e:
                        print(f"Error parsing saved state: {str(e)}")
                
                # Add default timezone if no state
                self.add_timezone("UTC")
        except Exception as e:
            print(f"Error restoring clock state: {str(e)}")
            # Add default timezone as fallback
            self.add_timezone("UTC")
    
    def load_timezones(self):
        """Load saved timezones from database"""
        try:
            saved_state = self.db_manager.get_widget_setting(self.widget_id, "state")
            if saved_state:
                try:
                    state = eval(saved_state)
                    self.restore_state(self.widget_id, state)
                except Exception as e:
                    print(f"Error parsing saved state: {str(e)}")
                    self.add_timezone("UTC")
            else:
                # Add default timezone
                self.add_timezone("UTC")
        except Exception as e:
            print(f"Error loading timezones: {str(e)}")
            self.add_timezone("UTC")
    
    def remove_timezone(self, display):
        """Remove a timezone display"""
        try:
            if display in self.displays:
                self.displays.remove(display)
                display.deleteLater()
                self._update_grid_layout()
                self.save_state()
        except Exception as e:
            print(f"Error removing timezone: {str(e)}")
            import traceback
            traceback.print_exc()

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "Clock",
        "title": "Clock",
        "description": "Display time in multiple time zones",
        "widget_class": ClockWidget
    }