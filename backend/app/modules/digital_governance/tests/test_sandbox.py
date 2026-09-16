"""Unit Tests for Cybersecurity Sandbox Suite, SQLAlchemy Persistence, and CTF Pipeline."""

import os
import shutil
import sys
import tempfile
import unittest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.seed_data import seed_cybersec_challenges
from app.models.models import (
    User,
    CyberSandboxChallenge,
    CyberSandboxSession,
    UserCyberCompetency,
)
from app.modules.digital_governance.services.llm_provider import MultiLLMProvider
from app.modules.digital_governance.services.templates import (
    TEMPLATE_REGISTRY,
    get_template,
    match_template_by_metadata,
    list_templates,
)
from app.modules.digital_governance.services.templates.soc_auth_template import SocAuthTemplate
from app.modules.digital_governance.services.templates.phishing_dfir_template import PhishingDfirTemplate
from app.modules.digital_governance.services.templates.linux_forensics_template import LinuxForensicsTemplate
from app.modules.digital_governance.services.templates.web_sqli_template import WebSqliTemplate
from app.modules.digital_governance.services.templates.threat_hunting_lotl_template import ThreatHuntingLotlTemplate
from app.modules.digital_governance.services.templates.pki_defense_template import PkiDefenseTemplate
from app.modules.digital_governance.services.templates.cloud_audit_template import CloudAuditTemplate
from app.modules.digital_governance.services.templates.dpi_replay_template import DpiReplayTemplate
from app.modules.digital_governance.services.content_pipeline import ContentGenerationPipeline
from app.modules.digital_governance.services.sandbox_manager import sandbox_manager
from app.modules.digital_governance.services.supabase_service import supabase_knowledge_service


