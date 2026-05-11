import sys
import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QFileDialog, 
                             QCheckBox, QTreeWidget, QTreeWidgetItem, QProgressBar, 
                             QMessageBox, QLabel, QSplitter, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap

from scanner import scan_directory

class ScannerThread(QThread):
    progress_updated = pyqtSignal(int)
    scan_finished = pyqtSignal(list)

    def __init__(self, directory, scan_photos, scan_videos):
        super().__init__()
        self.directory = directory
        self.scan_photos = scan_photos
        self.scan_videos = scan_videos

    def run(self):
        duplicates = scan_directory(
            self.directory, 
            self.scan_photos, 
            self.scan_videos, 
            self.update_progress
        )
        self.scan_finished.emit(duplicates)

    def update_progress(self, val):
        self.progress_updated.emit(val)

class DuplicateFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Duplicate Finder & Manager")
        self.resize(800, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Top Panel
        top_panel = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Select a directory to scan...")
        self.dir_input.setReadOnly(True)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_directory)
        
        self.photo_checkbox = QCheckBox("Photos")
        self.photo_checkbox.setChecked(True)
        self.video_checkbox = QCheckBox("Videos")
        self.video_checkbox.setChecked(True)
        
        self.scan_btn = QPushButton("Scan")
        self.scan_btn.clicked.connect(self.start_scan)
        
        top_panel.addWidget(self.dir_input)
        top_panel.addWidget(browse_btn)
        top_panel.addWidget(self.photo_checkbox)
        top_panel.addWidget(self.video_checkbox)
        top_panel.addWidget(self.scan_btn)
        layout.addLayout(top_panel)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Splitter for Tree and Preview
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter)
        
        # Tree Widget for Duplicates
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File / Group", "Size", "Date Modified", "Trash?"])
        self.tree.setColumnWidth(0, 300)
        self.tree.itemSelectionChanged.connect(self.preview_selected_item)
        self.splitter.addWidget(self.tree)
        
        # Preview Area
        self.preview_label = QLabel("Select a file to preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.preview_label.setMinimumWidth(300)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.splitter.addWidget(self.preview_label)
        
        self.splitter.setSizes([500, 300])
        
        # Bottom Panel
        bottom_panel = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.trash_btn = QPushButton("Move Selected to Trash")
        self.trash_btn.clicked.connect(self.move_to_trash)
        self.trash_btn.setEnabled(False)
        
        bottom_panel.addWidget(self.status_label)
        bottom_panel.addStretch()
        bottom_panel.addWidget(self.trash_btn)
        layout.addLayout(bottom_panel)
        
        self.scanner_thread = None
        self.current_duplicates = []
        self.current_directory = ""

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.dir_input.setText(directory)
            self.current_directory = directory

    def start_scan(self):
        if not self.current_directory:
            QMessageBox.warning(self, "Error", "Please select a directory first.")
            return
            
        if not self.photo_checkbox.isChecked() and not self.video_checkbox.isChecked():
            QMessageBox.warning(self, "Error", "Please select at least one file type to scan.")
            return

        self.tree.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.scan_btn.setEnabled(False)
        self.trash_btn.setEnabled(False)
        self.status_label.setText("Scanning...")
        
        self.scanner_thread = ScannerThread(
            self.current_directory, 
            self.photo_checkbox.isChecked(), 
            self.video_checkbox.isChecked()
        )
        self.scanner_thread.progress_updated.connect(self.progress_bar.setValue)
        self.scanner_thread.scan_finished.connect(self.on_scan_finished)
        self.scanner_thread.start()

    def format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def on_scan_finished(self, duplicates):
        self.progress_bar.hide()
        self.scan_btn.setEnabled(True)
        self.current_duplicates = duplicates
        
        if not duplicates:
            self.status_label.setText("No duplicates found.")
            QMessageBox.information(self, "Result", "No duplicates found!")
            return
            
        trash_path = os.path.normpath(os.path.join(self.current_directory, "Trash"))
        self.status_label.setText(f"Found {len(duplicates)} duplicate groups. Trash: {trash_path}")
        self.trash_btn.setEnabled(True)
        
        for i, group in enumerate(duplicates):
            size_str = self.format_size(group['size'])
            group_item = QTreeWidgetItem(self.tree, [f"Group {i+1} - {len(group['files'])} identical files", size_str, "", "", ""])
            group_item.setExpanded(True)
            
            for filepath in group['files']:
                norm_path = os.path.normpath(filepath)
                try:
                    mtime = os.path.getmtime(norm_path)
                    date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                except OSError:
                    date_str = "Unknown"
                    
                display_path = os.path.relpath(norm_path, os.path.normpath(self.current_directory))
                file_item = QTreeWidgetItem(group_item, [display_path, size_str, date_str, ""])
                file_item.setData(0, Qt.ItemDataRole.UserRole, norm_path) # Store full path
                
                # Add built-in Checkbox
                file_item.setFlags(file_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                file_item.setCheckState(3, Qt.CheckState.Unchecked)

    def preview_selected_item(self):
        selected = self.tree.selectedItems()
        if not selected:
            self.preview_label.clear()
            self.preview_label.setText("Select a file to preview")
            return
            
        item = selected[0]
        filepath = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not filepath: # It's a group item
            self.preview_label.clear()
            self.preview_label.setText("Select a specific file to preview")
            return
            
        filepath = os.path.normpath(filepath)
        if not os.path.exists(filepath):
            self.preview_label.clear()
            self.preview_label.setText("File not found")
            return
            
        ext = os.path.splitext(filepath)[1].lower()
        from scanner import PHOTO_EXTENSIONS
        if ext in PHOTO_EXTENSIONS:
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                # Use the available label size for scaling
                label_size = self.preview_label.size()
                if label_size.width() > 5 and label_size.height() > 5:
                    scaled_pixmap = pixmap.scaled(label_size, 
                                                Qt.AspectRatioMode.KeepAspectRatio, 
                                                Qt.TransformationMode.SmoothTransformation)
                    self.preview_label.setPixmap(scaled_pixmap)
                else:
                    self.preview_label.setText("Preview area too small")
            else:
                self.preview_label.clear()
                self.preview_label.setText("Could not load image")
        else:
            self.preview_label.clear()
            self.preview_label.setText(f"Video File:\n{os.path.basename(filepath)}\n\n(Preview not available)")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update preview when window is resized to keep it responsive
        self.preview_selected_item()

    def move_to_trash(self):
        trash_dir = os.path.join(self.current_directory, "Trash")
        
        # Collect files to move
        files_to_move = []
        for i in range(self.tree.topLevelItemCount()):
            group_item = self.tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                file_item = group_item.child(j)
                if file_item.checkState(3) == Qt.CheckState.Checked:
                    filepath = file_item.data(0, Qt.ItemDataRole.UserRole)
                    files_to_move.append((file_item, filepath))
                    
        if not files_to_move:
            QMessageBox.information(self, "Info", "No files selected to move to Trash.")
            return
            
        reply = QMessageBox.question(
            self, 'Confirm', 
            f"Are you sure you want to move {len(files_to_move)} file(s) to the Trash folder?\n({trash_dir})",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if not os.path.exists(trash_dir):
                os.makedirs(trash_dir)
                
            moved_count = 0
            parent_dirs_to_check = set()
            for file_item, filepath in files_to_move:
                if os.path.exists(filepath):
                    filename = os.path.basename(filepath)
                    dest_path = os.path.join(trash_dir, filename)
                    parent_dirs_to_check.add(os.path.dirname(filepath))
                    
                    # Handle name collisions in Trash
                    counter = 1
                    name, ext = os.path.splitext(filename)
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(trash_dir, f"{name}_{counter}{ext}")
                        counter += 1
                        
                    try:
                        shutil.move(filepath, dest_path)
                        moved_count += 1
                        # Remove item from tree
                        file_item.parent().removeChild(file_item)
                    except Exception as e:
                        print(f"Error moving {filepath}: {e}")

            # Check and move empty directories to Trash
            for p_dir in sorted(parent_dirs_to_check, key=len, reverse=True):
                current_p = p_dir
                # Don't trash the root directory or the Trash folder itself
                while current_p and current_p != self.current_directory and os.path.normpath(current_p) != os.path.normpath(trash_dir):
                    if os.path.exists(current_p) and os.path.isdir(current_p) and not os.listdir(current_p):
                        dir_name = os.path.basename(current_p)
                        dest_dir_path = os.path.join(trash_dir, dir_name)
                        
                        # Handle directory name collisions in Trash
                        d_counter = 1
                        while os.path.exists(dest_dir_path):
                            dest_dir_path = os.path.join(trash_dir, f"{dir_name}_{d_counter}")
                            d_counter += 1
                            
                        try:
                            parent_of_current = os.path.dirname(current_p)
                            shutil.move(current_p, dest_dir_path)
                            current_p = parent_of_current # Check the parent next
                        except:
                            break
                    else:
                        break
                        
            # Clean up empty groups
            for i in range(self.tree.topLevelItemCount() - 1, -1, -1):
                group_item = self.tree.topLevelItem(i)
                if group_item.childCount() == 0:
                    self.tree.takeTopLevelItem(i)
                    
            if self.tree.topLevelItemCount() == 0:
                self.trash_btn.setEnabled(False)
                
            QMessageBox.information(self, "Success", f"Moved {moved_count} file(s) to Trash.")
            self.status_label.setText(f"Moved {moved_count} file(s) to Trash.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Optional: Apply a modern style if desired
    app.setStyle("Fusion") 
    
    window = DuplicateFinderApp()
    window.show()
    sys.exit(app.exec())
