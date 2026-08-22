import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

APP_ENV = os.getenv("APP_ENV", "development").lower()
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "true" if APP_ENV == "production" else "false").lower() in ("1", "true", "yes")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# BNF08 : seuils configurables sans redéploiement
URGENCY_THRESHOLD_ECART = float(os.getenv("URGENCY_THRESHOLD_ECART", "0.4"))
URGENCY_THRESHOLD_SINISTRES_REPETES = int(os.getenv("URGENCY_THRESHOLD_SINISTRES_REPETES", "2"))
SINISTRES_REPETES_PERIODE_JOURS = int(os.getenv("SINISTRES_REPETES_PERIODE_JOURS", "30"))
RETARD_PAIEMENT_JOURS_LIMITE = int(os.getenv("RETARD_PAIEMENT_JOURS_LIMITE", "15"))

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))

CONTRATS_PATH = "data/contrats.json"
SINISTRES_PATH = "data/sinistres.json"
HISTORIQUE_PATH = "data/historique.json"
AUDIT_LOG_PATH = "data/audit_log.json"

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    if APP_ENV == "production":
        raise RuntimeError("JWT_SECRET_KEY doit etre defini dans .env en production")
    JWT_SECRET_KEY = "dev-only-change-me-in-env"

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
INTERNAL_WORKER_TOKEN = os.getenv("INTERNAL_WORKER_TOKEN", "")

GESTIONNAIRES_PATH = "data/gestionnaires.json"
AUTO_APPLY_LOW_RISK = os.getenv("AUTO_APPLY_LOW_RISK", "false").lower() in ("1", "true", "yes")
