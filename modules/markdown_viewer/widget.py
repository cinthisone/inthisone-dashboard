from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QFileDialog, QLabel, QScrollArea, QTextBrowser
)
from PySide6.QtCore import Qt, QFileSystemWatcher, QUrl
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication
import markdown2
import os

class MarkdownViewerWidget(QWidget):
    """A widget for viewing and rendering Markdown files"""
    
    def __init__(self, db_manager, ingest_manager):
        super().__init__()
        
        self.db_manager = db_manager
        self.ingest_manager = ingest_manager
        self.widget_id = "markdown_viewer"
        
        # Initialize variables
        self.current_file = None
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.fileChanged.connect(self.refresh)
        
        # Set up the UI
        self._init_ui()
        
        # Restore last opened file
        last_file = self.db_manager.get_widget_setting(self.widget_id, "last_file")
        if last_file and os.path.exists(last_file):
            self.open_file(last_file)
    
    def _init_ui(self):
        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)  # Add some spacing between elements
        
        # Create toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)  # Add spacing between buttons
        
        # Open file button
        self.open_button = QPushButton("Open File")
        self.open_button.clicked.connect(self._open_file_dialog)
        self.open_button.setMinimumWidth(80)  # Set minimum width for buttons
        toolbar.addWidget(self.open_button)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        self.refresh_button.setMinimumWidth(80)
        toolbar.addWidget(self.refresh_button)
        
        # Add spacer
        toolbar.addStretch()
        
        # File path label
        self.file_label = QLabel("No file opened")
        self.file_label.setMinimumWidth(100)
        toolbar.addWidget(self.file_label)
        
        # Add toolbar to layout
        layout.addLayout(toolbar)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create text browser for rendered markdown
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setMinimumSize(200, 100)  # Set minimum size
        
        # Add text browser to scroll area
        scroll_area.setWidget(self.text_browser)
        
        # Add scroll area to layout with stretch
        layout.addWidget(scroll_area, stretch=1)
        
        # Set layout
        self.setLayout(layout)
        
        # Set minimum size for the entire widget
        self.setMinimumSize(300, 200)
    
    def _open_file_dialog(self):
        """Open a file dialog to select a Markdown file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown File",
            "",
            "Markdown Files (*.md *.markdown);;All Files (*)"
        )
        
        if file_path:
            self.open_file(file_path)
    
    def open_file(self, file_path):
        """Open and render a Markdown file"""
        try:
            # Update file watcher
            if self.current_file:
                self.file_watcher.removePath(self.current_file)
            
            self.current_file = file_path
            self.file_watcher.addPath(file_path)
            
            # Update file label
            self.file_label.setText(os.path.basename(file_path))
            
            # Save as last opened file
            self.db_manager.set_widget_setting(self.widget_id, "last_file", file_path)
            
            # Render the file
            self.render_markdown_file(file_path)
            
        except Exception as e:
            self.text_browser.setHtml(f"<h2>Error opening file</h2><p>{str(e)}</p>")
    
    def render_markdown_file(self, file_path):
        """Render a Markdown file to HTML"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_text = f.read()
            
            # Convert Markdown to HTML
            html = markdown2.markdown(
                markdown_text,
                extras=["tables", "fenced-code-blocks", "header-ids"]
            )
            
            # Get current palette to determine if we're in dark mode
            app = QApplication.instance()
            is_dark = app.palette().color(QPalette.Window).lightness() < 128
            
            # Add some basic styling with dynamic colors
            text_color = "#ffffff" if is_dark else "#333333"
            bg_color = "#2b2b2b" if is_dark else "#ffffff"
            code_bg_color = "#353535" if is_dark else "#f6f8fa"
            border_color = "#555555" if is_dark else "#dfe2e5"
            link_color = "#42a5f5" if is_dark else "#0366d6"
            
            styled_html = f"""
            <html>
            <head>
                <style>
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; 
                        line-height: 1.6; 
                        color: {text_color}; 
                        background-color: {bg_color};
                        margin: 0;
                        padding: 20px;
                    }}
                    h1, h2, h3, h4, h5, h6 {{ 
                        margin-top: 1.5em; 
                        margin-bottom: 0.5em; 
                        color: {text_color}; 
                    }}
                    h1 {{ 
                        font-size: 2em; 
                        border-bottom: 1px solid {border_color}; 
                        padding-bottom: 0.3em; 
                    }}
                    h2 {{ 
                        font-size: 1.5em; 
                        border-bottom: 1px solid {border_color}; 
                        padding-bottom: 0.3em; 
                    }}
                    p {{ margin: 1em 0; }}
                    code {{ 
                        background-color: {code_bg_color}; 
                        padding: 0.2em 0.4em; 
                        border-radius: 3px; 
                        font-family: SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace; 
                    }}
                    pre {{ 
                        background-color: {code_bg_color}; 
                        padding: 16px; 
                        overflow: auto; 
                        border-radius: 3px; 
                    }}
                    pre code {{ 
                        background-color: transparent; 
                        padding: 0; 
                    }}
                    blockquote {{ 
                        margin: 1em 0; 
                        padding: 0 1em; 
                        color: {text_color}; 
                        border-left: 0.25em solid {border_color}; 
                    }}
                    table {{ 
                        border-collapse: collapse; 
                        width: 100%; 
                        margin: 1em 0; 
                    }}
                    table th, table td {{ 
                        padding: 6px 13px; 
                        border: 1px solid {border_color}; 
                    }}
                    table tr {{ 
                        background-color: {bg_color}; 
                        border-top: 1px solid {border_color}; 
                    }}
                    table tr:nth-child(2n) {{ 
                        background-color: {code_bg_color}; 
                    }}
                    img {{ max-width: 100%; }}
                    a {{ color: {link_color}; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                {html}
            </body>
            </html>
            """
            
            # Set the HTML content
            self.text_browser.setHtml(styled_html)
            
            # Set base URL for relative links and images
            base_url = QUrl.fromLocalFile(os.path.dirname(file_path) + "/")
            self.text_browser.setSearchPaths([os.path.dirname(file_path)])
            
        except Exception as e:
            self.text_browser.setHtml(f"<h2>Error rendering markdown</h2><p>{str(e)}</p>")
    
    def refresh(self):
        """Refresh the current file"""
        if self.current_file and os.path.exists(self.current_file):
            self.render_markdown_file(self.current_file)

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "Markdown Viewer",
        "title": "Markdown Viewer",
        "description": "View and render Markdown files",
        "widget_class": MarkdownViewerWidget
    }