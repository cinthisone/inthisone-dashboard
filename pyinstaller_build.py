#!/usr/bin/env python3
import os
import sys
import platform
import subprocess
import shutil

def build_for_platform():
    """Build the application for the current platform"""
    system = platform.system().lower()
    
    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=InthisoneDashboard",
        "--onefile",
        "--windowed",
        "--clean",
        "--add-data=modules:modules",
    ]
    
    # Platform-specific options
    if system == "darwin":  # macOS
        cmd.extend([
            "--icon=resources/icon.icns",
            "--osx-bundle-identifier=com.inthisone.dashboard",
            "--target-architecture=universal2",
        ])
        output_format = "dmg"
    elif system == "windows":  # Windows
        cmd.extend([
            "--icon=resources/icon.ico",
            "--version-file=version_info.txt",
        ])
        output_format = "exe"
    else:  # Linux
        cmd.extend([
            "--icon=resources/icon.png",
        ])
        output_format = "AppImage"
    
    # Add main script
    cmd.append("main.py")
    
    # Run PyInstaller
    print(f"Building for {system}...")
    subprocess.run(cmd, check=True)
    
    # Additional platform-specific post-processing
    if system == "darwin" and output_format == "dmg":
        # Create DMG
        print("Creating DMG...")
        subprocess.run([
            "hdiutil", "create",
            "-srcfolder", "dist/ModularDashboard.app",
            "-volname", "Modular Dashboard",
            "dist/ModularDashboard.dmg"
        ], check=True)
    elif system == "linux" and output_format == "AppImage":
        # Create AppImage (simplified, would need more setup in practice)
        print("Creating AppImage...")
        # This is a placeholder - actual AppImage creation requires more setup
        # You would typically use tools like linuxdeploy or appimagetool
    
    print(f"Build complete! Output: dist/ModularDashboard.{output_format}")

if __name__ == "__main__":
    # Create resources directory if it doesn't exist
    if not os.path.exists("resources"):
        os.makedirs("resources")
    
    # Build for current platform
    build_for_platform()