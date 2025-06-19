# tests/test-rep-export-Windows/test_tiddler_exporter.py

import sys
import pytest
import importlib.util
from pathlib import Path
from pathspec import PathSpec


@pytest.fixture
def tiddler_exporter(tmp_path, monkeypatch):
    # 1) Crea un repo mock
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    # Archivo .gitignore (vacío por defecto)
    (repo_dir / ".gitignore").write_text("")

    # 2) Carga dinámicamente el módulo tiddler_exporter.py
    module_path = Path(__file__).parent.parent / "rep-export-Windows" / "tiddler_exporter.py"
    spec = importlib.util.spec_from_file_location("tiddler_exporter", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tiddler_exporter"] = mod
    spec.loader.exec_module(mod)

    # 3) Monkeypatch de rutas internas
    monkeypatch.setattr(mod, "ROOT_DIR", repo_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", repo_dir / "tiddlers-export")
    monkeypatch.setattr(mod, "HASH_FILE", repo_dir / ".hashes.json")

    return mod, repo_dir


def collect_exported(mod, repo_dir):
    # Reconstruye el spec según .gitignore actual
    patterns = [ln for ln in (repo_dir / ".gitignore").read_text().splitlines()
                if ln.strip() and not ln.startswith("#")]
    mod.IGNORE_SPEC = PathSpec.from_lines("gitwildmatch", patterns)
    # Ejecuta la exportación real
    mod.export_tiddlers(dry_run=False)
    # Recoge nombres de tiddlers exportados
    exported = sorted(p.stem for p in (repo_dir / "tiddlers-export").glob("*.json"))
    return exported


def test_gitignore_excludes_secret_files(tiddler_exporter):
    mod, repo = tiddler_exporter
    # Prepara archivos
    (repo / ".gitignore").write_text("secret.txt\n")
    (repo / "visible.py").write_text("print('ok')")
    (repo / "secret.txt").write_text("dont export me")

    exported = collect_exported(mod, repo)
    # visible.py sí debe exportarse
    assert "-visible.py" in exported
    # secret.txt NO debe exportarse
    assert "-secret.txt" not in exported


def test_always_include_estructura_and_gitignore(tiddler_exporter):
    mod, repo = tiddler_exporter
    # Prepara archivos
    (repo / ".gitignore").write_text("estructura.txt\n")
    (repo / "estructura.txt").write_text("tree")
    (repo / "keep.md").write_text("ok")  # md no válido, no debe exportarse

    exported = collect_exported(mod, repo)
    # estructura.txt siempre incluido
    assert "-estructura.txt" in exported
    # .gitignore siempre incluido
    assert "-.gitignore" in exported
    # keep.md no está en VALID_EXT ni SPECIAL_FILENAMES: no debe exportarse
    assert "-keep.md" not in exported


def test_toml_files_are_exported(tiddler_exporter):
    mod, repo = tiddler_exporter
    # Prepara archivos
    (repo / ".gitignore").write_text("")  # nada ignorado
    (repo / "config.toml").write_text("key = 'value'")
    (repo / "other.txt").write_text("ignore me")  # txt no válido

    exported = collect_exported(mod, repo)
    # config.toml debe exportarse
    assert "-config.toml" in exported
    # other.txt no válido, no debe exportarse
    assert "-other.txt" not in exported
