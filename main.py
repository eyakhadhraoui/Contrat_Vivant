from graph.workflow import graph
from tools.auth_tool import login

if __name__ == "__main__":
    username = input("Nom d'utilisateur : ")
    password = input("Mot de passe : ")

    try:
        token = login(username, password)
    except PermissionError as e:
        print("Échec de connexion :", e)
        exit()

    initial_state = {
        "token": token,
        "contrat_id": "C001",
    }

    result = graph.invoke(initial_state)

    print("=== RESULTAT FINAL ===")
    print(result)
