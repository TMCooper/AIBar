#!/bin/bash

# Met un titre dans le terminal (ne fonctionne pas dans tous les terminaux)
echo -ne "\033]0;Lanceur d'application Python\007"

# --- VERIFICATIONS ---
# Vérifie si le dossier de l'environnement virtuel existe
if [ ! -f "./AIBar/bin/activate" ]; then
    echo "[ERREUR] Environnement virtuel 'AIBar' introuvable. Création en cours..."
    python3 -m venv AIBar
fi

# Vérifie si le fichier requirements.txt existe
if [ ! -f "requirements.txt" ]; then
    echo "[ERREUR] Le fichier 'requirements.txt' est introuvable."
    exit 1
fi

# Vérifie si le fichier main.py existe
if [ ! -f "main.py" ]; then
    echo "[ERREUR] Le script principal 'main.py' est introuvable."
    exit 1
fi

# --- EXECUTION ---
echo "[1/3] Activation de l'environnement virtuel..."
source ./AIBar/bin/activate

echo
echo "[2/3] Installation des dépendances depuis requirements.txt..."
pip install -r requirements.txt

# Vérifie si l'installation a réussi
if [ $? -ne 0 ]; then
    echo "[ERREUR] L'installation des dépendances a échoué."
    exit 1
fi

echo
echo "--------------------------------------------------"
echo
echo "Le script est terminé. Appuyez sur Entrée pour quitter."
read
