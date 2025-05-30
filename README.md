# Inthisone Dashboard

A cross-platform desktop dashboard application with dockable widgets, built with Python and PySide6 (Qt 6). Designed to provide real-time visualization and monitoring capabilities for quantitative trading systems and market analysis.

## Motivation

This dashboard is being developed to serve as a powerful visualization and monitoring tool for quantitative trading systems. It aims to:
- Display real-time market data and trading signals
- Visualize technical indicators and trading patterns
- Monitor portfolio performance and risk metrics
- Provide customizable layouts for different trading strategies
- Enable quick decision-making through intuitive data presentation

## Features

- **Dockable Widgets**: Drag, resize, and tab widgets to create your perfect layout
- **Persistent Layouts**: Your dashboard configuration is saved and restored between sessions
- **Plugin System**: Easily extend with new widgets
- **Background Data Ingestion**: Process data from PDFs, websites, and APIs
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Sample Widgets

- **Clock**: Displays the current time and date, updates every second
- **Markdown Viewer**: Opens and renders Markdown files, refreshes on save
- **REST API Table**: Fetches and displays JSON data from any REST API

## Future Roadmap

### Phase 1: Market Data Integration
- Real-time stock market data feeds
- Technical indicator visualization widgets
- Price chart widgets with multiple timeframes
- Volume and order flow analysis displays

### Phase 2: Trading System Integration
- Trading signal visualization
- Position and order management interface
- Risk metrics dashboard
- Performance analytics widgets

### Phase 3: Advanced Features
- Backtesting results visualization
- Strategy optimization metrics
- Portfolio allocation views
- Risk management controls
- Alert system for trading signals

## Requirements

- Python 3.8 or higher
- PySide6 (Qt 6)
- Additional dependencies listed in `requirements.txt`

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python main.py
   ```

## Building Standalone Executables

Use the included PyInstaller script to build standalone executables:

```
python pyinstaller_build.py
```

This will create platform-specific packages:
- Windows: `.exe` file
- macOS: `.dmg` package
- Linux: AppImage

## Creating Custom Widgets

1. Create a new directory in the `modules` folder with your widget name
2. Create a `widget.py` file in that directory
3. Implement your widget class and a `register_plugin()` function
4. Restart the application to see your widget in the Widgets menu

Example widget structure:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class MyCustomWidget(QWidget):
    def __init__(self, db_manager, ingest_manager):
        super().__init__()
        self.db_manager = db_manager
        self.ingest_manager = ingest_manager
        self.widget_id = "my_custom_widget"
        
        # Set up UI
        layout = QVBoxLayout()
        layout.addWidget(QLabel("My Custom Widget"))
        self.setLayout(layout)
    
    def refresh(self):
        # Implement refresh logic here
        pass

def register_plugin():
    return {
        "name": "My Custom Widget",
        "title": "My Custom Widget",
        "description": "Description of my custom widget",
        "widget_class": MyCustomWidget
    }
```

## C++ Integration

The dashboard supports C++ extensions through PySide6's Shiboken binding generator. See the documentation for details on creating high-performance C++ plugins.

## License

MIT License