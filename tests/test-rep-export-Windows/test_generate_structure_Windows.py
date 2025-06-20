# tests/test-rep-export-Windows/test_generate_structure_Windows.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rep_export_Windows"))

import importlib.util
import argparse               # ⬅️ añadido para Namespace

import pytest
from cli_utils_Windows import load_ignore_spec, is_ignored


def load_module():
    """
    Carga dinámicamente rep-export-Windows/generate_structure.py
    y asegura que la carpeta rep-export-Windows/ esté en sys.path
    para que 'import cli_utils' funcione correctamente.
    """
    project_root = Path(__file__).resolve().parents[2]
    module_path = project_root / "rep_export_Windows" / "generate_structure_windows.py"

    # Asegurarnos de poder importar cli_utils desde rep-export-Windows/
    windows_pkg = project_root / "rep-export-Windows"
    if str(windows_pkg) not in sys.path:
        sys.path.insert(0, str(windows_pkg))

    spec = importlib.util.spec_from_file_location("generate_structure", str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def gs_module():
    return load_module()


def test_ascii_tree_filters_hidden_and_ignored(gs_module, tmp_path):
    gen = gs_module
    repo = tmp_path / "repo"
    repo.mkdir()

    # Preparamos árbol con .gitignore que oculta __pycache__/ y secret.txt
    (repo / ".gitignore").write_text("__pycache__/\nsecret.txt\n")
    (repo / "visible.txt").write_text("ok")
    (repo / "secret.txt").write_text("no")
    (repo / "__pycache__").mkdir()
    (repo / "__pycache__" / "ignored.pyc").write_text("")

    # 1) Sin honor-gitignore -> secret.txt aparece, __pycache__ NO aparece
    lines_raw = gen.ascii_tree(
        repo,
        repo,
        args=argparse.Namespace(exclude=[], honor_gitignore=False),
        gitignore_spec=None
    )
    assert any("secret.txt" in l for l in lines_raw)
    assert all("__pycache__" not in l for l in lines_raw)

    # 2) Con honor-gitignore -> ambos deben desaparecer
    spec = gen.load_ignore_spec(repo)
    lines_clean = gen.ascii_tree(
        repo,
        repo,
        args=argparse.Namespace(exclude=[], honor_gitignore=True),
        gitignore_spec=spec
    )
    print("DEBUG lines_clean:", lines_clean)  # <-- aquí
    assert all("secret.txt" not in l for l in lines_clean)
    assert all("__pycache__" not in l for l in lines_clean)


def test_honor_gitignore(gs_module, tmp_path):
    gen = gs_module
    repo = tmp_path / "repo2"
    repo.mkdir()

    # .gitignore que ignora *.log
    (repo / ".gitignore").write_text("*.log\n")
    (repo / "a.log").write_text("data")
    (repo / "b.txt").write_text("data")

    spec = gen.load_ignore_spec(repo)
    lines_clean = gen.ascii_tree(
        repo,
        repo,
        args=argparse.Namespace(exclude=[], honor_gitignore=True),
        gitignore_spec=spec
    )
    assert all("a.log" not in l for l in lines_clean)
    assert any("b.txt" in l for l in lines_clean)


def test_write_atomic_creates_file(gs_module, tmp_path):
    gen = gs_module
    out_file = tmp_path / "estructura.txt"
    # Generamos un archivo provisional
    gen.write_atomic(out_file, ["root", "└── file.txt"])

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "root" in content and "file.txt" in content
