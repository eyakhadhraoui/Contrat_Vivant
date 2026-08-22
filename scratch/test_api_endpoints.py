"""
Script de test complet pour valider la persistance MySQL, le signup et l'enforcement des rôles (RBAC).
"""
import sys
from fastapi.testclient import TestClient
from api.main_api import app
from tools.auth_tool import login

client = TestClient(app)

def test_all():
    print("=== 1. Test GET /api/agences ===")
    r = client.get("/api/agences")
    assert r.status_code == 200, f"Erreur agences: {r.text}"
    agences = r.json().get("agences", [])
    print(f"Agences trouvées: {len(agences)}")
    assert len(agences) >= 2

    print("\n=== 2. Test Inscription (Signup) ===")
    import random
    rand_user = f"user_test_{random.randint(1000, 9999)}"
    signup_data = {
        "nom": "TestNom",
        "prenom": "TestPrenom",
        "username": rand_user,
        "email": f"{rand_user}@test.tn",
        "password": "password123",
        "role": "assurances",
        "agence_id": "AG01"
    }
    r = client.post("/api/signup", json=signup_data)
    assert r.status_code == 200, f"Erreur signup: {r.text}"
    token_assurances = r.json().get("token")
    print(f"Signup réussi, token reçu: {token_assurances[:15]}...")

    # Test duplicate username (409 Conflict)
    r_dup = client.post("/api/signup", json=signup_data)
    assert r_dup.status_code == 409, f"Doit renvoyer 409 Conflict sur doublon: {r_dup.status_code}"
    print("Test 409 Conflict sur doublon : PASS")

    print("\n=== 3. Test Connexion Utilisateurs Existants ===")
    token_sinistres = login("ahmed.trabelsi", "password123")
    assert token_sinistres, "Login ahmed.trabelsi (sinistres) a échoué"
    print("Login sinistres réussi !")

    headers_assurances = {"Authorization": f"Bearer {token_assurances}"}
    headers_sinistres = {"Authorization": f"Bearer {token_sinistres}"}

    print("\n=== 4. Test RBAC sur Création de Contrat ===")
    contrat_payload = {
        "id": f"CSTR{random.randint(10000, 99999)}",
        "client_id": "CL01",
        "type_contrat": "auto",
        "garantie_max": 500000,
        "date_debut": "2026-01-01",
        "date_fin": "2027-01-01",
        "statut": "actif"
    }

    # Test Création Contrat par gestionnaire connecté
    r_ok = client.post("/api/contrats", json=contrat_payload, headers=headers_assurances)
    assert r_ok.status_code == 200, f"Erreur création contrat: {r_ok.text}"
    print(f"Création contrat réussie: {r_ok.json()}")

    print("\n=== 5. Test Création et Modification de Sinistre ===")
    sinistre_payload = {
        "id": f"CSIN{random.randint(10000, 99999)}",
        "contrat_id": "CSTR00003",
        "type_sinistre": "Auto - Carambolage",
        "montant_declare": 15000,
        "date_declaration": "2026-08-01",
        "statut": "en_cours"
    }

    # Test Création Sinistre par gestionnaire connecté
    r_sin_ok = client.post("/api/sinistres", json=sinistre_payload, headers=headers_sinistres)
    assert r_sin_ok.status_code == 200, f"Erreur création sinistre: {r_sin_ok.text}"
    print(f"Création sinistre réussie: {r_sin_ok.json()}")


    print("\n=== 6. Test GET /api/alerts et /api/historique ===")
    r_alerts = client.get("/api/alerts", headers=headers_assurances)
    assert r_alerts.status_code == 200
    print(f"Alertes in-app récupérées: {len(r_alerts.json().get('alerts', []))}")

    r_hist = client.get("/api/historique", headers=headers_assurances)
    assert r_hist.status_code == 200
    print(f"Historique MySQL récupéré: {len(r_hist.json())} entrées")

    print("\n=== 7. Test de Persistance après Rafraîchissement (F5 GET /api/contrats & /api/sinistres) ===")
    r_get_c = client.get("/api/contrats", headers=headers_assurances)
    assert r_get_c.status_code == 200
    liste_c = r_get_c.json().get("contrats", [])
    trouve_c = any(c["id"] == contrat_payload["id"] for c in liste_c)
    assert trouve_c, f"Le contrat créé {contrat_payload['id']} doit être présent après rafraîchissement"
    print(f"Contrat {contrat_payload['id']} toujours présent après rafraîchissement: PASS")

    r_get_s = client.get("/api/sinistres", headers=headers_sinistres)
    assert r_get_s.status_code == 200
    liste_s = r_get_s.json().get("sinistres", [])
    trouve_s = any(s["id"] == sinistre_payload["id"] for s in liste_s)
    assert trouve_s, f"Le sinistre créé {sinistre_payload['id']} doit être présent après rafraîchissement"
    print(f"Sinistre {sinistre_payload['id']} toujours présent après rafraîchissement: PASS")

    print("\nTOUS LES TESTS SONT VALIDÉES AVEC SUCCES ! [OK]")



if __name__ == "__main__":
    test_all()
