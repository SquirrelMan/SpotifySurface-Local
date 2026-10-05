"""在 Windows 桌面驗證字幕控制，需要可用的圖形工作階段。"""
import runpy
from types import SimpleNamespace


def verifyControls() -> None:
    """驗證背景切換、拖曳後不開設定及點擊開設定。"""
    windowClass = runpy.run_path("spotify-surface-local.py")["LyricsWindow"]
    windowClass.runMonitor = lambda self: None
    window = windowClass()
    try:
        window.root.update()
        window.transparentBackground.set(False)
        window.applyBackground()
        assert str(window.root.attributes("-transparentcolor")) == ""
        window.transparentBackground.set(True)
        window.applyBackground()
        assert str(window.root.attributes("-transparentcolor")) == "#161616"
        originX, originY = window.root.winfo_x(), window.root.winfo_y()
        start = SimpleNamespace(x_root=100, y_root=100, widget=window.menuButton)
        end = SimpleNamespace(x_root=180, y_root=140, widget=window.menuButton)
        window.startDrag(start)
        window.dragWindow(end)
        window.root.update()
        assert window.root.winfo_x() == originX + 80
        assert window.root.winfo_y() == originY + 40
        window.endDrag(end)
        assert window.settings.state() == "withdrawn"
        window.startDrag(start)
        window.endDrag(start)
        window.root.update()
        assert window.settings.state() == "normal"
    finally:
        window.close()


if __name__ == "__main__":
    verifyControls()
