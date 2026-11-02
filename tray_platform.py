"""Windows single-instance and local-only logging helpers."""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import hashlib
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys


def _user_identity():
    """Hash the current token SID, avoiding usernames or SIDs in logs."""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    advapi = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    advapi.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    advapi.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                         wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    advapi.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        size = wintypes.DWORD()
        advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
        data = ctypes.create_string_buffer(size.value)
        if not advapi.GetTokenInformation(token, 1, data, size, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        sid = ctypes.cast(data, ctypes.POINTER(ctypes.c_void_p))[0]
        text = wintypes.LPWSTR()
        if not advapi.ConvertSidToStringSidW(sid, ctypes.byref(text)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return hashlib.sha256(text.value.encode()).hexdigest()[:24]
        finally:
            kernel.LocalFree(ctypes.cast(text, ctypes.c_void_p))
    finally:
        kernel.CloseHandle(token)


class SingleInstance:
    def __init__(self, name=None):
        if sys.platform != 'win32':
            raise RuntimeError('Windows required')
        self.name = name or 'Local\\WeTypeAudioGuard.Tray.' + _user_identity()
        self.handle = None
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        self.kernel.CreateMutexW.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    def acquire(self):
        if self.handle:
            return True
        ctypes.set_last_error(0)
        handle = self.kernel.CreateMutexW(None, False, self.name)
        error = ctypes.get_last_error()
        if not handle:
            raise ctypes.WinError(error)
        if error == 183:
            self.kernel.CloseHandle(handle)
            return False
        self.handle = handle
        return True
    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
    def __enter__(self):
        if not self.acquire():
            raise RuntimeError('Tray is already running in this user session')
        return self
    def __exit__(self, *args):
        self.close()


def cli_protect_running():
    """Conservative advisory exclusion; the unchanged CLI cannot share our lock."""
    import psutil
    try:
        for process in psutil.process_iter(['name', 'cmdline'], ad_value=None):
            info = process.info
            name = (info.get('name') or '').casefold()
            if not name:
                # Opaque OS processes are common without elevation. Only known
                # Python processes can be inspected by this advisory check.
                continue
            if name not in ('python.exe', 'pythonw.exe', 'python', 'python3', 'python3.exe'):
                continue
            args = info.get('cmdline')
            if args is None:
                return True
            script = any(os.path.basename(arg).casefold() == 'wetype_audio_guard.py' for arg in args)
            if script and '--protect' in args:
                return True
        return False
    except (psutil.Error, OSError):
        return True


def default_log_dir():
    base = os.environ.get('LOCALAPPDATA')
    if not base:
        raise RuntimeError('LOCALAPPDATA is unavailable')
    return Path(base) / 'WeTypeAudioGuard' / 'logs'


def configure_logging(directory, role='tray', max_bytes=1024*1024, backups=3):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('wetype_audio_guard.tray')
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    handler = RotatingFileHandler(directory / (role + '.log'), maxBytes=max_bytes,
                                  backupCount=backups, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
