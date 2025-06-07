import argparse
import importlib.util
from pathlib import Path
import os

def load_generate_structure_module():
    # Ubica el script generate_structure.py
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / 'rep-export-Windows' / 'generate_structure.py'
    spec = importlib.util.spec_from_file_location('generate_structure', script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ascii_tree_filters_hidden_and_ignored(tmp_path, monkeypatch):
    # Prepara un repo dummy
    root = tmp_path
    # Directorios y archivos a ignorar
    (root / '.git').mkdir()
    (root / '.git' / 'config').write_text('x')
    (root / 'node_modules').mkdir()
    (root / 'node_modules' / 'mod.js').write_text('x')
    (root / '.hidden').write_text('secret')
    # Archivo válido y directorio válido
    (root / 'keep.txt').write_text('keep')
    d = root / 'dir'
    d.mkdir()
    (d / 'inside.md').write_text('inside')

    # Carga el módulo
    module = load_generate_structure_module()
    args = argparse.Namespace(exclude=[], honor_gitignore=False, exclude_from=None, verbose=0)
    lines = module.ascii_tree(root, root, prefix='', args=args, gitignore_patterns=[])

    # Debe listar sólo dir/inside.md y keep.txt
    expected = [
        '├── dir',
        '│   └── inside.md',
        '└── keep.txt'
    ]
    assert lines == expected


def test_honor_gitignore(tmp_path):
    # Prepara repo dummy con .gitignore
    root = tmp_path
    (root / '.gitignore').write_text('keep.txt')
    # Archivos
    (root / 'keep.txt').write_text('keep')
    (root / 'other.txt').write_text('other')

    module = load_generate_structure_module()
    args = argparse.Namespace(exclude=[], honor_gitignore=True, exclude_from=None, verbose=0)
    gitignore_patterns = module.load_gitignore_patterns(root)
    lines = module.ascii_tree(root, root, prefix='', args=args, gitignore_patterns=gitignore_patterns)

    # Con .gitignore debe excluir keep.txt, sólo queda other.txt
    expected = ['└── other.txt']
    assert lines == expected


def test_write_atomic_creates_file(tmp_path):
    module = load_generate_structure_module()
    output = tmp_path / 'out.txt'
    lines = ['line1', 'line2']
    module.write_atomic(output, lines)
    # Verifica contenido
    content = output.read_text(encoding='utf-8').splitlines()
    assert content == lines
    # Verifica permisos en Unix (0o600) si aplica
    if os.name != 'nt':
        mode = output.stat().st_mode & 0o777
        assert mode == 0o600
