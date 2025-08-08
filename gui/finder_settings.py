"""Settings panel for horizon finder parameters.

Exposes Canny edge detection parameters and the horizon continuity constraint
(`line_jump_threshold`). Emits `settings_changed` with a structured dict on any
change so the main window can apply updates immediately.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSpinBox, 
                            QCheckBox, QGroupBox, QPushButton, QHBoxLayout, QSlider, QComboBox)
from PyQt6.QtCore import pyqtSignal, Qt
from core.constants import BUTTON_FONT, CONTENT_FONT


class FinderSettingsPanel(QWidget):
    """Settings panel for horizon finder parameters."""
    
    # Signal emitted when settings change
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the settings UI with two groups: Edge Detection and Horizon."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("Horizon Finder Settings")
        title.setFont(BUTTON_FONT)
        title.setStyleSheet("""
            font-weight: bold; 
            color: palette(text); 
            margin-bottom: 8px;
            padding: 8px;
            background-color: transparent;
            border: none;
            font-size: 12px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Canny Edge Detection Group (thresholds control sensitivity; aperture/L2 affect gradient precision)
        canny_group = self._create_canny_group()
        layout.addWidget(canny_group)
        
        # Horizon Line Detection Group (continuity constraint to reduce jitter)
        horizon_group = self._create_horizon_group()
        layout.addWidget(horizon_group)
        
        # Reset and Apply buttons; Apply is bound to emit changes immediately
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)
        
        layout.addStretch()  # Push everything to the top
        self.setLayout(layout)
        
        # Style the panel to match system theme
        self.setStyleSheet("""
            FinderSettingsPanel {
                border-left: 2px solid palette(mid);
            }
            QGroupBox {
                font-weight: bold;
                border: none;
                border-radius: 0px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                top: 5px;
                padding: 0 8px 0 8px;
                color: palette(text);
                background-color: transparent;
            }
            QLabel {
                color: palette(text);
                font-size: 11px;
                margin: 2px 0px;
                padding: 2px;
                background-color: transparent;
            }
            QSpinBox {
                background-color: palette(base);
                color: palette(text);
                border: none;
                border-bottom: 1px solid palette(mid);
                padding: 6px 24px 6px 6px; /* right padding for spin buttons */
                margin: 2px 0px;
                font-size: 11px;
                selection-background-color: palette(highlight);
                selection-color: palette(highlighted-text);
            }
            QSpinBox:focus {
                border-bottom: 2px solid palette(highlight);
            }
            /* Improve up/down button hit areas and visuals */
            QSpinBox::up-button, QSpinBox::down-button {
                subcontrol-origin: border;
                width: 18px;
                background: palette(button);
                border: 1px solid palette(mid);
                border-radius: 3px;
                margin: 2px 2px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: palette(light);
            }
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
                background: palette(dark);
            }
            QSpinBox::up-button {
                subcontrol-position: top right;
            }
            QSpinBox::down-button {
                subcontrol-position: bottom right;
            }
            QCheckBox {
                color: palette(text);
                margin: 4px 0px;
                spacing: 6px;
                background-color: transparent;
            }
            QPushButton {
                background-color: palette(button);
                color: palette(button-text);
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                margin: 2px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: palette(light);
            }
            QPushButton:pressed {
                background-color: palette(dark);
            }
        """)
        
        # Set fixed width
        self.setFixedWidth(250)
    
    def _create_canny_group(self) -> QGroupBox:
        """Create Canny edge detection settings group."""
        group = QGroupBox("Edge Detection")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(8)
        
        # Threshold 1 (lower hysteresis) – smaller value catches more edges/noise
        layout.addWidget(QLabel("Lower Threshold (intensity):"))
        self.threshold1_spin = QSpinBox()
        self.threshold1_spin.setRange(1, 500)
        self.threshold1_spin.setValue(100)
        layout.addWidget(self.threshold1_spin)
        
        # Threshold 2 (upper hysteresis) – larger value reduces noise
        layout.addWidget(QLabel("Upper Threshold (intensity):"))
        self.threshold2_spin = QSpinBox()
        self.threshold2_spin.setRange(1, 500)
        self.threshold2_spin.setValue(200)
        layout.addWidget(self.threshold2_spin)
        
        # Aperture Size – Sobel kernel size (OpenCV supports 3,5,7)
        layout.addWidget(QLabel("Aperture Size:"))
        self.aperture_combo = QComboBox()
        self.aperture_combo.addItems(["3", "5", "7"])  # OpenCV supports 3,5,7
        self.aperture_combo.setCurrentText("3")
        layout.addWidget(self.aperture_combo)
        
        # L2 Gradient – use more accurate gradient magnitude at the cost of speed
        self.l2_gradient_check = QCheckBox("Use L2 Gradient")
        self.l2_gradient_check.setChecked(False)
        layout.addWidget(self.l2_gradient_check)
        
        group.setLayout(layout)
        return group
    
    def _create_horizon_group(self) -> QGroupBox:
        """Create horizon line detection settings group."""
        group = QGroupBox("Horizon Detection")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(8)
        
        # Line Jump Threshold – max per-column change allowed to keep line continuous
        layout.addWidget(QLabel("Line Jump Threshold (pixels):"))
        self.line_jump_spin = QSpinBox()
        self.line_jump_spin.setRange(1, 100)
        self.line_jump_spin.setValue(15)
        layout.addWidget(self.line_jump_spin)
        
        # Playback/processing controls with visible values
        layout.addWidget(QLabel("Processing FPS (frames per second):"))
        pfps_row = QHBoxLayout()
        self.processing_fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.processing_fps_slider.setRange(1, 120)
        self.processing_fps_slider.setValue(30)
        self.processing_fps_value = QLabel("30 fps")
        pfps_row.addWidget(self.processing_fps_slider)
        pfps_row.addWidget(self.processing_fps_value)
        layout.addLayout(pfps_row)

        layout.addWidget(QLabel("Display Max FPS:"))
        dfps_row = QHBoxLayout()
        self.display_fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.display_fps_slider.setRange(5, 120)
        self.display_fps_slider.setValue(30)
        self.display_fps_value = QLabel("30 fps")
        dfps_row.addWidget(self.display_fps_slider)
        dfps_row.addWidget(self.display_fps_value)
        layout.addLayout(dfps_row)

        # Algorithm selection (v1 classic, v2 vectorized)
        algo_row = QHBoxLayout()
        algo_row.addWidget(QLabel("Algorithm:"))
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["v1", "v2"]) 
        self.algorithm_combo.setCurrentText("v1")
        algo_row.addWidget(self.algorithm_combo)
        layout.addLayout(algo_row)

        # Help text to clarify behavior for users (midlight for dark-mode readability)
        help_label = QLabel("Maximum pixel jump between adjacent horizon points")
        help_label.setStyleSheet("""
            color: palette(midlight);
            font-size: 9px;
            margin-top: 5px;
            padding: 4px;
            background-color: transparent;
            border: none;
        """)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        group.setLayout(layout)
        return group
    
    def _create_button_layout(self) -> QHBoxLayout:
        """Create button layout with Reset and Apply buttons."""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 10, 5, 5)
        layout.setSpacing(8)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setFont(BUTTON_FONT)
        self.reset_button.clicked.connect(self._reset_defaults)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.setFont(BUTTON_FONT)
        self.apply_button.clicked.connect(self._apply_settings)
        
        layout.addWidget(self.reset_button)
        layout.addWidget(self.apply_button)
        
        return layout
    
    def _connect_signals(self):
        """Connect all input signals to auto-apply changes."""
        self.threshold1_spin.valueChanged.connect(self._apply_settings)
        self.threshold2_spin.valueChanged.connect(self._apply_settings)
        self.aperture_combo.currentTextChanged.connect(self._apply_settings)
        self.l2_gradient_check.stateChanged.connect(self._apply_settings)
        self.line_jump_spin.valueChanged.connect(self._apply_settings)
        self.processing_fps_slider.valueChanged.connect(self._apply_settings)
        self.display_fps_slider.valueChanged.connect(self._apply_settings)
        self.algorithm_combo.currentTextChanged.connect(self._apply_settings)
    
    def _reset_defaults(self):
        """Reset all settings to default values and emit change."""
        self.threshold1_spin.setValue(100)
        self.threshold2_spin.setValue(200)
        self.aperture_combo.setCurrentText("3")
        self.l2_gradient_check.setChecked(False)
        self.line_jump_spin.setValue(15)
        self.processing_fps_slider.setValue(30)
        self.display_fps_slider.setValue(30)
        self._apply_settings()
    
    def _apply_settings(self):
        """Apply current settings by emitting a structured dict."""
        # Update inline labels for sliders
        self.processing_fps_value.setText(f"{self.processing_fps_slider.value()} fps")
        self.display_fps_value.setText(f"{self.display_fps_slider.value()} fps")

        settings = {
            "canny_edge_params": {
                "threshold1": self.threshold1_spin.value(),
                "threshold2": self.threshold2_spin.value(),
                "apertureSize": int(self.aperture_combo.currentText()),
                "L2gradient": self.l2_gradient_check.isChecked(),
            },
            "horizon_line_params": {
                "line_jump_threshold": self.line_jump_spin.value(),
            },
            "playback": {
                "processing_fps": self.processing_fps_slider.value(),
                "display_max_fps": self.display_fps_slider.value(),
            },
            "algorithm_version": self.algorithm_combo.currentText(),
        }
        self.settings_changed.emit(settings)
    
    def get_current_settings(self) -> dict:
        """Get current settings as a dictionary for inspection or persistence."""
        return {
            "canny_edge_params": {
                "threshold1": self.threshold1_spin.value(),
                "threshold2": self.threshold2_spin.value(),
                "apertureSize": int(self.aperture_combo.currentText()),
                "L2gradient": self.l2_gradient_check.isChecked(),
            },
            "horizon_line_params": {
                "line_jump_threshold": self.line_jump_spin.value(),
            },
            "playback": {
                "processing_fps": self.processing_fps_slider.value(),
                "display_max_fps": self.display_fps_slider.value(),
            },
            "algorithm_version": self.algorithm_combo.currentText(),
        }
    
    def set_settings(self, settings: dict):
        """Populate UI controls from a settings dictionary."""
        if "canny_edge_params" in settings:
            canny = settings["canny_edge_params"]
            self.threshold1_spin.setValue(canny.get("threshold1", 100))
            self.threshold2_spin.setValue(canny.get("threshold2", 200))
            self.aperture_combo.setCurrentText(str(canny.get("apertureSize", 3)))
            self.l2_gradient_check.setChecked(canny.get("L2gradient", False))
        
        if "horizon_line_params" in settings:
            horizon = settings["horizon_line_params"]
            self.line_jump_spin.setValue(horizon.get("line_jump_threshold", 15))
        if "playback" in settings:
            pb = settings["playback"]
            self.processing_fps_slider.setValue(pb.get("processing_fps", 30))
            self.display_fps_slider.setValue(pb.get("display_max_fps", 30))
        if "algorithm_version" in settings:
            self.algorithm_combo.setCurrentText(settings["algorithm_version"]) 
