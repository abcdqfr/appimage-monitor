#!/usr/bin/env python3
"""
AppImage Desktop File Generator

One-off script to scan a directory for AppImages and generate corresponding .desktop files.
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def detect_category(app_name):
    """Detect application category based on keywords in the name."""
    app_name_lower = app_name.lower()
    
    # Browser detection
    if any(browser in app_name_lower for browser in ['chrome', 'firefox', 'edge', 'brave', 'opera', 'safari', 'chromium', 'librewolf', 'libre']):
        return 'Network;WebBrowser;'
    
    # Development tools
    if any(dev in app_name_lower for dev in ['code', 'studio', 'ide', 'editor', 'vim', 'emacs', 'sublime']):
        return 'Development;IDE;'
    
    # Media players
    if any(media in app_name_lower for media in ['player', 'vlc', 'mpv', 'kodi', 'spotify', 'audacity']):
        return 'AudioVideo;Audio;Video;'
    
    # Image editors
    if any(img in app_name_lower for img in ['gimp', 'inkscape', 'blender', 'krita', 'darktable']):
        return 'Graphics;2DGraphics;3DGraphics;'
    
    # Office applications
    if any(office in app_name_lower for office in ['libreoffice', 'openoffice', 'word', 'excel', 'powerpoint']):
        return 'Office;'
    
    # Games
    if any(game in app_name_lower for game in ['game', 'steam', 'minecraft', 'roblox']):
        return 'Game;'
    
    # System tools
    if any(sys_tool in app_name_lower for sys_tool in ['terminal', 'system', 'admin', 'disk', 'backup']):
        return 'System;'
    
    # Default category
    return 'Utility;'

def extract_and_cache_icons(appimage_path):
    """
    Ironclad icon extraction: extract all icons, score them, cache all, return best.
    """
    app_name = appimage_path.stem
    icon_cache_dir = Path.home() / '.local/share/icons/hicolor'
    icon_cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create unique temp directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        logger.info(f"Extracting {appimage_path} to {temp_path}")
        
        try:
            # Extract AppImage
            result = subprocess.run(
                [str(appimage_path), '--appimage-extract'],
                cwd=temp_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to extract AppImage: {result.stderr}")
                return None
            
            # Find all icon files recursively
            icon_files = []
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    if file.lower().endswith(('.png', '.svg', '.xpm', '.ico')):
                        icon_path = Path(root) / file
                        icon_files.append(icon_path)
            
            if not icon_files:
                logger.warning(f"No icons found in {appimage_path}")
                return None
            
            logger.info(f"Found {len(icon_files)} icons in {appimage_path}")
            
            # Score and select best icon
            best_icon = None
            best_score = -1
            
            for icon_path in icon_files:
                score = 0
                file_size = icon_path.stat().st_size
                
                # Prefer SVG (vector, scalable)
                if icon_path.suffix.lower() == '.svg':
                    score += 1000
                # Then PNG (good quality, common)
                elif icon_path.suffix.lower() == '.png':
                    score += 500
                # Then XPM (legacy but supported)
                elif icon_path.suffix.lower() == '.xpm':
                    score += 100
                # Then ICO (Windows format)
                elif icon_path.suffix.lower() == '.ico':
                    score += 50
                
                # Prefer larger files (more detail)
                score += min(file_size // 1024, 100)  # Cap at 100 points
                
                # Try to get pixel dimensions for PNG files
                if icon_path.suffix.lower() == '.png':
                    try:
                        from PIL import Image
                        with Image.open(icon_path) as img:
                            width, height = img.size
                            score += min(width * height // 1000, 200)  # Cap at 200 points
                    except ImportError:
                        logger.warning("PIL not available, using file size for scoring")
                    except Exception as e:
                        logger.warning(f"Could not get PNG dimensions: {e}")
                
                if score > best_score:
                    best_score = score
                    best_icon = icon_path
            
            if not best_icon:
                logger.warning("No suitable icon found")
                return None
            
            logger.info(f"Selected best icon: {best_icon} (score: {best_score})")
            
            # Copy all icons to appropriate cache directories
            for icon_path in icon_files:
                # Use stem (no extension) for icon name in cache
                icon_name = icon_path.stem
                file_size = icon_path.stat().st_size
                
                # Determine size category based on file size and type
                if icon_path.suffix.lower() == '.svg':
                    # SVG is scalable, put in scalable directory
                    cache_subdir = icon_cache_dir / 'scalable/apps'
                    cache_subdir.mkdir(parents=True, exist_ok=True)
                    dest_path = cache_subdir / icon_name
                else:
                    # For bitmap icons, estimate size from file size
                    if file_size < 5000:  # Small icon
                        size_dir = '16x16'
                    elif file_size < 15000:  # Medium icon
                        size_dir = '32x32'
                    elif file_size < 50000:  # Large icon
                        size_dir = '48x48'
                    elif file_size < 100000:  # Extra large
                        size_dir = '64x64'
                    else:  # Very large
                        size_dir = '128x128'
                    
                    cache_subdir = icon_cache_dir / f'{size_dir}/apps'
                    cache_subdir.mkdir(parents=True, exist_ok=True)
                    dest_path = cache_subdir / icon_name
                
                # Copy icon to cache (without extension)
                dest_path_no_ext = cache_subdir / f"{icon_name}"
                shutil.copy2(icon_path, dest_path_no_ext)
                logger.info(f"Cached icon: {dest_path_no_ext}")
            
            # Return the best icon name for desktop file (without extension)
            return best_icon.stem
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout extracting {appimage_path}")
            return None
        except Exception as e:
            logger.error(f"Error extracting icons from {appimage_path}: {e}")
            return None

def generate_desktop_file(appimage_path, desktop_dir):
    """Generate a .desktop file for the given AppImage."""
    try:
        app_name = appimage_path.stem
        desktop_file = desktop_dir / f"{app_name}.desktop"
        
        # Extract and cache icons
        icon_name = extract_and_cache_icons(appimage_path)
        
        # Detect category
        category = detect_category(app_name)
        
        # Generate desktop file content
        desktop_content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Comment=AppImage Application
Exec={appimage_path} %u
Icon={icon_name if icon_name else 'application-x-executable'}
Terminal=false
Categories={category}
"""
        
        # Write desktop file
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        os.chmod(desktop_file, 0o755)
        logger.info(f"Generated desktop file: {desktop_file}")
        
        # Update desktop database
        try:
            subprocess.run(['update-desktop-database', str(desktop_dir)], 
                         capture_output=True, check=True)
            logger.info("Updated desktop database")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to update desktop database: {e}")
        except FileNotFoundError:
            logger.warning("update-desktop-database not found")
            
    except Exception as e:
        logger.error(f"Error generating desktop file for {appimage_path}: {e}")

def main():
    # Default directories
    appimage_dir = Path.home() / "AppImages"
    desktop_dir = Path.home() / ".local/share/applications"
    
    # Create directories if they don't exist
    appimage_dir.mkdir(parents=True, exist_ok=True)
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Scanning for AppImages in: {appimage_dir}")
    logger.info(f"Generating desktop files in: {desktop_dir}")
    
    # Find all AppImages
    appimages = list(appimage_dir.glob("*.AppImage"))
    
    if not appimages:
        logger.info("No AppImages found")
        return
    
    logger.info(f"Found {len(appimages)} AppImages")
    
    # Generate desktop files for each AppImage
    for appimage in appimages:
        logger.info(f"Processing: {appimage.name}")
        generate_desktop_file(appimage, desktop_dir)
    
    logger.info("Desktop file generation complete")

if __name__ == "__main__":
    main() 