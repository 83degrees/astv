#!/usr/bin/env python3
"""Require conclusive proof that the non-admin probe reached backend Unauthorized."""

from __future__ import annotations

import json
import sys
from pathlib import Path


EXPECTED_LOG_EVENT = (
    "Error during service call to "
    "astv_intent_catalogue.validate_intent_record: Unauthorized"
)


def write_report(evidence: Path, report: dict[str, object]) -> None:
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "permission-proof.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def verify(evidence: Path) -> tuple[bool, dict[str, object]]:
    permission_path = evidence / "permission.json"
    if not permission_path.is_file():
        return False, {"status": "failed", "reason": "browser permission evidence missing"}

    try:
        permission = json.loads(permission_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False, {"status": "failed", "reason": "browser permission evidence invalid"}

    probe = permission.get("probe")
    if not isinstance(probe, dict) or probe.get("kind") != "backend_denial":
        return False, {"status": "failed", "reason": "browser did not record a backend denial"}

    code = probe.get("code")
    if (
        code == "unauthorized"
        and permission.get("status") == "passed"
        and permission.get("proof") == "native_error_code"
    ):
        return True, {
            "status": "passed",
            "browser_code": "unauthorized",
            "proof": "native_error_code",
        }

    if not (
        code == "home_assistant_error"
        and permission.get("status") == "pending_backend_log"
        and permission.get("proof") == "exact_service_unauthorized_log"
    ):
        return False, {"status": "failed", "reason": "unsupported or inconsistent browser denial evidence"}

    log_path = evidence / "home-assistant.log"
    try:
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False, {"status": "failed", "reason": "Home Assistant log evidence missing or unreadable"}

    matches = log_text.count(EXPECTED_LOG_EVENT)
    if matches < 1:
        return False, {
            "status": "failed",
            "browser_code": "home_assistant_error",
            "reason": "exact backend Unauthorized service event absent",
        }
    return True, {
        "status": "passed",
        "browser_code": "home_assistant_error",
        "proof": "exact_service_unauthorized_log",
        "matching_events": matches,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_permission_evidence.py EVIDENCE_DIR", file=sys.stderr)
        return 2
    evidence = Path(sys.argv[1])
    passed, report = verify(evidence)
    write_report(evidence, report)
    if not passed:
        print(str(report.get("reason", "permission proof failed")), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
