from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QTextEdit, QInputDialog, QPushButton, QFontComboBox,
    QSpinBox, QColorDialog, QMenu, QDialog, QLabel,
    QLineEdit, QDialogButtonBox, QComboBox, QGridLayout,
    QStyle, QDockWidget
)
from PySide6.QtGui import (
    QTextCharFormat, QFont, QColor, QTextCursor,
    QAction, QIcon, QTextListFormat, QTextTableFormat,
    QTextLength, QTextBlockFormat, QPainter, QPixmap
)
from PySide6.QtCore import Qt, QSize, QRect

class LinkDialog(QDialog):
    """Dialog for inserting/editing links"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Link")
        layout = QGridLayout(self)
        
        # URL
        layout.addWidget(QLabel("URL:"), 0, 0)
        self.url_edit = QLineEdit()
        layout.addWidget(self.url_edit, 0, 1)
        
        # Text
        layout.addWidget(QLabel("Text:"), 1, 0)
        self.text_edit = QLineEdit()
        layout.addWidget(self.text_edit, 1, 1)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, 2, 0, 1, 2)

class TableDialog(QDialog):
    """Dialog for inserting tables"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Table")
        layout = QGridLayout(self)
        
        # Rows
        layout.addWidget(QLabel("Rows:"), 0, 0)
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 50)
        self.rows_spin.setValue(3)
        layout.addWidget(self.rows_spin, 0, 1)
        
        # Columns
        layout.addWidget(QLabel("Columns:"), 1, 0)
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 50)
        self.cols_spin.setValue(3)
        layout.addWidget(self.cols_spin, 1, 1)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, 2, 0, 1, 2)

