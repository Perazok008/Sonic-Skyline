"""Reusable UI components for the Sonic Skyline application.

Functions here construct styled widgets and layouts so they can be reused
consistently across the app and tweaked in one place.
"""
from PyQt6.QtWidgets import QPushButton, QLabel, QHBoxLayout, QCheckBox, QWidget, QSizePolicy
from PyQt6.QtCore import Qt
from core.constants import (BUTTON_FONT, CONTENT_FONT, PLACEHOLDER_COLOR, 
                      CONTENT_AREA_STYLE, CONTENT_AREA_MIN_SIZE)


def create_styled_button(text: str, enabled: bool = True) -> QPushButton:
    """Create a styled button with consistent appearance."""
    button = QPushButton(text)
    button.setFont(BUTTON_FONT)
    button.setEnabled(enabled)
    # Consistent sizing and padding across the app
    button.setMinimumHeight(36)
    button.setMinimumWidth(110)
    button.setStyleSheet(
        """
        QPushButton {
            padding: 6px 14px;
            border-radius: 6px;
            border: none;
            background-color: palette(button);
            color: palette(button-text);
        }
        QPushButton:hover {
            background-color: palette(light);
        }
        QPushButton:pressed {
            background-color: palette(dark);
        }
        QPushButton:disabled {
            background-color: palette(midlight);
            color: palette(mid);
        }
        """
    )
    return button


def create_content_area() -> QLabel:
    """Create the main content display area.

    This is a QLabel that will host scaled images or video frames as QPixmaps.
    """
    content_area = QLabel()
    content_area.setMinimumSize(CONTENT_AREA_MIN_SIZE)
    content_area.setStyleSheet(CONTENT_AREA_STYLE)
    content_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
    content_area.setText("Select a file to display content here")
    content_area.setFont(CONTENT_FONT)
    # Allow content area to grow/shrink with layout
    content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return content_area


def create_file_status_label() -> QLabel:
    """Create a label for displaying current file selection status."""
    label = QLabel("No file selected")
    label.setFont(CONTENT_FONT)
    label.setStyleSheet(f"color: {PLACEHOLDER_COLOR};")
    return label


def create_button_layout(*buttons) -> QHBoxLayout:
    """Create a horizontal layout for buttons with proper spacing."""
    layout = QHBoxLayout()
    layout.addStretch()
    for button in buttons:
        layout.addWidget(button)
    return layout


def create_toggle_checkbox(text: str, checked: bool = True) -> QCheckBox:
    """Create a styled toggle checkbox."""
    checkbox = QCheckBox(text)
    checkbox.setChecked(checked)
    checkbox.setFont(BUTTON_FONT)
    
    # Minimal toggle styling
    checkbox.setStyleSheet("""
        QCheckBox {
            font-weight: 500;
            color: palette(text);
            spacing: 8px;
            background-color: transparent;
        }
        QCheckBox::indicator {
            width: 40px;
            height: 20px;
            border-radius: 10px;
            background-color: palette(button);
        }
        QCheckBox::indicator:checked {
            background-color: palette(highlight);
        }
        QCheckBox::indicator:unchecked {
            background-color: palette(button);
        }
    """)
    
    return checkbox


def create_visualization_toggles() -> QWidget:
    """Create a compact row of toggle controls for visualization layers."""
    widget = QWidget()
    layout = QHBoxLayout()
    layout.setContentsMargins(10, 5, 10, 5)
    
    # Create toggle checkboxes
    image_toggle = create_toggle_checkbox("Show Image/Video", True)
    horizon_toggle = create_toggle_checkbox("Show Horizon Line", True)
    axis_toggle = create_toggle_checkbox("Show Axis", False)
    
    # Add label describing the toggle group
    toggles_label = QLabel("Visualization Layers:")
    toggles_label.setFont(BUTTON_FONT)
    toggles_label.setStyleSheet("color: palette(text); font-weight: bold; margin-right: 10px; background-color: transparent;")
    
    # Add to layout
    layout.addWidget(toggles_label)
    layout.addWidget(image_toggle)
    layout.addWidget(horizon_toggle)
    layout.addWidget(axis_toggle)
    layout.addStretch()
    
    widget.setLayout(layout)
    
    # Keep container minimal and non-intrusive; no borders
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    # Store references to toggles for easy access by the caller
    widget.image_toggle = image_toggle
    widget.horizon_toggle = horizon_toggle
    widget.axis_toggle = axis_toggle
    
    return widget 