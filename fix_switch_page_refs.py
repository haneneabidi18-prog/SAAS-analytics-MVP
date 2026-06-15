"""
Corrige les references st.switch_page() vers d'anciens noms de fichiers
avec emoji, qui n'existent plus depuis le renommage des pages.

Usage : place ce fichier a la racine de ton projet (ou ~/streamlit-analytics)
et lance : python3 fix_switch_page_refs.py
"""

import os

RENAMES = {
    "pages/1_Dashboard.py":        "pages/1_Dashboard.py",
    "pages/2_QoE_Score.py":         "pages/2_QoE_Score.py",
    "pages/3_AI_Decision_Engine.py": "pages/3_AI_Decision_Engine.py",
    "pages/4_AI_Copilot.py":        "pages/4_AI_Copilot.py",
}

ROOT = "."

changed_files = []

for dirpath, _, filenames in os.walk(ROOT):
    if "venv" in dirpath or ".git" in dirpath:
        continue
    for fname in filenames:
        if not fname.endswith(".py"):
            continue
        path = os.path.join(dirpath, fname)
        try:
            content = open(path, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue

        original = content
        for old, new in RENAMES.items():
            content = content.replace(old, new)

        if content != original:
            open(path, "w", encoding="utf-8").write(content)
            changed_files.append(path)

if changed_files:
    print("Fichiers corriges :")
    for f in changed_files:
        print(f"  - {f}")
else:
    print("Aucun fichier modifie.")
