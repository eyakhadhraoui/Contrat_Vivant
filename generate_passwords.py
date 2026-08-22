import bcrypt
import json

users_passwords = {
    'G123': 'password123',
    'G456': 'password456',
    'G789': 'password789',
    'G321': 'password321'
}

with open('data/gestionnaires.json', encoding='utf-8') as f:
    gestionnaires = json.load(f)

for g in gestionnaires:
    plain = users_passwords[g['id']]
    g['password_hash'] = bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

with open('data/gestionnaires.json', 'w', encoding='utf-8') as f:
    json.dump(gestionnaires, f, ensure_ascii=False, indent=2)

print('Mots de passe regeneres.')
