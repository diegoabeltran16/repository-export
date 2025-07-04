# tests/test-rep-export-LINUXandMAC/test_generate_structure_LINUX&MAC.py

import os
import sys
import argparse
import importlib.util
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

windows_dir = project_root / "rep-export-Windows"
linuxmac_dir = project_root / "rep_export_LINUXandMAC"

# Elimina el path de Windows si está en sys.path
if str(windows_dir) in sys.path:
    sys.path.remove(str(windows_dir))

# Elimina cli_utils del cache de módulos si ya fue importado
if "cli_utils" in sys.modules:
    del sys.modules["cli_utils"]

# Asegura que el path de Linux/Mac esté primero
if str(linuxmac_dir) not in sys.path:
    sys.path.insert(0, str(linuxmac_dir))

# Ahora sí importa tus módulos
import tag_mapper_UNIX
from cli_utils_UNIX import load_ignore_spec, is_ignored

def load_module():
    """
    Carga dinámicamente el módulo generate_structure_UNIX.py
    desde rep_export_LINUXandMAC para poder probar sus funciones.
    """
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / 'rep_export_LINUXandMAC' / 'generate_structure_UNIX.py'
    spec = importlib.util.spec_from_file_location('generate_structure', str(script_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def gs_module():
    return load_module()

def test_ascii_tree_filters_hidden_and_ignored(gs_module, tmp_path):
    # Prepara estructura con archivos/carpetas válidas y excluibles
    (tmp_path / 'keep.txt').write_text('keep')
    d = tmp_path / 'dir'
    d.mkdir()
    (d / 'inside.md').write_text('inside')

    # Elementos que deben excluirse por defecto
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

    lines = gs_module.ascii_tree(
        root=tmp_path,
        repo_root=tmp_path,
        prefix='',
        args=args,
        ignore_spec=None  # <-- Cambiado
    )
    output = "\n".join(lines)

    # Los válidos sí deben aparecer
    assert 'keep.txt' in output
    assert 'dir' in output
    assert 'inside.md' in output

    # Los excluidos no deben aparecer
    for excl in ['.git', '__pycache__', 'node_modules', 'secret.pyc', '.DS_Store']:
        assert excl not in output, f"Se encontró elemento excluido: {excl}"

def test_honor_gitignore(gs_module, tmp_path):
    # Crea .gitignore que excluye "keep"
    (tmp_path / '.gitignore').write_text('keep\n')

    # Archivos/directorios de prueba
    (tmp_path / 'keep').mkdir()
    (tmp_path / 'other').mkdir()

    args = argparse.Namespace(
        exclude=[],
        honor_gitignore=True,
        exclude_from=None,
        verbose=0
    )
    ignore_spec = gs_module.load_ignore_spec(tmp_path)  # <-- Cambiado
    lines = gs_module.ascii_tree(
        root=tmp_path,
        repo_root=tmp_path,
        prefix='',
        args=args,
        ignore_spec=ignore_spec  # <-- Cambiado
    )
    output = "\n".join(lines)

    # "other" debe quedar, "keep" no
    assert 'other' in output
    assert 'keep' not in output

def test_write_atomic_creates_file(gs_module, tmp_path):
    # Probar que write_atomic crea y escribe correctamente
    out_file = tmp_path / 'out.txt'
    content_lines = ['line1', 'line2', 'line3']

    gs_module.write_atomic(out_file, content_lines)

    # Leer y comparar contenido
    read_back = out_file.read_text(encoding='utf-8').splitlines()
    assert read_back == content_lines

    # En Unix verificar permisos 0o600
    if os.name != 'nt':
        mode = out_file.stat().st_mode & 0o777
        assert mode == 0o600
