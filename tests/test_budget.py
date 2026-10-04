"""Tests for budget packing."""

import pytest

from ctx_budget.budget import format_report, pack_files
from ctx_budget.scan import FileStat


def _files():
    return [
        FileStat("a.py", 100, 400),
        FileStat("b.py", 50, 200),
        FileStat("c.py", 500, 2000),
    ]


def test_everything_fits():
    r = pack_files(_files(), context_window=1000)
    assert len(r.included) == 3
    assert r.excluded == []
    assert r.tokens_used == 650


def test_biggest_first_packing():
    # 600 usable: c.py (500) fits, then a.py (100) fits, b.py (50) does not.
    r = pack_files(_files(), context_window=600)
    assert [f.path for f in r.included] == ["c.py", "a.py"]
    assert [f.path for f in r.excluded] == ["b.py"]


def test_reserve_shrinks_budget():
    r = pack_files(_files(), context_window=1000, reserved_for_output=500)
    assert r.usable_tokens == 500
    assert r.tokens_left == r.usable_tokens - r.tokens_used


def test_must_include_goes_first():
    # window 200: must-include b.py (50) packs first; a.py (100) also fits;
    # c.py (500) is excluded.
    r = pack_files(_files(), context_window=200, must_include=["b.py"])
    assert r.included[0].path == "b.py"
    assert [f.path for f in r.included] == ["b.py", "a.py"]
    assert [f.path for f in r.excluded] == ["c.py"]


def test_invalid_window_raises():
    with pytest.raises(ValueError):
        pack_files(_files(), context_window=0)
    with pytest.raises(ValueError):
        pack_files(_files(), context_window=100, reserved_for_output=200)


def test_report_mentions_key_numbers():
    r = pack_files(_files(), context_window=600)
    report = format_report(r, total_scanned_tokens=650)
    assert "600" in report
    assert "c.py" in report
