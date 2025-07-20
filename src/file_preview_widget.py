# src/file_preview_widget.py
# Owner TMCooper

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

class FilePreviewWidget(QWidget):
    removed = Signal()
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.setObjectName("file_preview")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        icon_label = QLabel("📄")
        filename_label = QLabel(filename)
        filename_label.setObjectName("file_name_label")
        
        close_button = QPushButton("\u2715")
        close_button.setObjectName("close_preview_btn")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout.addWidget(icon_label)
        layout.addWidget(filename_label, 1)
        layout.addWidget(close_button)
        
        close_button.clicked.connect(self.removed.emit)