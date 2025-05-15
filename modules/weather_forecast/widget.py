from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QScrollArea,
    QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont
import requests
import json
from datetime import datetime
import os

class WeatherDayWidget(QFrame):
    """Widget to display weather for a single day"""
    def __init__(self, weather_data, parent=None):
        super().__init__(parent)
        self.weather_data = weather_data
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Date
        date = datetime.fromtimestamp(self.weather_data['dt'])
        date_label = QLabel(date.strftime("%A\n%b %d"))
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: palette(text);
        """)
        layout.addWidget(date_label)
        
        # Temperature
        temp = self.weather_data['temp']
        temp_layout = QVBoxLayout()
        
        max_temp = QLabel(f"High: {temp['max']}°C")
        max_temp.setAlignment(Qt.AlignCenter)
        max_temp.setStyleSheet("color: palette(text);")
        temp_layout.addWidget(max_temp)
        
        min_temp = QLabel(f"Low: {temp['min']}°C")
        min_temp.setAlignment(Qt.AlignCenter)
        min_temp.setStyleSheet("color: palette(text);")
        temp_layout.addWidget(min_temp)
        
        layout.addLayout(temp_layout)
        
        # Weather description
        weather = self.weather_data['weather'][0]
        desc_label = QLabel(weather['description'].capitalize())
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: palette(text);")
        layout.addWidget(desc_label)
        
        # Additional info
        humidity = QLabel(f"Humidity: {self.weather_data['humidity']}%")
        humidity.setAlignment(Qt.AlignCenter)
        humidity.setStyleSheet("color: palette(text); font-size: 12px;")
        layout.addWidget(humidity)
        
        self.setLayout(layout)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            WeatherDayWidget {
                border: 1px solid palette(mid);
                border-radius: 5px;
                background-color: palette(base);
            }
        """)
        
        # Set size policies
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumWidth(120)

class WeatherForecastWidget(QWidget):
    """Widget to display 10-day weather forecast"""
    def __init__(self, db_manager, ingest_manager):
        super().__init__()
        self.db_manager = db_manager
        self.widget_id = "weather_forecast"
        
        # Load API key from environment or settings
        self.api_key = os.getenv('OPENWEATHER_API_KEY') or self.db_manager.get_widget_setting(
            self.widget_id, "api_key", ""
        )
        
        self._init_ui()
        
        # Set up refresh timer (every 30 minutes)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(30 * 60 * 1000)
        
        # Load saved location
        self.load_location()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Settings section
        settings_layout = QHBoxLayout()
        
        # Location input
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Enter city name")
        settings_layout.addWidget(self.location_input)
        
        # API key input - always visible
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter OpenWeather API key")
        self.api_key_input.setText(self.api_key)
        settings_layout.addWidget(self.api_key_input)
        
        # Update button
        update_btn = QPushButton("Update")
        update_btn.clicked.connect(self.update_weather)
        settings_layout.addWidget(update_btn)
        
        layout.addLayout(settings_layout)
        
        # Create scroll area for forecast
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container for forecast widgets
        self.forecast_container = QWidget()
        self.forecast_layout = QHBoxLayout()
        self.forecast_layout.setSpacing(10)
        self.forecast_container.setLayout(self.forecast_layout)
        
        scroll.setWidget(self.forecast_container)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
        
        # Set size policies
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    
    def sizeHint(self):
        return QSize(800, 300)
    
    def minimumSizeHint(self):
        return QSize(400, 200)
    
    def update_weather(self):
        """Update weather data"""
        try:
            # Get location
            location = self.location_input.text().strip()
            if not location:
                return
            
            # Always check API key input
            new_api_key = self.api_key_input.text().strip()
            if new_api_key:
                self.api_key = new_api_key
                self.db_manager.set_widget_setting(
                    self.widget_id, "api_key", self.api_key
                )
            
            if not self.api_key:
                print("No API key provided")
                return
            
            print(f"Using API key: {self.api_key}")  # Debug log
            
            # First, get coordinates for the location
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct"
            params = {
                "q": location,
                "limit": 1,
                "appid": self.api_key
            }
            
            print(f"Making request to: {geo_url} with params: {params}")  # Debug log
            response = requests.get(geo_url, params=params)
            
            if response.status_code != 200:
                print(f"API Error: Status {response.status_code}")
                print(f"Response content: {response.text}")  # Debug log
                response.raise_for_status()
            
            location_data = response.json()
            if not location_data:
                print(f"Location not found: {location}")
                return
            
            lat = location_data[0]['lat']
            lon = location_data[0]['lon']
            
            # Get weather forecast
            weather_url = "https://api.openweathermap.org/data/2.5/onecall"
            params = {
                "lat": lat,
                "lon": lon,
                "exclude": "current,minutely,hourly,alerts",
                "units": "metric",
                "appid": self.api_key
            }
            
            response = requests.get(weather_url, params=params)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Save location
            self.db_manager.set_widget_setting(
                self.widget_id, "location", location
            )
            
            # Update display
            self._update_forecast_display(weather_data['daily'][:10])
            
        except Exception as e:
            print(f"Error updating weather: {str(e)}")
    
    def _update_forecast_display(self, forecast_data):
        """Update the forecast display"""
        try:
            # Clear existing widgets
            while self.forecast_layout.count():
                item = self.forecast_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add new forecast widgets
            for day_data in forecast_data:
                day_widget = WeatherDayWidget(day_data)
                self.forecast_layout.addWidget(day_widget)
            
            # Add stretch to keep widgets aligned to the left
            self.forecast_layout.addStretch()
            
        except Exception as e:
            print(f"Error updating forecast display: {str(e)}")
    
    def load_location(self):
        """Load saved location"""
        try:
            location = self.db_manager.get_widget_setting(
                self.widget_id, "location", ""
            )
            if location:
                self.location_input.setText(location)
                self.update_weather()
                
        except Exception as e:
            print(f"Error loading location: {str(e)}")
    
    def refresh(self):
        """Refresh the weather data"""
        if self.location_input.text().strip():
            self.update_weather()

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "Weather Forecast",
        "title": "Weather Forecast",
        "description": "Display 10-day weather forecast",
        "widget_class": WeatherForecastWidget
    } 