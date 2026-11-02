"""Build a standalone, windowless Windows EXE; run only on Windows."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "dist" / "WeTypeAudioGuard.exe"


def main() -> int:
    if sys.platform != "win32":
        print("Windows is required to build a Windows EXE.", file=sys.stderr)
        return 2
    sys.path.insert(0, str(ROOT))
    from tray_icon import whale_icon

    assets = ROOT / "build" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    icon = assets / "WeTypeAudioGuard.ico"
    # Generated entirely from the original Pillow drawing; no third-party icon.
    whale_icon(256, enabled=True).save(
        icon,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
               (64, 64), (128, 128), (256, 256)],
    )

    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed", "--noupx",
        "--name", "WeTypeAudioGuard",
        "--icon", str(icon),
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build" / "pyinstaller"),
        "--specpath", str(ROOT / "build" / "spec"),
        "--paths", str(ROOT),
        "--hidden-import", "pystray._win32",
        "--collect-submodules", "pycaw",
        "--collect-submodules", "comtypes",
        str(ROOT / "tools" / "packaging_entry.py"),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    if not EXE.is_file():
        raise RuntimeError("PyInstaller did not generate the expected EXE.")
    checksum = hashlib.sha256(EXE.read_bytes()).hexdigest()
    checksum_file = EXE.with_suffix(".exe.sha256")
    checksum_file.write_text(
        f"{checksum}  {EXE.name}\n", encoding="utf-8"
    )
    print("Built:", EXE)
    print("SHA256:", checksum)
    print("Verify with: WeTypeAudioGuard.exe --package-smoke-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
