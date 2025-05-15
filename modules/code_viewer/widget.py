from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QComboBox, QInputDialog,
    QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor,
    QFont, QPalette
)
import json
import re

class CodeHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for code"""
    def __init__(self, parent=None, language='python'):
        super().__init__(parent)
        self.language = language
        self._init_formats()
        self._init_rules()
    
    def _init_formats(self):
        """Initialize text formats for different syntax elements"""
        # Keywords
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#FF79C6"))  # Pink
        self.keyword_format.setFontWeight(QFont.Bold)
        
        # Strings
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#F1FA8C"))  # Yellow
        
        # Comments
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6272A4"))  # Blue-grey
        self.comment_format.setFontItalic(True)
        
        # Numbers
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#BD93F9"))  # Purple
        
        # Functions
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#50FA7B"))  # Green
        
        # Class names
        self.class_format = QTextCharFormat()
        self.class_format.setForeground(QColor("#8BE9FD"))  # Cyan
        self.class_format.setFontWeight(QFont.Bold)
    
    def _init_rules(self):
        """Initialize syntax highlighting rules based on language"""
        self.rules = []
        
        if self.language == 'python':
            keywords = [
                'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
                'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
                'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None',
                'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True',
                'try', 'while', 'with', 'yield'
            ]
            
            # Add keyword rules
            self.rules.extend(
                (re.compile(r'\b' + kw + r'\b'), self.keyword_format)
                for kw in keywords
            )
            
            # Add other Python-specific rules
            self.rules.extend([
                # Strings (single and double quotes)
                (re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format),
                (re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), self.string_format),
                # Comments
                (re.compile(r'#[^\n]*'), self.comment_format),
                # Numbers
                (re.compile(r'\b[0-9]+\b'), self.number_format),
                # Functions
                (re.compile(r'\bdef\s+(\w+)'), self.function_format),
                # Classes
                (re.compile(r'\bclass\s+(\w+)'), self.class_format),
            ])
        
        elif self.language == 'javascript':
            keywords = [
                'break', 'case', 'catch', 'class', 'const', 'continue',
                'debugger', 'default', 'delete', 'do', 'else', 'export',
                'extends', 'finally', 'for', 'function', 'if', 'import',
                'in', 'instanceof', 'new', 'return', 'super', 'switch',
                'this', 'throw', 'try', 'typeof', 'var', 'void', 'while',
                'with', 'yield', 'let', 'static', 'enum', 'await', 'true',
                'false', 'null', 'undefined'
            ]
            
            # Add keyword rules
            self.rules.extend(
                (re.compile(r'\b' + kw + r'\b'), self.keyword_format)
                for kw in keywords
            )
            
            # Add other JavaScript-specific rules
            self.rules.extend([
                # Strings (single and double quotes)
                (re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format),
                (re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), self.string_format),
                # Template literals
                (re.compile(r'`[^`\\]*(\\.[^`\\]*)*`'), self.string_format),
                # Comments (single and multi-line)
                (re.compile(r'//[^\n]*'), self.comment_format),
                (re.compile(r'/\*.*?\*/', re.DOTALL), self.comment_format),
                # Numbers
                (re.compile(r'\b[0-9]+\b'), self.number_format),
                # Functions
                (re.compile(r'\bfunction\s+(\w+)'), self.function_format),
                # Classes
                (re.compile(r'\bclass\s+(\w+)'), self.class_format),
            ])
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text"""
        for pattern, format in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class CodeViewerWidget(QWidget):
    """Widget for displaying and editing code with syntax highlighting"""
    def __init__(self, db_manager, ingest_manager, title=None):
        super().__init__()
        self.db_manager = db_manager
        self.base_widget_id = "code_viewer"
        
        # Handle title initialization
        if title is None:
            title, ok = QInputDialog.getText(
                self, "Code Block Title", "Enter a title for this code block:"
            )
            if not ok or not title.strip():
                title = f"Code Block {len(self.parent().findChildren(CodeViewerWidget)) + 1}"
        self.code_title = title
        
        # Create a unique widget ID based on the title
        self.widget_id = f"{self.base_widget_id}_{self.code_title.lower().replace(' ', '_')}"
        
        # Initialize UI
        self._init_ui()
        
        # Load saved content and settings
        self.load_content()
        
        # If this is a restored widget (has a title), load its content
        if title:
            # Load saved content
            content = self.db_manager.get_widget_setting(self.widget_id, "content", "")
            if content:
                self.code_editor.setPlainText(content)
            
            # Load saved language
            language = self.db_manager.get_widget_setting(self.widget_id, "language", "python")
            index = self.language_combo.findText(language)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
                self.change_language(language)
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Title bar
        title_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel(self.code_title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: palette(text);
        """)
        title_layout.addWidget(title_label)
        
        # Edit title button
        edit_title_btn = QPushButton("Edit Title")
        edit_title_btn.clicked.connect(self.edit_title)
        title_layout.addWidget(edit_title_btn)
        
        # Language selector
        self.language_combo = QComboBox()
        self.language_combo.addItems(['python', 'javascript'])
        self.language_combo.currentTextChanged.connect(self.change_language)
        title_layout.addWidget(self.language_combo)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Code editor
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setLineWrapMode(QTextEdit.NoWrap)
        self.code_editor.textChanged.connect(self.save_content)
        
        # Set a monospace font
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        self.code_editor.setFont(font)
        
        # Create and set the syntax highlighter
        self.highlighter = CodeHighlighter(self.code_editor.document(), 'python')
        
        # Set dark theme colors for the editor
        palette = self.code_editor.palette()
        palette.setColor(QPalette.Base, QColor("#282A36"))  # Dracula theme background
        palette.setColor(QPalette.Text, QColor("#F8F8F2"))  # Dracula theme foreground
        self.code_editor.setPalette(palette)
        
        layout.addWidget(self.code_editor)
        
        self.setLayout(layout)
    
    def edit_title(self):
        """Edit the code block title"""
        new_title, ok = QInputDialog.getText(
            self, "Edit Title", "Enter new title:",
            text=self.code_title
        )
        if ok and new_title.strip():
            old_widget_id = self.widget_id
            self.code_title = new_title
            
            # Update widget ID
            self.widget_id = f"{self.base_widget_id}_{self.code_title.lower().replace(' ', '_')}"
            
            # Move settings to new widget ID if it changed
            if old_widget_id != self.widget_id:
                content = self.db_manager.get_widget_setting(old_widget_id, "content")
                language = self.db_manager.get_widget_setting(old_widget_id, "language")
                
                if content:
                    self.db_manager.set_widget_setting(self.widget_id, "content", content)
                if language:
                    self.db_manager.set_widget_setting(self.widget_id, "language", language)
                
                # Clear old settings
                self.db_manager.set_widget_setting(old_widget_id, "content", "")
                self.db_manager.set_widget_setting(old_widget_id, "language", "")
            
            # Update title label
            title_label = self.layout().itemAt(0).layout().itemAt(0).widget()
            title_label.setText(self.code_title)
    
    def change_language(self, language):
        """Change the syntax highlighting language"""
        self.highlighter = CodeHighlighter(self.code_editor.document(), language)
        self.db_manager.set_widget_setting(self.widget_id, "language", language)
    
    def save_content(self):
        """Save the current content"""
        content = self.code_editor.toPlainText()
        self.db_manager.set_widget_setting(self.widget_id, "content", content)
    
    def load_content(self):
        """Load saved content and settings"""
        # Load language
        language = self.db_manager.get_widget_setting(self.widget_id, "language", "python")
        index = self.language_combo.findText(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        # Load content
        content = self.db_manager.get_widget_setting(self.widget_id, "content", "")
        if content:
            self.code_editor.setPlainText(content)
    
    def refresh(self):
        """Refresh the widget (called by dashboard)"""
        self.load_content()

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "Code Viewer",
        "title": "Code Viewer",
        "description": "Display and edit code with syntax highlighting",
        "widget_class": CodeViewerWidget,
        "supports_multiple": True  # Allow multiple instances with different titles
    } 