import argparse
from pathlib import Path

import pytest

pytest.importorskip("requests")

from scripts import plugins


def test_cmd_sync_recipes_uses_default_dir(monkeypatch, tmp_path):
    packages = {"echo": "echo-pkg", "foo": "foo-pkg"}

    def fake_run(cmd, *a, **k):
        dest = Path(cmd[cmd.index("--target") + 1])
        pkg = cmd[-1]
        (dest / pkg).write_text("installed")

        class Res:
            returncode = 0

        return Res()

    monkeypatch.setattr(plugins, "load_registry", lambda section="plugins", update=False: packages)
    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "RECIPE_DOWNLOAD_DIR", tmp_path)

    args = argparse.Namespace(dest=None, update=False)
    rc = plugins._cmd_sync_recipes(args)
    assert rc == 0
    for pkg in packages.values():
        assert (tmp_path / pkg).is_file()

