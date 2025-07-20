# src/command_bar.py
# Owner TMCooper

import os
import io
import re
import sys
import markdown
from PIL import Image
from pygments.formatters import HtmlFormatter

from PySide6.QtCore import (Qt, QObject, Signal, QThread, QTimer, QPoint, 
                            QEasingCurve, QPropertyAnimation, QRect, QSize)
from PySide6.QtGui import QKeySequence, QImage, QIcon
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLineEdit, QLabel, QScrollArea, QTextBrowser, 
                               QPushButton, QFileDialog)

from src.styles import STYLESHEET
from src.file_preview_widget import FilePreviewWidget

def resource_path(relative_path):
    """ Obtient le chemin absolu vers une ressource, fonctionne pour le dev et pour PyInstaller. """
    try:
        # PyInstaller crée un dossier temporaire et y stocke le chemin dans _MEIPASS.
        base_path = sys._MEIPASS
    except Exception:
        # _MEIPASS n'est pas défini, nous sommes en mode développement.
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class BlockStreamer(QObject):
    """
    Affiche le texte bloc par bloc (paragraphe par paragraphe)
    avec un effet de fondu enchaîné.
    """
    stream_finished = Signal()

    def __init__(self, browser: QTextBrowser, markdown_text: str, parent=None):
        super().__init__(parent)
        self.browser = browser
        # On divise le texte en blocs en se basant sur les doubles sauts de ligne
        self.blocks_to_display = markdown_text.split('\n\n')
        self.displayed_blocks = []
        self.timer = QTimer(self)

    def start(self):
        # Un intervalle un peu plus long pour laisser le temps de lire chaque bloc
        self.timer.setInterval(350) 
        self.timer.timeout.connect(self._add_block)
        self.timer.start()

    def _add_block(self):
        if self.blocks_to_display:
            # On ajoute le prochain bloc à la liste de ceux déjà affichés
            next_block = self.blocks_to_display.pop(0)
            self.displayed_blocks.append(next_block)
            
            # On reconstruit le texte Markdown et on le convertit en HTML
            current_markdown = "\n\n".join(self.displayed_blocks)
            html_to_display = markdown.markdown(current_markdown)
            
            # On met à jour le contenu du navigateur
            self.browser.setHtml(html_to_display)
        else:
            # Quand il n'y a plus de blocs, on s'arrête
            self.timer.stop()
            self.stream_finished.emit()

class GeminiWorker(QObject):
    finished = Signal(str)
    error = Signal(str)
    def __init__(self, chat_session, prompt_parts):
        super().__init__()
        self.chat_session = chat_session
        self.prompt_parts = prompt_parts
    def run(self):
        try:
            response = self.chat_session.send_message(self.prompt_parts)
            self.finished.emit(response.text)
        except Exception as e:
            print(f"Erreur API Gemini : {e}")
            self.error.emit(f"Une erreur est survenue : {e}")

