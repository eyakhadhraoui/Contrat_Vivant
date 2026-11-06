# InsurAgent AI — prototype d'analyse de contrats

Ce dépôt contient une application d'assurance React/FastAPI et un parcours d'analyse de contrats piloté par quatre **Cominty Managed Agents**. Le parcours Cominty est ajouté au tableau de bord existant sous **Analyse de contrats IA**.

## Parcours d'analyse

1. L'utilisateur connecté envoie un PDF (20 Mo maximum).
2. FastAPI extrait le texte avec pypdf; si le PDF est scanné, Tesseract tente l'OCR.
3. Le backend transmet le document à l'agent Cominty d'extraction, puis appelle séparément les agents d'anomalies, de risques et de synthèse. Les agents reçoivent les résultats précédents et retournent du JSON.
4. Les résultats structurés sont enregistrés dans `data/contract_analyses.sqlite3` et un rapport PDF est généré. Les analyses et téléchargements sont filtrés par utilisateur applicatif.

Cominty est le seul fournisseur utilisé pour les quatre tâches d'agents de ce parcours. Les clés restent dans l'environnement du backend. L'écran n'affiche que les résultats renvoyés par les agents, sans réponses simulées.

## Configuration locale

1. Installer les dépendances Python existantes et `cominty-sdk` depuis `requirements.txt`.
2. Copier `.env.example` vers `.env`, puis renseigner `COMINTY_API_KEY` et `COMINTY_USER_ID` avec les valeurs de la plateforme Cominty.
3. Optionnellement, fournir les identifiants de quatre agents privés déjà créés avec `COMINTY_AGENT_EXTRACTION_ID`, `COMINTY_AGENT_ANOMALIES_ID`, `COMINTY_AGENT_RISK_ID` et `COMINTY_AGENT_REPORT_ID`. Si les identifiants sont absents, l'application cherche les quatre agents par nom et les crée au premier lancement du workflow.
4. Démarrer FastAPI comme pour l'application existante. Pour le frontend: `cd frontend`, `npm install`, `npm run dev`.

Il faut installer Tesseract OCR avec les langues françaises et anglaises pour les PDF image. Sans identifiants Cominty, l'API retourne une erreur explicite `503`; elle ne produit pas de données factices.

## Docker Compose

Les variables Cominty sont transmises au service backend par `docker-compose.yml`. Ajoutez les valeurs dans le fichier `.env` à la racine, puis démarrez les services avec `docker compose up --build`. Le volume `./data:/app/data` conserve les analyses.

## API ajoutée

- `POST /api/contract-analysis` — multipart `file` PDF, exécute les quatre agents.
- `GET /api/contract-analysis` — liste les analyses du gestionnaire connecté.
- `GET /api/contract-analysis/{id}/report.pdf` — télécharge le rapport PDF de cette analyse.
- `POST /api/contract-analysis/compare` — compare deux versions PDF.
- `POST /api/contract-analysis/{id}/ask` — pose une question au sujet du PDF original.
- `POST /api/contract-analysis/prioritize` — classe les analyses du gestionnaire.
- `POST /api/contract-analysis/{id}/clarification` — rédige un brouillon non envoyé.
- `POST /api/contract-analysis/{id}/compliance` — crée une checklist de revue humaine.

Les routes réutilisent l'authentification de l'application et n'acceptent jamais une clé Cominty depuis le navigateur.
