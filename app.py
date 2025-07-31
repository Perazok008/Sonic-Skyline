"""
Main application entry point for Sonic Skyline
"""
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout
from core.constants import APP_NAME, WINDOW_MIN_SIZE
from gui.file_selection import FileSelectionManager
from gui.ui_components import create_content_area, create_styled_button, create_button_layout, create_visualization_toggles
from gui.file_display import FileDisplayManager
from gui.finder_settings import FinderSettingsPanel
from horizon_finder.horizon_finder import HorizonFinder


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()
        self.horizon_finder = HorizonFinder()  # Create horizon_finder before connecting signals
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
        
        # Create horizontal layout for main content and settings panel
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Create left side content layout
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Create components
        self.file_selection_widget = FileSelectionManager()
        self.visualization_toggles = create_visualization_toggles()
        self.content_area = create_content_area()
        
        # Create buttons
        self.process_button = create_styled_button("Process", enabled=False)
        self.export_button = create_styled_button("Export", enabled=False)
        self.connect_ableton = create_styled_button("Connect to Ableton", enabled=False)
        
        # Create button layout
        button_layout = create_button_layout(self.process_button, self.export_button, self.connect_ableton)
        
        # Add all components to left layout
        left_layout.addWidget(self.file_selection_widget)
        left_layout.addWidget(self.visualization_toggles)  # Add toggles above content area
        left_layout.addWidget(self.content_area)
        left_layout.addLayout(button_layout)
        
        # Create settings panel
        self.settings_panel = FinderSettingsPanel()
        
        # Add left content and settings panel to main layout
        main_layout.addWidget(left_widget, stretch=1)  # Main content takes most space
        main_layout.addWidget(self.settings_panel)     # Settings panel fixed width
    
    def _connect_signals(self) -> None:
        """Connect signals to their respective slots"""
        self.file_selection_widget.file_selected.connect(self._on_file_selected)
        self.process_button.clicked.connect(self._process_file)
        self.export_button.clicked.connect(self._export_file)
        
        # Connect visualization toggle signals
        self.visualization_toggles.image_toggle.stateChanged.connect(self._on_toggle_changed)
        self.visualization_toggles.horizon_toggle.stateChanged.connect(self._on_toggle_changed)
        self.visualization_toggles.axis_toggle.stateChanged.connect(self._on_toggle_changed)
        
        # Connect settings panel signals
        self.settings_panel.settings_changed.connect(self._on_settings_changed)
        
        # Initialize settings panel with current horizon finder parameters
        current_params = self.horizon_finder.get_current_parameters()
        self.settings_panel.set_settings(current_params)
    
    def _on_file_selected(self, file_path: str) -> None:
        """Handle file selection"""
        self._enable_buttons(True)
        show_image, show_horizon, show_axis = self._get_toggle_states()
        FileDisplayManager.display_file(
            self.content_area, file_path, None, 
            show_image=show_image, show_horizon=False, show_axis=show_axis,
            horizon_finder=self.horizon_finder
        )
    
    def _enable_buttons(self, enabled: bool) -> None:
        """Enable or disable process and export buttons"""
        self.process_button.setEnabled(enabled)
        self.export_button.setEnabled(enabled)
        self.connect_ableton.setEnabled(enabled)

    def _process_file(self) -> None:
        """Process the selected file"""
        file_path = self.file_selection_widget.get_selected_file()
        # For images, process horizon line once; for videos, this will be processed frame by frame
        horizon_line = None
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            horizon_line = self.horizon_finder.find_horizon_line(file_path)
        
        show_image, show_horizon, show_axis = self._get_toggle_states()
        FileDisplayManager.display_file(
            self.content_area, file_path, horizon_line, 
            show_image=show_image, show_horizon=show_horizon, show_axis=show_axis,
            horizon_finder=self.horizon_finder
        )


    def _export_file(self) -> None:
        """Export the processed file"""
        self.file_processor.export_file(self)

    def _get_toggle_states(self) -> tuple[bool, bool, bool]:
        """Get current state of all visualization toggles"""
        show_image = self.visualization_toggles.image_toggle.isChecked()
        show_horizon = self.visualization_toggles.horizon_toggle.isChecked()
        show_axis = self.visualization_toggles.axis_toggle.isChecked()
        return show_image, show_horizon, show_axis

    def _on_toggle_changed(self) -> None:
        """Handle toggle state changes - refresh the display"""
        if hasattr(self, 'file_selection_widget'):
            file_path = self.file_selection_widget.get_selected_file()
            if file_path:  # Only refresh if a file is selected
                self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the current display with current toggle states"""
        file_path = self.file_selection_widget.get_selected_file()
        if not file_path:
            return
        
        show_image, show_horizon, show_axis = self._get_toggle_states()
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Check if this is a video file and if video is currently playing
        if file_extension in ['.mp4', '.avi', '.mov', '.mkv']:
            # For videos, just update the display settings for ongoing playback
            FileDisplayManager.update_video_display_settings(show_image, show_horizon, show_axis)
        else:
            # For images, check if we're currently processing (horizon line detection is active)
            is_processing = self.process_button.isEnabled() and show_horizon
            
            if is_processing:
                # If processing mode is active, use the processed display
                horizon_line = None
                try:
                    horizon_line = self.horizon_finder.find_horizon_line(file_path)
                except Exception:
                    horizon_line = None
                
                FileDisplayManager.display_file(
                    self.content_area, file_path, horizon_line,
                    show_image=show_image, show_horizon=show_horizon, show_axis=show_axis,
                    horizon_finder=self.horizon_finder
                )
            else:
                # If not processing, show file without horizon detection
                FileDisplayManager.display_file(
                    self.content_area, file_path, None,
                    show_image=show_image, show_horizon=False, show_axis=show_axis,
                    horizon_finder=self.horizon_finder
                )

    def _on_settings_changed(self, settings: dict) -> None:
        """Handle settings panel changes"""
        # Update horizon finder parameters
        self.horizon_finder.update_parameters(settings)
        
        # Refresh display if a file is loaded and we're in processing mode
        file_path = self.file_selection_widget.get_selected_file()
        if file_path:
            self._refresh_display()


def main() -> None:
    """Main application entry point"""
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()