"""Zero-API-key demo: budget this very repo for a 200k context window."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ctx_budget import pack_files, scan_directory  # noqa: E402
from ctx_budget.budget import format_report  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    scanned = scan_directory(ROOT)
    result = pack_files(
        scanned.files,
        context_window=200_000,
        reserved_for_output=8_192,
        must_include=["README.md"],
    )
    print(format_report(result, scanned.total_tokens))
    print()
    print(f"Skipped files (binary/ignored): {len(scanned.skipped)}")
