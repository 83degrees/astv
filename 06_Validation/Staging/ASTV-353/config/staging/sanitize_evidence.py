"""Redact disposable credentials from staging evidence before artifact upload."""

from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> None:
    secrets_path = Path(sys.argv[1])
    evidence_root = Path(sys.argv[2])
    payload = json.loads(secrets_path.read_text())
    secret_values = [*payload["admin"], *payload["reader"], payload["admin_access_token"]]
    patterns = sorted((value.encode() for value in secret_values if value), key=len, reverse=True)
    redacted_files: list[str] = []

    for path in sorted(candidate for candidate in evidence_root.rglob("*") if candidate.is_file()):
        content = path.read_bytes()
        redacted = content
        for pattern in patterns:
            redacted = redacted.replace(pattern, b"[REDACTED]")
        if redacted != content:
            path.write_bytes(redacted)
            redacted_files.append(path.relative_to(evidence_root).as_posix())

    for path in (candidate for candidate in evidence_root.rglob("*") if candidate.is_file()):
        content = path.read_bytes()
        assert not any(pattern in content for pattern in patterns), path

    (evidence_root / "artifact-privacy.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "secret_patterns_checked": len(patterns),
                "redacted_files": redacted_files,
                "trace_capture": "disabled",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
