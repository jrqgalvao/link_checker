from __future__ import annotations

import base64
import filecmp
import mimetypes
import os
import shutil
import sys
import tempfile
from pathlib import Path

from link_checker.ui.api import LinkCheckerUIApi


def _html_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "link_checker" / "ui" / "templates" / "link_checker_ui.html"
    return Path(__file__).with_name("templates") / "link_checker_ui.html"


def _asset_path(name: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets" / name
    return Path(__file__).resolve().parents[3] / "assets" / name


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _load_html() -> str:
    html = _html_path().read_text(encoding="utf-8")
    return html.replace(
        "{{LOGO_WHITE}}", _data_uri(_asset_path("logo_placeholder_white.svg"))
    ).replace("{{LOGO_COLOR}}", _data_uri(_asset_path("logo_placeholder_color.svg")))


def _prepare_pythonnet_runtime() -> None:
    os.environ["PYTHONNET_RUNTIME"] = "netfx"
    if not getattr(sys, "frozen", False):
        return

    source = Path(sys._MEIPASS) / "pythonnet" / "runtime" / "Python.Runtime.dll"
    target_dir = Path(tempfile.gettempdir()) / "link_checker_pythonnet" / "pythonnet"
    target_runtime = target_dir / "runtime"
    target = target_runtime / "Python.Runtime.dll"
    target_runtime.mkdir(parents=True, exist_ok=True)
    if not target.exists() or not filecmp.cmp(source, target, shallow=False):
        shutil.copy2(source, target)

    import pythonnet

    pythonnet.__file__ = str(target_dir / "__init__.py")


def _prepare_webview_runtime() -> str | None:
    if not getattr(sys, "frozen", False):
        return None

    source_lib = Path(sys._MEIPASS) / "webview" / "lib"
    target_lib = Path(tempfile.gettempdir()) / "link_checker_webview" / "lib"
    _copy_changed_tree(source_lib, target_lib)
    return str(target_lib)


def _copy_changed_tree(source_dir: Path, target_dir: Path) -> None:
    for source in source_dir.rglob("*"):
        target = target_dir / source.relative_to(source_dir)
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or not filecmp.cmp(source, target, shallow=False):
            shutil.copy2(source, target)


def _redirect_webview_lib(webview, lib_path: str | None) -> None:
    if not lib_path or not hasattr(webview, "util"):
        return

    def interop_dll_path(dll_name: str) -> str:
        if dll_name == "WebBrowserInterop.dll":
            dll_name = (
                "WebBrowserInterop.x64.dll" if sys.maxsize > 2**32 else "WebBrowserInterop.x86.dll"
            )

        direct_path = Path(lib_path) / dll_name
        if direct_path.exists():
            return str(direct_path)

        runtime_path = Path(lib_path) / "runtimes" / dll_name / "native"
        if runtime_path.exists():
            return str(runtime_path)

        return str(direct_path)

    webview.util.interop_dll_path = interop_dll_path


def main() -> None:
    # ponytail: pythonnet/netfx breaks when its DLL is loaded from some frozen paths.
    _prepare_pythonnet_runtime()
    webview_lib_path = _prepare_webview_runtime()

    try:
        import webview
    except ImportError as exc:
        raise SystemExit("pywebview nao esta instalado. Reinstale o aplicativo.") from exc
    _redirect_webview_lib(webview, webview_lib_path)

    api = LinkCheckerUIApi()
    window = webview.create_window(
        "Link Checker",
        html=_load_html(),
        js_api=api,
        width=1180,
        height=760,
        min_size=(960, 620),
    )
    api.set_window(window)
    webview.start(debug=False)


if __name__ == "__main__":
    main()