class WysiwygEditorWidget(QWidget):
    """Widget for rich text editing with formatting options"""
    def __init__(self, db_manager, ingest_manager, title=None):
        super().__init__()
        self.db_manager = db_manager
        self.base_widget_id = "wysiwyg_editor"
        
        # Handle title initialization
        if title is None:
            title, ok = QInputDialog.getText(
                self, "Editor Title", "Enter a title for this editor:"
            )
            if not ok or not title.strip():
                title = f"Editor {len(self.parent().findChildren(WysiwygEditorWidget)) + 1}"
        self.editor_title = title
        
        # Create a unique widget ID based on the title
        self.widget_id = f"{self.base_widget_id}_{self.editor_title.lower().replace(' ', '_')}"
        
        # Initialize UI
        self._init_ui()
        
        # Load saved content
        self.load_content()
    
    def _create_custom_icon(self, text, color=Qt.black, size=16):
        """Create a custom icon with text"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setFont(QFont("Arial", size * 0.7))
        painter.setPen(color)
        
        # Draw text centered in the pixmap
        rect = QRect(0, 0, size, size)
        painter.drawText(rect, Qt.AlignCenter, text)
        painter.end()
        
        return QIcon(pixmap)

    def _create_action(self, icon_name, tooltip, slot, checkable=False):
        """Helper to create QAction with icon"""
        # Custom icon mappings
        custom_icons = {
            "format-text-bold": "B",
            "format-text-italic": "I",
            "format-text-underline": "U",
            "format-text-strikethrough": "S",
            "format-text-superscript": "^",
            "format-text-subscript": "_",
            "format-text-color": "A",
            "format-fill-color": "⬚",
            "format-justify-left": "⇤",
            "format-justify-center": "⇔",
            "format-justify-right": "⇥",
            "format-justify-fill": "≡",
            "format-list-unordered": "•",
            "format-list-ordered": "1.",
            "format-list-ordered-alpha": "a.",
            "format-list-ordered-roman": "i.",
            "format-indent-less": "←",
            "format-indent-more": "→",
            "insert-link": "⛓",
            "insert-table": "⊞",
            "insert-horizontal-rule": "—"
        }
        
        # Create custom icon
        if icon_name in custom_icons:
            icon = self._create_custom_icon(custom_icons[icon_name])
            action = QAction(icon, "", self)
        else:
            action = QAction(custom_icons.get(icon_name, "?"), self)
            action.setFont(QFont("Arial", 10))
        
        # Set object name for style actions
        if icon_name == "format-text-bold":
            action.setObjectName("action_bold")
        elif icon_name == "format-text-italic":
            action.setObjectName("action_italic")
        elif icon_name == "format-text-underline":
            action.setObjectName("action_underline")
        elif icon_name == "format-text-strikethrough":
            action.setObjectName("action_strikethrough")
        
        action.setToolTip(tooltip)
        if checkable:
            action.setCheckable(True)
        action.triggered.connect(slot)
        return action
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Title bar
        title_layout = QHBoxLayout()
        
        # Title label
        self.title_label = QLabel(self.editor_title)
        self.title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: palette(text);
        """)
        title_layout.addWidget(self.title_label)
        
        # Edit title button
        edit_title_btn = QPushButton("Edit Title")
        edit_title_btn.clicked.connect(self.edit_title)
        title_layout.addWidget(edit_title_btn)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Create format toolbar
        format_toolbar = QToolBar()
        format_toolbar.setIconSize(QSize(16, 16))
        
        # Heading combo box
        self.heading_combo = QComboBox()
        self.heading_combo.addItem("Paragraph")
        for i in range(1, 7):
            self.heading_combo.addItem(f"Heading {i}")
        self.heading_combo.setToolTip("Paragraph Format")
        self.heading_combo.currentIndexChanged.connect(self.heading_changed)
        format_toolbar.addWidget(self.heading_combo)
        
        format_toolbar.addSeparator()
        
        # Font family
        self.font_combo = QFontComboBox()
        self.font_combo.setToolTip("Font Family")
        self.font_combo.currentFontChanged.connect(self.font_family_changed)
        format_toolbar.addWidget(self.font_combo)
        
        # Font size
        self.size_spin = QSpinBox()
        self.size_spin.setToolTip("Font Size")
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(12)
        self.size_spin.valueChanged.connect(self.font_size_changed)
        format_toolbar.addWidget(self.size_spin)
        
        format_toolbar.addSeparator()
        
        # Text style actions
        style_actions = [
            ("format-text-bold", "Bold", self.bold_toggled, True),
            ("format-text-italic", "Italic", self.italic_toggled, True),
            ("format-text-underline", "Underline", self.underline_toggled, True),
            ("format-text-strikethrough", "Strikethrough", self.strikethrough_toggled, True),
            ("format-text-superscript", "Superscript", self.superscript_toggled, True),
            ("format-text-subscript", "Subscript", self.subscript_toggled, True)
        ]
        
        for icon_name, tooltip, slot, checkable in style_actions:
            action = self._create_action(icon_name, tooltip, slot, checkable)
            format_toolbar.addAction(action)
        
        format_toolbar.addSeparator()
        
        # Color actions
        color_actions = [
            ("format-text-color", "Text Color", self.text_color_clicked),
            ("format-fill-color", "Background Color", self.background_color_clicked)
        ]
        
        for icon_name, tooltip, slot in color_actions:
            action = self._create_action(icon_name, tooltip, slot)
            format_toolbar.addAction(action)
        
        layout.addWidget(format_toolbar)
        
        # Create paragraph toolbar
        para_toolbar = QToolBar()
        para_toolbar.setIconSize(QSize(16, 16))
        
        # Alignment actions
        alignment_actions = [
            ("format-justify-left", "Align Left", Qt.AlignLeft),
            ("format-justify-center", "Align Center", Qt.AlignCenter),
            ("format-justify-right", "Align Right", Qt.AlignRight),
            ("format-justify-fill", "Justify", Qt.AlignJustify)
        ]
        
        for icon_name, tooltip, alignment in alignment_actions:
            action = self._create_action(icon_name, tooltip, 
                lambda a, align=alignment: self.alignment_changed(align))
            para_toolbar.addAction(action)
        
        para_toolbar.addSeparator()
        
        # List actions
        list_actions = [
            ("format-list-unordered", "Bullet List", QTextListFormat.ListDisc),
            ("format-list-ordered", "Numbered List", QTextListFormat.ListDecimal),
            ("format-list-ordered-alpha", "Alphabet List", QTextListFormat.ListLowerAlpha),
            ("format-list-ordered-roman", "Roman List", QTextListFormat.ListLowerRoman)
        ]
        
        for icon_name, tooltip, style in list_actions:
            action = self._create_action(icon_name, tooltip,
                lambda a, s=style: self.list_format_changed(s))
            para_toolbar.addAction(action)
        
        para_toolbar.addSeparator()
        
        # Indentation actions
        indent_actions = [
            ("format-indent-less", "Decrease Indent", self.decrease_indent),
            ("format-indent-more", "Increase Indent", self.increase_indent)
        ]
        
        for icon_name, tooltip, slot in indent_actions:
            action = self._create_action(icon_name, tooltip, slot)
            para_toolbar.addAction(action)
        
        layout.addWidget(para_toolbar)
        
        # Create insert toolbar
        insert_toolbar = QToolBar()
        insert_toolbar.setIconSize(QSize(16, 16))
        
        # Insert actions
        insert_actions = [
            ("insert-link", "Insert Link", self.insert_link),
            ("insert-table", "Insert Table", self.insert_table),
            ("insert-horizontal-rule", "Insert Horizontal Rule", self.insert_horizontal_rule)
        ]
        
        for icon_name, tooltip, slot in insert_actions:
            action = self._create_action(icon_name, tooltip, slot)
            insert_toolbar.addAction(action)
        
        layout.addWidget(insert_toolbar)
        
        # Create text editor
        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.save_content)
        self.editor.cursorPositionChanged.connect(self.update_format)
        layout.addWidget(self.editor)
        
        self.setLayout(layout)
    
    def font_family_changed(self, font):
        """Change font family of selected text"""
        self.editor.setFontFamily(font.family())
    
    def font_size_changed(self, size):
        """Change font size of selected text"""
        self.editor.setFontPointSize(size)
    
    def bold_toggled(self, checked):
        """Toggle bold for selected text"""
        self.editor.setFontWeight(QFont.Bold if checked else QFont.Normal)
    
    def italic_toggled(self, checked):
        """Toggle italic for selected text"""
        self.editor.setFontItalic(checked)
    
    def underline_toggled(self, checked):
        """Toggle underline for selected text"""
        self.editor.setFontUnderline(checked)
    
    def strikethrough_toggled(self, checked):
        """Toggle strikethrough for selected text"""
        format = QTextCharFormat()
        format.setFontStrikeOut(checked)
        self.merge_format(format)
    
    def superscript_toggled(self, checked):
        """Toggle superscript for selected text"""
        format = QTextCharFormat()
        format.setVerticalAlignment(
            QTextCharFormat.VerticalAlignment.AlignSuperScript if checked
            else QTextCharFormat.VerticalAlignment.AlignNormal
        )
        self.merge_format(format)
    
    def subscript_toggled(self, checked):
        """Toggle subscript for selected text"""
        format = QTextCharFormat()
        format.setVerticalAlignment(
            QTextCharFormat.VerticalAlignment.AlignSubScript if checked
            else QTextCharFormat.VerticalAlignment.AlignNormal
        )
        self.merge_format(format)
    
    def text_color_clicked(self):
        """Change text color"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.editor.setTextColor(color)
    
    def background_color_clicked(self):
        """Change text background color"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.editor.setTextBackgroundColor(color)
    
    def alignment_changed(self, alignment):
        """Change text alignment"""
        self.editor.setAlignment(alignment)
    
    def list_format_changed(self, style):
        """Change list format"""
        cursor = self.editor.textCursor()
        if cursor.currentList():
            # If already in a list, remove it
            cursor.beginEditBlock()
            list_format = cursor.currentList().format()
            if list_format.style() == style:
                cursor.createList(QTextListFormat())
            else:
                list_format.setStyle(style)
                cursor.createList(list_format)
            cursor.endEditBlock()
        else:
            # Create new list
            list_format = QTextListFormat()
            list_format.setStyle(style)
            cursor.createList(list_format)
    
    def increase_indent(self):
        """Increase text indentation"""
        cursor = self.editor.textCursor()
        block_format = cursor.blockFormat()
        block_format.setIndent(block_format.indent() + 1)
        cursor.setBlockFormat(block_format)
    
    def decrease_indent(self):
        """Decrease text indentation"""
        cursor = self.editor.textCursor()
        block_format = cursor.blockFormat()
        if block_format.indent() > 0:
            block_format.setIndent(block_format.indent() - 1)
            cursor.setBlockFormat(block_format)
    
    def insert_link(self):
        """Insert a hyperlink"""
        dialog = LinkDialog(self)
        cursor = self.editor.textCursor()
        dialog.text_edit.setText(cursor.selectedText())
        
        if dialog.exec_():
            url = dialog.url_edit.text()
            text = dialog.text_edit.text() or url
            
            format = QTextCharFormat()
            format.setAnchorHref(url)
            format.setAnchor(True)
            format.setForeground(QColor("blue"))
            format.setFontUnderline(True)
            
            if cursor.hasSelection():
                cursor.insertText(text, format)
            else:
                cursor.insertText(text, format)
    
    def insert_table(self):
        """Insert a table"""
        dialog = TableDialog(self)
        if dialog.exec_():
            rows = dialog.rows_spin.value()
            cols = dialog.cols_spin.value()
            
            format = QTextTableFormat()
            format.setCellPadding(5)
            format.setCellSpacing(0)
            format.setBorder(1)
            
            cursor = self.editor.textCursor()
            cursor.insertTable(rows, cols, format)
    
    def insert_horizontal_rule(self):
        """Insert a horizontal rule"""
        cursor = self.editor.textCursor()
        cursor.insertHtml("<hr>")
    
    def merge_format(self, format):
        """Apply text format to selection"""
        cursor = self.editor.textCursor()
        cursor.mergeCharFormat(format)
        self.editor.mergeCurrentCharFormat(format)
    
    def save_content(self):
        """Save the current content"""
        content = self.editor.toHtml()
        print(f"Saving content for {self.widget_id}")
        self.db_manager.set_widget_setting(self.widget_id, "content", content)
    
    def load_content(self):
        """Load saved content"""
        content = self.db_manager.get_widget_setting(self.widget_id, "content", "")
        print(f"Loading content for {self.widget_id}: {'Found content' if content else 'No content found'}")
        if content:
            self.editor.setHtml(content)
    
    def heading_changed(self, index):
        """Change the heading level of the current paragraph"""
        cursor = self.editor.textCursor()
        format = cursor.blockFormat()
        
        if index == 0:  # Paragraph
            format.setHeadingLevel(0)
            self.editor.setFontPointSize(12)  # Reset to default size
        else:
            format.setHeadingLevel(index)
            # Set font size based on heading level
            sizes = {1: 24, 2: 20, 3: 18, 4: 16, 5: 14, 6: 12}
            self.editor.setFontPointSize(sizes[index])
        
        cursor.setBlockFormat(format)
        self.editor.setTextCursor(cursor)
    
    def update_format(self):
        """Update format controls based on current cursor position"""
        cursor = self.editor.textCursor()
        
        # Update heading combo
        format = cursor.blockFormat()
        heading_level = format.headingLevel()
        self.heading_combo.setCurrentIndex(heading_level)
        
        # Update font size spin
        font = cursor.charFormat().font()
        self.size_spin.setValue(int(font.pointSize()))
        
        # Update font family combo
        self.font_combo.setCurrentFont(font)
        
        # Update style buttons based on current format
        char_format = cursor.charFormat()
        # Bold
        if self.findChild(QAction, "action_bold"):
            self.findChild(QAction, "action_bold").setChecked(font.bold())
        # Italic
        if self.findChild(QAction, "action_italic"):
            self.findChild(QAction, "action_italic").setChecked(font.italic())
        # Underline
        if self.findChild(QAction, "action_underline"):
            self.findChild(QAction, "action_underline").setChecked(font.underline())
    
    def refresh(self):
        """Refresh the widget (called by dashboard)"""
        self.load_content()
        # Reset heading combo to paragraph
        self.heading_combo.setCurrentIndex(0)

    def edit_title(self):
        """Edit the editor title"""
        new_title, ok = QInputDialog.getText(
            self, "Edit Title", "Enter new title:",
            text=self.editor_title
        )
        if ok and new_title.strip():
            old_widget_id = self.widget_id
            self.editor_title = new_title
            
            # Update widget ID
            self.widget_id = f"{self.base_widget_id}_{self.editor_title.lower().replace(' ', '_')}"
            
            # Move settings to new widget ID if it changed
            if old_widget_id != self.widget_id:
                content = self.db_manager.get_widget_setting(old_widget_id, "content")
                if content:
                    self.db_manager.set_widget_setting(self.widget_id, "content", content)
                    # Clear old settings
                    self.db_manager.set_widget_setting(old_widget_id, "content", "")
            
            # Update title label
            self.title_label.setText(self.editor_title)
            
            # Update parent dock widget title if it exists
            if self.parent() and self.parent().parent():
                dock = self.parent().parent()
                if isinstance(dock, QDockWidget):
                    dock.setWindowTitle(self.editor_title)

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "WYSIWYG Editor",
        "title": "WYSIWYG Editor",
        "description": "Rich text editor with formatting options",
        "widget_class": WysiwygEditorWidget,
        "supports_multiple": True  # Allow multiple instances with different titles
    } 