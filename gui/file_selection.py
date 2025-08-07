"""File selection widget for the Sonic Skyline application.

Provides a small UI with a button to open the OS file dialog and a label that
shows the selected filename. Emits `file_selected` with the chosen path.
"""
import os
from typing import Optional
from PyQt6.QtWidgets import QHBoxLayout, QFileDialog, QWidget
from PyQt6.QtCore import pyqtSignal
from core.constants import FILE_DIALOG_FILTER, FILE_SELECTION_SIZE, SUCCESS_COLOR
from gui.ui_components import create_styled_button, create_file_status_label


class FileSelectionManager(QWidget):
    """Widget for selecting media files."""
    
    # Signal emitted when a file is selected
    file_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.selected_file_path: Optional[str] = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the file selection UI components."""
        self.setFixedSize(FILE_SELECTION_SIZE)
        
        # Create layout and components
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        self.file_select_button = create_styled_button("Select File")
        self.file_select_button.clicked.connect(self._select_file)
        
        self.file_label = create_file_status_label()
        
        # Add widgets to layout
        layout.addWidget(self.file_select_button)
        layout.addWidget(self.file_label)
        layout.addStretch()
    
    def _select_file(self) -> None:
        """Open file dialog to select a video or image file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video or Image File",
            "",
            FILE_DIALOG_FILTER
        )
        
        if file_path:
            self._update_selected_file(file_path)
    
    def _update_selected_file(self, file_path: str) -> None:
        """Update the selected file path, UI label, and emit signal."""
        self.selected_file_path = file_path
        filename = os.path.basename(file_path)
        
        self.file_label.setText(filename)
        self.file_label.setStyleSheet(f"color: {SUCCESS_COLOR};")
        
        # Emit signal that a file was selected
        self.file_selected.emit(file_path)
    
    def get_selected_file(self) -> Optional[str]:
        """Return the currently selected file path, or None if not set."""
        return self.selected_file_path 