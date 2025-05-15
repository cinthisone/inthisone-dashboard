from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt, QSettings

class ThemeManager:
    """Manages application-wide theming"""
    
    @staticmethod
    def apply_dark_theme(app):
        """Apply dark theme to the entire application"""
        # Create dark palette
        palette = QPalette()
        
        # Set window/background colors
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        
        # Set text colors
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))
        
        # Set button colors
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        
        # Set highlight colors
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        
        # Set link colors
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.LinkVisited, QColor(100, 100, 250))
        
        # Set disabled colors
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
        
        # Apply palette to application
        app.setPalette(palette)
        
        # Apply additional stylesheet for fine-tuning
        app.setStyleSheet("""
            QToolTip {
                color: #ffffff;
                background-color: #2a82da;
                border: 1px solid white;
            }
            QMenuBar {
                background-color: #353535;
            }
            QMenuBar::item {
                background-color: #353535;
            }
            QMenuBar::item:selected {
                background-color: #2a82da;
            }
            QMenu {
                background-color: #353535;
                border: 1px solid #000000;
            }
            QMenu::item:selected {
                background-color: #2a82da;
            }
            QDockWidget::title {
                background-color: #353535;
                text-align: center;
            }
            QGroupBox {
                border: 1px solid #555555;
                border-radius: 3px;
                margin-top: 0.5em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QScrollBar:vertical {
                border: none;
                background: #353535;
                width: 14px;
                margin: 15px 0 15px 0;
                border-radius: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 15px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::add-line:vertical {
                border: none;
                background: none;
                height: 15px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
    
    @staticmethod
    def apply_light_theme(app):
        """Reset to light theme (system default)"""
        app.setPalette(app.style().standardPalette())
        app.setStyleSheet("")
    
    @staticmethod
    def toggle_theme(app):
        """Toggle between light and dark themes"""
        settings = QSettings("Dashboard", "ModularDesktopDashboard")
        is_dark = settings.value("dark_mode", False, type=bool)
        
        if is_dark:
            ThemeManager.apply_light_theme(app)
            settings.setValue("dark_mode", False)
        else:
            ThemeManager.apply_dark_theme(app)
            settings.setValue("dark_mode", True)
    
    @staticmethod
    def load_saved_theme(app):
        """Load the saved theme preference"""
        settings = QSettings("Dashboard", "ModularDesktopDashboard")
        is_dark = settings.value("dark_mode", False, type=bool)
        
        if is_dark:
            ThemeManager.apply_dark_theme(app) 