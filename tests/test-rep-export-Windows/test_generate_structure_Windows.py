# tests/test-rep-export-Windows/test_generate_structure_Windows.py

import os
import sys
import argparse
import importlib.util
from pathlib import Path
import pytest


def load_module():
    # Subir dos niveles desde tests/.../test_...py → raíz del repo
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / 'rep-export-Windows' / 'generate_structure.py'
    spec = importlib.util.spec_from_file_location("generate_structure", str(script_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def gs_module():
    return load_module()


def test_ascii_tree_filters_hidden_and_ignored(gs_module, tmp_path):
    # Prepara un arbol con cosas válidas y excluibles
    (tmp_path / 'keep.txt').write_text('keep')
    d = tmp_path / 'folder'
    d.mkdir()
    (d / 'file.md').write_text('hello')

    # Crea elementos que deben ignorarse
    (tmp_path / '.git').mkdir()
    (tmp_path / '__pycache__').mkdir()
    (tmp_path / 'node_modules').mkdir()
    (tmp_path / 'secret.pyc').write_text('')
    (tmp_path / '.DS_Store').write_text('')

    args = argparse.Namespace(
        exclude=[],
        honor_gitignore=False,
        exclude_from=None,
        verbose=0
    )
    gitignore_patterns = []

    lines = gs_module.ascii_tree(tmp_path, tmp_path, prefix='', args=args, gitignore_patterns=gitignore_patterns)
    output = "\n".join(lines)

    # Deberían verse los válidos
    assert 'keep.txt' in output
    assert 'folder' in output
    assert 'file.md' in output

    # No deberían verse los excluidos por defecto
    for excl in ['.git', '__pycache__', 'node_modules', 'secret.pyc', '.DS_Store']:
        assert excl not in output, f"Encontrado elemento excluido: {excl}"


def test_honor_gitignore(gs_module, tmp_path):
    # Crea .gitignore que excluye keep.txt
    (tmp_path / '.gitignore').write_text('keep.txt\n')

    # Archivos
    (tmp_path / 'keep.txt').write_text('x')
    (tmp_path / 'other.txt').write_text('y')

    args = argparse.Namespace(
        exclude=[],
        honor_gitignore=True,
        exclude_from=None,
        verbose=0
    )
    patterns = gs_module.load_gitignore_patterns(tmp_path)
    lines = gs_module.ascii_tree(tmp_path, tmp_path, prefix='', args=args, gitignore_patterns=patterns)
    output = "\n".join(lines)

    # keep.txt queda fuera, other.txt dentro
    assert 'other.txt' in output
    assert 'keep.txt' not in output


def test_write_atomic_creates_file(gs_module, tmp_path):
    out_file = tmp_path / 'out.txt'
    lines = ['line1', 'line2', 'line3']
    gs_module.write_atomic(out_file, lines)

    # Verifica contenido
    content = out_file.read_text(encoding='utf-8').splitlines()
    assert content == lines

    # En Unix la permisión resultante suele ser 0o600
    if os.name != 'nt':
        mode = out_file.stat().st_mode & 0o777
        assert mode == 0o600
