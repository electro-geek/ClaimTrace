import tempfile,unittest
from pathlib import Path
import json
from claimtrace.generator import build
from claimtrace.db import connect
from claimtrace.validation import validate
from claimtrace.detection import detect
from claimtrace.evaluation import evaluate
class ClaimTraceTest(unittest.TestCase):
    def test_generate_validate_detect(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); self.assertEqual(build(20261022,"starter",p)["claims"],250); c=connect(p/"claimtrace.db"); self.assertEqual(c.execute("SELECT COUNT(*) FROM claims").fetchone()[0],250); self.assertGreater(detect(p/"claimtrace.db"),0); self.assertTrue(any(x["passed"] for x in validate(p/"claimtrace.db") if x["name"]=="primary_key_uniqueness"))
    def test_ids(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); build(1,"starter",p); c=connect(p/"claimtrace.db"); self.assertTrue(c.execute("SELECT id FROM claims LIMIT 1").fetchone()[0].startswith("CLM-2026-")); self.assertTrue(c.execute("SELECT id FROM providers LIMIT 1").fetchone()[0].startswith("PRV-"))
    def test_exports_and_planted_scenarios(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); build(20261022,"starter",p); self.assertTrue((p/"exports"/"claims.csv").exists()); self.assertTrue((p/"exports"/"claims.json").exists()); truth=(p/"ground_truth.csv").read_text(); self.assertIn("missing_relationship_edge",truth); self.assertIn("unusual_timing",truth); self.assertIn("shared_contact_cluster",truth); self.assertTrue((p/"exports"/"seed.sql").exists()); c=connect(p/"claimtrace.db"); self.assertEqual(c.execute("SELECT COUNT(*) FROM claims WHERE status NOT IN ('PAID','REVIEW')").fetchone()[0],0)
