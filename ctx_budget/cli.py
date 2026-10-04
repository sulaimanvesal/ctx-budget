"""Command-line interface for ctx-budget."""

import argparse
import sys

from .budget import format_report, pack_files
from .scan import scan_directory


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ctx-budget",
        description="Estimate how much of a directory fits in an LLM context window.",
    )
    p.add_argument("path", nargs="?", default=".",
                   help="directory to scan (default: current directory)")
    p.add_argument("--window", type=int, default=200_000,
                   help="context window size in tokens (default: 200000)")
    p.add_argument("--reserve", type=int, default=8_192,
                   help="tokens to reserve for model output (default: 8192)")
    p.add_argument("--must-include", action="append", default=[],
                   metavar="REL_PATH",
                   help="relative path that must be packed first (repeatable)")
    p.add_argument("--json", action="store_true",
                   help="emit machine-readable JSON instead of the text report")
    return p


def main(argv: list | None = None) -> int:
    args = build_parser().parse_args(argv)

    scanned = scan_directory(args.path)
    result = pack_files(
        scanned.files,
        context_window=args.window,
        reserved_for_output=args.reserve,
        must_include=args.must_include,
    )

    if args.json:
        import json
        print(json.dumps({
            "context_window": result.context_window,
            "reserved_for_output": result.reserved_for_output,
            "usable_tokens": result.usable_tokens,
            "tokens_used": result.tokens_used,
            "tokens_left": result.tokens_left,
            "included": [{"path": f.path, "tokens": f.tokens} for f in result.included],
            "excluded": [{"path": f.path, "tokens": f.tokens} for f in result.excluded],
        }, indent=2))
    else:
        print(format_report(result, scanned.total_tokens))

    return 0


if __name__ == "__main__":
    sys.exit(main())
