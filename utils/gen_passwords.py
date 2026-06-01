"""
Utilitaire pour générer les hash de mots de passe.
Usage : python3 utils/gen_passwords.py
"""
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Utilisateurs de démonstration
users = [
    ("admin",   "Admin StreamAnalytics", "admin@streamanalytics.pro",   "admin123",   "premium"),
    ("hanene",  "Hanene Abidi",          "hanene@streamanalytics.pro",   "abc123",     "premium"),
    ("demo",    "Demo Client",           "demo@streamanalytics.pro",     "demo2024",   "basic"),
    ("client1", "Client Basic",          "client1@example.com",          "client123",  "basic"),
]

print("# Copiez ce bloc dans .streamlit/secrets.toml\n")
print("[users]")
for username, display, email, pwd, plan in users:
    h = hash_password(pwd)
    print(f"\n[users.{username}]")
    print(f'password_hash = "{h}"')
    print(f'plan = "{plan}"')
    print(f'display_name = "{display}"')
    print(f'email = "{email}"')

print("\n# ─────────────────────────────────────────")
print("# Résumé des comptes créés :")
for username, display, email, pwd, plan in users:
    print(f"# {username} / {pwd} → {plan}")
