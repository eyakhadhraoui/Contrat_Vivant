import bcrypt
import json

users = [
    ('ahmed.trabelsi', 'password123'),
    ('sarra.khelifi', 'password123'),
    ('karim.bouazizi', 'password123'),
    ('lina.mansour', 'password123')
]

print("Generated password hashes:")
for username, password in users:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    print(f"{username}: {hashed.decode('utf-8')}")
