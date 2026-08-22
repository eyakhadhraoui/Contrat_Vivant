"""
Tests unitaires et d'intégration du Système Multi-Agents (Le Contrat Vivant).
Valide l'autonomie et l'exécution de CollectorAgent, RiskAnalysisAgent, AlertNotificationAgent
ainsi que la coordination globale par le SupervisorAgent sous LangGraph.
"""

import unittest
from unittest.mock import patch, MagicMock
from agents.collector_agent import CollectorAgent, run_collector_agent
from agents.risk_agent import RiskAnalysisAgent, run_risk_agent
from agents.alert_agent import AlertNotificationAgent, run_alert_agent
from agents.multi_agent_system import SupervisorAgent, supervisor_orchestrate
from graph.workflow import graph


class TestMultiAgentSystem(unittest.TestCase):

    def setUp(self):
        self.mock_contrat = {
            "id": "CSTR00001",
            "client_id": "CL01",
            "client": "Dupont Jean",
            "garantie_max": 50000.0,
            "statut": "actif",
            "agence_id": "AG01"
        }
        self.mock_sinistres = [
            {
                "id": "S001",
                "contrat_id": "CSTR00001",
                "montant_declare": 12000.0,
                "type_sinistre": "Auto - Carambolage",
                "statut": "ouvert",
                "date": "2026-01-15"
            }
        ]
        self.mock_gestionnaire = {
            "id": "GEST01",
            "username": "jdupont",
            "role": "assurances",
            "nom": "Dupont",
            "prenom": "Jean",
            "agence_id": "AG01",
            "email": "jdupont@assurance.fr"
        }

    @patch("nodes.collect_node.get_contrat")
    @patch("nodes.collect_node.get_sinistres")
    @patch("agents.collector_agent.authenticate")
    def test_collector_agent_execution(self, mock_auth, mock_sinistres_tool, mock_contrat_tool):

        mock_contrat_tool.return_value = self.mock_contrat
        mock_sinistres_tool.return_value = self.mock_sinistres
        mock_auth.side_effect = lambda s: {**s, "gestionnaire_role": "assurances", "gestionnaire_id": "GEST01"}

        initial_state = {
            "token": "valid_token",
            "contrat_id": "CSTR00001",
            "modification_type": "contrat"
        }

        collector = CollectorAgent()
        res = collector.execute(initial_state)

        self.assertIsNotNone(res.get("contrat_data"))
        self.assertEqual(res["contrat_data"]["id"], "CSTR00001")
        self.assertEqual(len(res["sinistres_data"]), 1)
        self.assertEqual(res["confidence"], "haute")
        self.assertIn("collector_agent", res["agent_metadata"])
        self.assertEqual(res["agent_metadata"]["collector_agent"]["status"], "success")

    @patch("agents.risk_agent.cross_analysis")
    @patch("agents.risk_agent.classify_event")
    @patch("agents.risk_agent.calculate_urgency")
    def test_risk_analysis_agent_execution(self, mock_urgency, mock_classify, mock_cross):
        mock_cross.side_effect = lambda s: {**s, "risk_analysis": {"score": 75, "urgency_level": "eleve"}, "anomalies": [{"rule": "CAP_EXCEEDED"}]}
        mock_classify.side_effect = lambda s: {**s, "event_type": "risque"}
        mock_urgency.side_effect = lambda s: {**s, "urgency_score": 75, "urgency_level": "eleve", "dominant_rule": "CAP_EXCEEDED"}

        state = {
            "contrat_id": "CSTR00001",
            "contrat_data": self.mock_contrat,
            "sinistres_data": self.mock_sinistres,
            "confidence": "haute",
        }

        risk_agent = RiskAnalysisAgent()
        res = risk_agent.execute(state)

        self.assertEqual(res["urgency_score"], 75)
        self.assertEqual(res["urgency_level"], "eleve")
        self.assertEqual(res["event_type"], "risque")
        self.assertIn("risk_agent", res["agent_metadata"])
        self.assertEqual(res["agent_metadata"]["risk_agent"]["nb_anomalies"], 1)

    @patch("agents.alert_agent.summarize_dossier")
    @patch("agents.alert_agent.build_alert")
    @patch("agents.alert_agent.generate_recommendation")
    @patch("agents.alert_agent.route_to_gestionnaire")
    @patch("agents.alert_agent.cross_notify")
    def test_alert_notification_agent_execution(self, mock_notify, mock_route, mock_reco, mock_alert, mock_summarize):
        mock_summarize.side_effect = lambda s: {**s, "resume_dossier": "Synthèse du dossier."}
        mock_alert.side_effect = lambda s: {**s, "alert": {"contrat_id": "CSTR00001"}}
        mock_reco.side_effect = lambda s: {**s, "recommendation": "Réviser le dossier."}
        mock_route.side_effect = lambda s: {**s, "routed_to": [self.mock_gestionnaire], "routing_alerte": False}
        mock_notify.side_effect = lambda s: {**s, "gestionnaires_a_notifier": [self.mock_gestionnaire]}

        state = {
            "contrat_id": "CSTR00001",
            "contrat_data": self.mock_contrat,
            "sinistres_data": self.mock_sinistres,
            "urgency_level": "eleve",
            "urgency_score": 75,
        }

        alert_agent = AlertNotificationAgent()
        res = alert_agent.execute(state)

        self.assertEqual(res["resume_dossier"], "Synthèse du dossier.")
        self.assertEqual(len(res["routed_to"]), 1)
        self.assertIn("alert_agent", res["agent_metadata"])
        self.assertEqual(res["agent_metadata"]["alert_agent"]["status"], "success")

    @patch("agents.multi_agent_system.CollectorAgent.execute")
    @patch("agents.multi_agent_system.RiskAnalysisAgent.execute")
    @patch("agents.multi_agent_system.AlertNotificationAgent.execute")
    @patch("agents.multi_agent_system.human_validation")
    @patch("agents.multi_agent_system.update_history")
    def test_supervisor_agent_workflow(self, mock_hist, mock_val, mock_alert, mock_risk, mock_coll):
        mock_coll.side_effect = lambda s: {**s, "contrat_data": self.mock_contrat, "agent_metadata": {"collector": "ok"}}
        mock_risk.side_effect = lambda s: {**s, "urgency_score": 50, "urgency_level": "moyen", "agent_metadata": {**s.get("agent_metadata", {}), "risk": "ok"}}
        mock_alert.side_effect = lambda s: {**s, "alert": {"ok": True}, "agent_metadata": {**s.get("agent_metadata", {}), "alert": "ok"}}
        mock_val.side_effect = lambda s: {**s, "validation_status": "en_attente_validation"}
        mock_hist.side_effect = lambda s: {**s, "history_updated": True}

        supervisor = SupervisorAgent()
        initial_state = {"contrat_id": "CSTR00001", "token": "test_token"}

        final_state = supervisor.run_workflow(initial_state)

        self.assertEqual(final_state["validation_status"], "en_attente_validation")
        self.assertEqual(final_state["agent_metadata"]["supervisor_status"], "completed")
        self.assertTrue(mock_coll.called)
        self.assertTrue(mock_risk.called)
        self.assertTrue(mock_alert.called)

    @patch("nodes.collect_node.get_contrat")
    @patch("nodes.collect_node.get_sinistres")
    @patch("agents.collector_agent.authenticate")

    @patch("nodes.cross_analysis_node.ask_gemini")
    @patch("nodes.summarizer_node.ask_gemini")
    @patch("tools.cross_notification_tool.get_gestionnaires_sinistres_concernes")
    @patch("tools.cross_notification_tool.get_gestionnaire_assurances_du_contrat")
    def test_langgraph_workflow_invoke(self, mock_gest_assurances, mock_gest_sinistres, mock_summary_llm, mock_cross_llm, mock_auth, mock_sinistres_tool, mock_contrat_tool):
        mock_contrat_tool.return_value = self.mock_contrat
        mock_sinistres_tool.return_value = self.mock_sinistres
        mock_auth.side_effect = lambda s: {**s, "gestionnaire_role": "assurances", "gestionnaire_id": "GEST01"}
        mock_cross_llm.return_value = '{"anomalies": []}'
        mock_summary_llm.return_value = "Résumé généré."
        mock_gest_assurances.return_value = self.mock_gestionnaire
        mock_gest_sinistres.return_value = [self.mock_gestionnaire]

        initial_state = {
            "token": "valid_token",
            "contrat_id": "CSTR00001",
            "modification_type": "contrat"
        }

        output = graph.invoke(initial_state)

        self.assertIsNotNone(output)
        self.assertEqual(output["contrat_id"], "CSTR00001")
        self.assertIn("agent_metadata", output)
        self.assertIn("collector_agent", output["agent_metadata"])
        self.assertIn("risk_agent", output["agent_metadata"])
        self.assertIn("alert_agent", output["agent_metadata"])


if __name__ == "__main__":
    unittest.main()
