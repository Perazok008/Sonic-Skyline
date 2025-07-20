from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QFileDialog, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
import os

class FileSelectionWidget(QWidget):
    # Signal emitted when a file is selected
    file_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.selected_file_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the file selection UI components"""
        # Create file selection layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        self.file_select_button = QPushButton("Select File")
        self.file_select_button.setFont(QFont("Arial", 10))
        self.file_select_button.clicked.connect(self.select_file)
        
        self.file_label = QLabel("No file selected")
        self.file_label.setFont(QFont("Arial", 9))
        self.file_label.setStyleSheet("color: gray;")
        
        self.layout.addWidget(self.file_select_button)
        self.layout.addWidget(self.file_label)
        self.layout.addStretch()
    
    def select_file(self):
        """Open file dialog to select video or image files"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Video or Image File",
            "",
            "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.gif);;Video Files (*.mp4 *.avi *.mov *.mkv);;Image Files (*.jpg *.jpeg *.png *.bmp *.gif)"
        )
        
        if file_path:
            self.selected_file_path = file_path
            self.file_label.setText(f"{os.path.basename(file_path)}")
            self.file_label.setFont(QFont("Arial", 12))
            self.file_label.setStyleSheet("color: green;")
            
            # Emit signal that a file was selected
            self.file_selected.emit(file_path)
    
    def get_selected_file(self):
        """Return the currently selected file path"""
        return self.selected_file_path
    
    def display_file_in_area(self, content_area, file_path):
        """Display the selected file in the provided content area"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            # Display image
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
        
        elif file_extension in ['.mp4', '.avi', '.mov', '.mkv']:
            # For video files, show a placeholder (video playback would require additional setup)
            content_area.setText(f"Video file loaded:\n{os.path.basename(file_path)}\n\n(Video preview not implemented)")
            content_area.setFont(QFont("Arial", 12))
        
        else:
            content_area.setText(f"Unsupported file type:\n{file_extension}") 