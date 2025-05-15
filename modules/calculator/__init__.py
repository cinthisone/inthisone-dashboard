from .widget import register_plugin as register_basic_calculator
from .scientific_widget import register_plugin as register_scientific_calculator

def register_plugins():
    """Register all calculator widgets"""
    return [
        register_basic_calculator(),
        register_scientific_calculator()
    ] 