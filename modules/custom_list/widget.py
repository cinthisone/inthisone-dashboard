from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
    QComboBox, QCheckBox, QMessageBox, QInputDialog,
    QTextEdit, QDialogButtonBox, QApplication, QDateEdit,
    QMenu, QColorDialog
)
from PySide6.QtCore import Qt, QUrl, QDate
from PySide6.QtGui import QDesktopServices, QFont, QColor, QPalette, QPixmap, QIcon
import json
import os
from datetime import datetime

class AddItemDialog(QDialog):
    """Dialog for adding or editing list items"""
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.columns = columns
        self._init_ui()
        
    def _init_ui(self):
        self.setWindowTitle("Add/Edit Item")
        layout = QFormLayout()
        
        # Create input fields for each column
        self.inputs = {}
        for col in self.columns:
            col_id = col['id']
            col_name = col['name']
            col_type = col.get('type', 'text')
            
            print(f"Creating input for column: {col_name} (type: {col_type})")  # Debug print
            
            if col_type == 'link':
                # For link columns, create two fields: text and URL
                text_input = QLineEdit()
                text_input.setPlaceholderText("Link Text (optional)")
                url_input = QLineEdit()
                url_input.setPlaceholderText("URL")
                link_layout = QHBoxLayout()
                link_layout.addWidget(text_input)
                link_layout.addWidget(url_input)
                layout.addRow(f"{col_name}:", link_layout)
                self.inputs[col_id] = {'text': text_input, 'url': url_input}
            elif col_type == 'date':
                # For date columns, create a date picker
                date_input = QDateEdit()
                date_input.setCalendarPopup(True)  # Enable calendar popup
                date_input.setDate(QDate.currentDate())  # Set to current date by default
                layout.addRow(f"{col_name}:", date_input)
                self.inputs[col_id] = date_input
            elif col_type == 'checkbox':
                # For checkbox columns
                check_input = QCheckBox()
                layout.addRow(f"{col_name}:", check_input)
                self.inputs[col_id] = check_input
            else:
                # Text input with optional color picker
                input_layout = QHBoxLayout()
                input_field = QLineEdit()
                input_layout.addWidget(input_field)
                
                if col.get('color_enabled', False):
                    color_btn = QPushButton("Color")
                    color_btn.setFixedWidth(60)
                    color_btn.clicked.connect(lambda checked, f=input_field: self._pick_color(f))
                    input_layout.addWidget(color_btn)
                    self.inputs[col_id] = {'field': input_field, 'color': None}
                else:
                    self.inputs[col_id] = input_field
                
                layout.addRow(f"{col_name}:", input_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        self.setLayout(layout)
    
    def _pick_color(self, input_field):
        """Open color picker and store the selected color"""
        color = QColorDialog.getColor()
        if color.isValid():
            # Store the color in the input dictionary
            for col_id, input_dict in self.inputs.items():
                if isinstance(input_dict, dict) and input_dict.get('field') == input_field:
                    input_dict['color'] = color.name()
                    # Set background color of input field as preview
                    input_field.setStyleSheet(f"background-color: {color.name()};")
                    break
    
    def get_values(self):
        """Get the values from all input fields"""
        values = {}
        for col_id, input_field in self.inputs.items():
            if isinstance(input_field, dict):
                if 'url' in input_field:  # Link column
                    url = input_field['url'].text().strip()
                    text = input_field['text'].text().strip()
                    if url:
                        values[col_id] = {
                            'text': text,
                            'url': url
                        }
                    else:
                        values[col_id] = ''
                elif 'field' in input_field:  # Text with color
                    text = input_field['field'].text().strip()
                    color = input_field['color']
                    if text or color:
                        values[col_id] = {
                            'text': text,
                            'color': color
                        }
                    else:
                        values[col_id] = ''
            elif isinstance(input_field, QDateEdit):  # Date column
                date = input_field.date()
                values[col_id] = date.toString("yyyy-MM-dd")
            elif isinstance(input_field, QCheckBox):  # Checkbox column
                values[col_id] = input_field.isChecked()
            else:
                values[col_id] = input_field.text().strip()
        return values
    
    def set_values(self, values):
        """Set values in input fields"""
        for col_id, value in values.items():
            if col_id in self.inputs:
                input_field = self.inputs[col_id]
                if isinstance(input_field, dict):
                    if 'url' in input_field:  # Link column
                        if isinstance(value, dict):
                            input_field['text'].setText(value.get('text', ''))
                            input_field['url'].setText(value.get('url', ''))
                        else:
                            input_field['text'].setText('')
                            input_field['url'].setText('')
                    elif 'field' in input_field:  # Text with color
                        if isinstance(value, dict):
                            input_field['field'].setText(value.get('text', ''))
                            color = value.get('color') or value.get('background_color')
                            if color:
                                input_field['color'] = color
                                input_field['field'].setStyleSheet(f"background-color: {color};")
                        else:
                            input_field['field'].setText(str(value))
                            input_field['color'] = None
                            input_field['field'].setStyleSheet("")
                elif isinstance(input_field, QDateEdit):  # Date column
                    try:
                        if value:
                            date = QDate.fromString(value, "yyyy-MM-dd")
                            if date.isValid():
                                input_field.setDate(date)
                            else:
                                input_field.setDate(QDate.currentDate())
                        else:
                            input_field.setDate(QDate.currentDate())
                    except Exception as e:
                        print(f"Error setting date value: {e}")
                        input_field.setDate(QDate.currentDate())
                elif isinstance(input_field, QCheckBox):  # Checkbox column
                    input_field.setChecked(bool(value))
                else:
                    # Handle text fields that might contain a dictionary value
                    if isinstance(value, dict):
                        input_field.setText(value.get('text', ''))
                    else:
                        input_field.setText(str(value))

class AddColumnDialog(QDialog):
    """Dialog for adding a new column"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        self.setWindowTitle("Add Column")
        layout = QFormLayout()
        
        # Column name
        self.name_input = QLineEdit()
        layout.addRow("Column Name:", self.name_input)
        
        # Column type
        self.type_input = QComboBox()
        self.type_input.addItems(['text', 'link', 'date', 'checkbox'])
        layout.addRow("Column Type:", self.type_input)
        
        # Sortable option
        self.sortable_input = QCheckBox("Sortable")
        self.sortable_input.setChecked(True)
        layout.addRow("", self.sortable_input)
        
        # Color option
        self.color_enabled = QCheckBox("Enable Color")
        self.color_enabled.setChecked(False)
        layout.addRow("", self.color_enabled)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow("", button_layout)
        
        self.setLayout(layout)
    
    def get_values(self):
        """Get the column configuration"""
        return {
            'name': self.name_input.text().strip(),
            'type': self.type_input.currentText(),
            'sortable': self.sortable_input.isChecked(),
            'color_enabled': self.color_enabled.isChecked()
        }

class ImportDialog(QDialog):
    """Dialog for importing multiple items from text"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle("Import Items")
        layout = QVBoxLayout()
        
        # Add instructions label
        instructions = QLabel(
            "Paste your text below. Each line will become a new item.\n"
            "Empty lines will be skipped."
        )
        layout.addWidget(instructions)
        
        # Add text edit
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Paste your text here...")
        self.text_edit.setMinimumWidth(400)
        self.text_edit.setMinimumHeight(200)
        layout.addWidget(self.text_edit)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_lines(self):
        """Get non-empty lines from the text edit"""
        text = self.text_edit.toPlainText()
        return [line.strip() for line in text.split('\n') if line.strip()]

class CustomListWidget(QWidget):
    """Widget for displaying customizable lists with sorting and links"""
    
    # Add predefined colors as class constants
    PREDEFINED_COLORS = {
        'Green': '#2ecc71',
        'Blue': '#3498db',
        'Red': '#e74c3c',
        'Yellow': '#f1c40f',
        'White': '#ffffff',
        'Orange': '#e67e22',
        'Pink': '#e84393'
    }
    
    def __init__(self, db_manager, ingest_manager, list_title=None, widget_id=None):
        super().__init__()
        self.db_manager = db_manager
        self.base_widget_id = "custom_list"
        
        # Store the widget_id if provided (for restoration)
        self._widget_id = widget_id
        
        # Handle title initialization
        if list_title is None:
            # For new instances, always prompt for title
            title, ok = QInputDialog.getText(
                self, "List Title", "Enter a title for this list:"
            )
            if not ok or not title.strip():
                title = f"List {len(self.parent().findChildren(CustomListWidget)) + 1}"
            self.list_title = title
        else:
            self.list_title = list_title
        
        # Create a unique widget ID based on the title only if not provided
        if not self._widget_id:
            self._widget_id = f"{self.base_widget_id}_{self.list_title.lower().replace(' ', '_')}"
        
        print(f"Initializing custom list widget with ID: {self._widget_id}")  # Debug print
        
        # Initialize with default column
        self.default_column = {
            'id': 'title',
            'name': 'Title',
            'type': 'text',
            'sortable': True
        }
        self.columns = [self.default_column]
        
        # Start with empty items list
        self.items = []
        
        # Initialize UI
        self._init_ui()
        
        # Load saved state
        self.load_columns()
        self.load_items()
        
        # Ensure we always have at least the default column
        if not self.columns:
            self.columns = [self.default_column]
            self.save_columns()
        
        self.refresh_table()
        
        # Save initial state
        self.save_columns()
        self.save_items()

    @property
    def widget_id(self):
        return self._widget_id

    @widget_id.setter
    def widget_id(self, value):
        """Set widget_id and load state"""
        if value:
            print(f"Setting widget ID to: {value}")  # Debug print
            self._widget_id = value
            # Load state with new ID
            self.load_columns()
            self.load_items()
            self.refresh_table()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel(self.list_title)
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
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Add item button
        add_btn = QPushButton("Add Item")
        add_btn.clicked.connect(self.add_item)
        toolbar.addWidget(add_btn)
        
        # Delete item button
        delete_btn = QPushButton("Delete Item")
        delete_btn.clicked.connect(self.delete_item)
        delete_btn.setToolTip("Delete selected item (or use Delete key)")
        toolbar.addWidget(delete_btn)
        
        # Import items button
        import_btn = QPushButton("Import Items")
        import_btn.clicked.connect(self.import_items)
        toolbar.addWidget(import_btn)
        
        # Add clear checkmarks button (initially hidden)
        self.clear_checks_btn = QPushButton("Clear Checkmarks")
        self.clear_checks_btn.clicked.connect(self.clear_all_checkmarks)
        self.clear_checks_btn.setVisible(False)  # Initially hidden
        toolbar.addWidget(self.clear_checks_btn)
        
        # Add column button
        add_col_btn = QPushButton("Add Column")
        add_col_btn.clicked.connect(self.add_column)
        toolbar.addWidget(add_col_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSortingEnabled(True)
        
        # Handle both double-click for editing and single-click for links
        self.table.cellDoubleClicked.connect(self.handle_double_click)
        self.table.cellClicked.connect(self.handle_cell_click)
        
        # Enable drag and drop
        self.table.setDragEnabled(True)
        self.table.setAcceptDrops(True)
        self.table.setDragDropMode(QTableWidget.InternalMove)
        self.table.dropEvent = self.handleDropEvent
        
        # Context menu for table
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Handle keyboard shortcuts
        self.table.keyPressEvent = self.handle_key_press
        
        # Set up header behavior
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        
        # Add context menu to header
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.show_header_context_menu)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
    
    def handle_double_click(self, row, column):
        """Handle double-click events"""
        self.edit_item()

    def handle_cell_click(self, row, column):
        """Handle single-click events"""
        print(f"Cell clicked - Row: {row}, Column: {column}")  # Debug print
        item = self.table.item(row, column)
        print(f"Item: {item}")  # Debug print
        
        # Make sure we have valid column index
        if column < len(self.columns):
            col = self.columns[column]
            print(f"Column type: {col.get('type')}")  # Debug print
            
            # Only handle clicks for link columns
            if col['type'] == 'link' and item:
                url = item.data(Qt.UserRole)
                print(f"URL data: {url}")  # Debug print
                if url:
                    print(f"Attempting to open URL: {url}")  # Debug print
                    try:
                        # Create a proper QUrl object
                        qurl = QUrl(url)
                        if not qurl.scheme():  # If no scheme (http://, https://, etc.)
                            qurl = QUrl("http://" + url)  # Add http:// by default
                        
                        # Try using QDesktopServices first
                        success = QDesktopServices.openUrl(qurl)
                        
                        # If that fails and we're on WSL, try using explorer.exe
                        if not success and os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower():
                            import subprocess
                            try:
                                # Use explorer.exe to open the URL
                                subprocess.run(['explorer.exe', qurl.toString()], check=True)
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
                        print(f"Error opening URL: {e}")
                        QMessageBox.warning(
                            self,
                            "Error Opening Link",
                            f"Could not open the URL: {url}\nError: {str(e)}"
                        )

    def handleDropEvent(self, event):
        """Handle drop events for row reordering"""
        if not self.table.rowCount():
            return
            
        # Get the source and destination rows
        source_row = self.table.currentRow()
        dest_row = self.table.rowAt(event.pos().y())
        
        if dest_row < 0:
            dest_row = self.table.rowCount() - 1
        
        # Move the item in our data
        if 0 <= source_row < len(self.items) and 0 <= dest_row < len(self.items):
            item = self.items.pop(source_row)
            self.items.insert(dest_row, item)
            self.save_items()
            self.refresh_table()
            self.table.selectRow(dest_row)
    
    def edit_title(self):
        """Edit the list title"""
        new_title, ok = QInputDialog.getText(
            self, "Edit Title", "Enter new title:",
            text=self.list_title
        )
        if ok and new_title.strip():
            old_widget_id = self.widget_id
            self.list_title = new_title
            
            # Update widget ID
            self.widget_id = f"{self.base_widget_id}_{self.list_title.lower().replace(' ', '_')}"
            
            # Save the current title
            self.db_manager.set_widget_setting(
                self.base_widget_id, "current_title", self.list_title
            )
            
            # Move settings to new widget ID if it changed
            if old_widget_id != self.widget_id:
                # Get existing data
                columns = self.columns
                items = self.items
                
                # Save under new ID
                self.save_columns()
                self.save_items()
                
                # Clear old settings
                self.db_manager.set_widget_setting(old_widget_id, "columns", "[]")
                self.db_manager.set_widget_setting(old_widget_id, "items", "[]")
            
            # Update UI
            self.refresh_table()
            
            # Update title label
            title_label = self.layout().itemAt(0).layout().itemAt(0).widget()
            title_label.setText(self.list_title)
    
    def refresh_table(self):
        """Refresh the table display"""
        print(f"Refreshing table for {self.widget_id} with {len(self.items)} items")
        self.table.clear()
        
        # Set up columns
        self.table.setColumnCount(len(self.columns))
        headers = []
        has_checkbox_columns = False
        for col in self.columns:
            headers.append(col['name'])
            if col.get('type') == 'checkbox':
                has_checkbox_columns = True
        self.table.setHorizontalHeaderLabels(headers)
        
        # Show/hide clear checkmarks button based on whether we have checkbox columns
        self.clear_checks_btn.setVisible(has_checkbox_columns)
        
        # Add items
        self.table.setRowCount(len(self.items))
        for row, item in enumerate(self.items):
            for col_idx, col in enumerate(self.columns):
                col_id = col['id']
                value = item.get(col_id, '')
                
                if col['type'] == 'link' and isinstance(value, dict):
                    # Handle link columns
                    link_text = value.get('text', '')
                    url = value.get('url', '')
                    display_text = link_text if link_text else url
                    
                    table_item = QTableWidgetItem(display_text)
                    if url:
                        table_item.setData(Qt.UserRole, url)
                        app = QApplication.instance()
                        is_dark = app.palette().color(QPalette.Window).lightness() < 128
                        link_color = QColor("#42a5f5") if is_dark else QColor("#0366d6")
                        table_item.setForeground(link_color)
                        table_item.setToolTip(f"Click to open: {url}")
                        font = QFont()
                        font.setUnderline(True)
                        table_item.setFont(font)
                elif col['type'] == 'date':
                    # Handle date columns
                    table_item = QTableWidgetItem()
                    if value:
                        try:
                            date = QDate.fromString(value, "yyyy-MM-dd")
                            if date.isValid():
                                table_item.setData(Qt.UserRole, value)
                                display_date = date.toString("MMM d, yyyy")
                                table_item.setText(display_date)
                            else:
                                table_item.setText(value)
                        except Exception as e:
                            print(f"Error processing date: {e}")
                            table_item.setText(value)
                    else:
                        table_item.setText("")
                elif col['type'] == 'checkbox':
                    # Handle checkbox columns
                    table_item = QTableWidgetItem()
                    table_item.setTextAlignment(Qt.AlignCenter)
                    if value:
                        table_item.setText("✓")
                        table_item.setForeground(QColor("#2ecc71"))
                        font = QFont()
                        font.setBold(True)
                        table_item.setFont(font)
                    else:
                        table_item.setText("")
                else:
                    # Handle text columns with colors
                    if isinstance(value, dict):
                        text = value.get('text', '')
                        table_item = QTableWidgetItem(text)
                        
                        # Apply background color if set
                        if value.get('background_color'):
                            table_item.setBackground(QColor(value['background_color']))
                        elif value.get('color'):  # Support old color format
                            table_item.setBackground(QColor(value['color']))
                        
                        # Apply text color if set
                        if value.get('text_color'):
                            table_item.setForeground(QColor(value['text_color']))
                    else:
                        table_item = QTableWidgetItem(str(value))
                        
                        # If this is a color column, set the background color
                        if col.get('color_enabled', False) and value:
                            try:
                                table_item.setBackground(QColor(value))
                            except:
                                pass
                
                # Set flags based on column configuration
                if col.get('sortable', True):
                    table_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                else:
                    table_item.setFlags(table_item.flags() & ~Qt.ItemIsEnabled)
                
                self.table.setItem(row, col_idx, table_item)
        
        # Adjust column widths
        self.table.resizeColumnsToContents()
        
        # Re-enable drag and drop
        self.table.setDragEnabled(True)
        self.table.setAcceptDrops(True)
        self.table.setDragDropMode(QTableWidget.InternalMove)
    
    def add_item(self):
        """Add a new item"""
        print(f"Adding item with columns: {self.columns}")  # Debug print
        dialog = AddItemDialog(self.columns, self)
        if dialog.exec():
            item = dialog.get_values()
            print(f"New item values: {item}")  # Debug print
            self.items.append(item)
            self.save_items()
            self.refresh_table()
    
    def edit_item(self):
        """Edit the selected item"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            dialog = AddItemDialog(self.columns, self)
            dialog.set_values(self.items[current_row])
            if dialog.exec():
                self.items[current_row] = dialog.get_values()
                self.save_items()
                self.refresh_table()
    
    def delete_item(self):
        """Delete the selected item"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self, "Delete Item",
                "Are you sure you want to delete this item?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.items.pop(current_row)
                self.save_items()
                self.refresh_table()
                self.statusBar().showMessage("Item deleted", 3000)  # Show confirmation message
    
    def add_column(self):
        """Add a new column"""
        dialog = AddColumnDialog(self)
        if dialog.exec():
            col_config = dialog.get_values()
            col_config['id'] = col_config['name'].lower().replace(' ', '_')
            self.columns.append(col_config)
            self.save_columns()
            self.refresh_table()
    
    def save_items(self):
        """Save items to database"""
        try:
            json_data = json.dumps(self.items)
            self.db_manager.set_widget_setting(self.widget_id, "items", json_data)
            print(f"Saved {len(self.items)} items for {self.widget_id}")
        except Exception as e:
            print(f"Error saving items for {self.widget_id}: {str(e)}")
    
    def save_columns(self):
        """Save column configuration to database"""
        self.db_manager.set_widget_setting(
            self.widget_id, "columns", json.dumps(self.columns)
        )
    
    def show_context_menu(self, position):
        """Show context menu for table items"""
        menu = QMenu(self)
        
        # Get the item at the position
        item = self.table.itemAt(position)
        if item:
            row = item.row()
            col = item.column()
            
            # Add edit and delete actions
            edit_action = menu.addAction("Edit")
            edit_action.triggered.connect(self.edit_item)
            
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(self.delete_item)
            
            # Check if we're on a link cell
            if item.data(Qt.UserRole):  # Has URL data
                menu.addSeparator()
                open_link_action = menu.addAction("Open Link")
                open_link_action.triggered.connect(
                    lambda: QDesktopServices.openUrl(QUrl(item.data(Qt.UserRole)))
                )
            
            # Add color menus for the title column (first column)
            if col == 0:  # Title column
                menu.addSeparator()
                
                # Background Color submenu
                bg_color_menu = QMenu("Background Color", menu)
                menu.addMenu(bg_color_menu)
                
                # Add "None" option for background color
                none_bg_action = bg_color_menu.addAction("None")
                none_bg_action.triggered.connect(lambda: self._set_item_color(row, None, is_background=True))
                bg_color_menu.addSeparator()
                
                # Add predefined background colors
                for color_name, color_code in self.PREDEFINED_COLORS.items():
                    action = bg_color_menu.addAction(color_name)
                    # Create a color icon
                    pixmap = QPixmap(16, 16)
                    pixmap.fill(QColor(color_code))
                    action.setIcon(QIcon(pixmap))
                    action.triggered.connect(
                        lambda checked, c=color_code: self._set_item_color(row, c, is_background=True)
                    )
                
                # Text Color submenu
                text_color_menu = QMenu("Text Color", menu)
                menu.addMenu(text_color_menu)
                
                # Add "None" option for text color
                none_text_action = text_color_menu.addAction("None")
                none_text_action.triggered.connect(lambda: self._set_item_color(row, None, is_background=False))
                text_color_menu.addSeparator()
                
                # Add predefined text colors
                for color_name, color_code in self.PREDEFINED_COLORS.items():
                    action = text_color_menu.addAction(color_name)
                    # Create a color icon
                    pixmap = QPixmap(16, 16)
                    pixmap.fill(QColor(color_code))
                    action.setIcon(QIcon(pixmap))
                    action.triggered.connect(
                        lambda checked, c=color_code: self._set_item_color(row, c, is_background=False)
                    )
        
        menu.exec_(self.table.viewport().mapToGlobal(position))
    
    def _set_item_color(self, row, color, is_background=True):
        """Set the background or text color for an item in the title column"""
        if 0 <= row < len(self.items):
            item = self.items[row]
            title_col_id = self.columns[0]['id']  # Get the ID of the title column
            
            # Convert the current value to dict format if it's not already
            if not isinstance(item.get(title_col_id), dict):
                current_text = item.get(title_col_id, '')
                item[title_col_id] = {'text': current_text}
            
            # Update the color
            if is_background:
                item[title_col_id]['background_color'] = color
            else:
                item[title_col_id]['text_color'] = color
            
            # Save the changes
            self.save_items()
            self.refresh_table()
    
    def show_header_context_menu(self, position):
        """Show context menu for table header"""
        header = self.table.horizontalHeader()
        column = header.logicalIndexAt(position)
        
        if column >= 0 and column < len(self.columns):
            menu = QMenu(self)
            
            # Don't allow deleting the first column
            if column > 0:
                delete_action = menu.addAction("Delete Column")
                delete_action.triggered.connect(lambda: self.delete_column(column))
            
            # Show the menu at the right position
            menu.exec_(header.viewport().mapToGlobal(position))
    
    def delete_column(self, column_index):
        """Delete a column and its data"""
        if column_index <= 0:  # Don't allow deleting the first column
            return
            
        column_name = self.columns[column_index]['name']
        reply = QMessageBox.question(
            self,
            "Delete Column",
            f"Are you sure you want to delete the column '{column_name}'?\nThis will delete all data in this column.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove the column configuration
            deleted_column = self.columns.pop(column_index)
            column_id = deleted_column['id']
            
            # Remove the column's data from all items
            for item in self.items:
                if column_id in item:
                    del item[column_id]
            
            # Save changes
            self.save_columns()
            self.save_items()
            
            # Refresh the display
            self.refresh_table()

    def load_columns(self):
        """Load saved columns from database"""
        try:
            saved_columns = self.db_manager.get_widget_setting(self.widget_id, "columns")
            if saved_columns:
                loaded_columns = json.loads(saved_columns)
                if loaded_columns:  # Only update if we got some columns
                    self.columns = loaded_columns
                    print(f"Loaded {len(self.columns)} columns for {self.widget_id}")
                else:
                    print(f"No columns found for {self.widget_id}, using default")
                    self.columns = [self.default_column]
            else:
                print(f"No saved columns for {self.widget_id}, using default")
                self.columns = [self.default_column]
        except Exception as e:
            print(f"Error loading columns for {self.widget_id}: {str(e)}")
            print("Using default column configuration")
            self.columns = [self.default_column]

    def load_items(self):
        """Load saved items from database"""
        try:
            saved_items = self.db_manager.get_widget_setting(self.widget_id, "items")
            if saved_items:
                self.items = json.loads(saved_items)
                print(f"Loaded {len(self.items)} items for {self.widget_id}")
        except Exception as e:
            print(f"Error loading items for {self.widget_id}: {str(e)}")
            self.items = []

    def import_items(self):
        """Import multiple items from text"""
        if not self.columns:
            print("No columns defined, using default column")
            self.columns = [self.default_column]
            self.save_columns()
        
        dialog = ImportDialog(self)
        if dialog.exec():
            lines = dialog.get_lines()
            if not lines:
                QMessageBox.warning(
                    self,
                    "Import Items",
                    "No valid lines found to import."
                )
                return
            
            print(f"Importing {len(lines)} lines")  # Debug print
            print(f"Current columns: {self.columns}")  # Debug print
            
            # For each line, create an item with the line as the title
            for line in lines:
                # Initialize all columns as empty
                item = {}
                for col in self.columns:
                    col_id = col['id']
                    if col.get('type') == 'link':
                        item[col_id] = {'text': '', 'url': ''}
                    else:
                        item[col_id] = ''
                
                # Set the first column (title) to the line text
                first_col = self.columns[0]['id']
                if self.columns[0].get('type') == 'link':
                    item[first_col] = {'text': line, 'url': line}
                else:
                    item[first_col] = line
                
                print(f"Created item: {item}")  # Debug print
                self.items.append(item)
            
            print(f"Total items after import: {len(self.items)}")  # Debug print
            
            # Save and refresh
            self.save_items()
            self.refresh_table()
            
            QMessageBox.information(
                self,
                "Import Complete",
                f"Successfully imported {len(lines)} items."
            )

    def handle_key_press(self, event):
        """Handle keyboard events"""
        if event.key() == Qt.Key_Delete:
            self.delete_item()
        else:
            # Call the parent class's keyPressEvent for other keys
            QTableWidget.keyPressEvent(self.table, event)

    def clear_all_checkmarks(self):
        """Clear all checkmarks in checkbox columns"""
        # Find all checkbox columns
        checkbox_columns = [(i, col['id']) for i, col in enumerate(self.columns) if col.get('type') == 'checkbox']
        
        if not checkbox_columns:
            return
        
        # Clear all checkmarks
        for row in range(len(self.items)):
            for _, col_id in checkbox_columns:
                self.items[row][col_id] = False
        
        # Save and refresh
        self.save_items()
        self.refresh_table()

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "Custom List",
        "title": "Custom List",
        "description": "Create customizable lists with sorting and links",
        "widget_class": CustomListWidget,
        "supports_multiple": True  # Allow multiple instances with different titles
    } 