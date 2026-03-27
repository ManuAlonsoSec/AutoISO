import sys
import argparse
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QCheckBox, QPushButton, 
                             QFileDialog, QProgressBar, QGridLayout, QMessageBox,
                             QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QSize
from qt_material import apply_stylesheet
from config import ConfigManager
from downloader import DownloadThread

class ISOAutomatorApp(QMainWindow):
    def __init__(self, start_hidden=False, auto_start=False):
        super().__init__()
        self.config_manager = ConfigManager()
        self.download_thread = None
        self.distro_widgets = {}
        
        self.init_ui()
        
        # When started by Windows Registry upon login
        if auto_start:
            self.start_update()
            
    def init_ui(self):
        self.setWindowTitle("ISO Autoupdate")
        self.setMinimumSize(QSize(650, 450))

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title Label
        title_label = QLabel("ISO Autoupdater")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Settings Group
        settings_frame = QFrame()
        settings_frame.setFrameShape(QFrame.Shape.StyledPanel)
        settings_layout = QVBoxLayout(settings_frame)
        
        # Directory Selection
        path_layout = QHBoxLayout()
        self.path_label = QLabel(f"<b>Download Directory:</b><br>{self.config_manager.get('download_dir')}")
        self.path_label.setWordWrap(True)
        path_btn = QPushButton("Change Directory")
        path_btn.clicked.connect(self.change_directory)
        path_btn.setMinimumWidth(150)
        
        path_layout.addWidget(self.path_label, stretch=1)
        path_layout.addWidget(path_btn)
        
        # Startup Checkbox
        self.startup_cb = QCheckBox("Run at Login (Startup)")
        self.startup_cb.setChecked(self.config_manager.get("run_at_startup"))
        self.startup_cb.toggled.connect(self.toggle_startup)
        self.startup_cb.setStyleSheet("margin-top: 10px;")
        
        # Download Betas Checkbox
        self.betas_cb = QCheckBox("Download Beta/RC versions")
        self.betas_cb.setChecked(bool(self.config_manager.get("download_betas")))
        self.betas_cb.toggled.connect(self.toggle_betas)

        settings_layout.addLayout(path_layout)
        settings_layout.addWidget(self.startup_cb)
        settings_layout.addWidget(self.betas_cb)
        main_layout.addWidget(settings_frame)

        # Distro Grid Title
        main_layout.addWidget(QLabel("<b>Select distributions to keep updated:</b>"))

        # Distro Grid frame (uses QGridLayout for clean alignment)
        grid_frame = QFrame()
        self.grid_layout = QGridLayout(grid_frame)
        self.grid_layout.setSpacing(10)
        
        distros = self.config_manager.get("distros")
        
        # Generate rows for each supported distribution
        row = 0
        for name, enabled in distros.items():
            # Checkbox
            cb = QCheckBox(name)
            cb.setChecked(enabled)
            cb.toggled.connect(self.save_distro_selections)
            cb.setMinimumWidth(100)
            
            # Status Text
            status_label = QLabel("Idle")
            status_label.setMinimumWidth(150)
            
            # Progress Bar
            progress = QProgressBar()
            progress.setValue(0)
            progress.setTextVisible(True)
            
            self.grid_layout.addWidget(cb, row, 0)
            self.grid_layout.addWidget(status_label, row, 1)
            self.grid_layout.addWidget(progress, row, 2)
            
            self.distro_widgets[name] = {
                "checkbox": cb,
                "status": status_label,
                "progress": progress
            }
            row += 1
            
        main_layout.addWidget(grid_frame)

        # Push elements to the top
        main_layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Check & Update Now")
        self.start_btn.setMinimumHeight(45)
        self.start_btn.clicked.connect(self.start_update)
        # Style strictly for material theme button pop
        self.start_btn.setProperty('class', 'success')
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(45)
        self.cancel_btn.clicked.connect(self.cancel_update)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setProperty('class', 'danger')
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.start_btn, stretch=1)
        
        main_layout.addLayout(btn_layout)

    def change_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Download Directory", 
            self.config_manager.get("download_dir")
        )
        if dir_path:
            self.config_manager.set("download_dir", dir_path)
            self.path_label.setText(f"<b>Download Directory:</b><br>{dir_path}")

    def toggle_startup(self, state):
        self.config_manager.set_startup(state)

    def toggle_betas(self, state):
        self.config_manager.set("download_betas", state)

    def save_distro_selections(self):
        distros = self.config_manager.get("distros")
        for name, widgets in self.distro_widgets.items():
            distros[name] = widgets["checkbox"].isChecked()
        self.config_manager.set("distros", distros)

    def start_update(self):
        selected_distros = [name for name, widgets in self.distro_widgets.items() 
                            if widgets["checkbox"].isChecked()]
        
        if not selected_distros:
            QMessageBox.warning(self, "No Distro Selected", "Please select at least one distribution to update.")
            return

        self.start_btn.setEnabled(False)
        self.start_btn.setText("Updating...")
        self.cancel_btn.setEnabled(True)

        for name in selected_distros:
            self.distro_widgets[name]["progress"].setValue(0)
            self.distro_widgets[name]["status"].setText("Queued...")
            
        for name, widgets in self.distro_widgets.items():
            if not widgets["checkbox"].isChecked():
                self.distro_widgets[name]["status"].setText("Skipped")
                self.distro_widgets[name]["progress"].setValue(0)

        # Initiate downloader thread
        self.download_thread = DownloadThread(selected_distros, self.config_manager.get("download_dir"), self.config_manager.get("download_betas"))
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.status_updated.connect(self.update_status)
        self.download_thread.finished.connect(self.all_tasks_finished)
        self.download_thread.start()

    def cancel_update(self):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.cancel_btn.setEnabled(False)
            self.start_btn.setText("Canceling...")

    def update_progress(self, distro, percent):
        self.distro_widgets[distro]["progress"].setValue(percent)

    def update_status(self, distro, msg):
        self.distro_widgets[distro]["status"].setText(msg)

    def all_tasks_finished(self):
        self.start_btn.setEnabled(True)
        self.start_btn.setText("Check & Update Now")
        self.cancel_btn.setEnabled(False)
        QMessageBox.information(self, "Update Complete", "Finished checking and downloading updates.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ISO Autoupdate tool")
    parser.add_argument("--startup", action="store_true", help="Launch app automatically via system startup")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    
    # Apply a modern dark theme using qt-material
    # Dark teal offers a very professional dark gray layout with teal accent colors
    apply_stylesheet(app, theme='dark_teal.xml', invert_secondary=False)

    # Initialize Main application Window
    auto_start = getattr(args, 'startup', False)
    window = ISOAutomatorApp(start_hidden=False, auto_start=auto_start)
    window.show()

    sys.exit(app.exec())