class TestCybersecuritySandbox(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=cls.engine)
        cls.TestSession = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.TestSession()
        seed_cybersec_challenges(self.db)
        self.scratch_dir = Path(tempfile.gettempdir()) / "test_cybersec_scratch"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.db.close()
        if self.scratch_dir.exists():
            shutil.rmtree(self.scratch_dir, ignore_errors=True)

    def test_01_multi_llm_provider_initialization_and_status(self):
        provider = MultiLLMProvider()
        status = provider.get_provider_status()

        self.assertIn("groq", status)
        self.assertIn("nim", status)
        self.assertIn("gemini", status)
        self.assertIn("openai", status)

        # Test safe json parsing
        valid_json = '{"domain": "Cybersecurity", "tags": ["soc", "auth"]}'
        self.assertIsNotNone(provider.parse_json_safely(valid_json))

        markdown_json = '```json\n{"domain": "Data Privacy", "score": 90}\n```'
        parsed = provider.parse_json_safely(markdown_json)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["domain"], "Data Privacy")

    def test_02_all_eight_templates_registered(self):
        templates = list_templates()
        self.assertEqual(len(templates), 8)

        # Check all expected canonical keys exist
        expected_keys = [
            "01-soc-auth-investigation",
            "02-phishing-dfir",
            "03-compromised-linux-server",
            "04-vulnerable-web-app",
            "05-threat-hunting-lotl",
            "06-pki-token-dispute",
            "07-meghraj-cloud-audit",
            "08-dpi-apisetu-replay",
        ]
        for key in expected_keys:
            tmpl = get_template(key)
            self.assertIsNotNone(tmpl, f"Template {key} should be resolvable")

    def test_03_tag_and_keyword_matching_across_governance_domains(self):
        # Domain 1: SOC / Brute force
        t1 = match_template_by_metadata(domain="Cybersecurity", tags=["event-4625", "brute-force"])
        self.assertEqual(t1.template_id, "soc-auth-investigation")

        # Domain 2: Phishing DFIR
        t2 = match_template_by_metadata(domain="DFIR", tags=["phish", "dmarc", "email"])
        self.assertEqual(t2.template_id, "phishing-dfir")

        # Domain 3: Linux Persistence
        t3 = match_template_by_metadata(domain="CII", tags=["linux", "crontab", "sudo"])
        self.assertEqual(t3.template_id, "03-compromised-linux-server")

        # Domain 4: Web SQLi
        t4 = match_template_by_metadata(domain="Data Privacy", tags=["web", "sqli", "dpdp"])
        self.assertEqual(t4.template_id, "04-vulnerable-web-app")

        # Domain 5: Threat Hunting LOTL
        t5 = match_template_by_metadata(domain="Cybersecurity", tags=["lotl", "dns-tunneling", "sysmon"])
        self.assertEqual(t5.template_id, "05-threat-hunting-lotl")

        # Domain 6: Digital Signatures / PKI
        t6 = match_template_by_metadata(domain="Digital Signatures", tags=["pki", "dsc", "gem"])
        self.assertEqual(t6.template_id, "06-pki-token-dispute")

        # Domain 7: Government Cloud / MeghRaj
        t7 = match_template_by_metadata(domain="Government Cloud", tags=["meghraj", "stqc"])
        self.assertEqual(t7.template_id, "cloud-meghraj-audit")

        # Domain 8: DPI / API Setu
        t8 = match_template_by_metadata(domain="DPI", tags=["aadhaar", "api-setu", "replay"])
        self.assertEqual(t8.template_id, "dpi-apisetu-replay")

    def test_04_database_seeding_and_challenge_listing(self):
        challenges = sandbox_manager.list_challenges(db=self.db)
        self.assertEqual(len(challenges), 6)

        ids = [c.id for c in challenges]
        self.assertIn("01-soc-auth-investigation", ids)
        self.assertIn("03-compromised-linux-server", ids)
        self.assertIn("04-vulnerable-web-app", ids)
        self.assertIn("05-threat-hunting-lotl", ids)
        self.assertIn("06-pki-token-dispute", ids)
        self.assertIn("07-meghraj-cloud-audit", ids)

        c1 = next(c for c in challenges if c.id == "01-soc-auth-investigation")
        self.assertFalse(c1.is_flagship)

        c3 = next(c for c in challenges if c.id == "03-compromised-linux-server")
        self.assertEqual(c3.category, "Incident Response / Linux Forensics")

    async def test_05_session_lifecycle_with_db_materialization(self):
        # Start session for Upgraded Module 3 (Linux Forensics)
        sess = await sandbox_manager.start_session(
            "03-compromised-linux-server", duration_minutes=30, db=self.db
        )
        self.assertTrue(sess.session_id.startswith("sess_"))
        self.assertEqual(sess.challenge_id, "03-compromised-linux-server")
        self.assertGreater(sess.assigned_port, 8000)
        self.assertEqual(sess.status, "running")

        # Check session recorded in DB
        db_sess = self.db.query(CyberSandboxSession).filter_by(id=sess.session_id).first()
        self.assertIsNotNone(db_sess)
        self.assertEqual(db_sess.status, "running")

        # Unlock hint
        hint_res = sandbox_manager.unlock_hint(sess.session_id, 1, db=self.db)
        self.assertGreater(hint_res.penalty, 0)
        self.assertIn("crontab", hint_res.content)

        # Verify hint recorded in DB
        self.db.refresh(db_sess)
        self.assertIn("1", db_sess.unlocked_hints_json)

        # Submit wrong flag
        bad_res = sandbox_manager.submit_flag(sess.session_id, "FLAG{wrong_guess}", db=self.db)
        self.assertFalse(bad_res.correct)

        # Submit correct flag
        good_res = sandbox_manager.submit_flag(sess.session_id, sess_flag := db_sess.flag, db=self.db)
        self.assertTrue(good_res.correct)
        self.assertGreater(good_res.points_awarded, 0)

        # Verify solved status in DB
        self.db.refresh(db_sess)
        self.assertTrue(db_sess.is_solved)
        self.assertEqual(db_sess.status, "solved")

        # Stop session
        stopped = await sandbox_manager.stop_session(sess.session_id, db=self.db)
        self.assertTrue(stopped)

        self.db.refresh(db_sess)
        self.assertEqual(db_sess.status, "stopped")

    async def test_06_content_pipeline_and_db_persistence(self):
        sample_transcript = """
        In this cyber audit session, we analyze a critical vulnerability on the citizen welfare web portal.
        Attackers used SQL injection techniques with UNION SELECT on the citizen search parameter
        to bypass authentication and dump confidential data violating the Digital Personal Data Protection (DPDP) Act 2023.
        """
        res = await sandbox_manager.generate_from_transcript(
            transcript_text=sample_transcript,
            student_id="test_nodal_42",
            db=self.db,
        )

        self.assertIn("challenge_id", res)
        self.assertTrue(res["flag"].startswith("FLAG{"))

        # Verify challenge was saved into cyber_sandbox_challenges
        chal_db = self.db.query(CyberSandboxChallenge).filter_by(id=res["challenge_id"]).first()
        self.assertIsNotNone(chal_db)
        self.assertEqual(chal_db.title, res["title"])

    def test_07_supabase_read_only_knowledge_base(self):
        kb = supabase_knowledge_service.get_full_knowledge_base()
        self.assertEqual(len(kb), 5)
        pillar_names = [p["topic_name"] for p in kb]
        self.assertIn("Cybersecurity", pillar_names)
        self.assertIn("Data Privacy", pillar_names)
        self.assertIn("Digital Signatures", pillar_names)
        self.assertIn("Government Cloud", pillar_names)
        self.assertIn("Digital Public Infrastructure", pillar_names)


    async def test_08_hint_unlock_after_server_reload_and_fallback(self):
        # 1. Start a session
        sess = await sandbox_manager.start_session(
            "01-soc-auth-investigation", duration_minutes=30, db=self.db
        )
        session_id = sess.session_id

        # 2. Simulate server restart/reload by clearing in-memory sessions dictionary
        if session_id in sandbox_manager._sessions:
            active_s = sandbox_manager._sessions[session_id]
            if active_s.log_file:
                active_s.log_file.close()
        sandbox_manager._sessions.clear()
        self.assertNotIn(session_id, sandbox_manager._sessions)

        # 3. Unlock hint with cleared memory: should restore from DB without error
        hint_res = sandbox_manager.unlock_hint(session_id, 1, db=self.db)
        self.assertNotEqual(hint_res.content, "Session not found.")
        self.assertIn("4625", hint_res.content)
        self.assertGreater(hint_res.penalty, 0)

        # 4. Verify session was re-hydrated into memory
        self.assertIn(session_id, sandbox_manager._sessions)

        # 5. Client fallback test: simulated session with challenge_id
        sim_hint_res = sandbox_manager.unlock_hint(
            "sim_custom_client_123",
            1,
            db=self.db,
            challenge_id="01-soc-auth-investigation",
        )
        self.assertNotEqual(sim_hint_res.content, "Session not found.")
        self.assertIn("4625", sim_hint_res.content)

    async def test_09_marimo_launcher_uses_backend_interpreter_and_popen(self):
        """Regression: Windows Uvicorn selector loops cannot create asyncio subprocesses."""
        fake_process = MagicMock()
        fake_process.poll.return_value = None
        fake_process.stderr = None
        fake_process.wait.return_value = 0

        module = "app.modules.digital_governance.services.sandbox_manager"
        with (
            patch.object(sandbox_manager, "_find_available_port", return_value=8085),
            patch.object(sandbox_manager, "_is_port_listening", return_value=True),
            patch(f"{module}.subprocess.Popen", return_value=fake_process) as popen,
            patch(
                "asyncio.create_subprocess_exec",
                side_effect=AssertionError("asyncio subprocess launcher must not be used"),
            ),
        ):
            session = await sandbox_manager.start_session(
                "01-soc-auth-investigation", duration_minutes=5, db=self.db
            )
            command = popen.call_args.args[0]
            self.assertEqual(command[:3], [sys.executable, "-m", "marimo"])
            self.assertEqual(session.status, "running")
            self.assertEqual(session.assigned_port, 8085)
            await sandbox_manager.stop_session(session.session_id, db=self.db)


if __name__ == "__main__":
    unittest.main()
