from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QMessageBox,
    QInputDialog, QLabel, QSizePolicy
)
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QDesktopServices
import os

class WebViewWidget(QWidget):
    """Widget for displaying web pages"""
    def __init__(self, db_manager, ingest_manager, url=None):
        super().__init__()
        self.db_manager = db_manager
        self.base_widget_id = "web_view"
        
        # Create a unique widget ID
        self.widget_id = self.base_widget_id
        counter = 1
        while self.db_manager.get_widget_setting(self.widget_id, "url"):
            self.widget_id = f"{self.base_widget_id}_{counter}"
            counter += 1
        
        # Initialize UI
        self._init_ui()
        
        # Load saved URL or prompt for new one
        saved_url = self.db_manager.get_widget_setting(self.widget_id, "url")
        if saved_url:
            self.load_url(saved_url)
        elif url:
            self.load_url(url)
        else:
            self.prompt_url()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # URL bar
        url_layout = QHBoxLayout()
        
        # URL input
        self.url_input = QLineEdit()
        self.url_input.returnPressed.connect(self.url_changed)
        url_layout.addWidget(self.url_input)
        
        # Go button
        go_button = QPushButton("Go")
        go_button.clicked.connect(self.url_changed)
        url_layout.addWidget(go_button)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_page)
        url_layout.addWidget(refresh_button)
        
        # Open in Browser button
        browser_button = QPushButton("Open in Browser")
        browser_button.clicked.connect(self.open_in_browser)
        url_layout.addWidget(browser_button)
        
        layout.addLayout(url_layout)
        
        try:
            print("Initializing QWebEngineView...")  # Debug print
            # Web view
            self.web_view = QWebEngineView()
            print("QWebEngineView created successfully")  # Debug print
            
            # Connect signals
            self.web_view.loadFinished.connect(self.handle_load_finished)
            self.web_view.loadStarted.connect(lambda: print("Page load started"))  # Debug print
            self.web_view.loadProgress.connect(lambda p: print(f"Load progress: {p}%"))  # Debug print
            
            # Set size policy
            self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # Set minimum size
            self.web_view.setMinimumSize(400, 300)
            
            layout.addWidget(self.web_view)
            self.has_web_view = True
            print("Web view initialization complete")  # Debug print
        except Exception as e:
            print(f"Error initializing QWebEngineView: {e}")
            # Fallback to status label if web view fails
            self.status_label = QLabel("Web view not available. Use 'Open in Browser' instead.")
            self.status_label.setWordWrap(True)
            layout.addWidget(self.status_label)
            self.has_web_view = False
        
        self.setLayout(layout)
    
    def prompt_url(self):
        """Prompt user for URL"""
        url, ok = QInputDialog.getText(
            self,
            "Enter URL",
            "Please enter the website URL:",
            text="https://"
        )
        if ok and url:
            self.load_url(url)
    
    def url_changed(self):
        """Handle URL input changes"""
        url = self.url_input.text()
        self.load_url(url)
    
    def load_url(self, url):
        """Load a URL into the web view"""
        if url:
            # Add scheme if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            print(f"Loading URL: {url}")  # Debug print
            
            # Update URL bar
            self.url_input.setText(url)
            
            # Save URL
            self.db_manager.set_widget_setting(self.widget_id, "url", url)
            
            if self.has_web_view:
                try:
                    print("Attempting to load URL in web view...")  # Debug print
                    # Load URL in web view
                    qurl = QUrl(url)
                    print(f"Created QUrl: {qurl.toString()}")  # Debug print
                    print(f"QUrl is valid: {qurl.isValid()}")  # Debug print
                    
                    self.web_view.setUrl(qurl)
                    print("URL set in web view")  # Debug print
                except Exception as e:
                    print(f"Error loading URL in web view: {e}")
                    self.open_in_browser()
            else:
                self.open_in_browser()
    
    def open_in_browser(self):
        """Open current URL in system browser"""
        url = self.url_input.text()
        if url:
            try:
                # Try using QDesktopServices first
                success = QDesktopServices.openUrl(QUrl(url))
                
                # If that fails and we're on WSL, try using explorer.exe
                if not success and os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower():
                    import subprocess
                    try:
                        # Use explorer.exe to open the URL
                        subprocess.run(['explorer.exe', url], check=True)
                        success = True
                    except subprocess.CalledProcessError as e:
                        print(f"Error using explorer.exe: {e}")
                        success = False
                
                if not success:
                    QMessageBox.warning(
                        self,
                        "Error Opening Link",
                        f"Could not open the URL: {url}"
                    )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error Opening Link",
                    f"Could not open the URL: {url}\nError: {str(e)}"
                )
    
    def refresh_page(self):
        """Refresh the current page"""
        if self.has_web_view:
            self.web_view.reload()
        else:
            self.open_in_browser()
    
    def handle_load_finished(self, ok):
        """Handle page load completion"""
        print(f"Page load finished - Success: {ok}")  # Debug print
        if not ok:
            print("Page load failed, showing error message")  # Debug print
            QMessageBox.warning(
                self,
                "Load Error",
                "Failed to load the webpage. Please check the URL and try again."
            )
    
    def refresh(self):
        """Refresh the widget (called by dashboard)"""
        self.refresh_page()

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "Web View",
        "title": "Web View",
        "description": "Display websites directly in the dashboard",
        "widget_class": WebViewWidget,
        "supports_multiple": True  # Allow multiple instances
    } 