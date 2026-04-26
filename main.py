import sys
import os

# ── Single instance check ─────────────────────────────────────────────────────
import socket
_LOCK_PORT = 47832  # arbitrary port just for lock

def _is_already_running() -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", _LOCK_PORT))
        s.listen(1)
        # Keep socket alive — stored globally
        _is_already_running._lock = s
        return False
    except OSError:
        return True  # port taken = another instance running

# ── Splash screen ─────────────────────────────────────────────────────────────
from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QPainterPath, QFont, QRadialGradient
from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer


def _make_splash_pixmap(w=320, h=220) -> QPixmap:
    px = QPixmap(w, h)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background card
    p.setBrush(QBrush(QColor("#0f1e2e")))
    p.setPen(QPen(QColor("#1D9E75"), 1.5))
    p.drawRoundedRect(QRectF(1, 1, w-2, h-2), 16, 16)

    # Stars
    p.setPen(Qt.PenStyle.NoPen)
    for sx, sy, sr in [(0.15,0.15,3),(0.8,0.12,2.5),(0.88,0.35,2),(0.1,0.45,2),(0.82,0.65,2.5)]:
        p.setBrush(QBrush(QColor(255,255,255,140)))
        p.drawEllipse(QPointF(w*sx, h*sy), sr, sr)

    # Crescent moon
    cx, cy, rm = w*0.5, h*0.38, min(w,h)*0.22
    outer = QPainterPath()
    outer.addEllipse(QPointF(cx, cy), rm, rm)
    inner = QPainterPath()
    inner.addEllipse(QPointF(cx+rm*0.46, cy-rm*0.08), rm*0.78, rm*0.78)
    p.setBrush(QBrush(QColor("#1D9E75")))
    p.drawPath(outer.subtracted(inner))

    # App name
    p.setPen(QColor("#ffffff"))
    p.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
    p.drawText(QRectF(0, h*0.65, w, 36), Qt.AlignmentFlag.AlignHCenter, "Waqt")

    # Subtitle
    p.setPen(QColor("#8888aa"))
    p.setFont(QFont("Segoe UI", 10))
    p.drawText(QRectF(0, h*0.82, w, 24), Qt.AlignmentFlag.AlignHCenter, "Loading prayer times...")

    p.end()
    return px


class App(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)


if __name__ == "__main__":
    if _is_already_running():
        # Bring existing window to front via socket message
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", _LOCK_PORT))
            s.send(b"show")
            s.close()
        except Exception:
            pass
        sys.exit(0)

    app = App(sys.argv)

    # Show splash
    splash = QSplashScreen(_make_splash_pixmap(), Qt.WindowType.WindowStaysOnTopHint)
    splash.setWindowFlag(Qt.WindowType.FramelessWindowHint)
    splash.show()
    app.processEvents()

    # Import and create window (heavy part)
    from ui.main_window import MainWindow
    window = MainWindow()

    def on_close(event):
        event.ignore()
        window.hide()

    def on_quit():
        window._tray.hide()
        splash.close()
        app.quit()
        sys.exit(0)

    window.closeEvent = on_close
    try:
        window._tray.quit_action.triggered.disconnect()
    except Exception:
        pass
    window._tray.quit_action.triggered.connect(on_quit)

    # Close splash and show window after short delay
    def _finish():
        splash.finish(window)
        window.show()

    QTimer.singleShot(1200, _finish)
    sys.exit(app.exec())