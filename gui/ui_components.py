"""
Reusable UI components for the Sonic Skyline application
"""
from PyQt6.QtWidgets import QPushButton, QLabel, QHBoxLayout, QCheckBox, QWidget
from PyQt6.QtCore import Qt
from core.constants import (BUTTON_FONT, CONTENT_FONT, PLACEHOLDER_COLOR, 
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


def create_toggle_checkbox(text: str, checked: bool = True) -> QCheckBox:
    """Create a styled toggle checkbox with modern appearance"""
    checkbox = QCheckBox(text)
    checkbox.setChecked(checked)
    checkbox.setFont(BUTTON_FONT)
    
    # Modern toggle styling that matches system theme
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
            border: 2px solid palette(mid);
            background-color: palette(button);
        }
        QCheckBox::indicator:checked {
            background-color: palette(highlight);
            border: 2px solid palette(highlight);
        }
        QCheckBox::indicator:unchecked {
            background-color: palette(button);
            border: 2px solid palette(mid);
        }
        QCheckBox::indicator:hover {
            border: 2px solid palette(dark);
        }
        QCheckBox::indicator:checked:hover {
            border: 2px solid palette(highlight);
            background-color: palette(highlight);
        }
    """)
    
    return checkbox


def create_visualization_toggles() -> QWidget:
    """Create the visualization toggle controls widget"""
    widget = QWidget()
    layout = QHBoxLayout()
    layout.setContentsMargins(10, 5, 10, 5)
    
    # Create toggle checkboxes
    image_toggle = create_toggle_checkbox("Show Image/Video", True)
    horizon_toggle = create_toggle_checkbox("Show Horizon Line", True)
    axis_toggle = create_toggle_checkbox("Show Axis", False)
    
    # Add label
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
    
    # Style the container to match system theme
    widget.setStyleSheet("""
        QWidget {
            background-color: palette(window);
            border: 1px solid palette(mid);
            border-radius: 8px;
            margin: 2px;
        }
    """)
    
    # Store references to toggles for easy access
    widget.image_toggle = image_toggle
    widget.horizon_toggle = horizon_toggle
    widget.axis_toggle = axis_toggle
    
    return widget 