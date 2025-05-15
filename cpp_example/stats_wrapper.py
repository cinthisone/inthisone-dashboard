import os
import sys
import ctypes
import platform
import numpy as np
from typing import List, Union, Optional

class StatsLibrary:
    """Wrapper for the C++ stats library"""
    
    def __init__(self):
        # Determine the library file name based on platform
        if platform.system() == "Windows":
            lib_name = "stats.dll"
        elif platform.system() == "Darwin":  # macOS
            lib_name = "libstats.dylib"
        else:  # Linux and others
            lib_name = "libstats.so"
        
        # Find the library
        module_dir = os.path.dirname(os.path.abspath(__file__))
        lib_path = os.path.join(module_dir, lib_name)
        
        if not os.path.exists(lib_path):
            raise FileNotFoundError(f"Stats library not found at {lib_path}")
        
        # Load the library
        self.lib = ctypes.CDLL(lib_path)
        
        # Define function signatures
        self.lib.calculate_mean.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t]
        self.lib.calculate_mean.restype = ctypes.c_double
        
        self.lib.calculate_stddev.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t, ctypes.c_bool]
        self.lib.calculate_stddev.restype = ctypes.c_double
        
        self.lib.calculate_median.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t]
        self.lib.calculate_median.restype = ctypes.c_double
    
    def mean(self, data: Union[List[float], np.ndarray]) -> float:
        """Calculate the mean of a list of values"""
        if len(data) == 0:
            return 0.0
        
        # Convert data to numpy array of doubles
        np_array = np.array(data, dtype=np.float64)
        
        # Get pointer to the data
        data_ptr = np_array.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        
        # Call C++ function
        return self.lib.calculate_mean(data_ptr, len(np_array))
    
    def stddev(self, data: Union[List[float], np.ndarray], sample: bool = True) -> float:
        """Calculate the standard deviation of a list of values"""
        if len(data) <= 1:
            return 0.0
        
        # Convert data to numpy array of doubles
        np_array = np.array(data, dtype=np.float64)
        
        # Get pointer to the data
        data_ptr = np_array.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        
        # Call C++ function
        return self.lib.calculate_stddev(data_ptr, len(np_array), sample)
    
    def median(self, data: Union[List[float], np.ndarray]) -> float:
        """Calculate the median of a list of values"""
        if len(data) == 0:
            return 0.0
        
        # Convert data to numpy array of doubles
        np_array = np.array(data, dtype=np.float64).copy()  # Make a copy since this will be modified
        
        # Get pointer to the data
        data_ptr = np_array.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        
        # Call C++ function
        return self.lib.calculate_median(data_ptr, len(np_array))

# Create a singleton instance
stats = StatsLibrary()