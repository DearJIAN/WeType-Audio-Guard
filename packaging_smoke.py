"""Real frozen tray + spawned worker smoke test; NEVER uses Windows audio devices."""
from __future__ import annotations

import os
import threading
import time

from wetype_audio_guard import AudioItem


class SimulatedPlayback:
    """Minimal, pickle-safe fake used only by the frozen test."""
    def snapshot(self):
        item = AudioItem('mock', 'simulated-output', False, None)
        return False, {'mock': item}, ('mock-render', 'mock-capture')

    def close(self):
        pass


def _wait(predicate, timeout=12.0):
    stop_at = time.monotonic() + timeout
    while time.monotonic() < stop_at:
        if predicate():
            return
        time.sleep(.04)
    raise RuntimeError('Timed out waiting for frozen worker state')


def run_frozen_smoke():
    """Tests a native UI message and full frozen multiprocessing lifecycle."""
    from tray_icon import whale_icon
    from tray_platform import SingleInstance
    from tray_runtime import TrayController
    from tray_windows import WindowsTrayIcon

    seen = threading.Event()
    class SmokeIcon(WindowsTrayIcon):
        def _on_refresh(self, wparam, lparam):
            super()._on_refresh(wparam, lparam)
            seen.set()
            self.stop()

    icon = SmokeIcon('WeTypeAudioGuardSmoke', whale_icon(), 'WeType Audio Guard test')
    icon.apply_state = lambda state: None
    def setup(instance):
        instance.visible = True
        instance.request_refresh({'enabled': False, 'error': '', 'pending': False})
    stop_fallback = threading.Timer(10.0, icon.stop)
    stop_fallback.daemon = True
    controller = None
    try:
        with SingleInstance(name='Local\\WeTypeAudioGuard.FrozenSmoke.' + str(os.getpid())):
            stop_fallback.start()
            try:
                icon.run(setup=setup)
            finally:
                stop_fallback.cancel()
                icon.stop()
            if not seen.is_set():
                return 3

            controller = TrayController(factory=SimulatedPlayback, interval=.05,
                                        timeout=10.0, conflict_check=lambda: False)
            controller.start()
            controller.set_enabled(True)
            _wait(lambda: controller.snapshot()['enabled'] and
                  not controller.snapshot()['pending'] and controller.snapshot()['ready'])
            controller.set_enabled(False)
            _wait(lambda: not controller.snapshot()['enabled'] and
                  not controller.snapshot()['pending'])
            controller.close()
            if controller._thread.is_alive() or controller._process is not None:
                return 4
            return 0
    except Exception:
        return 2
    finally:
        stop_fallback.cancel()
        if controller is not None:
            controller.close()
