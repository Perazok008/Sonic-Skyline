"""
Reusable UI components for the Sonic Skyline application
"""
from PyQt6.QtWidgets import QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from constants import (BUTTON_FONT, CONTENT_FONT, PLACEHOLDER_COLOR, 
                      CONTENT_AREA_STYLE, CONTENT_AREA_MIN_SIZE)


def create_styled_button(text: str, enabled: bool = True) -> QPushButton:
    """Create a styled button with consistent appearance"""
    button = QPushButton(text)
    button.setFont(BUTTON_FONT)
    button.setEnabled(enabled)
    return button


def create_content_area() -> QLabel:
    """Create the main content display area"""
    content_area = QLabel()
    content_area.setMinimumSize(CONTENT_AREA_MIN_SIZE)
    content_area.setStyleSheet(CONTENT_AREA_STYLE)
    content_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
    content_area.setText("Select a file to display content here")
    content_area.setFont(CONTENT_FONT)
    return content_area


def create_file_status_label() -> QLabel:
    """Create a label for displaying file selection status"""
    label = QLabel("No file selected")
    label.setFont(CONTENT_FONT)
    label.setStyleSheet(f"color: {PLACEHOLDER_COLOR};")
    return label


def create_button_layout(*buttons) -> QHBoxLayout:
    """Create a horizontal layout for buttons with proper spacing"""
    layout = QHBoxLayout()
    layout.addStretch()
    for button in buttons:
        layout.addWidget(button)
    return layout 