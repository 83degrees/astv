"""Fail-closed post-browser evidence and artifact-upload controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys


CATALOGUE_SUFFIX = "/astv/astv_intent_catalogue.yaml"
MAPPING_SUFFIX = "/AdvNFC/advnfc_tag_mapping.yaml"
FORBIDDEN_STAGE_CONTENT = re.compile(
    rb"ha-starburst|assistive/nfc|mqtt:|password:|api_key:|bearer ", re.IGNORECASE
)
PRIVATE_FILENAMES = {"browser-session.json", "private-artifact-secrets.json"}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _baseline_hash(baseline: Path, suffix: str) -> str:
    matches = []
    for line in baseline.read_text().splitlines():
        digest, separator, filename = line.partition("  ")
        if separator and filename.replace("\\", "/").endswith(suffix):
            matches.append(digest)
    if len(matches) != 1 or not re.fullmatch(r"[0-9a-f]{64}", matches[0]):
        raise ValueError(f"baseline must contain exactly one valid hash for {suffix}")
    return matches[0]


def post_browser(stage_root: Path) -> int:
    evidence = stage_root / "evidence"
    config = stage_root / "config"
    errors: list[str] = []
    browser_status = "not_run"
    fixture_integrity = "not_run"
    segregation = "not_run"
    stage_preparation = "not_run"

    browser_marker = evidence / "browser-execution.status"
    try:
        if browser_marker.exists():
            browser_status = browser_marker.read_text().strip()
            if browser_status == "started":
                browser_status = "failed"
                browser_marker.write_text("failed\n")
            elif browser_status not in {"passed", "failed"}:
                errors.append("browser execution marker is invalid")
                browser_status = "failed"
    except OSError:
        errors.append("browser execution marker is inaccessible")
        browser_status = "failed"

    prepared_marker = evidence / "stage-prepared.status"
    try:
        if prepared_marker.exists():
            if prepared_marker.read_text().strip() != "prepared":
                raise ValueError("invalid stage preparation marker")
            stage_preparation = "passed"
    except (OSError, ValueError):
        errors.append("stage preparation marker is invalid or inaccessible")
        stage_preparation = "failed"

    if stage_preparation == "passed":
        baseline = evidence / "config-before.sha256"
        catalogue = config / "astv" / "astv_intent_catalogue.yaml"
        mapping = config / "AdvNFC" / "advnfc_tag_mapping.yaml"
        required_config = [
            config / "configuration.yaml",
            config / "staging" / "prepare_stage.py",
            config / "staging" / "browser-session.json",
            config / "staging" / "private-artifact-secrets.json",
        ]

        try:
            expected_catalogue = _baseline_hash(baseline, CATALOGUE_SUFFIX)
            expected_mapping = _baseline_hash(baseline, MAPPING_SUFFIX)
            if _sha256(catalogue) != expected_catalogue or _sha256(mapping) != expected_mapping:
                raise ValueError("fixture hash mismatch")
            fixture_integrity = "passed"
        except (OSError, ValueError):
            errors.append("required baseline or fixture is missing, inaccessible, invalid, or changed")
            fixture_integrity = "failed"

        try:
            if not config.is_dir():
                raise FileNotFoundError("staging configuration directory is missing")
            for required in required_config:
                required.read_bytes()
            for candidate in config.rglob("*"):
                if candidate.is_symlink():
                    raise ValueError("staging configuration contains a symlink")
                if candidate.is_relative_to(config / "staging"):
                    continue
                if candidate.is_file():
                    if FORBIDDEN_STAGE_CONTENT.search(candidate.read_bytes()):
                        raise ValueError("forbidden production-like content detected")
            segregation = "passed"
        except (OSError, ValueError):
            errors.append("required staging configuration is missing, inaccessible, unsafe, or cannot be scanned")
            segregation = "failed"

    result = {
        "browser_checks": browser_status,
        "errors": errors,
        "fixture_integrity": fixture_integrity,
        "restoration": "not_applicable_read_only",
        "segregation": segregation,
        "stage_preparation": stage_preparation,
    }
    try:
        _write_json(evidence / "post-browser-validation.json", result)
    except OSError:
        return 1
    return 0 if not errors and browser_status != "failed" else 1


def authorize_upload(stage_root: Path) -> int:
    evidence = stage_root / "evidence"
    try:
        if not evidence.is_dir() or evidence.is_symlink():
            return 1
        privacy = json.loads((evidence / "artifact-privacy.json").read_text())
        if (
            privacy.get("status") != "passed"
            or privacy.get("trace_capture") != "disabled"
            or not isinstance(privacy.get("secret_patterns_checked"), int)
            or privacy["secret_patterns_checked"] < 5
        ):
            return 1
        if not (evidence / "post-browser-validation.json").is_file():
            return 1
        disposal = (evidence / "disposal.txt").read_text().splitlines()
        if disposal != ["containers_removed=true", "network_removed=true"]:
            return 1
        for private_name in PRIVATE_FILENAMES:
            if (stage_root / "config" / "staging" / private_name).exists():
                return 1
        for candidate in evidence.rglob("*"):
            if candidate.is_symlink():
                return 1
            lowered = candidate.name.lower()
            if candidate.is_file():
                if "trace" in lowered or candidate.suffix.lower() in {".webm", ".zip"}:
                    return 1
                with candidate.open("rb") as stream:
                    stream.read(1)
            elif not candidate.is_dir():
                return 1
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 1
    return 0


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: evidence_controls.py post-browser|authorize-upload STAGE_ROOT")
    action, root = sys.argv[1], Path(sys.argv[2])
    if action == "post-browser":
        raise SystemExit(post_browser(root))
    if action == "authorize-upload":
        raise SystemExit(authorize_upload(root))
    raise SystemExit(f"unknown action: {action}")


if __name__ == "__main__":
    main()
