"""
File display functionality for the Sonic Skyline application
"""
import os
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, CONTENT_FONT


class FileDisplayManager:
    """Manages the display of files in the content area"""
    
    @staticmethod
    def display_file(content_area: QLabel, file_path: str) -> None:
        """Display the selected file in the provided content area"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in IMAGE_EXTENSIONS:
            FileDisplayManager._display_image(content_area, file_path)
        elif file_extension in VIDEO_EXTENSIONS:
            FileDisplayManager._display_video_placeholder(content_area, file_path)
        else:
            FileDisplayManager._display_unsupported_file(content_area, file_extension)
    
    @staticmethod
    def _display_image(content_area: QLabel, file_path: str) -> None:
        """Display an image file"""
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # Scale image to fit content area while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                content_area.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            content_area.setPixmap(scaled_pixmap)
        else:
            content_area.setText("Failed to load image")
            content_area.setFont(CONTENT_FONT)
    
    @staticmethod
    def _display_video_placeholder(content_area: QLabel, file_path: str) -> None:
        """Display a placeholder for video files"""
        filename = os.path.basename(file_path)
        content_area.setText(
            f"Video file loaded:\n{filename}\n\n(Video preview not implemented)"
        )
        content_area.setFont(CONTENT_FONT)
    
    @staticmethod
    def _display_unsupported_file(content_area: QLabel, file_extension: str) -> None:
        """Display message for unsupported file types"""
        content_area.setText(f"Unsupported file type:\n{file_extension}")
        content_area.setFont(CONTENT_FONT) 