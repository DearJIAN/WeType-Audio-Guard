"""Frozen EXE entry point; keep the validated CLI and tray entry untouched."""
from __future__ import annotations

import multiprocessing
import sys


def package_smoke_test() -> int:
    """Verify frozen imports and whale icon without opening a tray or touching audio."""
    try:
        from PIL import Image
        from pystray._win32 import Icon
        from pycaw.api.mmdeviceapi import IMMDeviceEnumerator
        from pycaw.api.audiopolicy import IAudioSessionManager2
        from pycaw.api.endpointvolume import IAudioEndpointVolume
        from tray_icon import whale_icon
        from tray_runtime import TrayController, StrictWindowsAudio
        from tray_platform import SingleInstance
        from wetype_audio_tray import main
        image = whale_icon(32, enabled=True)
        if image.size != (32, 32) or image.getbbox() is None:
            return 3
        assert all((Image, Icon, IMMDeviceEnumerator, IAudioSessionManager2,
                    IAudioEndpointVolume, TrayController, StrictWindowsAudio,
                    SingleInstance, main))
        return 0
    except Exception:
        return 2


if __name__ == '__main__':
    # Important: PyInstaller overrides freeze_support to divert spawned workers.
    # Call before importing the tray UI or starting any COM/audio operations.
    multiprocessing.freeze_support()
    if sys.argv[1:] == ['--package-smoke-test']:
        raise SystemExit(package_smoke_test())
    if sys.argv[1:] == ['--frozen-tray-smoke-test']:
        from packaging_smoke import run_frozen_smoke
        raise SystemExit(run_frozen_smoke())
    from wetype_audio_tray import main
    raise SystemExit(main())
