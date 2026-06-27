from pathlib import Path
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

RESOURCES_DIR = BASE_DIR / 'resources'
CONFIG_FILE = BASE_DIR / 'resources_config.json'
CHARACTERS_FILE = BASE_DIR / 'characters.json'