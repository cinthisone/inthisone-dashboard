import os
import sys
import importlib
import importlib.util
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt

class PluginManager:
    """Manages loading and registering of widget plugins"""
    
    def __init__(self, main_window, db_manager, ingest_manager):
        self.main_window = main_window
        self.db_manager = db_manager
        self.ingest_manager = ingest_manager
        self.plugins = {}
        
        # Create widgets menu
        self.widgets_menu = self.main_window.widgets_menu
    
    def load_plugins(self):
        """Load all available plugins from the modules directory"""
        # Get the modules directory path
        modules_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules")
        
        # Ensure the modules directory exists
        if not os.path.exists(modules_dir):
            os.makedirs(modules_dir)
            return
        
        # Add modules directory to Python path if not already there
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)
        
        # Scan for module directories
        for item in os.listdir(modules_dir):
            module_path = os.path.join(modules_dir, item)
            
            # Check if it's a directory and has a widget.py file
            if os.path.isdir(module_path) and os.path.exists(os.path.join(module_path, "widget.py")):
                self._load_plugin(item)
        
        # Also load built-in plugins
        self._load_builtin_plugins()
    
    def _load_plugin(self, module_name):
        """Load a specific plugin by module name"""
        try:
            # Import the module
            module = importlib.import_module(f"{module_name}.widget")
            
            # Check if the module has a register_plugin function
            if hasattr(module, "register_plugin"):
                # Register the plugin
                plugin_info = module.register_plugin()
                
                # Store plugin info
                self.plugins[module_name] = plugin_info
                
                # Add to widgets menu
                self._add_widget_to_menu(module_name, plugin_info)
                
                print(f"Loaded plugin: {plugin_info.get('name', module_name)}")
            else:
                print(f"Module {module_name} does not have a register_plugin function")
        
        except Exception as e:
            print(f"Error loading plugin {module_name}: {e}")
    
    def _load_builtin_plugins(self):
        """Load built-in plugins"""
        # Clear existing menu items to prevent duplicates
        self.widgets_menu.clear()
        
        # Clock widget
        from modules.clock.widget import register_plugin
        plugin_info = register_plugin()
        self.plugins["clock"] = plugin_info
        self._add_widget_to_menu("clock", plugin_info)
        
        # Markdown viewer widget
        from modules.markdown_viewer.widget import register_plugin
        plugin_info = register_plugin()
        self.plugins["markdown_viewer"] = plugin_info
        self._add_widget_to_menu("markdown_viewer", plugin_info)
        
        # REST API table widget
        from modules.rest_api_table.widget import register_plugin
        plugin_info = register_plugin()
        self.plugins["rest_api_table"] = plugin_info
        self._add_widget_to_menu("rest_api_table", plugin_info)
        
        # Custom list widget
        from modules.custom_list.widget import register_plugin
        plugin_info = register_plugin()
        self.plugins["custom_list"] = plugin_info
        self._add_widget_to_menu("custom_list", plugin_info)
        
        # Web view widget
        from modules.web_view.widget import register_plugin
        plugin_info = register_plugin()
        self.plugins["web_view"] = plugin_info
        self._add_widget_to_menu("web_view", plugin_info)
        
        # Weather forecast widget
        from modules.weather_forecast.widget import register_plugin
        plugin_info = register_plugin()
        self.plugins["weather_forecast"] = plugin_info
        self._add_widget_to_menu("weather_forecast", plugin_info)
        
        # Stock market widget
        from modules.stock_market.widget import register_plugin
        plugin_info = register_plugin()
        self.plugins["stock_market"] = plugin_info
        self._add_widget_to_menu("stock_market", plugin_info)
        
        # Code viewer widget
        from modules.code_viewer.widget import register_plugin
        plugin_info = register_plugin()
        self.plugins["code_viewer"] = plugin_info
        self._add_widget_to_menu("code_viewer", plugin_info)
        
        # WYSIWYG editor widget
        from modules.wysiwyg_editor.widget import register_plugin
        plugin_info = register_plugin()
        self.plugins["wysiwyg_editor"] = plugin_info
        self._add_widget_to_menu("wysiwyg_editor", plugin_info)

        # Calculator widgets
        from modules.calculator import register_plugins
        for plugin_info in register_plugins():
            # Use explicit module name if available, otherwise derive from plugin name
            module_name = plugin_info.get("module_name") or plugin_info["name"].lower().replace(" ", "_")
            self.plugins[module_name] = plugin_info
            self._add_widget_to_menu(module_name, plugin_info)

        # Tree list widget
        from modules.tree_list import register_plugins
        for plugin_info in register_plugins():
            module_name = plugin_info["widget_class"].__name__.lower().replace("widget", "")
            self.plugins[module_name] = plugin_info
            self._add_widget_to_menu(module_name, plugin_info)
    
    def _add_widget_to_menu(self, module_name, plugin_info):
        """Add a widget to the widgets menu"""
        widget_name = plugin_info.get("name", module_name)
        widget_class = plugin_info.get("widget_class")
        
        if not widget_class:
            return
        
        # Create action for adding this widget
        action = QAction(f"Add {widget_name}", self.main_window)
        action.triggered.connect(lambda: self._add_widget_instance(module_name, plugin_info))
        
        # Add to widgets menu
        self.widgets_menu.addAction(action)
    
    def _add_widget_instance(self, module_name, plugin_info):
        """Add an instance of a widget to the main window"""
        widget_name = plugin_info.get("name", module_name)
        widget_class = plugin_info.get("widget_class")
        widget_title = plugin_info.get("title", widget_name)
        
        # Add the widget to the main window
        self.main_window.add_widget(widget_class, module_name, widget_title)