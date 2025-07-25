"""
File operations and business logic for the Sonic Skyline application
"""
import os
from typing import Optional
from PyQt6.QtWidgets import QMessageBox, QWidget
from constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS


class FileProcessor:
    """Handles file processing operations"""
    
    def __init__(self):
        self.current_file: Optional[str] = None
    
    def set_current_file(self, file_path: str) -> None:
        """Set the current file for processing"""
        self.current_file = file_path
    
    def process_file(self, parent: QWidget) -> None:
        """Process the current file"""
        if not self.current_file:
            self._show_warning(parent, "No file selected!")
            return
        
        filename = os.path.basename(self.current_file)
        QMessageBox.information(
            parent,
            "Process",
            f"Processing file: {filename}\n\n(Processing functionality to be implemented)"
        )
    
    def export_file(self, parent: QWidget) -> None:
        """Export the processed file"""
        if not self.current_file:
            self._show_warning(parent, "No file selected!")
            return
        
        filename = os.path.basename(self.current_file)
        QMessageBox.information(
            parent,
            "Export",
            f"Exporting file: {filename}\n\n(Export functionality to be implemented)"
        )
    
    def is_image_file(self, file_path: str) -> bool:
        """Check if the file is an image"""
        return os.path.splitext(file_path)[1].lower() in IMAGE_EXTENSIONS
    
    def is_video_file(self, file_path: str) -> bool:
        """Check if the file is a video"""
        return os.path.splitext(file_path)[1].lower() in VIDEO_EXTENSIONS
    
    def _show_warning(self, parent: QWidget, message: str) -> None:
        """Show a warning message"""
        QMessageBox.warning(parent, "Warning", message) 