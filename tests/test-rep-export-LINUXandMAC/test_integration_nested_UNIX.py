# tests/test-rep-export-LINUXandMAC/test_integration_nested_UNIX.py
"""
Test de integración – Linux/macOS:
Verifica que el exportador lee el repo más externo cuando la herramienta
está anidada dentro de otro repo git.

Flujo:
  outer_repo/.git
  outer_repo/repository-export/.git          ← herramienta anidada
  outer_repo/MARKER.py                        ← archivo objetivo

  find_repo_root(...) debe devolver outer_repo
  export_tiddlers() debe generar MARKER.py.json
"""
import sys
import importlib.util
from pathlib import Path
import pytest

# Añadir rep_export_LINUXandMAC y project_root al path
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
_linuxmac_dir = _project_root / "rep_export_LINUXandMAC"
if str(_linuxmac_dir) not in sys.path:
    sys.path.insert(0, str(_linuxmac_dir))


def _load_module(unique_name: str, rel_path: str):
    """Carga dinámicamente un módulo desde una ruta relativa al proyecto."""
    module_path = _project_root / rel_path
    spec = importlib.util.spec_from_file_location(unique_name, str(module_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.integration
def test_exporter_reads_outermost_repo(tmp_path, monkeypatch):
    """Herramienta anidada en otro repo → exporta archivos del repo externo."""
    # 1. Estructura de repos anidados
    outer = tmp_path / "outer_repo"
    outer.mkdir()
    (outer / ".git").mkdir()

    tool = outer / "repository-export"
    tool.mkdir()
    (tool / ".git").mkdir()

    # Archivo objetivo en el outer repo (extensión .py → VALID_EXT)
    (outer / "MARKER.py").write_text("# archivo del repo objetivo")
    (outer / ".gitignore").write_text("")

    # 2. find_repo_root debe señalar al outer repo
    detect_mod = _load_module("_detect_root_int_u", "rep_export_LINUXandMAC/detect_root.py")
    detected_root = detect_mod.find_repo_root(tool / "rep_export_LINUXandMAC" / "module.py")
    assert detected_root == outer, f"Esperado {outer}, obtenido {detected_root}"

    # 3. Cargar exportador y parchear ROOT_DIR al valor detectado
    exp_mod = _load_module(
        "_tiddler_exp_int_u", "rep_export_LINUXandMAC/tiddler_exporter_UNIX.py"
    )
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    monkeypatch.setattr(exp_mod, "ROOT_DIR", detected_root)
    monkeypatch.setattr(exp_mod, "OUTPUT_DIR", out_dir)
    monkeypatch.setattr(exp_mod, "HASH_FILE", tmp_path / ".hashes.json")
    monkeypatch.setattr(exp_mod, "IGNORE_SPEC", exp_mod.load_ignore_spec(detected_root))

    # 4. Exportar y verificar que MARKER.py fue incluido
    exp_mod.export_tiddlers(dry_run=False)

    files = [f.name for f in out_dir.glob("*.json")]
    assert any("MARKER" in f for f in files), (
        f"MARKER.py del outer repo no fue exportado.\nArchivos generados: {files}"
    )
