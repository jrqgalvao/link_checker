from __future__ import annotations

import base64
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
    target_runtime.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target_runtime / "Python.Runtime.dll")

    import pythonnet

    pythonnet.__file__ = str(target_dir / "__init__.py")


def main() -> None:
    # ponytail: pythonnet/netfx breaks when its DLL is loaded from some frozen paths.
    _prepare_pythonnet_runtime()

    try:
        import webview
    except ImportError as exc:
        raise SystemExit("pywebview nao esta instalado. Reinstale o aplicativo.") from exc

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
