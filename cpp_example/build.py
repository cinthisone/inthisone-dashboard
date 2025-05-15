#!/usr/bin/env python3
import os
import platform
import subprocess
import shutil

def build_libstats():
    """Build the libstats shared library"""
    # Create build directory
    if not os.path.exists("build"):
        os.makedirs("build")
    
    # Change to build directory
    os.chdir("build")
    
    # Run CMake
    cmake_cmd = ["cmake", ".."]
    subprocess.run(cmake_cmd, check=True)
    
    # Build the library
    if platform.system() == "Windows":
        build_cmd = ["cmake", "--build", ".", "--config", "Release"]
    else:
        build_cmd = ["make"]
    
    subprocess.run(build_cmd, check=True)
    
    # Copy the library to the modules directory
    lib_name = get_library_name()
    lib_path = os.path.join("lib", lib_name)
    
    if os.path.exists(lib_path):
        # Create stats module directory if it doesn't exist
        stats_module_dir = os.path.join("..", "..", "modules", "stats")
        if not os.path.exists(stats_module_dir):
            os.makedirs(stats_module_dir)
        
        # Copy the library
        shutil.copy(lib_path, stats_module_dir)
        print(f"Library copied to {stats_module_dir}/{lib_name}")
    else:
        print(f"Library not found at {lib_path}")
    
    # Return to original directory
    os.chdir("..")

def get_library_name():
    """Get the platform-specific library name"""
    system = platform.system()
    if system == "Windows":
        return "stats.dll"
    elif system == "Darwin":  # macOS
        return "libstats.dylib"
    else:  # Linux and others
        return "libstats.so"

if __name__ == "__main__":
    build_libstats()