# main.py

import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# print(f"DEBUG: Racine du projet ajoutée au chemin de recherche -> {project_root}")

import keyboard
from dotenv import load_dotenv
import google.generativeai as genai

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from src.command_bar import CommandBar


class HotkeyEmitter(QObject):
    show_command_bar_signal = Signal()

command_bar_instance = None
chat_session = None

def show_command_bar():
    global command_bar_instance, chat_session
    if not command_bar_instance:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        chat_session = model.start_chat(history=[])
        command_bar_instance = CommandBar(chat_session)
    command_bar_instance.show_and_focus()

def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Erreur: Clé API 'GEMINI_API_KEY' manquante dans le fichier .env")
        return
    genai.configure(api_key=api_key)
    
    app = QApplication(sys.argv)
    
    emitter = HotkeyEmitter()
    emitter.show_command_bar_signal.connect(show_command_bar)
    
    print("Programme en arrière-plan. Raccourci : ctrl+shift+a")
    keyboard.add_hotkey('ctrl+shift+a', lambda: emitter.show_command_bar_signal.emit())
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()