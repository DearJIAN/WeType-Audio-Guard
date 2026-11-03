"""User-invoked, local-only diagnostic log view and clipboard export.

No telemetry, uploads, background notifications, or additional audio calls.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path
import subprocess

from tray_platform import default_log_dir


def diagnostic_text(directory=None, per_file_lines=120):
    """Return recent sanitized application log lines in a readable block."""
    root = Path(directory) if directory is not None else default_log_dir()
    output = [
        'WeType Audio Guard - 最近诊断日志（仅本机）',
        '查看：记事本打开此文件；复制：托盘菜单「复制日志」后可直接粘贴到聊天。',
        '不会自动发送到网络。分享前请检查日志内容。',
        '',
    ]
    for name in ('audio.log', 'tray.log'):
        output.append('========== ' + name + ' ==========')
        path = root / name
        try:
            with path.open('r', encoding='utf-8', errors='replace') as file:
                recent = deque(file, maxlen=per_file_lines)
            output.extend(line.rstrip('\n\r') for line in recent)
            if not recent:
                output.append('（暂无记录）')
        except FileNotFoundError:
            output.append('（尚未生成）')
        output.append('')
    return '\n'.join(output) + '\n'


def open_diagnostic_logs(directory=None):
    """Open a bounded combined log snapshot with the stock Windows Notepad."""
    root = Path(directory) if directory is not None else default_log_dir()
    root.mkdir(parents=True, exist_ok=True)
    path = root / 'recent-diagnostics.txt'
    path.write_text(diagnostic_text(root), encoding='utf-8')
    subprocess.Popen(['notepad.exe', str(path)], close_fds=True)
    return path


def _copy_unicode_to_clipboard(text):
    """Write CF_UNICODETEXT with correct Win32 handle ownership."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p

    wide = ctypes.create_unicode_buffer(text)
    if not user32.OpenClipboard(None):
        raise OSError('clipboard-unavailable')
    memory = None
    try:
        memory = kernel32.GlobalAlloc(0x0002, ctypes.sizeof(wide))
        if not memory:
            raise OSError('clipboard-allocation-failed')
        pointer = kernel32.GlobalLock(memory)
        if not pointer:
            raise OSError('clipboard-lock-failed')
        try:
            ctypes.memmove(pointer, wide, ctypes.sizeof(wide))
        finally:
            kernel32.GlobalUnlock(memory)
        if not user32.EmptyClipboard():
            raise OSError('clipboard-empty-failed')
        if not user32.SetClipboardData(13, memory):  # CF_UNICODETEXT
            raise OSError('clipboard-set-failed')
        memory = None  # Windows now owns the handle.
    finally:
        if memory:
            kernel32.GlobalFree(memory)
        user32.CloseClipboard()


def copy_diagnostic_logs(directory=None):
    """Only copy when explicitly clicked; never upload diagnostics."""
    text = diagnostic_text(directory)
    _copy_unicode_to_clipboard(text)
    return len(text)