class CommandBar(QWidget):
    def __init__(self, chat_session):
        super().__init__()
        self.chat_session = chat_session
        self.is_processing = False
        self.file_to_send = None
        self.drag_position = None
        self.file_preview_widget = None
        self.init_ui()
        self.setAcceptDrops(True)
        self.setWindowOpacity(0.0)

    def init_ui(self):
        self.setObjectName("main_widget")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(STYLESHEET) # Utilisation du style importé

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content_widget = QWidget()
        self.scroll_content_widget.setObjectName("scroll_content")
        self.scroll_layout = QVBoxLayout(self.scroll_content_widget)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content_widget)
        self.scroll_area.hide()
        
        self.bottom_container = QWidget(self)
        self.bottom_layout = QVBoxLayout(self.bottom_container)
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setSpacing(0)
        
        self.input_area_widget = QWidget(self)
        self.input_area_widget.setObjectName("input_container")
        self.input_area_layout = QVBoxLayout(self.input_area_widget)
        self.input_area_layout.setContentsMargins(5, 5, 5, 5)
        self.input_area_layout.setSpacing(8)
        
        input_line_layout = QHBoxLayout()
        
        self.add_file_btn = QPushButton()
        self.add_file_btn.setObjectName("add_file_btn")
        self.add_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_file_btn.clicked.connect(self.open_file_dialog)
        
        icon_path = resource_path('ressources/images/holo_icon.png')
        icon = QIcon(icon_path)
        self.add_file_btn.setIcon(icon)
        self.add_file_btn.setIconSize(QSize(26, 26))
        self.add_file_btn.setFixedSize(34, 34)
        
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Poser une question à Gemini...")
        self.input_field.returnPressed.connect(self.process_input)
        
        input_line_layout.addWidget(self.add_file_btn)
        input_line_layout.addWidget(self.input_field)
        
        self.input_area_layout.addLayout(input_line_layout)
        self.bottom_layout.addWidget(self.input_area_widget)
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.bottom_container)

    def run_show_animation(self):
        self.pos_anim = QPropertyAnimation(self, b"pos")
        start_pos = self.pos()
        self.pos_anim.setStartValue(QPoint(start_pos.x(), start_pos.y() - 40))
        self.pos_anim.setEndValue(start_pos)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.pos_anim.setDuration(300)
        
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.setDuration(250)
        
        self.pos_anim.start()
        self.opacity_anim.start()

    def animate_window_expansion(self):
        self.scroll_area.show()
        start_geo = self.geometry()
        end_geo = QRect(start_geo.x(), start_geo.y(), start_geo.width(), 600)
        self.expand_anim = QPropertyAnimation(self, b"geometry")
        self.expand_anim.setStartValue(start_geo)
        self.expand_anim.setEndValue(end_geo)
        self.expand_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.expand_anim.setDuration(400)
        self.expand_anim.start()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        self.drag_position = None
        event.accept()
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        if urls := event.mimeData().urls():
            self.handle_file(urls[0].toLocalFile())
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.matches(QKeySequence.StandardKey.Paste):
            if cb := QApplication.clipboard():
                if cb.mimeData().hasImage():
                    self.handle_file(cb.image())
        else:
            super().keyPressEvent(event)

    def handle_file(self, file_data):
        IMAGE_EXTS = ['.png', '.jpg', '.jpeg', '.webp', '.bmp']
        TEXT_EXTS = ['.txt', '.py', '.js', '.html', '.css', '.json', '.md', '.log']
        try:
            if isinstance(file_data, str):
                filename = os.path.basename(file_data)
                _, ext = os.path.splitext(filename.lower())
                if ext in IMAGE_EXTS:
                    img = Image.open(file_data)
                    self.file_to_send = {'type': 'image', 'data': img, 'name': filename}
                    self.show_file_preview(filename)
                elif ext in TEXT_EXTS:
                    with open(file_data, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    self.file_to_send = {'type': 'text', 'data': content, 'name': filename}
                    self.show_file_preview(filename)
                else:
                    self.add_message_to_view(f"Type de fichier non supporté : {filename}", "ai")
            elif isinstance(file_data, QImage):
                buffer = io.BytesIO()
                file_data.save(buffer, "PNG")
                img_pil = Image.open(io.BytesIO(buffer.getvalue()))
                self.file_to_send = {'type': 'image', 'data': img_pil, 'name': 'capture.png'}
                self.show_file_preview('Capture d\'écran')
            self.input_field.setFocus()
        except Exception as e:
            self.add_message_to_view(f"Impossible de lire le fichier : {e}", "ai")
    
    def open_file_dialog(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Sélectionner un fichier")
        if file_paths:
            self.handle_file(file_paths[0])
        
    def show_file_preview(self, filename):
        if self.file_preview_widget:
            self.remove_file_preview()
        self.file_preview_widget = FilePreviewWidget(filename, self.input_area_widget)
        self.file_preview_widget.removed.connect(self.remove_file_preview)
        self.input_area_layout.insertWidget(0, self.file_preview_widget)
        self.input_field.setPlaceholderText("Ajoutez un commentaire sur le fichier...")

    def remove_file_preview(self):
        if self.file_preview_widget:
            self.file_to_send = None
            self.file_preview_widget.deleteLater()
            self.file_preview_widget = None
            self.input_field.setPlaceholderText("Poser une question à Gemini...")

    def add_message_to_view(self, text, role):
        bubble = QWidget()
        bubble.setObjectName("bubble_widget")
        bubble.setProperty("role", role)
        bubble.setMaximumWidth(self.width() * 0.80)
        
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 12, 12, 12)
        
        message_browser = QTextBrowser()
        message_browser.setHtml(text)
        message_browser.setReadOnly(True)
        message_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        message_browser.document().documentLayout().documentSizeChanged.connect(lambda size: message_browser.setFixedHeight(int(size.height())))
        
        bubble_layout.addWidget(message_browser)
        
        if role == 'user':
            self.scroll_layout.addWidget(bubble, alignment=Qt.AlignmentFlag.AlignRight)
        else:
            self.scroll_layout.addWidget(bubble, alignment=Qt.AlignmentFlag.AlignLeft)
            
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))
        return message_browser

    def add_code_block(self, raw_code, lang):
        container = QWidget()
        container.setObjectName("code_container")
        container.setMaximumWidth(self.width() * 0.85)
        
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(0)
        
        top_bar_layout = QHBoxLayout()
        lang_label = QLabel(lang if lang else "code")
        lang_label.setObjectName("language_label")
        copy_btn = QPushButton("Copier")
        copy_btn.setObjectName("copy_btn")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(raw_code, copy_btn))
        
        top_bar_layout.addWidget(lang_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(copy_btn)
        
        formatter_callable = lambda **kwargs: HtmlFormatter(style='monokai', nobackground=True, noclasses=True)
        html_code = markdown.markdown(
            f"```{lang}\n{raw_code}\n```",
            extensions=['fenced_code', 'codehilite'],
            extension_configs={'codehilite': {'pygments_formatter': formatter_callable}}
        )
        
        code_browser = QTextBrowser()
        code_browser.setHtml(html_code)
        code_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        code_browser.document().documentLayout().documentSizeChanged.connect(lambda size: code_browser.setFixedHeight(int(size.height())))
        
        container_layout.addLayout(top_bar_layout)
        container_layout.addWidget(code_browser)
        
        self.scroll_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignLeft)
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def copy_to_clipboard(self, text, button):
        QApplication.clipboard().setText(text)
        original_text = button.text()
        button.setText("Copié !")
        QTimer.singleShot(1200, lambda: button.setText(original_text))

    def on_gemini_result(self, response_text):
        code_pattern = re.compile(r"```(\w*)\n([\s\S]*?)```")
        last_index = 0
        text_parts = []
        for match in code_pattern.finditer(response_text):
            text_part = response_text[last_index:match.start()].strip()
            if text_part:
                text_parts.append(text_part)
            lang = match.group(1)
            raw_code = match.group(2)
            self.add_code_block(raw_code, lang)
            last_index = match.end()
            
        remaining_text = response_text[last_index:].strip()
        if remaining_text:
            text_parts.append(remaining_text)
            
        if text_parts:
            full_text = "\n\n".join(text_parts)
            ai_browser = self.add_message_to_view("", "ai")
            self.streamer = BlockStreamer(ai_browser, full_text) 
            self.streamer.stream_finished.connect(lambda: setattr(self, 'is_processing', False))
            self.streamer.start()
        else:
            self.is_processing = False

    def process_input(self):
        demande = self.input_field.text().strip()
        if demande.lower() == "exit":
            QApplication.quit()
            return
        if self.is_processing or (not demande and not self.file_to_send):
            return
        if not self.scroll_area.isVisible():
            self.animate_window_expansion()
            
        self.is_processing = True
        prompt_parts = []
        message_html = ""
        
        if file_info := self.file_to_send:
            if file_info['type'] == 'image':
                prompt_parts.append(file_info['data'])
                message_html += f"<i>[Image : {file_info['name']}]</i><br>"
            elif file_info['type'] == 'text':
                formatted_text = f"Analyse le contenu du fichier '{file_info['name']}':\n---\n{file_info['data']}\n---"
                prompt_parts.append(formatted_text)
                message_html += f"<i>[Fichier : {file_info['name']}]</i><br>"
                
        if demande:
            prompt_parts.append(demande)
            safe_html = demande.replace('&', '&').replace('<', '<').replace('>', '>')
            message_html += safe_html
            
        if message_html:
            self.add_message_to_view(message_html, "user")
            
        self.input_field.clear()
        self.remove_file_preview()
        
        self.worker = GeminiWorker(self.chat_session, prompt_parts)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_gemini_result)
        self.worker.error.connect(self.on_gemini_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        
    def on_gemini_error(self, error_text):
        self.add_message_to_view(f"<i>Erreur : {error_text}</i>", "ai")
        self.is_processing = False
    
    def clear_chat_view(self):
        while self.scroll_layout.count():
            item_to_remove = self.scroll_layout.takeAt(0)
            if widget := item_to_remove.widget():
                widget.deleteLater()

    def show_and_focus(self):
        self.clear_chat_view()
        self.remove_file_preview()
        if self.chat_session:
            self.chat_session.history.clear()
            
        self.scroll_area.hide()
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(int((screen_geometry.width() - 700) / 2), int((screen_geometry.height() - 80) / 4), 700, 80)
        self.setMaximumHeight(800)
        self.show()
        self.activateWindow()
        self.raise_()
        QTimer.singleShot(50, self.input_field.setFocus)
        self.run_show_animation()