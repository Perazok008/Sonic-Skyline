from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QLabel, QMessageBox)
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont
from gui.file_selection import FileSelectionWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sonic Skyline")
        self.setFixedSize(QSize(800, 600))
        
        # Create the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Create main vertical layout
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Create file selection widget
        self.file_selection_widget = FileSelectionWidget()
        self.file_selection_widget.file_selected.connect(self.on_file_selected)
        
        # Create main content area
        self.content_area = QLabel()
        self.content_area.setMinimumSize(QSize(760, 400))
        self.content_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #cccccc;
                background-color: #f9f9f9;
                border-radius: 10px;
            }
        """)
        self.content_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_area.setText("Select a file to display content here")
        self.content_area.setFont(QFont("Arial", 12))
        
        # Create button section
        from PyQt6.QtWidgets import QHBoxLayout
        button_section_layout = QHBoxLayout()
        
        self.process_button = QPushButton("Process")
        self.process_button.setFont(QFont("Arial", 10))
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.process_file)
        
        self.export_button = QPushButton("Export")
        self.export_button.setFont(QFont("Arial", 10))
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_file)
        
        button_section_layout.addStretch()
        button_section_layout.addWidget(self.process_button)
        button_section_layout.addWidget(self.export_button)
        
        # Add all sections to main layout
        main_layout.addWidget(self.file_selection_widget)
        main_layout.addWidget(self.content_area)
        main_layout.addLayout(button_section_layout)
    
    def on_file_selected(self, file_path):
        """Handle file selection from the file selection widget"""
        # Enable process and export buttons
        self.process_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
        # Display the selected file using the widget's display method
        self.file_selection_widget.display_file_in_area(self.content_area, file_path)
    
    def process_file(self):
        """Process the selected file"""
        selected_file = self.file_selection_widget.get_selected_file()
        if selected_file:
            import os
            QMessageBox.information(
                self,
                "Process",
                f"Processing file: {os.path.basename(selected_file)}\n\n(Processing functionality to be implemented)"
            )
        else:
            QMessageBox.warning(self, "Warning", "No file selected!")
    
    def export_file(self):
        """Export the processed file"""
        selected_file = self.file_selection_widget.get_selected_file()
        if selected_file:
            import os
            QMessageBox.information(
                self,
                "Export",
                f"Exporting file: {os.path.basename(selected_file)}\n\n(Export functionality to be implemented)"
            )
        else:
            QMessageBox.warning(self, "Warning", "No file selected!")

app = QApplication([])
window = MainWindow()

window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()