# tests/test-rep-export-Windows/test_tiddler_exporter.py

import sys
import importlib.util
from pathlib import Path
import json
import pytest
from cli_utils_Windows import load_ignore_spec, is_ignored

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rep_export_Windows"))

project_root = Path(__file__).resolve().parents[2]
windows_dir = project_root / "rep-export-Windows"
linuxmac_dir = project_root / "rep_export_LINUXandMAC"

if str(linuxmac_dir) in sys.path:
    sys.path.remove(str(linuxmac_dir))
if "cli_utils" in sys.modules:
    del sys.modules["cli_utils"]
if str(windows_dir) not in sys.path:
    sys.path.insert(0, str(windows_dir))


@pytest.fixture
def tiddler_exporter(tmp_path, monkeypatch):
    """Prepara un entorno temporal y carga dinámicamente el módulo."""
    # Crear estructura de proyecto falsa
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".gitignore").write_text("__pycache__/\nsecret.env\n")

    (repo_dir / "estructura.txt").write_text("estructura")
    (repo_dir / "visible.py").write_text("print('ok')")
    (repo_dir / "secret.env").write_text("NO_EXPORT=1")
    (repo_dir / "config.toml").write_text("[project]\nname = 'test'")

    # Redefinir ROOT_DIR para apuntar al repo falso
    module_path = Path(__file__).resolve().parents[2] / "rep_export_Windows" / "tiddler_exporter_windows.py"
    spec = importlib.util.spec_from_file_location("tiddler_exporter", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tiddler_exporter"] = mod
    spec.loader.exec_module(mod)

    monkeypatch.setattr(mod, "ROOT_DIR", repo_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", repo_dir / "tiddlers-export")
    monkeypatch.setattr(mod, "HASH_FILE", repo_dir / ".hashes.json")

    return mod


def test_gitignore_excludes_secret_files(tiddler_exporter):
    tiddler_exporter.export_tiddlers(dry_run=False)
    out_dir = tiddler_exporter.OUTPUT_DIR
    files = [f.name for f in out_dir.glob("*.json")]
    assert all("secret" not in f for f in files), "Archivo ignorado fue exportado por error."


def test_always_include_estructura_and_gitignore(tiddler_exporter):
    tiddler_exporter.export_tiddlers(dry_run=False)
    files = [f.name for f in tiddler_exporter.OUTPUT_DIR.glob("*.json")]
    expected = ["-estructura.txt.json", "-.gitignore.json"]
    for name in expected:
        assert name in files, f"{name} debería estar presente siempre."


def test_toml_files_are_exported(tiddler_exporter):
    tiddler_exporter.export_tiddlers(dry_run=False)
    out_file = tiddler_exporter.OUTPUT_DIR / "-config.toml.json"
    assert out_file.exists(), "Archivo .toml no fue exportado correctamente"
    content = json.loads(out_file.read_text(encoding="utf-8"))
    assert "project" in content["text"], "Contenido del archivo .toml no fue exportado correctamente"
