# AppImage Desktop Tools

Robust AppImage desktop file generator with ironclad icon extraction and browser URL support.

## Features
- **Ironclad icon extraction:** Extracts all icons from AppImages, scores them, caches all, and sets the best one for desktop files
- **Browser URL support:** Generates `.desktop` files with `%u` so AppImage browsers can be set as default and accept URLs
- **Deterministic & idempotent:** Safe to run multiple times, always produces correct results
- **Executable permissions:** Automatically sets correct permissions on `.desktop` files
- **Category detection:** Intelligent application categorization for menus
- **Icon caching:** Stores icons without extensions in proper hicolor theme structure
- **Desktop database updates:** Automatically updates desktop environment

## Usage

### One-off generation
```sh
python3 src/appimage_tools/generate_once/generate_once.py
```
- Scans `~/AppImages` for AppImages
- Generates `.desktop` files in `~/.local/share/applications`
- Extracts and caches icons in `~/.local/share/icons/hicolor`

### Real-time monitoring
```sh
python3 src/appimage_tools/monitor/monitor.py
```
- Watches `~/AppImages` for new AppImages
- Automatically generates `.desktop` files and caches icons

## Requirements
- Python 3.7+
- [Pillow](https://pypi.org/project/Pillow/) (for PNG dimension scoring, optional but recommended)
- [watchdog](https://pypi.org/project/watchdog/) (for monitor script)

Install requirements:
```sh
pip install Pillow watchdog
```

## Why?
- AppImage `--icon` is unreliable; this tool guarantees robust icon extraction and desktop integration
- Lets you use AppImage browsers (like LibreWolf) as your system default browser

## License
MIT 