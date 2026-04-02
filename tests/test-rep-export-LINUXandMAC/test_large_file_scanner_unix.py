# tests/test-rep-export-LINUXandMAC/test_large_file_scanner_unix.py

import sys
import importlib.util
import json
import gzip
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rep_export_LINUXandMAC"))

from large_file_scanner import scan_large_files, fmt_size, suggest_max, ScanResult


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_repo(tmp_path, files: dict) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    for name, size in files.items():
        p = repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x" * size)
    return repo


# ── fmt_size ────────────────────────────────────────────────────────────────

def test_fmt_size_bytes():
    assert fmt_size(512) == "512 B"

def test_fmt_size_kb():
    assert "KB" in fmt_size(2048)

def test_fmt_size_mb():
    assert "MB" in fmt_size(2 * 1024 * 1024)


# ── suggest_max ─────────────────────────────────────────────────────────────

def test_suggest_max_below_1mb():
    result = suggest_max(100 * 1024)
    assert result >= 1 * 1024 * 1024

def test_suggest_max_scales_with_median():
    median = 3 * 1024 * 1024
    result = suggest_max(median)
    assert result == 2 * median


# ── scan_large_files ────────────────────────────────────────────────────────

def test_no_large_files(tmp_path):
    repo = _make_repo(tmp_path, {"small.py": 100, "readme.md": 200})
    result = scan_large_files(repo, max_bytes=1 * 1024 * 1024)
    assert result.large == []
    assert result.total == 2


def test_detects_large_files(tmp_path):
    repo = _make_repo(tmp_path, {
        "small.py": 100,
        "big.bin": 2 * 1024 * 1024,
    })
    result = scan_large_files(repo, max_bytes=1 * 1024 * 1024)
    assert len(result.large) == 1
    large_path, large_size = result.large[0]
    assert large_path.name == "big.bin"


def test_large_files_sorted_descending(tmp_path):
    repo = _make_repo(tmp_path, {
        "medium.bin": 1_500_000,
        "huge.bin": 5_000_000,
        "big.bin": 3_000_000,
    })
    result = scan_large_files(repo, max_bytes=1_000_000)
    sizes = [s for _, s in result.large]
    assert sizes == sorted(sizes, reverse=True)


def test_skips_tiddlers_export_dir(tmp_path):
    repo = _make_repo(tmp_path, {"normal.py": 50})
    skip_dir = repo / "tiddlers-export"
    skip_dir.mkdir()
    (skip_dir / "big.json").write_bytes(b"x" * 5_000_000)
    result = scan_large_files(repo, max_bytes=1_000_000)
    assert result.large == []


def test_skips_git_dir(tmp_path):
    repo = _make_repo(tmp_path, {"normal.py": 50})
    git_dir = repo / ".git"
    git_dir.mkdir()
    (git_dir / "pack.idx").write_bytes(b"x" * 5_000_000)
    result = scan_large_files(repo, max_bytes=1_000_000)
    assert result.large == []


def test_stats_mean_median(tmp_path):
    # Three files: 100, 300, 500 bytes → mean/median stored in KB
    repo = _make_repo(tmp_path, {"a.py": 100, "b.py": 300, "c.py": 500})
    result = scan_large_files(repo, max_bytes=1_000_000)
    assert result.total == 3
    expected_mean_kb = 300 / 1024
    assert abs(result.mean - expected_mean_kb) < 0.01
    expected_median_kb = 300 / 1024
    assert abs(result.median - expected_median_kb) < 0.01


def test_suggested_max_in_result(tmp_path):
    repo = _make_repo(tmp_path, {"a.py": 100})
    result = scan_large_files(repo, max_bytes=1_000_000)
    assert result.suggested_max_bytes >= 1 * 1024 * 1024


# ── build_large_tiddler (via tiddler_exporter_UNIX) ─────────────────────────

def _load_exporter(tmp_path, monkeypatch):
    module_path = Path(__file__).resolve().parents[2] / "rep_export_LINUXandMAC" / "tiddler_exporter_UNIX.py"
    spec = importlib.util.spec_from_file_location("tiddler_exporter_u", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tiddler_exporter_u"] = mod
    spec.loader.exec_module(mod)

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(mod, "ROOT_DIR", repo_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", repo_dir / "tiddlers-export")
    monkeypatch.setattr(mod, "HASH_FILE", repo_dir / ".hashes.json")
    return mod, repo_dir


def test_build_large_tiddler_preview_text(tmp_path, monkeypatch):
    mod, repo_dir = _load_exporter(tmp_path, monkeypatch)
    large_file = repo_dir / "large.py"
    large_file.write_text("A" * 200_000, encoding="utf-8")

    tiddler = mod.build_large_tiddler(large_file, action="preview", preview_bytes=1024)
    assert tiddler["large_file"] is True
    assert tiddler["large_action"] == "preview"
    assert "PREVIEW" in tiddler["text"] or "A" in tiddler["text"]


def test_build_large_tiddler_binary_detected(tmp_path, monkeypatch):
    mod, repo_dir = _load_exporter(tmp_path, monkeypatch)
    bin_file = repo_dir / "data.bin"
    bin_file.write_bytes(b"\x00\x01\x02" * 1000)

    tiddler = mod.build_large_tiddler(bin_file, action="preview", preview_bytes=512)
    assert "[binary]" in tiddler["text"] or "binario" in tiddler["text"].lower()


def test_build_large_tiddler_copy_creates_gz(tmp_path, monkeypatch):
    mod, repo_dir = _load_exporter(tmp_path, monkeypatch)
    large_file = repo_dir / "large.txt"
    large_file.write_text("B" * 50_000, encoding="utf-8")
    (repo_dir / "tiddlers-export").mkdir(exist_ok=True)
    monkeypatch.setattr(mod, "OUTPUT_DIR", repo_dir / "tiddlers-export")

    tiddler = mod.build_large_tiddler(large_file, action="copy", preview_bytes=1024)
    assert tiddler["large_action"] == "copy"
    gz_files = list((repo_dir / "tiddlers-export" / "large").glob("*.gz"))
    assert len(gz_files) == 1
    with gzip.open(gz_files[0], "rb") as f:
        content = f.read()
    assert b"B" * 100 in content


def test_export_tiddlers_skips_large_by_default(tmp_path, monkeypatch):
    mod, repo_dir = _load_exporter(tmp_path, monkeypatch)
    (repo_dir / "normal.py").write_text("hello")
    (repo_dir / "big.bin").write_bytes(b"x" * 2_000_000)
    out_dir = repo_dir / "tiddlers-export"
    monkeypatch.setattr(mod, "OUTPUT_DIR", out_dir)
    monkeypatch.setattr(mod, "MAX_FILE_SIZE_BYTES", 1_000_000)

    mod.export_tiddlers(dry_run=False, include_large=False)
    exported = [f.name for f in out_dir.glob("*.json")]
    assert all("big" not in f for f in exported)


def test_export_tiddlers_includes_large_when_flag_set(tmp_path, monkeypatch):
    mod, repo_dir = _load_exporter(tmp_path, monkeypatch)
    (repo_dir / "big.txt").write_text("C" * 2_000_000, encoding="utf-8")
    out_dir = repo_dir / "tiddlers-export"
    monkeypatch.setattr(mod, "OUTPUT_DIR", out_dir)
    monkeypatch.setattr(mod, "MAX_FILE_SIZE_BYTES", 100)

    mod.export_tiddlers(dry_run=False, include_large=True, large_action="preview")
    exported = [f.name for f in out_dir.glob("*.json")]
    assert any("big" in f for f in exported)
