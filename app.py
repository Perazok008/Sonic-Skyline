"""Main application entry point for Sonic Skyline.

Wires together the GUI: file selection, visualization toggles, settings panel,
and export dialog. Manages application state for the currently selected file
and the computed horizon line, ensuring preview and export remain consistent.
"""
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QMessageBox
from core.constants import APP_NAME, WINDOW_MIN_SIZE, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from gui.file_selection import FileSelectionManager
from gui.ui_components import create_content_area, create_styled_button, create_button_layout, create_visualization_toggles
from gui.file_display import FileDisplayManager
from gui.finder_settings import FinderSettingsPanel
from gui.export_dialog import ExportDialog
from core.export_manager import ExportManager
from horizon_finder.horizon_finder import HorizonFinder


class MainWindow(QMainWindow):
    """Main application window.

    Responsibilities:
    - Own global state for the current file and computed horizon data
    - Connect UI signals to processing, display refresh, and export
    - Coordinate with `HorizonFinder` and `FileDisplayManager`
    """
    
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()
        self.horizon_finder = HorizonFinder()  # Create horizon_finder before connecting signals
        
        # Track export data
        self.current_horizon_line = None
        self.current_video_horizon_lines = []
        self.is_video_processed = False
        self._has_processed_image = False
        
        self._connect_signals()
    
    def _setup_window(self) -> None:
        """Configure the main window"""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_SIZE)
    
    def _setup_ui(self) -> None:
        """Setup the user interface"""
        # Create main widget and layout container for left content + right settings
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Create horizontal layout for main content and settings panel
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Create left side content layout that hosts file selection, toggles, content, buttons
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Create components
        self.file_selection_widget = FileSelectionManager()
        self.visualization_toggles = create_visualization_toggles()
        self.content_area = create_content_area()
        
        # Create primary action buttons (disabled until a file is picked)
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
        
        # Create settings panel on the right (fixed width)
        self.settings_panel = FinderSettingsPanel()
        
        # Add left content and settings panel to main layout
        # Give the left content area a larger stretch so it grows preferentially
        main_layout.addWidget(left_widget, stretch=4)
        main_layout.addWidget(self.settings_panel, stretch=0)
    
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
        
        # Initialize settings panel with current horizon finder parameters so UI reflects engine defaults
        current_params = self.horizon_finder.get_current_parameters()
        self.settings_panel.set_settings(current_params)
    
    def _on_file_selected(self, file_path: str) -> None:
        """Handle file selection"""
        self._enable_buttons(True)
        # Reset processing state for new selection
        self.current_horizon_line = None
        self.current_video_horizon_lines = []
        self.is_video_processed = False
        self._has_processed_image = False
        show_image, show_horizon, show_axis = self._get_toggle_states()
        # Initial render for images shows no horizon until processing is triggered
        FileDisplayManager.display_file(
            self.content_area, file_path, None, 
            show_image=show_image, show_horizon=False, show_axis=show_axis,
            horizon_finder=self.horizon_finder
        )
    
    def _enable_buttons(self, enabled: bool) -> None:
        """Enable or disable process and export buttons."""
        # Keep buttons in sync with selection availability
        self.process_button.setEnabled(enabled)
        self.export_button.setEnabled(enabled)
        self.connect_ableton.setEnabled(enabled)

    def _process_file(self) -> None:
        """Process the selected file"""
        file_path = self.file_selection_widget.get_selected_file()
        if not file_path:
            QMessageBox.warning(self, "Process Error", "No file selected.")
            return
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Reset export data
        self.current_horizon_line = None
        self.current_video_horizon_lines = []
        self.is_video_processed = False
        self._has_processed_image = False
        
        # For images, process horizon line once and cache it
        # For videos, processing happens continuously during playback
        horizon_line = None
        if file_extension in IMAGE_EXTENSIONS:
            horizon_line = self.horizon_finder.find_horizon_line(file_path)
            self.current_horizon_line = horizon_line
            self._has_processed_image = True
        else:
            # For videos, we'll collect horizon lines during playback
            self.is_video_processed = True
        
        show_image, show_horizon, show_axis = self._get_toggle_states()
        FileDisplayManager.display_file(
            self.content_area, file_path, horizon_line, 
            show_image=show_image, show_horizon=show_horizon, show_axis=show_axis,
            horizon_finder=self.horizon_finder
        )


    def _export_file(self) -> None:
        """Export the processed file"""
        file_path = self.file_selection_widget.get_selected_file()
        if not file_path:
            QMessageBox.warning(self, "Export Error", "No file selected.")
            return
        
        # Check if we have any horizon data available to export
        has_horizon_data = (self.current_horizon_line is not None or 
                           self.current_video_horizon_lines or 
                           self.is_video_processed)
        
        # Show export dialog
        dialog = ExportDialog(current_file=file_path, has_horizon_data=has_horizon_data)
        dialog.export_confirmed.connect(self._handle_export)
        dialog.exec()

    def _handle_export(self, export_config: dict, save_path: str, base_name: str) -> None:
        """Handle export request from dialog"""
        file_path = self.file_selection_widget.get_selected_file()
        
        try:
            # Determine what horizon data to pass
            horizon_line = self.current_horizon_line
            all_horizon_lines = None
            
            # For videos, we need to collect horizon lines if processing in real-time
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension in VIDEO_EXTENSIONS and self.is_video_processed:
                # For videos, we'll need to process all frames for export
                # This is a simplified approach - in a real application you might want to
                # cache the results during playback or show a progress dialog
                all_horizon_lines = self._collect_video_horizon_lines(file_path)
            
            # Perform export
            success = ExportManager.export_results(
                export_config=export_config,
                save_path=save_path,
                base_name=base_name,
                file_path=file_path,
                horizon_line=horizon_line,
                all_horizon_lines=all_horizon_lines
            )
            
            if success:
                QMessageBox.information(
                    self, "Export Complete", 
                    f"Files exported successfully to:\n{save_path}"
                )
            else:
                QMessageBox.warning(
                    self, "Export Error", 
                    "Some files could not be exported. Check the console for details."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, "Export Error", 
                f"Export failed: {str(e)}"
            )

    def _collect_video_horizon_lines(self, file_path: str) -> list[list[int]]:
        """Collect horizon lines for all frames in a video"""
        try:
            import cv2 as cv
            
            horizon_lines = []
            cap = cv.VideoCapture(file_path)
            
            if not cap.isOpened():
                return []
            
            frame_count = 0
            max_frames = 1000  # Hard limit to keep export predictable for very long videos
            
            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                try:
                    # Convert frame to RGB for processing
                    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                    horizon_line = self.horizon_finder.find_horizon_line_from_array(frame_rgb)
                    horizon_lines.append(horizon_line)
                except Exception:
                    # If processing fails, add empty line
                    horizon_lines.append([])
                
                frame_count += 1
            
            cap.release()
            return horizon_lines
            
        except Exception as e:
            print(f"Error collecting video horizon lines: {e}")
            return []

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
        if file_extension in VIDEO_EXTENSIONS:
            # For videos, just update the display settings for ongoing playback
            FileDisplayManager.update_video_display_settings(show_image, show_horizon, show_axis)
        else:
            # For images, reuse cached horizon line if available; don't recompute here
            horizon_line = self.current_horizon_line if self._has_processed_image else None
            FileDisplayManager.display_file(
                self.content_area, file_path, horizon_line,
                show_image=show_image, show_horizon=show_horizon and self._has_processed_image, show_axis=show_axis,
                horizon_finder=self.horizon_finder
            )

    def _on_settings_changed(self, settings: dict) -> None:
        """Handle settings panel changes"""
        # Update horizon finder parameters
        self.horizon_finder.update_parameters(settings)
        
        # Recompute for images to avoid stale previews/exports when settings change
        file_path = self.file_selection_widget.get_selected_file()
        if file_path:
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension in IMAGE_EXTENSIONS:
                try:
                    self.current_horizon_line = self.horizon_finder.find_horizon_line(file_path)
                    self._has_processed_image = True
                except Exception:
                    self.current_horizon_line = None
                    self._has_processed_image = False
            # Refresh display to reflect new settings and cached line
            self._refresh_display()

    def closeEvent(self, event) -> None:
        """Ensure video resources are released when window closes"""
        try:
            FileDisplayManager._stop_video()
        finally:
            return super().closeEvent(event)


def main() -> None:
    """Main application entry point"""
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()