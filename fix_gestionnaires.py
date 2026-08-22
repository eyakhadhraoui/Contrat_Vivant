import json

gestionnaires = [
    {
        "id": "G123",
        "username": "ahmed.trabelsi",
        "email": "eya.khadhraoui@esprit.tn",
        "password_hash": "",
        "role": "sinistres"
    },
    {
        "id": "G456",
        "username": "sarra.khelifi",
        "email": "eyakhadhraoui249@gmail.com",
        "password_hash": "",
        "role": "assurances"
    }
]

with open("data/gestionnaires.json", "w", encoding="utf-8") as f:
    json.dump(gestionnaires, f, ensure_ascii=False, indent=2)

print("Fichier recréé avec succès.")