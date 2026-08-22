from tools.auth_tool import login, verify_token

# simulation d'une connexion
token = login("ahmed.trabelsi", "password123")
print("Token généré :", token)

# vérification du token (ce que fera auth_node.py)
payload = verify_token(token)
print("Contenu du token :", payload)