# tests/test-rep-export-Windows/test_detect_root.py
"""
Tests unitarios para rep_export_Windows/detect_root.py

Escenarios cubiertos:
  1. REPO_EXPORT_ROOT válido → retorna esa ruta directamente.
  2. REPO_EXPORT_ROOT inválido → imprime advertencia a stderr y cae a detección .git.
  3. Un único .git en el árbol → retorna ese directorio.
  4. Repos anidados → retorna el más externo.
  5. Sin .git en ningún nivel → fallback a tmp_path con advertencia en stderr.
"""
import sys
import importlib.util
from pathlib import Path
import pytest

# Cargar el módulo bajo prueba sin contaminar sys.modules globales
def _load_detect_root():
    module_path = Path(__file__).resolve().parents[2] / "rep_export_Windows" / "detect_root.py"
    spec = importlib.util.spec_from_file_location("detect_root_win", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_detect_root()
find_repo_root = _mod.find_repo_root


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Garantiza que REPO_EXPORT_ROOT no interfiera entre tests."""
    monkeypatch.delenv("REPO_EXPORT_ROOT", raising=False)


# ── Test 1 ──────────────────────────────────────────────────────────────────
def test_env_var_returns_path(tmp_path, monkeypatch):
    """REPO_EXPORT_ROOT válido → retorna esa ruta sin buscar .git."""
    monkeypatch.setenv("REPO_EXPORT_ROOT", str(tmp_path))
    result = find_repo_root(tmp_path / "module.py")
    assert result == tmp_path


# ── Test 2 ──────────────────────────────────────────────────────────────────
def test_env_var_invalid_prints_warning(tmp_path, monkeypatch, capsys):
    """REPO_EXPORT_ROOT inválido → advertencia en stderr y cae a búsqueda .git."""
    monkeypatch.setenv("REPO_EXPORT_ROOT", str(tmp_path / "no_existe"))
    repo = tmp_path / "my_repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    result = find_repo_root(repo / "rep_export_Windows" / "module.py")
    assert result == repo
    captured = capsys.readouterr()
    assert "no es un directorio válido" in captured.err


# ── Test 3 ──────────────────────────────────────────────────────────────────
def test_single_git_root(tmp_path):
    """Un único .git en el árbol → retorna ese directorio."""
    repo = tmp_path / "my_repo"
    inner = repo / "rep_export_Windows"
    inner.mkdir(parents=True)
    (repo / ".git").mkdir()
    result = find_repo_root(inner / "module.py")
    assert result == repo


# ── Test 4 ──────────────────────────────────────────────────────────────────
def test_nested_repos_returns_outermost(tmp_path):
    """Herramienta anidada en otro repo → retorna el repo más externo."""
    outer = tmp_path / "outer_repo"
    outer.mkdir()
    (outer / ".git").mkdir()
    inner = outer / "repository-export"
    inner.mkdir()
    (inner / ".git").mkdir()
    result = find_repo_root(inner / "rep_export_Windows" / "module.py")
    assert result == outer


# ── Test 5 ──────────────────────────────────────────────────────────────────
def test_no_git_returns_fallback(tmp_path, capsys):
    """Sin .git en ningún nivel → fallback a parent del módulo + advertencia."""
    # Ensure tmp_path is not itself inside a git repo
    if any((p / ".git").exists() for p in tmp_path.parents):
        pytest.skip("tmp_path está dentro de un repo git; test no aplica en este entorno")
    module_dir = tmp_path / "rep_export_Windows"
    result = find_repo_root(module_dir / "module.py")
    # fallback = module_dir.parent = tmp_path
    assert result == tmp_path
    captured = capsys.readouterr()
    assert "No se encontró ningún .git" in captured.err
