import sys
import os
import keyboard
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal

# On importe la fenêtre principale depuis notre dossier src
from src.command_bar import CommandBar

# --- GESTIONNAIRE DE RACCOURCI CLAVIER (INCHANGÉ) ---
class HotkeyEmitter(QObject):
    """
    Objet simple qui émet un signal Qt depuis un thread non-Qt (celui du hook clavier).
    """
    show_command_bar_signal = Signal()

# --- GESTION DE L'INSTANCE DE LA FENÊTRE ---
# Garde une référence à notre fenêtre pour ne pas en créer plusieurs.
command_bar_instance = None

def show_command_bar():
    """
    Crée la fenêtre si elle n'existe pas, puis l'affiche.
    """
    global command_bar_instance
    if not command_bar_instance:
        # Notez qu'on ne passe plus de "chat_session"
        command_bar_instance = CommandBar()
    
    command_bar_instance.show_and_focus()

def main():
    """
    Point d'entrée de l'application.
    """
    app = QApplication(sys.argv)

    # Crée un émetteur pour communiquer entre le hook clavier et l'application Qt
    emitter = HotkeyEmitter()
    emitter.show_command_bar_signal.connect(show_command_bar)

    print("Programme en arrière-plan. Appuyez sur 'ctrl+shift+a' pour afficher la barre de commande.")
    
    # Ajoute le raccourci clavier global qui déclenche le signal
    keyboard.add_hotkey('ctrl+shift+a', lambda: emitter.show_command_bar_signal.emit())

    sys.exit(app.exec())

if __name__ == "__main__":
    main()