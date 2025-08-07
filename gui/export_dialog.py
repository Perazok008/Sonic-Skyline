"""Export dialog for saving horizon detection results.

Lets the user choose export formats (CSV/Graph/Overlay), a base filename, and a
save location. Emits `export_confirmed(export_config, path, base_name)` on
success. The dialog disables options that require horizon data when none is
available.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QCheckBox, QLineEdit, QPushButton, QFileDialog,
                            QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from core.constants import BUTTON_FONT, CONTENT_FONT


class ExportDialog(QDialog):
    """Dialog for configuring and executing export operations."""
    
    # Signal emitted when export is confirmed with (export_config, save_path, base_name)
    export_confirmed = pyqtSignal(dict, str, str)
    
    def __init__(self, current_file: Optional[str] = None, has_horizon_data: bool = False):
        super().__init__()
        self.current_file = current_file
        self.has_horizon_data = has_horizon_data
        self.selected_path = str(Path.home() / "Desktop")  # Default to desktop
        
        self._setup_ui()
        self._connect_signals()
        self._update_export_options()
        # Ensure initial button state reflects current selections and name
        self._update_export_button()
    
    def _setup_ui(self):
        """Setup the export dialog UI with 3 sections and action buttons."""
        self.setWindowTitle("Export Horizon Detection Results")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Export Options")
        title.setFont(BUTTON_FONT)
        title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Export format selection (enables CSV always; others when horizon data exists)
        format_group = self._create_format_group()
        layout.addWidget(format_group)
        
        # File naming section – base name only; suffixes are added automatically
        naming_group = self._create_naming_group()
        layout.addWidget(naming_group)
        
        # Path selection for save directory
        path_group = self._create_path_group()
        layout.addWidget(path_group)
        
        # Buttons
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Style the dialog to match system theme
        self.setStyleSheet("""
            QDialog {
                background-color: palette(window);
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid palette(mid);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: palette(base);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                top: 5px;
                padding: 0 8px 0 8px;
                color: palette(text);
                background-color: palette(base);
            }
            QLabel {
                color: palette(text);
                background-color: transparent;
            }
            QCheckBox {
                color: palette(text);
                spacing: 8px;
                background-color: transparent;
            }
            QLineEdit {
                background-color: palette(base);
                color: palette(text);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid palette(highlight);
            }
            QPushButton {
                background-color: palette(button);
                color: palette(button-text);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: palette(light);
            }
            QPushButton:pressed {
                background-color: palette(dark);
            }
            QPushButton:default {
                border: 2px solid palette(highlight);
                font-weight: bold;
            }
        """)
    
    def _create_format_group(self) -> QGroupBox:
        """Create export format selection group."""
        group = QGroupBox("What to Export")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)
        
        # CSV export (always allowed) – serializes horizon coordinates
        self.csv_checkbox = QCheckBox("CSV Data - Horizon line coordinates")
        self.csv_checkbox.setChecked(True)
        layout.addWidget(self.csv_checkbox)
        
        # Graph image/video export – quick visualization via matplotlib
        self.graph_checkbox = QCheckBox("Graph - Horizon line visualization")
        self.graph_checkbox.setChecked(False)
        layout.addWidget(self.graph_checkbox)
        
        # Overlay image/video export – draws line onto the original frames
        self.overlay_checkbox = QCheckBox("Overlay - Original with horizon line")
        self.overlay_checkbox.setChecked(False)
        layout.addWidget(self.overlay_checkbox)
        
        # Help text
        help_text = QLabel("For videos, all processed frames will be included.")
        help_text.setStyleSheet("color: palette(dark); font-size: 10px; margin-top: 5px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        group.setLayout(layout)
        return group
    
    def _create_naming_group(self) -> QGroupBox:
        """Create file naming group."""
        group = QGroupBox("File Name")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(8)
        
        layout.addWidget(QLabel("Base name (suffixes will be added automatically):"))
        
        self.name_input = QLineEdit()
        if self.current_file:
            # Use the current file name without extension as default
            base_name = Path(self.current_file).stem
            self.name_input.setText(f"{base_name}_export")
        else:
            self.name_input.setText("horizon_export")
        
        layout.addWidget(self.name_input)
        
        # Example text to show resulting files
        example_text = QLabel("Examples: filename_csv.csv, filename_graph.png, filename_overlay.mp4")
        example_text.setStyleSheet("color: palette(dark); font-size: 10px; margin-top: 5px;")
        example_text.setWordWrap(True)
        layout.addWidget(example_text)
        
        group.setLayout(layout)
        return group
    
    def _create_path_group(self) -> QGroupBox:
        """Create path selection group."""
        group = QGroupBox("Save Location")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(8)
        
        # Path display label and browse button
        path_layout = QHBoxLayout()
        
        self.path_label = QLabel(self.selected_path)
        self.path_label.setStyleSheet("""
            background-color: palette(base);
            border: 1px solid palette(mid);
            border-radius: 4px;
            padding: 6px;
            font-size: 11px;
        """)
        self.path_label.setWordWrap(True)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setFont(BUTTON_FONT)
        
        path_layout.addWidget(self.path_label, stretch=1)
        path_layout.addWidget(self.browse_button)
        
        layout.addLayout(path_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_button_layout(self) -> QHBoxLayout:
        """Create dialog button layout."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 20, 0, 0)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(BUTTON_FONT)
        
        # Export button
        self.export_button = QPushButton("Export")
        self.export_button.setFont(BUTTON_FONT)
        self.export_button.setDefault(True)
        
        layout.addStretch()
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.export_button)
        
        return layout
    
    def _connect_signals(self):
        """Connect dialog signals for browsing, cancel, export, and enablement."""
        self.browse_button.clicked.connect(self._browse_path)
        self.cancel_button.clicked.connect(self.reject)
        self.export_button.clicked.connect(self._validate_and_export)
        
        # Update export button state when options change
        self.csv_checkbox.stateChanged.connect(self._update_export_button)
        self.graph_checkbox.stateChanged.connect(self._update_export_button)
        self.overlay_checkbox.stateChanged.connect(self._update_export_button)
        self.name_input.textChanged.connect(self._update_export_button)
    
    def _update_export_options(self):
        """Update available export options based on presence of horizon data."""
        if not self.has_horizon_data:
            # Disable options that require horizon data
            self.graph_checkbox.setEnabled(False)
            self.overlay_checkbox.setEnabled(False)
            self.graph_checkbox.setChecked(False)
            self.overlay_checkbox.setChecked(False)
    
    def _update_export_button(self):
        """Enable Export only if at least one option and a name are provided."""
        has_selection = (self.csv_checkbox.isChecked() or 
                        self.graph_checkbox.isChecked() or 
                        self.overlay_checkbox.isChecked())
        has_name = bool(self.name_input.text().strip())
        
        self.export_button.setEnabled(has_selection and has_name)
    
    def _browse_path(self):
        """Open directory browser to set the export target path."""
        path = QFileDialog.getExistingDirectory(
            self, 
            "Select Export Directory", 
            self.selected_path
        )
        
        if path:
            self.selected_path = path
            self.path_label.setText(path)
    
    def _validate_and_export(self):
        """Validate inputs, then emit `export_confirmed` and close the dialog."""
        # Validate selections
        if not (self.csv_checkbox.isChecked() or 
               self.graph_checkbox.isChecked() or 
               self.overlay_checkbox.isChecked()):
            QMessageBox.warning(self, "Export Error", 
                              "Please select at least one export format.")
            return
        
        # Validate name
        base_name = self.name_input.text().strip()
        if not base_name:
            QMessageBox.warning(self, "Export Error", 
                              "Please enter a file name.")
            return
        
        # Check if path exists
        if not os.path.exists(self.selected_path):
            QMessageBox.warning(self, "Export Error", 
                              "Selected directory does not exist.")
            return
        
        # Build export configuration
        export_config = {
            'csv': self.csv_checkbox.isChecked(),
            'graph': self.graph_checkbox.isChecked(),
            'overlay': self.overlay_checkbox.isChecked(),
        }
        
        # Emit signal and close dialog
        self.export_confirmed.emit(export_config, self.selected_path, base_name)
        self.accept()
    
    def get_export_config(self) -> Tuple[Dict[str, bool], str, str]:
        """Get current export configuration for testing or inspection."""
        export_config = {
            'csv': self.csv_checkbox.isChecked(),
            'graph': self.graph_checkbox.isChecked(),
            'overlay': self.overlay_checkbox.isChecked(),
        }
        
        return export_config, self.selected_path, self.name_input.text().strip()