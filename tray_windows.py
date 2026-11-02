"""Small Windows-only adapter for pystray 0.19.5's window message dispatch.

Never rebuild an open native menu from the supervisor thread. State delivery
uses PostMessage; menu text is refreshed immediately before opening the menu.
"""
import threading
from pystray._win32 import Icon
from pystray._util import win32

WM_TRAY_REFRESH = 0x8001


class WindowsTrayIcon(Icon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state_lock = threading.Lock()
        self._latest_state = None
        self.apply_state = lambda state: None
        self._message_handlers[WM_TRAY_REFRESH] = self._on_refresh

    def request_refresh(self, state):
        with self._state_lock:
            self._latest_state = dict(state)
        if self._hwnd:
            win32.PostMessage(self._hwnd, WM_TRAY_REFRESH, 0, 0)

    def _on_refresh(self, wparam, lparam):
        with self._state_lock:
            state = self._latest_state
        if state is not None:
            self.apply_state(state)

    def _on_notify(self, wparam, lparam):
        if lparam == win32.WM_RBUTTONUP:
            self.update_menu()
        return super()._on_notify(wparam, lparam)
