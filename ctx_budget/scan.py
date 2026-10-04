"""Directory scanning with token estimates per file."""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field

from .tokenizer import estimate_tokens_file

# Directories that are almost never useful context for an LLM agent.
DEFAULT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".tox",
    ".venv",
    "venv",
    ".env",
    "node_modules",
    ".next",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "target",
    ".idea",
    ".vscode",
}

# Binary-ish extensions we skip rather than tokenize as text.
DEFAULT_SKIP_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".whl", ".so", ".dylib", ".dll",
    ".exe", ".bin", ".mp4", ".mp3", ".wav", ".woff", ".woff2", ".ttf",
}


@dataclass
class FileStat:
    """Token statistics for a single scanned file."""

    path: str           # path relative to the scanned root
    tokens: int
    size_bytes: int
    skipped: bool = False


@dataclass
class ScanResult:
    files: list = field(default_factory=list)
    skipped: list = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return sum(f.tokens for f in self.files)


def _matches_any(name: str, patterns: set) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def scan_directory(
    root: str,
    skip_dirs: set | None = None,
    skip_exts: set | None = None,
    max_file_bytes: int = 2_000_000,
) -> ScanResult:
    """Walk *root*, estimating tokens for every text file.

    Returns a ScanResult with per-file stats; skipped files (binary,
    oversized, or inside ignored dirs) are listed separately.
    """
    skip_dirs = skip_dirs if skip_dirs is not None else DEFAULT_SKIP_DIRS
    skip_exts = skip_exts if skip_exts is not None else DEFAULT_SKIP_EXTS
    root = os.path.abspath(root)
    result = ScanResult()

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in-place so os.walk never descends.
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]

        for fname in filenames:
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root)
            ext = os.path.splitext(fname)[1].lower()

            if _matches_any(fname, skip_exts) or ext in skip_exts:
                result.skipped.append(FileStat(rel, 0, 0, skipped=True))
                continue

            try:
                size = os.path.getsize(full)
            except OSError:
                continue

            if size > max_file_bytes:
                result.skipped.append(FileStat(rel, 0, size, skipped=True))
                continue

            try:
                tokens = estimate_tokens_file(full)
            except (OSError, UnicodeError):
                result.skipped.append(FileStat(rel, 0, size, skipped=True))
                continue

            result.files.append(FileStat(rel, tokens, size))

    result.files.sort(key=lambda f: f.tokens, reverse=True)
    return result
