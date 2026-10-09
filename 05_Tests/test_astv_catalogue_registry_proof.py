"""Tests for the ASTV-331 isolated registry proof."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

PROOF_PATH = Path(__file__).with_name("proofs") / "astv_catalogue_registry_proof.py"
SPEC = importlib.util.spec_from_file_location("astv_catalogue_registry_proof", PROOF_PATH)
assert SPEC and SPEC.loader
proof = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proof)


def candidate() -> dict:
    return {
        "schema": "astv.intent_catalogue",
        "schema_version": "1.0.0",
        "records": {
            "classic_fm": {
                "intent": "media.play_source",
                "title": "Play Classic FM",
                "params": {
                    "output": {"domain": "audio"},
                    "catalogue_id": "curated_media",
                    "item_id": "classic_fm",
                },
            },
            "morning_routine": {
                "intent": "routine.run",
                "routine": "morning",
                "title": "Good Morning Routine",
                "params": {},
            },
        },
    }


class CatalogueRegistryProofTests(unittest.TestCase):
    def test_lookup_is_normalized_and_record_shape_is_unchanged(self) -> None:
        provider = proof.CatalogueProvider()
        provider.activate(candidate(), "revision-1")

        response = provider.lookup("  CLASSIC_FM ")

        self.assertTrue(response["ok"])
        self.assertTrue(response["found"])
        self.assertEqual(response["normalized_intent_id"], "classic_fm")
        self.assertEqual(
            response["record"],
            candidate()["records"]["classic_fm"],
        )
        self.assertNotIn("intent_id", response["record"])
        self.assertNotIn("schema_version", response["record"])

    def test_absent_id_is_success_with_empty_record(self) -> None:
        provider = proof.CatalogueProvider()
        provider.activate(candidate(), "revision-1")

        response = provider.lookup("does_not_exist")

        self.assertTrue(response["ok"])
        self.assertFalse(response["found"])
        self.assertEqual(response["record"], {})

    def test_invalid_initial_load_leaves_no_active_registry(self) -> None:
        provider = proof.CatalogueProvider()
        invalid = candidate()
        invalid["schema_version"] = "2.0.0"

        with self.assertRaises(proof.CatalogueValidationError):
            provider.activate(invalid, "bad-revision")

        self.assertIsNone(provider.active_revision)
        with self.assertRaises(proof.RegistryUnavailable):
            provider.lookup("classic_fm")

    def test_failed_refresh_retains_prior_complete_snapshot(self) -> None:
        provider = proof.CatalogueProvider()
        provider.activate(candidate(), "revision-1")
        prior = provider.active
        invalid = candidate()
        invalid["records"]["classic_fm"]["params"]["item_id"] = ""

        with self.assertRaises(proof.CatalogueValidationError):
            provider.activate(invalid, "revision-2")

        self.assertIs(provider.active, prior)
        self.assertEqual(provider.active_revision, "revision-1")
        self.assertEqual(
            provider.lookup("classic_fm")["record"]["params"]["item_id"],
            "classic_fm",
        )

    def test_response_mutation_cannot_mutate_active_registry(self) -> None:
        provider = proof.CatalogueProvider()
        provider.activate(candidate(), "revision-1")

        first = provider.lookup("classic_fm")
        first["record"]["title"] = "Mutated by caller"

        self.assertEqual(
            provider.lookup("classic_fm")["record"]["title"],
            "Play Classic FM",
        )
        with self.assertRaises(TypeError):
            provider.active.records["classic_fm"]["title"] = "mutation"


if __name__ == "__main__":
    unittest.main()
