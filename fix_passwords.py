import json
import bcrypt

# Génère les hashs
users_with_passwords = {
    'ahmed.trabelsi': 'password123',
    'sarra.khelifi': 'password123',
    'karim.bouazizi': 'password123',
    'lina.mansour': 'password123'
}

# Charger les gestionnaires actuels
with open('data/gestionnaires.json', 'r', encoding='utf-8-sig') as f:
    gestionnaires = json.load(f)

# Mettre à jour les hashs
for gestionnaire in gestionnaires:
    username = gestionnaire['username']
    if username in users_with_passwords:
        password = users_with_passwords[username]
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        gestionnaire['password_hash'] = hashed.decode('utf-8')

# Sauvegarder
with open('data/gestionnaires.json', 'w', encoding='utf-8') as f:
    json.dump(gestionnaires, f, indent=2, ensure_ascii=False)

print("✓ gestionnaires.json mis à jour avec les hashs bcrypt")
