# src/style.py

STYLESHEET = """
QWidget#main_widget { background-color: #2b2d31; border: 1px solid #1e1f22; border-radius: 18px; }
QScrollArea { border: none; border-radius: 16px; background-color: #313338; }
QWidget#scroll_content { background-color: #313338; }
QTextBrowser { background-color: transparent; border: none; color: #dbdee1; font-size: 14px; }
QWidget.bubble_widget { border-radius: 18px; }
QWidget.bubble_widget[role="user"] { background-color: #404eed; }
QWidget.bubble_widget[role="ai"] { background-color: #45475a; }
QWidget#code_container { background-color: #1e1f22; border-radius: 8px; }
QLabel#language_label { color: #8a9099; padding: 2px 8px; font-size: 12px; }
QPushButton#copy_btn { background-color: #313338; color: #d0d0d0; border: none; border-radius: 5px; padding: 4px 8px; font-size: 12px; }
QPushButton#copy_btn:hover { background-color: #45475a; }
QWidget#input_container { background-color: #404eed; border-radius: 12px; }
QLineEdit { background-color: transparent; border: none; padding: 12px; font-size: 15px; color: #ffffff; }
QLineEdit::placeholder-text { color: #bbbcff; }

/* Style du bouton avec l'icône Holo */
QPushButton#add_file_btn {
    background-color: #4f57ff;
    border: none;
    border-radius: 17px; /* La moitié de la taille (34px) pour un cercle parfait */
}
QPushButton#add_file_btn:hover {
    background-color: #6066ff;
}

QWidget#file_preview { background-color: #2b2d31; border-radius: 8px; padding: 8px; }
QLabel#file_name_label { color: #dbdee1; font-weight: bold; }
QPushButton#close_preview_btn {
    background-color: #45475a; color: #dbdee1; border: none;
    border-radius: 9px; font-weight: bold; font-size: 14px;
    min-width: 18px; max-width: 18px; min-height: 18px; max-height: 18px;
}
QPushButton#close_preview_btn:hover { background-color: #c42b1c; color: white; }

pre { padding: 5px; margin: 0px; white-space: pre-wrap; word-wrap: break-word; }
QScrollBar:vertical { border: none; background: #313338; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #1e1f22; min-height: 20px; border-radius: 4px; }
"""