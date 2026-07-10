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


def test_main_redirects_only_webview_dll_lookup_before_start(monkeypatch) -> None:
    calls = {}
    fake_window = object()
    fake_util = SimpleNamespace(
        __file__="network/webview/util.py",
        interop_dll_path=lambda name: f"network/{name}",
    )
    fake_webview = SimpleNamespace(util=fake_util)

    class FakeApi:
        def set_window(self, window) -> None:
            pass

    def create_window(*args, **kwargs):
        return fake_window

    def start(*args, **kwargs):
        calls["util_file_at_start"] = fake_webview.util.__file__
        calls["core_dll_at_start"] = fake_webview.util.interop_dll_path(
            "Microsoft.Web.WebView2.Core.dll"
        )

    fake_webview.create_window = create_window
    fake_webview.start = start

    monkeypatch.setitem(sys.modules, "webview", fake_webview)
    monkeypatch.setattr(app, "LinkCheckerUIApi", FakeApi)
    monkeypatch.setattr(app, "_load_html", lambda: "<html>ok</html>")
    monkeypatch.setattr(app, "_prepare_pythonnet_runtime", lambda: None)
    monkeypatch.setattr(app, "_prepare_webview_runtime", lambda: str(app.Path("local-webview/lib")))

    app.main()

    assert calls["util_file_at_start"] == "network/webview/util.py"
    assert calls["core_dll_at_start"] == str(
        app.Path("local-webview/lib") / "Microsoft.Web.WebView2.Core.dll"
    )


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


def test_prepare_webview_runtime_copies_frozen_lib_to_local_temp(monkeypatch, tmp_path) -> None:
    source_lib = tmp_path / "bundle" / "webview" / "lib"
    source_lib.mkdir(parents=True)
    (source_lib / "Microsoft.Web.WebView2.Core.dll").write_bytes(b"dll")
    target_root = tmp_path / "temp"

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setattr(app.tempfile, "gettempdir", lambda: str(target_root))

    path = app._prepare_webview_runtime()

    target = target_root / "link_checker_webview" / "lib" / "Microsoft.Web.WebView2.Core.dll"
    assert path == str(target_root / "link_checker_webview" / "lib")
    assert target.read_bytes() == b"dll"


def test_prepare_webview_runtime_reuses_cached_files(monkeypatch, tmp_path) -> None:
    source_lib = tmp_path / "bundle" / "webview" / "lib"
    source_lib.mkdir(parents=True)
    (source_lib / "Microsoft.Web.WebView2.Core.dll").write_bytes(b"dll")
    target_root = tmp_path / "temp"
    target_lib = target_root / "link_checker_webview" / "lib"
    target_lib.mkdir(parents=True)
    (target_lib / "Microsoft.Web.WebView2.Core.dll").write_bytes(b"dll")
    copies = []

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setattr(app.tempfile, "gettempdir", lambda: str(target_root))
    monkeypatch.setattr(app.shutil, "copy2", lambda *args: copies.append(args))

    path = app._prepare_webview_runtime()

    assert path == str(target_lib)
    assert copies == []


def test_prepare_pythonnet_runtime_reuses_cached_dll(monkeypatch, tmp_path) -> None:
    source_runtime = tmp_path / "bundle" / "pythonnet" / "runtime"
    source_runtime.mkdir(parents=True)
    source_dll = source_runtime / "Python.Runtime.dll"
    source_dll.write_bytes(b"dll")
    target_root = tmp_path / "temp"
    target_runtime = target_root / "link_checker_pythonnet" / "pythonnet" / "runtime"
    target_runtime.mkdir(parents=True)
    (target_runtime / "Python.Runtime.dll").write_bytes(b"dll")
    fake_pythonnet = SimpleNamespace(__file__="original")
    copies = []

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setattr(app.tempfile, "gettempdir", lambda: str(target_root))
    monkeypatch.setattr(app.shutil, "copy2", lambda *args: copies.append(args))
    monkeypatch.setitem(sys.modules, "pythonnet", fake_pythonnet)

    app._prepare_pythonnet_runtime()

    assert copies == []
    assert fake_pythonnet.__file__ == str(
        target_root / "link_checker_pythonnet" / "pythonnet" / "__init__.py"
    )


def test_ui_waits_for_pywebview_api_before_enabling_actions() -> None:
    template = app._html_path().read_text(encoding="utf-8")

    assert 'id="select-file" type="button" disabled' in template
    assert "state.apiReady" in template
    assert "pywebviewready" in template
