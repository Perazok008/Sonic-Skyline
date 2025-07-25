"""
Main application entry point for Sonic Skyline
"""
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from constants import APP_NAME, WINDOW_MIN_SIZE
from gui.file_selection import FileSelectionWidget
from gui.ui_components import create_content_area, create_styled_button, create_button_layout
from gui.file_display import FileDisplayManager
from core.file_operations import FileProcessor


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.file_processor = FileProcessor()
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
    
    def _setup_window(self) -> None:
        """Configure the main window"""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_SIZE)
    
    def _setup_ui(self) -> None:
        """Setup the user interface"""
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Create components
        self.file_selection_widget = FileSelectionWidget()
        self.content_area = create_content_area()
        
        # Create buttons
        self.process_button = create_styled_button("Process", enabled=False)
        self.export_button = create_styled_button("Export", enabled=False)
        self.connect_ableton = create_styled_button("Connect to Ableton", enabled=False)
        
        # Create button layout
        button_layout = create_button_layout(self.process_button, self.export_button, self.connect_ableton)
        
        # Add all components to main layout
        main_layout.addWidget(self.file_selection_widget)
        main_layout.addWidget(self.content_area)
        main_layout.addLayout(button_layout)
    
    def _connect_signals(self) -> None:
        """Connect signals to their respective slots"""
        self.file_selection_widget.file_selected.connect(self._on_file_selected)
        self.process_button.clicked.connect(self._process_file)
        self.export_button.clicked.connect(self._export_file)
    
    def _on_file_selected(self, file_path: str) -> None:
        """Handle file selection"""
        # Update file processor
        self.file_processor.set_current_file(file_path)
        
        # Enable buttons
        self._enable_buttons(True)
        
        # Display the file
        FileDisplayManager.display_file(self.content_area, file_path)
    
    def _enable_buttons(self, enabled: bool) -> None:
        """Enable or disable process and export buttons"""
        self.process_button.setEnabled(enabled)
        self.export_button.setEnabled(enabled)
        self.connect_ableton.setEnabled(enabled)
    
    def _process_file(self) -> None:
        """Process the selected file"""
        self.file_processor.process_file(self)
    
    def _export_file(self) -> None:
        """Export the processed file"""
        self.file_processor.export_file(self)


def main() -> None:
    """Main application entry point"""
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()