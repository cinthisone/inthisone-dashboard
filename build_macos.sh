#!/bin/bash

# Exit on error
set -e

echo "Installing required packages..."
pip install pyinstaller dmgbuild

# Create the icon if it doesn't exist
if [ ! -d "assets" ]; then
    mkdir assets
fi

# Build the application
echo "Building application..."
pyinstaller desktop-dashboard.spec

# Create DMG configuration
echo "Creating DMG configuration..."
cat > dmg_config.py << EOL
from pathlib import Path

# Configuration for dmgbuild
files = [
    ('Desktop Dashboard.app', Path('dist/Desktop Dashboard.app')),
]
symlinks = {
    'Applications': '/Applications'
}
badge_icon = 'assets/icon.icns'
icon_locations = {
    'Desktop Dashboard.app': (140, 120),
    'Applications': (500, 120)
}
window_rect = ((100, 100), (640, 280))
background = 'builtin-arrow'
EOL

# Build DMG
echo "Building DMG..."
dmgbuild -s dmg_config.py "Desktop Dashboard" "dist/Desktop Dashboard.dmg"

echo "Build complete! DMG file is in the dist directory." 