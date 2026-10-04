"""Tests for directory scanning."""

import os

from ctx_budget.scan import scan_directory


def _write(root, rel, content):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(content)
    return path


def test_scan_counts_text_files(tmp_path):
    _write(str(tmp_path), "a.py", "print('hello')\n" * 50)
    _write(str(tmp_path), "sub/b.md", "# docs\n" * 30)
    result = scan_directory(str(tmp_path))
    paths = {f.path for f in result.files}
    assert "a.py" in paths
    assert os.path.join("sub", "b.md") in paths
    assert result.total_tokens > 0


def test_scan_skips_git_dir(tmp_path):
    _write(str(tmp_path), ".git/objects/big.py", "x = 1\n" * 1000)
    _write(str(tmp_path), "real.py", "y = 2\n")
    result = scan_directory(str(tmp_path))
    assert {f.path for f in result.files} == {"real.py"}


def test_scan_skips_binary_extensions(tmp_path):
    _write(str(tmp_path), "img.png", "not really a png but has the ext")
    result = scan_directory(str(tmp_path))
    assert result.files == []
    assert len(result.skipped) == 1


def test_scan_sorts_by_tokens_descending(tmp_path):
    _write(str(tmp_path), "small.py", "x = 1\n")
    _write(str(tmp_path), "big.py", "x = 1\n" * 500)
    result = scan_directory(str(tmp_path))
    assert result.files[0].path == "big.py"
