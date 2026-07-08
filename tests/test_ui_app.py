from __future__ import annotations

import sys
from types import SimpleNamespace

from link_checker.ui import app


def test_main_creates_local_desktop_window(monkeypatch) -> None:
    calls = {}
    fake_window = object()

    class FakeApi:
        def set_window(self, window) -> None:
            calls["api_window"] = window

    def create_window(*args, **kwargs):
        calls["create_window"] = (args, kwargs)
        return fake_window

    def start(*args, **kwargs):
        calls["start"] = (args, kwargs)

    fake_webview = SimpleNamespace(create_window=create_window, start=start)

    monkeypatch.setitem(sys.modules, "webview", fake_webview)
    monkeypatch.setattr(app, "LinkCheckerUIApi", FakeApi)
    monkeypatch.setattr(app, "_load_html", lambda: "<html>ok</html>")

    app.main()

    args, kwargs = calls["create_window"]
    assert args == ("Link Checker",)
    assert kwargs["html"] == "<html>ok</html>"
    assert "url" not in kwargs
    assert kwargs["js_api"].__class__ is FakeApi
    assert calls["api_window"] is fake_window
    assert calls["start"] == ((), {"debug": False})


def test_main_prepares_pythonnet_before_webview_import(monkeypatch) -> None:
    imported_runtime = {}
    fake_window = object()

    class FakeApi:
        def set_window(self, window) -> None:
            pass

    class LazyWebview:
        def create_window(self, *args, **kwargs):
            return fake_window

        def start(self, *args, **kwargs):
            pass

    def import_webview(name, *args, **kwargs):
        if name == "webview":
            import os

            imported_runtime["value"] = os.environ.get("PYTHONNET_RUNTIME")
            return LazyWebview()
        return original_import(name, *args, **kwargs)

    original_import = __builtins__["__import__"]
    monkeypatch.delenv("PYTHONNET_RUNTIME", raising=False)
    monkeypatch.delitem(sys.modules, "webview", raising=False)
    monkeypatch.setattr("builtins.__import__", import_webview)
    monkeypatch.setattr(app, "LinkCheckerUIApi", FakeApi)
    monkeypatch.setattr(app, "_load_html", lambda: "<html>ok</html>")

    app.main()

    assert imported_runtime["value"] == "netfx"


def test_prepare_pythonnet_runtime_redirects_frozen_dll(monkeypatch, tmp_path) -> None:
    source_runtime = tmp_path / "bundle" / "pythonnet" / "runtime"
    source_runtime.mkdir(parents=True)
    source_dll = source_runtime / "Python.Runtime.dll"
    source_dll.write_bytes(b"dll")
    target_root = tmp_path / "temp"
    fake_pythonnet = SimpleNamespace(__file__="original")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setenv("PYTHONNET_RUNTIME", "coreclr")
    monkeypatch.setattr(app.tempfile, "gettempdir", lambda: str(target_root))
    monkeypatch.setitem(sys.modules, "pythonnet", fake_pythonnet)

    app._prepare_pythonnet_runtime()

    target_dll = (
        target_root / "link_checker_pythonnet" / "pythonnet" / "runtime" / ("Python.Runtime.dll")
    )
    assert target_dll.read_bytes() == b"dll"
    assert fake_pythonnet.__file__ == str(
        target_root / "link_checker_pythonnet" / "pythonnet" / "__init__.py"
    )
