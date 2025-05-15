from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QWidget, QInputDialog, QMenu, QLabel, QLineEdit,
    QTreeWidgetItemIterator
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QAction, QFont
import json

class TreeListWidget(QWidget):
    """A tree-structured list widget with drag and drop support"""
    
    def __init__(self, db_manager, ingest_manager, title=None):
        super().__init__()
        self.db_manager = db_manager
        self.ingest_manager = ingest_manager
        self._widget_id = None
        self.title = title or "Tree List"
        
        # Create a unique widget ID based on title
        base_id = "treelist"
        if title and title != "Tree List":
            self._widget_id = f"{base_id}_{title.lower().replace(' ', '_')}"
        else:
            # Find next available ID
            counter = 1
            test_id = base_id
            while self.db_manager.get_widget_setting(test_id, "test_state"):
                test_id = f"{base_id}_{counter}"
                counter += 1
            self._widget_id = test_id
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Items")
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        # Connect to itemChanged signal to save when items are edited
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree)
        
        # Add item buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Item")
        add_btn.clicked.connect(self._add_item)
        button_layout.addWidget(add_btn)
        
        add_child_btn = QPushButton("Add Child")
        add_child_btn.clicked.connect(self._add_child)
        button_layout.addWidget(add_child_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def hideEvent(self, event):
        """Called when widget is hidden (including app close)"""
        self.save_state()
        super().hideEvent(event)

    def _on_item_changed(self, item, column):
        """Called when an item is edited"""
        self.save_state()

    @property
    def widget_id(self):
        return self._widget_id

    @widget_id.setter
    def widget_id(self, value):
        """Set widget_id and load state if available"""
        if value:
            print(f"\nWidget ID set to: {value}, attempting to load saved state...")
            saved_data = self.db_manager.get_widget_setting(value, "test_state")
            if saved_data:
                try:
                    state = json.loads(saved_data)
                    print(f"Found saved state: {state}")
                    self._load_state(state)
                except Exception as e:
                    print(f"Error loading saved state: {str(e)}")
            else:
                print("No saved state found")
    
    def save_state(self):
        """Save the current state to database"""
        if not self.widget_id:
            print("No widget_id set")
            return
            
        # Create simple test data
        items = []
        
        # Save top-level items
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item:
                item_data = {
                    "id": len(items),
                    "text": item.text(0),
                    "parent": None
                }
                items.append(item_data)
                
                # Save children
                self._save_item_children(item, items, item_data["id"])
        
        test_data = {
            "items": items
        }
        
        # Save to database
        print(f"\nSaving tree state:")
        print(f"Data to save: {test_data}")
        
        try:
            json_data = json.dumps(test_data)
            success = self.db_manager.set_widget_setting(self.widget_id, "test_state", json_data)
            print(f"Save successful: {success}")
            
            # Verify save
            saved = self.db_manager.get_widget_setting(self.widget_id, "test_state")
            print(f"Verification - saved data: {saved}")
            if saved:
                try:
                    verified = json.loads(saved)
                    print(f"Verified {len(verified['items'])} items saved")
                except Exception as e:
                    print(f"Error verifying save: {str(e)}")
        except Exception as e:
            print(f"Save error: {str(e)}")
    
    def _save_item_children(self, parent_item, items, parent_id):
        """Save children of an item"""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child:
                item_data = {
                    "id": len(items),
                    "text": child.text(0),
                    "parent": parent_id
                }
                items.append(item_data)
                
                # Recurse for this child's children
                self._save_item_children(child, items, item_data["id"])

    def _load_state(self, state):
        """Load state into the tree widget"""
        if not isinstance(state, dict) or "items" not in state:
            print("Invalid state format")
            return
            
        # Clear tree
        self.tree.clear()
        
        if "items" in state:
            # Create all items first
            items_dict = {}
            for item_data in state["items"]:
                item = QTreeWidgetItem()
                item.setText(0, item_data["text"])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                items_dict[item_data["id"]] = item
            
            # Build hierarchy
            for item_data in state["items"]:
                item = items_dict[item_data["id"]]
                if item_data["parent"] is None:
                    self.tree.addTopLevelItem(item)
                else:
                    parent = items_dict.get(item_data["parent"])
                    if parent:
                        parent.addChild(item)
            
            print(f"Restored {len(items_dict)} items")
        else:
            print("No items in state")
    
    def _add_item(self):
        """Add a top-level item"""
        text, ok = QInputDialog.getText(self, "Add Item", "Enter item text:")
        if ok and text:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.save_state()  # Save after adding
    
    def _add_child(self):
        """Add a child to the selected item"""
        current = self.tree.currentItem()
        if current:
            text, ok = QInputDialog.getText(self, "Add Child", "Enter child text:")
            if ok and text:
                child = QTreeWidgetItem(current)
                child.setText(0, text)
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsEditable)
                current.setExpanded(True)
                self.save_state()  # Save after adding

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "Tree List",
        "title": "Tree List",
        "description": "A hierarchical list with drag and drop support",
        "widget_class": TreeListWidget,
        "module_name": "tree_list",
        "supports_multiple": True,  # Allow multiple instances with different titles
        "default_title": "Tree List"  # Default title for new instances
    } 