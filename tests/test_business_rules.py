import unittest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from rules_engine.rules.ecart_garantie_montant import EcartGarantieMontant
from tools.permissions_tool import (
    peut_acceder_au_contrat,
    peut_ajouter_contrat,
    peut_modifier_contrat,
    peut_ajouter_sinistre,
    peut_modifier_sinistre,
)
from nodes.cross_notification_node import cross_notify
from tools.si_contrats_tool import ajouter_contrat, modifier_contrat
from tools.si_sinistres_tool import ajouter_sinistre, modifier_sinistre, get_sinistres


class BusinessRulesTests(unittest.TestCase):

    def test_assurances_can_access_contracts_from_same_agency_only(self):
        contrat = {
            "id": "C001",
            "agence_id": "AG01",
        }

        self.assertTrue(peut_acceder_au_contrat("assurances", contrat, "AG01"))
        self.assertFalse(peut_acceder_au_contrat("assurances", contrat, "AG02"))

    def test_roles_permissions(self):
        self.assertTrue(peut_ajouter_contrat("assurances"))
        self.assertFalse(peut_ajouter_contrat("sinistres"))

    def test_ecart_rule_handles_mixed_numeric_types(self):
        rule = EcartGarantieMontant()
        contrat = {"garantie_max": Decimal("1000")}
        sinistres = [{"montant_declare": 1500.0}]

        result = rule.check(contrat, sinistres)

        self.assertIsNotNone(result)
        self.assertEqual(result["rule"], "ecart_garantie_montant")

        self.assertTrue(peut_modifier_contrat("assurances"))
        self.assertFalse(peut_modifier_contrat("sinistres"))

        self.assertTrue(peut_ajouter_sinistre("sinistres"))
        self.assertFalse(peut_ajouter_sinistre("assurances"))

        self.assertTrue(peut_modifier_sinistre("sinistres"))
        self.assertTrue(peut_modifier_sinistre("assurances"))

    def test_cross_notification_for_contract_modification_notifies_claim_managers(self):
        state = {
            "contrat_id": "C001",
            "gestionnaire_id": "G456",
            "gestionnaire_role": "assurances",
            "modification_type": "contrat",
        }

        with patch("nodes.cross_notification_node.send_email") as mock_email, \
             patch("nodes.cross_notification_node.send_teams") as mock_teams:
            updated_state = cross_notify(state)

        self.assertIn("gestionnaires_a_notifier", updated_state)
        self.assertEqual(len(updated_state["gestionnaires_a_notifier"]), 1)
        self.assertEqual(updated_state["gestionnaires_a_notifier"][0]["id"], "G123")
        mock_email.assert_called_once()
        mock_teams.assert_called_once()

    @patch("tools.si_contrats_tool.get_connection")
    @patch("tools.si_contrats_tool._resolve_client_id", return_value="CL01")
    @patch("tools.si_contrats_tool._load_contrats")
    @patch("tools.si_contrats_tool._save_contrats")
    def test_ajouter_contrat_assurances(self, mock_save, mock_load, mock_resolve, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        mock_load.return_value = []
        g_assurances = {"gestionnaire_id": "G456", "role": "assurances", "agence_id": "AG01"}
        contrat_data = {"id": "C999", "client": "CL01", "garantie_max": 30000}
        
        res = ajouter_contrat(contrat_data, g_assurances)
        self.assertIn("999", res["id"])
        self.assertEqual(res["gestionnaire_createur_id"], "G456")
        self.assertEqual(res["agence_id"], "AG01")

    @patch("tools.si_contrats_tool.get_connection")
    @patch("tools.si_contrats_tool._load_contrats")
    @patch("tools.si_contrats_tool._save_contrats")
    @patch("tools.si_contrats_tool.get_sinistres")
    @patch("tools.si_contrats_tool.get_gestionnaires_sinistres_concernes")
    @patch("tools.si_contrats_tool.send_email")
    def test_modifier_contrat_with_existing_sinistre_notifies_sinistres_manager(
        self, mock_email, mock_get_g_sinistres, mock_get_sinistres, mock_save, mock_load, mock_get_conn
    ):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        mock_load.return_value = [{"id": "C001", "client": "Ahmed", "garantie_max": 50000, "agence_id": "AG01"}]
        mock_get_sinistres.return_value = [{"id": "S001", "contrat_id": "C001"}]
        mock_get_g_sinistres.return_value = [{"id": "G123", "email": "g123@test.com"}]
        
        g_assurances = {"gestionnaire_id": "G456", "role": "assurances", "agence_id": "AG01"}
        res = modifier_contrat("C001", {"garantie_max": 60000}, g_assurances)

        self.assertTrue(res["sinistres_existant"])
        self.assertEqual(res["gestionnaires_sinistres_notifies"], ["G123"])
        mock_email.assert_called_once()

    @patch("tools.si_sinistres_tool.get_connection")
    @patch("tools.si_sinistres_tool._get_contrat_details", return_value={"id": "C001", "type_contrat": "auto", "statut": "actif", "gestionnaire_createur_id": "G456"})
    @patch("tools.si_sinistres_tool._get_contrat_type", return_value="auto")
    @patch("tools.si_sinistres_tool._load_sinistres")
    @patch("tools.si_sinistres_tool._save_sinistres")
    @patch("tools.si_sinistres_tool.get_gestionnaire_assurances_du_contrat")
    @patch("tools.si_sinistres_tool.send_email")
    def test_ajouter_sinistre_notifies_assurances_manager(
        self, mock_email, mock_get_g_assurances, mock_save, mock_load, mock_get_type, mock_get_details, mock_get_conn
    ):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        mock_load.return_value = []
        mock_get_g_assurances.return_value = {"id": "G456", "email": "g456@test.com"}
        
        g_sinistres = {"gestionnaire_id": "G123", "role": "sinistres", "agence_id": "AG01"}
        sinistre_data = {"id": "S999", "contrat_id": "C001", "montant_declare": 10000, "type_sinistre": "Auto - Carambolage"}

        res = ajouter_sinistre(sinistre_data, g_sinistres)
        self.assertEqual(res["sinistre"]["id"], "S999")
        self.assertEqual(res["gestionnaire_assurances_notifie"], "G456")
        mock_email.assert_called_once()

    @patch("tools.si_sinistres_tool._get_contrat_details", return_value={"id": "C001", "type_contrat": "auto", "statut": "suspendu"})
    @patch("tools.si_sinistres_tool.get_gestionnaire_assurances_du_contrat")
    @patch("tools.si_sinistres_tool.send_email")
    def test_ajouter_sinistre_blocked_when_contract_is_suspended(
        self, mock_email, mock_get_g_assurances, mock_get_details
    ):
        mock_get_g_assurances.return_value = {"id": "G456", "email": "g456@test.com"}
        g_sinistres = {"gestionnaire_id": "G123", "role": "sinistres", "agence_id": "AG01"}
        sinistre_data = {"id": "S999", "contrat_id": "C001", "type_sinistre": "Auto - Carambolage", "montant_declare": 10000}

        with self.assertRaises(ValueError) as ctx:
            ajouter_sinistre(sinistre_data, g_sinistres)
        self.assertIn("suspendu", str(ctx.exception).lower())
        mock_email.assert_not_called()

    @patch("tools.si_sinistres_tool._get_contrat_details", return_value={"id": "C001", "type_contrat": "auto", "statut": "resilie"})
    @patch("tools.si_sinistres_tool.get_gestionnaire_assurances_du_contrat")
    @patch("tools.si_sinistres_tool.send_email")
    def test_ajouter_sinistre_blocked_when_contract_is_resiliated(
        self, mock_email, mock_get_g_assurances, mock_get_details
    ):
        mock_get_g_assurances.return_value = {"id": "G456", "email": "g456@test.com"}
        g_sinistres = {"gestionnaire_id": "G123", "role": "sinistres", "agence_id": "AG01"}
        sinistre_data = {"id": "S999", "contrat_id": "C001", "type_sinistre": "Auto - Carambolage", "montant_declare": 10000}

        with self.assertRaises(ValueError) as ctx:
            ajouter_sinistre(sinistre_data, g_sinistres)
        self.assertIn("résilié", str(ctx.exception).lower().replace("resilie", "résilié"))
        mock_email.assert_not_called()

    @patch("tools.si_sinistres_tool._get_contrat_type", return_value="habitation")
    @patch("tools.si_sinistres_tool._get_contrat_details", return_value={"id": "C001", "type_contrat": "habitation", "statut": "actif"})
    @patch("tools.si_sinistres_tool.get_gestionnaire_assurances_du_contrat")
    @patch("tools.si_sinistres_tool.send_email")
    def test_ajouter_sinistre_invalid_type_for_contract(
        self, mock_email, mock_get_g_assurances, mock_get_details, mock_get_type
    ):
        mock_get_g_assurances.return_value = {"id": "G456", "email": "g456@test.com"}
        g_sinistres = {"gestionnaire_id": "G123", "role": "sinistres", "agence_id": "AG01"}
        sinistre_data = {"id": "S999", "contrat_id": "C001", "type_sinistre": "Auto - Carambolage", "montant_declare": 10000}

        with self.assertRaises(ValueError):
            ajouter_sinistre(sinistre_data, g_sinistres)
        mock_email.assert_not_called()

    @patch("tools.si_sinistres_tool.get_connection")
    def test_get_sinistres_normalizes_contract_ids(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("contrat_id",), ("montant_declare",), ("date",), ("date_sinistre",)]
        mock_cursor.fetchall.return_value = [("S001", "C001", 15000, "2026-08-01", "2026-08-01")]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = get_sinistres("CSTR00001")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "S001")
        self.assertEqual(result[0]["contrat_id"], "C001")

    @patch("tools.cross_notification_tool.get_connection", return_value=None)
    @patch("tools.cross_notification_tool._load_json")
    def test_cross_notification_helpers_accept_short_and_canonical_ids(self, mock_load_json, mock_get_connection):
        def fake_load(filename):
            if filename == "sinistres.json":
                return [
                    {"id": "S001", "contrat_id": "C001", "gestionnaire_traitant_id": "G123"},
                    {"id": "S002", "contrat_id": "CSTR00001", "gestionnaire_traitant_id": "G456"},
                ]
            if filename == "gestionnaires.json":
                return [
                    {"id": "G123", "email": "g123@test.com"},
                    {"id": "G456", "email": "g456@test.com"},
                    {"id": "G789", "email": "g789@test.com"},
                ]
            if filename == "contrats.json":
                return [
                    {"id": "C001", "gestionnaire_createur_id": "G789"},
                    {"id": "CSTR00001", "gestionnaire_createur_id": "G789"},
                ]
            return []

        mock_load_json.side_effect = fake_load

        from tools.cross_notification_tool import get_gestionnaires_sinistres_concernes, get_gestionnaire_assurances_du_contrat

        sinistre_managers = get_gestionnaires_sinistres_concernes("CSTR00001")
        assurances_manager = get_gestionnaire_assurances_du_contrat("C001")

        self.assertEqual({m["id"] for m in sinistre_managers}, {"G123", "G456"})
        self.assertEqual(assurances_manager["id"], "G789")

    @patch("tools.si_sinistres_tool.get_connection")
    @patch("tools.si_sinistres_tool.get_gestionnaire_assurances_du_contrat")
    @patch("tools.si_sinistres_tool.send_email")
    @patch("tools.si_sinistres_tool.get_sinistres")
    @patch("tools.si_contrats_tool.get_contrat")
    def test_modifier_sinistre_notifies_assurances_and_triggers_cross_analysis(
        self, mock_get_contrat, mock_get_sinistres, mock_email, mock_get_g_assurances, mock_get_conn
    ):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [
            ("id",), ("contrat_id",), ("type_sinistre",), ("montant_declare",),
            ("statut",), ("date",), ("gestionnaire_traitant_id",), ("agence_id",)
        ]
        mock_cursor.fetchone.return_value = (
            "S001", "C001", "Auto", 15000, "en_cours", "2026-08-01", "G123", "AG01"
        )
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        mock_get_g_assurances.return_value = {"id": "G456", "email": "g456@test.com"}
        mock_get_contrat.return_value = {"id": "C001", "garantie_max": 50000}
        mock_get_sinistres.return_value = [{"id": "S001", "contrat_id": "C001", "montant_declare": 20000}]

        g_sinistres = {"gestionnaire_id": "G123", "role": "sinistres", "agence_id": "AG01"}
        res = modifier_sinistre("S001", {"montant_declare": 20000}, g_sinistres)

        self.assertTrue(res["cross_analysis_declenchee"])
        self.assertEqual(res["gestionnaire_assurances_notifie"], "G456")
        mock_email.assert_called_once()


if __name__ == "__main__":
    unittest.main()
