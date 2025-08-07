"""Constants used throughout the Sonic Skyline application.

Centralized sizes, colors, fonts, file filters, and supported extensions to
ensure the UI and logic stay consistent across modules.
"""
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QSize

# Application settings
APP_NAME = "Sonic Skyline"
WINDOW_MIN_SIZE = QSize(1100, 600)  # Increased width to accommodate settings panel

# UI Dimensions
CONTENT_AREA_MIN_SIZE = QSize(760, 400)
FILE_SELECTION_SIZE = QSize(800, 100)

# Fonts
TITLE_FONT = QFont("Arial", 14, QFont.Weight.Bold)
BUTTON_FONT = QFont("Arial", 10)
CONTENT_FONT = QFont("Arial", 12)

# Colors
BORDER_COLOR = "#cccccc"
SUCCESS_COLOR = "green"
PLACEHOLDER_COLOR = "gray"

# File extensions
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv']
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS

# File dialog filter for open dialog – grouped for convenience
FILE_DIALOG_FILTER = (
    "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.gif);;"
    "Video Files (*.mp4 *.avi *.mov *.mkv);;"
    "Image Files (*.jpg *.jpeg *.png *.bmp *.gif)"
)

# Styles
CONTENT_AREA_STYLE = f"""
    QLabel {{
        border: 2px solid {BORDER_COLOR};
        border-radius: 10px;
    }}
"""