from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QMenu, QMenuBar, 
    QToolBar, QStatusBar, QMessageBox, QApplication, QSizePolicy, QWidget, QVBoxLayout,
    QTabWidget, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt, QSize, QSettings, QByteArray, QEvent
from PySide6.QtGui import QAction, QIcon

import os
import importlib
import sys
import json

from app.plugin_manager import PluginManager
from app.theme_manager import ThemeManager

class DashboardTab(QMainWindow):
    """A single dashboard tab that can contain multiple widgets"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        
        # Set proper window flags and attributes
        self.setWindowFlags(Qt.Widget)  # Ensure it behaves as a widget in the tab
        self.setAttribute(Qt.WA_DeleteOnClose)  # Clean up properly when closed
        
        # Enable all dock widget features
        self.setDockOptions(
            QMainWindow.DockOption.AnimatedDocks | 
            QMainWindow.DockOption.AllowNestedDocks | 
            QMainWindow.DockOption.AllowTabbedDocks |
            QMainWindow.DockOption.VerticalTabs  # Enable vertical tab layout for nested docks
        )
        
        # Create a central widget to properly handle dock layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Set size policy to expand properly
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

class MainWindow(QMainWindow):
    def __init__(self, db_manager, ingest_manager):
        super().__init__()
        
        self.db_manager = db_manager
        self.ingest_manager = ingest_manager
        
        # Set window properties
        self.setWindowTitle("Inthisone Dashboard")
        self.setMinimumSize(1280, 720)
        
        # Enable window features
        self.setWindowFlags(
            Qt.Window |  # Regular window
            Qt.WindowMinMaxButtonsHint |  # Enable minimize/maximize buttons
            Qt.WindowSystemMenuHint |  # Enable system menu
            Qt.WindowCloseButtonHint    # Enable close button
        )
        
        # Create central tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        # Enable tab renaming on double click
        self.tab_widget.tabBarDoubleClicked.connect(self._rename_tab)
        
        # Create a central widget to hold the tab widget
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        central_layout.addWidget(self.tab_widget)
        self.setCentralWidget(central_widget)
        
        # Initialize UI components
        self._init_ui()
        
        # Load plugins
        self.plugin_manager = PluginManager(self, self.db_manager, self.ingest_manager)
        self.plugin_manager.load_plugins()
        
        # Restore layout
        self.restore_layout()
        
        # Load saved theme
        ThemeManager.load_saved_theme(QApplication.instance())
        
        # Force an update after initialization
        self.update()
        QApplication.processEvents()

    def showEvent(self, event):
        """Handle window show event"""
        super().showEvent(event)
        # Force a redraw when the window is shown
        self.update()
        for i in range(self.tab_widget.count()):
            dashboard = self.tab_widget.widget(i)
            if dashboard:
                dashboard.update()
                # Update all dock widgets
                for dock in dashboard.findChildren(QDockWidget):
                    dock.update()
                    if dock.widget():
                        dock.widget().update()
        QApplication.processEvents()

    def resizeEvent(self, event):
        """Handle window resize event"""
        super().resizeEvent(event)
        # Update layout after resize
        self.update()
        QApplication.processEvents()

    def changeEvent(self, event):
        """Handle window state changes"""
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            # Force update when window state changes (maximize, minimize, etc.)
            self.update()
            QApplication.processEvents()
    
    def _init_ui(self):
        # Create menu bar
        self._create_menu_bar()
        
        # Create toolbar
        self._create_toolbar()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
    
    def _create_menu_bar(self):
        # Create menu bar
        self.menuBar = QMenuBar()
        self.setMenuBar(self.menuBar)
        
        # File menu
        self.file_menu = QMenu("&File", self)
        self.menuBar.addMenu(self.file_menu)
        
        # Add new dashboard action
        new_dashboard_action = QAction("New Dashboard", self)
        new_dashboard_action.setShortcut("Ctrl+N")
        new_dashboard_action.triggered.connect(self.add_dashboard)
        self.file_menu.addAction(new_dashboard_action)
        
        self.file_menu.addSeparator()
        
        # Add exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)
        
        # View menu
        self.view_menu = QMenu("&View", self)
        self.menuBar.addMenu(self.view_menu)
        
        # Add theme toggle action
        toggle_theme_action = QAction("Toggle Dark Mode", self)
        toggle_theme_action.setShortcut("Ctrl+Shift+D")
        toggle_theme_action.triggered.connect(lambda: ThemeManager.toggle_theme(QApplication.instance()))
        self.view_menu.addAction(toggle_theme_action)
        
        self.view_menu.addSeparator()
        
        # Widgets menu
        self.widgets_menu = QMenu("&Widgets", self)
        self.menuBar.addMenu(self.widgets_menu)
        
        # Help menu
        self.help_menu = QMenu("&Help", self)
        self.menuBar.addMenu(self.help_menu)
        
        # Add about action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        self.help_menu.addAction(about_action)
    
    def _create_toolbar(self):
        """Create the main toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("main_toolbar")  # Set object name for state saving
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # Add refresh action
        refresh_action = QAction("Refresh All", self)
        refresh_action.triggered.connect(self._refresh_current_dashboard)
        toolbar.addAction(refresh_action)
    
    def _refresh_current_dashboard(self):
        """Refresh all widgets in the current dashboard"""
        current_dashboard = self.tab_widget.currentWidget()
        if current_dashboard:
            for dock in current_dashboard.findChildren(QDockWidget):
                if hasattr(dock.widget(), 'refresh'):
                    dock.widget().refresh()
            self.statusBar.showMessage("Current dashboard refreshed", 3000)
    
    def add_dashboard(self):
        """Add a new dashboard tab"""
        # Only prompt for title if we're adding a new dashboard manually
        # (not during restoration)
        if self.isVisible():
            title, ok = QInputDialog.getText(
                self, "New Dashboard", "Enter dashboard name:"
            )
            if not ok or not title.strip():
                title = f"Dashboard {self.tab_widget.count() + 1}"
        else:
            title = f"Dashboard {self.tab_widget.count() + 1}"
        
        dashboard = DashboardTab(title)
        index = self.tab_widget.addTab(dashboard, title)
        self.tab_widget.setCurrentIndex(index)
        return dashboard
    
    def close_tab(self, index):
        """Close a dashboard tab"""
        if self.tab_widget.count() > 1:  # Keep at least one dashboard
            # Save the tab's layout before closing
            dashboard = self.tab_widget.widget(index)
            self.save_dashboard_layout(dashboard)
            self.tab_widget.removeTab(index)
        else:
            QMessageBox.warning(
                self,
                "Cannot Close Dashboard",
                "At least one dashboard must remain open."
            )
    
    def add_widget(self, widget_class, widget_name, widget_title, widget_area=Qt.DockWidgetArea.RightDockWidgetArea):
        """Add a widget to the current dashboard tab"""
        current_dashboard = self.tab_widget.currentWidget()
        if not current_dashboard:
            current_dashboard = self.add_dashboard()
            if not current_dashboard:
                return None
        
        # Create a unique object name for the dock
        base_name = f"dock_{widget_name}"
        counter = 1
        dock_name = base_name
        
        # Find next available unique name
        existing_names = [dock.objectName() for dock in current_dashboard.findChildren(QDockWidget)]
        while dock_name in existing_names:
            dock_name = f"{base_name}_{counter}"
            counter += 1
        
        # Create new dock widget
        display_title = widget_title if counter == 1 else f"{widget_title} {counter}"
        dock = QDockWidget(display_title, current_dashboard)
        dock.setObjectName(dock_name)
        
        # Enable all dock widget features
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar
        )
        
        # Allow docking in all areas
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        
        # Create widget instance
        if widget_name == "tree_list":
            # Special handling for tree list widgets
            # Create a unique widget_id based on the dashboard and counter
            dashboard_index = self.tab_widget.indexOf(current_dashboard)
            widget_id = f"treelist_d{dashboard_index}_{counter}"
            widget = widget_class(self.db_manager, self.ingest_manager, title=display_title)
            widget._widget_id = widget_id  # Set ID directly
            print(f"Created tree list with title: {display_title}, id: {widget_id}")
            
            # Load any existing state
            saved_data = self.db_manager.get_widget_setting(widget_id, "test_state")
            if saved_data:
                try:
                    state = json.loads(saved_data)
                    print(f"Loading saved state for tree list: {state}")
                    widget._load_state(state)
                except Exception as e:
                    print(f"Error loading tree list state: {str(e)}")
        elif widget_name == "custom_list":
            # Special handling for custom list widgets
            widget = widget_class(self.db_manager, self.ingest_manager, list_title=display_title)
            sanitized_title = display_title.lower().replace(' ', '_')
            widget_id = f"custom_list_{sanitized_title}"
            print(f"Created custom list with title: {display_title}, id: {widget_id}")
        elif widget_name == "code_viewer":
            # Special handling for code viewer widgets
            widget = widget_class(self.db_manager, self.ingest_manager, title=display_title)
            sanitized_title = display_title.lower().replace(' ', '_')
            widget_id = f"code_viewer_{sanitized_title}"
            print(f"Created code viewer with title: {display_title}, id: {widget_id}")
        elif widget_name == "wysiwyg_editor":
            # Special handling for wysiwyg editor widgets
            widget = widget_class(self.db_manager, self.ingest_manager, title=display_title)
            sanitized_title = display_title.lower().replace(' ', '_')
            widget_id = f"wysiwyg_editor_{sanitized_title}"
            print(f"Created wysiwyg editor with title: {display_title}, id: {widget_id}")
        else:
            widget = widget_class(self.db_manager, self.ingest_manager)
            widget_id = widget_name
        
        # Set the widget_id
        if hasattr(widget, 'widget_id') and widget_name != "tree_list":  # Skip for tree list since we set it directly
            widget.widget_id = widget_id
            print(f"Set widget ID: {widget_id} for {display_title}")
        
        # Set size policies
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create a wrapper widget to handle resizing
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(widget)
        
        dock.setWidget(wrapper)
        
        # Add dock to current dashboard
        current_dashboard.addDockWidget(widget_area, dock)
        
        # Add toggle action to view menu
        toggle_action = dock.toggleViewAction()
        toggle_action.setText(display_title)
        self.view_menu.addAction(toggle_action)
        
        # Connect close event
        dock.closeEvent = lambda event, d=dock: self._handle_dock_close(event, d)
        
        # Set initial size if the widget specifies preferred dimensions
        if hasattr(widget, 'sizeHint'):
            size_hint = widget.sizeHint()
            if size_hint.isValid():
                dock.resize(size_hint)
        
        # Save initial state if widget supports it
        if hasattr(widget, 'save_state'):
            widget.save_state()
        
        return dock
    
    def _handle_dock_close(self, event, dock):
        """Handle dock widget close events"""
        reply = QMessageBox.question(
            self,
            "Delete Widget",
            "Do you want to delete this widget?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove the toggle action from the View menu
            for action in self.view_menu.actions():
                if action.text() == dock.windowTitle():
                    self.view_menu.removeAction(action)
                    break
            
            # Delete the widget and dock
            dock.deleteLater()
            event.accept()
        else:
            # Just hide the dock if user chooses not to delete
            event.ignore()
            dock.hide()
    
    def save_layout(self):
        """Save the layout of all dashboards"""
        try:
            print("\nSaving layout...")
            settings = QSettings("Dashboard", "ModularDesktopDashboard")
            
            # Save main window geometry
            settings.setValue("geometry", self.saveGeometry())
            
            # Save dashboard information
            dashboards = []
            for i in range(self.tab_widget.count()):
                dashboard = self.tab_widget.widget(i)
                title = self.tab_widget.tabText(i)
                print(f"\nSaving dashboard: {title}")
                
                # Get all widgets in this dashboard
                widgets = dashboard.findChildren(QDockWidget)
                print(f"Found {len(widgets)} widgets in dashboard {title}")
                
                dashboard_info = self.save_dashboard_layout(dashboard)
                dashboard_info["title"] = title
                dashboards.append(dashboard_info)
                
                # Print widget info for debugging
                for widget_info in dashboard_info.get("widgets", []):
                    print(f"Saved widget: {widget_info.get('title')} ({widget_info.get('module_name')})")
            
            # Save to database
            dashboards_json = json.dumps(dashboards)
            print(f"\nSaving {len(dashboards)} dashboards to database")
            self.db_manager.set_widget_setting(
                "main_window", "dashboards", dashboards_json
            )
            
            print("Layout saved successfully")
            
        except Exception as e:
            print(f"Error saving layout: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def save_dashboard_layout(self, dashboard):
        """Save the layout of a single dashboard"""
        try:
            # Save widget instances information
            widget_instances = []
            for dock in dashboard.findChildren(QDockWidget):
                try:
                    wrapper = dock.widget()
                    if wrapper and wrapper.layout().count() > 0:
                        widget = wrapper.layout().itemAt(0).widget()
                        if widget:
                            # Convert DockWidgetArea to int properly
                            dock_area = dashboard.dockWidgetArea(dock)
                            area_value = int(dock_area.value)  # Get the enum value
                            
                            # Get the module name, handling custom list widgets specially
                            module_name = getattr(widget, 'widget_id', '')
                            
                            # For custom list widgets, get the actual title
                            if module_name.startswith('custom_list'):
                                title = getattr(widget, 'list_title', dock.windowTitle())
                            else:
                                title = dock.windowTitle()
                            
                            # Save position and size
                            geometry = dock.geometry()
                            
                            widget_info = {
                                "module_name": module_name,
                                "dock_name": dock.objectName(),
                                "title": title,
                                "area": area_value,
                                "floating": dock.isFloating(),
                                "visible": True,  # Always save as visible
                                "geometry": {
                                    "x": geometry.x(),
                                    "y": geometry.y(),
                                    "width": geometry.width(),
                                    "height": geometry.height()
                                }
                            }
                            widget_instances.append(widget_info)
                except Exception as e:
                    print(f"Error saving dock widget: {str(e)}")
                    continue
            
            # Save state only if there are widgets
            state_hex = ""
            if widget_instances:
                state = dashboard.saveState()
                if state is not None:
                    state_hex = state.data().hex()
                    print(f"Saved dashboard state with {len(widget_instances)} widgets")
            
            return {
                "state": state_hex,
                "widgets": widget_instances
            }
            
        except Exception as e:
            print(f"Error saving dashboard layout: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {"state": "", "widgets": []}
    
    def restore_layout(self):
        """Restore the layout of all dashboards"""
        try:
            print("\nRestoring layout...")
            settings = QSettings("Dashboard", "ModularDesktopDashboard")
            
            # Restore main window geometry
            geometry = settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
            
            # Get saved dashboards from database
            dashboards_json = self.db_manager.get_widget_setting("main_window", "dashboards", "[]")
            try:
                dashboards = json.loads(dashboards_json)
                print(f"\nFound {len(dashboards)} saved dashboards")
            except (json.JSONDecodeError, TypeError):
                print("No valid saved layout found")
                # Create default dashboard
                self.add_dashboard()
                return
            
            if not dashboards:
                print("No dashboards to restore")
                # Create default dashboard
                self.add_dashboard()
                return
            
            # Remove any existing tabs
            while self.tab_widget.count() > 0:
                self.tab_widget.removeTab(0)
            
            # Restore each dashboard
            restored_count = 0
            for dashboard_info in dashboards:
                try:
                    title = dashboard_info.get("title", "Dashboard")
                    print(f"\nRestoring dashboard: {title}")
                    print(f"Found {len(dashboard_info.get('widgets', []))} widgets to restore")
                    
                    # Create new dashboard with saved title
                    dashboard = DashboardTab(title)
                    index = self.tab_widget.addTab(dashboard, title)
                    
                    # Restore the dashboard's layout
                    self.restore_dashboard_layout(dashboard, dashboard_info)
                    
                    # Make the dashboard visible
                    dashboard.show()
                    dashboard.raise_()
                    
                    # Process events to ensure UI updates
                    QApplication.processEvents()
                    
                    restored_count += 1
                    
                except Exception as e:
                    print(f"Error restoring dashboard: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    continue
            
            # If no dashboards were restored, create a default one
            if restored_count == 0:
                print("No dashboards were restored, creating default")
                self.add_dashboard()
            else:
                print(f"Successfully restored {restored_count} dashboards")
                
                # Ensure first tab is selected and visible
                if self.tab_widget.count() > 0:
                    self.tab_widget.setCurrentIndex(0)
                    current_dashboard = self.tab_widget.widget(0)
                    if current_dashboard:
                        current_dashboard.show()
                        current_dashboard.raise_()
                        
                        # Force update of all widgets in the current dashboard
                        for dock in current_dashboard.findChildren(QDockWidget):
                            dock.setVisible(True)
                            if dock.widget():
                                dock.widget().update()
        
        except Exception as e:
            print(f"Error restoring layout: {str(e)}")
            import traceback
            print(traceback.format_exc())
            # If restoration fails, ensure window is in a usable state
            self.resize(1280, 720)
            self.move(100, 100)
            # Create default dashboard
            self.add_dashboard()
    
    def restore_dashboard_layout(self, dashboard, dashboard_info):
        """Restore the layout of a single dashboard"""
        try:
            print(f"\nRestoring layout for dashboard: {dashboard_info.get('title')}")
            
            # Store current dashboard
            current_dashboard = self.tab_widget.currentWidget()
            
            # Set the target dashboard as current
            self.tab_widget.setCurrentWidget(dashboard)
            
            # First create all widgets
            docks = []
            for instance in dashboard_info.get("widgets", []):
                try:
                    module_name = instance.get("module_name", "")
                    print(f"\nRestoring widget: {instance}")
                    
                    if not module_name:
                        print("No module name found, skipping")
                        continue
                    
                    # Get base module name by handling special cases
                    if module_name.startswith("custom_list_"):
                        base_module = "custom_list"
                    elif module_name.startswith("code_viewer_"):
                        base_module = "code_viewer"
                    elif module_name.startswith("treelist_"):
                        base_module = "tree_list"
                    elif module_name.startswith("wysiwyg_editor_"):
                        base_module = "wysiwyg_editor"
                    else:
                        base_module = module_name
                    
                    # Get the widget class from plugin manager
                    plugin_info = self.plugin_manager.plugins.get(base_module)
                    if not plugin_info or "widget_class" not in plugin_info:
                        print(f"No plugin info found for module {module_name} (base: {base_module})")
                        continue
                    
                    widget_class = plugin_info["widget_class"]
                    title = instance.get("title", plugin_info.get("title", "Widget"))
                    
                    print(f"Creating widget with class {widget_class.__name__}")
                    
                    # Special handling for custom list widgets during restoration
                    if base_module == "custom_list":
                        # Create widget instance with the saved title and widget_id
                        widget = widget_class(
                            self.db_manager,
                            self.ingest_manager,
                            list_title=title,
                            widget_id=module_name  # Pass the exact saved widget ID
                        )
                        
                        # Create wrapper and dock
                        wrapper = QWidget()
                        wrapper_layout = QVBoxLayout(wrapper)
                        wrapper_layout.setContentsMargins(0, 0, 0, 0)
                        wrapper_layout.addWidget(widget)
                        
                        dock = QDockWidget(title, dashboard)
                        dock.setObjectName(instance.get("dock_name", "dock_custom_list"))
                        dock.setWidget(wrapper)
                        
                        # Set dock properties
                        dock.setFeatures(
                            QDockWidget.DockWidgetFeature.DockWidgetMovable |
                            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                            QDockWidget.DockWidgetFeature.DockWidgetClosable |
                            QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar
                        )
                        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
                        
                        # Add to dashboard
                        dashboard.addDockWidget(Qt.DockWidgetArea(instance.get("area", Qt.RightDockWidgetArea)), dock)
                        
                        print(f"Restored custom list widget with ID: {module_name}")  # Debug print
                    elif base_module == "tree_list":
                        # Special handling for tree list widgets
                        widget = widget_class(self.db_manager, self.ingest_manager, title=title)
                        widget._widget_id = module_name  # Set ID directly
                        
                        # Create wrapper and dock
                        wrapper = QWidget()
                        wrapper_layout = QVBoxLayout(wrapper)
                        wrapper_layout.setContentsMargins(0, 0, 0, 0)
                        wrapper_layout.addWidget(widget)
                        
                        dock = QDockWidget(title, dashboard)
                        dock.setObjectName(instance.get("dock_name", "dock_tree_list"))
                        dock.setWidget(wrapper)
                        
                        # Set dock properties
                        dock.setFeatures(
                            QDockWidget.DockWidgetFeature.DockWidgetMovable |
                            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                            QDockWidget.DockWidgetFeature.DockWidgetClosable |
                            QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar
                        )
                        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
                        
                        # Add to dashboard
                        dashboard.addDockWidget(Qt.DockWidgetArea(instance.get("area", Qt.RightDockWidgetArea)), dock)
                        
                        # Load saved state
                        saved_data = self.db_manager.get_widget_setting(module_name, "test_state")
                        if saved_data:
                            try:
                                state = json.loads(saved_data)
                                print(f"Loading saved state for tree list: {state}")
                                widget._load_state(state)
                            except Exception as e:
                                print(f"Error loading tree list state: {str(e)}")
                    else:
                        # Create other widgets normally
                        dock = self.add_widget(
                            widget_class,
                            base_module,
                            title,
                            Qt.DockWidgetArea(instance.get("area", Qt.RightDockWidgetArea))
                        )
                    
                    if dock:
                        # Store the dock and its saved state for later restoration
                        docks.append((dock, instance))
                        print(f"Successfully created widget: {title}")
                        
                        # Get the actual widget
                        wrapper = dock.widget()
                        if wrapper and wrapper.layout().count() > 0:
                            widget = wrapper.layout().itemAt(0).widget()
                            if widget and base_module != "tree_list" and base_module != "custom_list":  # Skip for tree list and custom list since we handled them above
                                # For other widgets, set widget_id and restore state normally
                                widget.widget_id = module_name
                                print(f"Set widget ID: {module_name}")
                                
                                # Restore state
                                if hasattr(widget, 'restore_state'):
                                    saved_state = self.db_manager.get_widget_setting(module_name, "state")
                                    if saved_state:
                                        try:
                                            state = eval(saved_state)
                                            print(f"Restoring state for {module_name}: {state}")
                                            widget.restore_state(module_name, state)
                                        except Exception as e:
                                            print(f"Error restoring widget state: {str(e)}")
                                    else:
                                        print(f"No saved state found for {module_name}")
                
                except Exception as e:
                    print(f"Error restoring widget instance: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    continue
            
            print(f"\nRestored {len(docks)} widgets for dashboard {dashboard_info.get('title')}")
            
            # Then restore dashboard state if available
            if docks and "state" in dashboard_info and dashboard_info["state"]:
                try:
                    state_data = bytes.fromhex(dashboard_info["state"])
                    if state_data:
                        # Store current visibility states
                        widget_states = [(dock, dock.isVisible()) for dock, _ in docks]
                        
                        # Restore the dashboard state
                        success = dashboard.restoreState(QByteArray(state_data))
                        print(f"Restored dashboard state: {'Success' if success else 'Failed'}")
                        
                        # Re-apply visibility states
                        for dock, was_visible in widget_states:
                            if was_visible:
                                dock.setVisible(True)
                except Exception as e:
                    print(f"Error restoring dashboard state: {str(e)}")
            
            # Ensure all widgets are visible and properly initialized
            for dock, instance in docks:
                try:
                    # Normalize geometry
                    if "geometry" in instance:
                        geom = instance["geometry"]
                        x = max(0, geom["x"])
                        y = max(0, geom["y"])
                        width = min(max(100, geom["width"]), 2000)
                        height = min(max(100, geom["height"]), 1200)
                        dock.setGeometry(x, y, width, height)
                    
                    # Ensure dock is visible
                    dock.setVisible(True)
                    dock.raise_()
                    
                    # Get the widget and ensure it's visible
                    wrapper = dock.widget()
                    if wrapper:
                        wrapper.show()
                        if wrapper.layout() and wrapper.layout().count() > 0:
                            widget = wrapper.layout().itemAt(0).widget()
                            if widget:
                                widget.show()
                                if hasattr(widget, 'refresh'):
                                    widget.refresh()
                except Exception as e:
                    print(f"Error ensuring widget visibility: {str(e)}")
                    continue
            
            # Process events to ensure UI updates
            QApplication.processEvents()
            
            # Restore the previously current dashboard
            if current_dashboard:
                self.tab_widget.setCurrentWidget(current_dashboard)
            
        except Exception as e:
            print(f"Error restoring dashboard layout: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def _create_special_widget(self, dashboard, base_module, widget_class, instance):
        """Create special widget types (custom list, code viewer, wysiwyg editor)"""
        try:
            title = instance.get("title", "Widget")
            
            if base_module == "custom_list":
                widget = widget_class(self.db_manager, self.ingest_manager, list_title=title)
            elif base_module == "code_viewer":
                code_title = instance.get("module_name", "").replace("code_viewer_", "").replace("_", " ")
                widget = widget_class(self.db_manager, self.ingest_manager, title=code_title)
            elif base_module == "wysiwyg_editor":
                editor_title = instance.get("module_name", "").replace("wysiwyg_editor_", "").replace("_", " ")
                widget = widget_class(self.db_manager, self.ingest_manager, title=editor_title)
            
            wrapper = QWidget()
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.addWidget(widget)
            
            dock = QDockWidget(title, dashboard)
            dock.setObjectName(instance.get("dock_name", f"dock_{base_module}_{len(dashboard.findChildren(QDockWidget))}"))
            dock.setWidget(wrapper)
            
            dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable |
                QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                QDockWidget.DockWidgetFeature.DockWidgetClosable |
                QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar
            )
            dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            dashboard.addDockWidget(Qt.DockWidgetArea(instance.get("area", Qt.RightDockWidgetArea)), dock)
            
            return dock
            
        except Exception as e:
            print(f"Error creating special widget: {str(e)}")
            return None
    
    def _show_about(self):
        QMessageBox.about(
            self, 
            "About Inthisone Dashboard",
            "Inthisone Dashboard\n\n"
            "A customizable dashboard application with dockable widgets.\n"
            "Version 1.0.0"
        )

    def closeEvent(self, event):
        """Handle application close event"""
        try:
            # Save layout before closing
            self.save_layout()
            event.accept()
        except Exception as e:
            print(f"Error in closeEvent: {str(e)}")
            event.accept()

    def _rename_tab(self, index):
        """Handle double-click on tab to rename it"""
        current_name = self.tab_widget.tabText(index)
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Dashboard",
            "Enter new dashboard name:",
            QLineEdit.EchoMode.Normal,
            current_name
        )
        
        if ok and new_name.strip():
            # Update the tab text
            self.tab_widget.setTabText(index, new_name)
            
            # Update the dashboard title
            dashboard = self.tab_widget.widget(index)
            if isinstance(dashboard, DashboardTab):
                dashboard.title = new_name
            
            # Save the layout to persist the name change
            self.save_layout()