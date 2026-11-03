"""Tray-only guard orchestration. The validated CLI is imported, never modified."""
from __future__ import annotations

import contextlib
import gc
import io
import logging
import multiprocessing as mp
import queue
import threading
import time
from wetype_audio_guard import GuardPolicy, WindowsAudio

LOG = logging.getLogger('wetype_audio_guard.tray')
LOG.addHandler(logging.NullHandler())


class GuardEngine:
    """Value state only; all methods run on the owning audio thread."""
    def __init__(self, conflict_check=lambda: False):
        self.enabled = False
        self.recording = None
        self.restored = 0
        self.error = ''
        self.policy = GuardPolicy()
        self.topology = None
        self.idle_keys = None
        self.conflict_check = conflict_check
        self._last_error = None
        self._last_error_time = 0.0
        self._last_slow_snapshot_warning = 0.0

    def reset(self):
        self.policy = GuardPolicy()
        self.topology = None
        self.idle_keys = None

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        self.recording = None
        self.error = ''
        self.reset()
        LOG.info('Protection %s', 'enabled' if enabled else 'paused')

    def fault(self, code):
        self.reset()
        self.recording = None
        self.error = code
        now = time.monotonic()
        if code != self._last_error or now - self._last_error_time >= 30:
            LOG.warning('Audio error: %s', code)
            self._last_error, self._last_error_time = code, now

    def status(self):
        return dict(enabled=self.enabled, recording=self.recording,
                    restored=self.restored, error=self.error,
                    ready=bool(self.policy.baseline))

    def poll(self, audio, now, allowed=lambda: True):
        try:
            scan_started = time.monotonic()
            recording, items, topology = audio.snapshot()
            scan_seconds = time.monotonic() - scan_started
            if (scan_seconds >= 1.0 and
                    scan_started - self._last_slow_snapshot_warning >= 15.0):
                # Deliberately omit process names, device IDs and raw exceptions.
                LOG.warning('Slow Windows audio snapshot: %.2fs', scan_seconds)
                self._last_slow_snapshot_warning = scan_started
            if not allowed():
                return self.status()
            if recording != self.recording:
                LOG.info('WeType recording %s', 'ON' if recording else 'OFF')
            self.recording = recording
            if not self.enabled:
                self.reset()
                return self.status()
            if self.topology != topology:
                self.reset()
                self.topology = topology
            if not recording:
                keys = frozenset(items)
                if keys != self.idle_keys:
                    self.policy = GuardPolicy()
                    self.idle_keys = keys
            candidates = self.policy.tick(recording, items, now)
            # Keep a failed write visible until idle / a deliberate toggle.
            if not recording:
                self.error = ''
            for item in candidates:
                if not allowed():
                    break
                check_started = time.monotonic()
                conflict = self.conflict_check()
                if time.monotonic() - check_started >= 1.0:
                    LOG.warning('Slow CLI conflict inspection: %.2fs',
                                time.monotonic() - check_started)
                if conflict:
                    self.enabled = False
                    self.fault('cli-conflict')
                    break
                try:
                    restore_started = time.monotonic()
                    item.controller.SetMute(0, None)
                    restore_seconds = time.monotonic() - restore_started
                    if restore_seconds >= 1.0:
                        LOG.warning('Slow audio mute restore call: %.2fs', restore_seconds)
                    self.restored += 1
                    # No labels: these may contain paths, device IDs and PIDs.
                    LOG.info('Playback mute restored; total=%d', self.restored)
                except Exception:
                    self.error = 'restore-failed'
                    LOG.warning('Playback restore failed; no retry this recording')
            return self.status()
        except Exception:
            self.fault('snapshot-failed')
            return self.status()


class ComAudio:
    """Own the backend and balance explicit COM initialization on one thread."""
    def __init__(self):
        from comtypes import CoInitialize, CoUninitialize
        self.owner = threading.get_ident()
        self._uninitialize = CoUninitialize
        self.backend = None
        self.initialized = False
        CoInitialize()
        self.initialized = True
        try:
            self.backend = StrictWindowsAudio()
        except Exception:
            self.close()
            raise

    def snapshot(self):
        if threading.get_ident() != self.owner:
            raise RuntimeError('COM owner thread mismatch')
        return self.backend.snapshot()

    def close(self):
        if threading.get_ident() != self.owner:
            raise RuntimeError('COM owner thread mismatch')
        self.backend = None
        gc.collect()
        if self.initialized:
            self._uninitialize()
            self.initialized = False


class _CompleteSession:
    """Require a playback volume interface instead of silently dropping it."""
    def __init__(self, session):
        self._session = session

    def __getattr__(self, name):
        return getattr(self._session, name)

    @property
    def SimpleAudioVolume(self):
        volume = self._session.SimpleAudioVolume
        if volume is None:
            raise RuntimeError('Missing playback volume interface')
        return volume


class StrictWindowsAudio(WindowsAudio):
    """Convert the CLI's partial-enumeration warnings into fail-closed snapshots."""
    def _sessions(self, dev):
        obj = dev.Activate(self._mgr_type._iid_, self._clsctx, None)
        manager = obj.QueryInterface(self._mgr_type)
        sessions = manager.GetSessionEnumerator()
        for index in range(sessions.GetCount()):
            control = sessions.GetSession(index)
            if control is None:
                raise RuntimeError('Incomplete session enumeration')
            sc2 = control.QueryInterface(self._sc_type)
            if sc2 is None:
                raise RuntimeError('Incomplete session control')
            yield _CompleteSession(self._audio_session(sc2)), index

    def _devices(self, flow):
        for device in super()._devices(flow):
            self._seen[flow].append(str(device.GetId()))
            yield device

    def snapshot(self):
        self._seen = {0: [], 1: []}
        warnings = io.StringIO()
        # Redirect only inside the isolated audio process, never the tray UI.
        with contextlib.redirect_stderr(warnings):
            recording = False
            for device in self._devices(1):
                for session, _ in self._sessions(device):
                    if int(session.State) == 1:
                        name = self._process_name(session.ProcessId)
                        if name.startswith('pid:'):
                            raise RuntimeError('Capture process cannot be inspected')
                        if name.casefold() == 'wetype_update.exe':
                            recording = True
            items = self.playback()
        capture = tuple(sorted(self._seen[1]))
        render = tuple(sorted(self._seen[0]))
        if warnings.getvalue() or not capture or not render:
            raise RuntimeError('Incomplete audio snapshot')
        return recording, items, (render, capture)


def _audio_child(connection, factory, interval, log_dir):
    """Spawn target: this process's main thread is the sole COM/audio owner."""
    from tray_platform import cli_protect_running, configure_logging
    if log_dir:
        configure_logging(log_dir, role='audio')
    engine = GuardEngine(conflict_check=cli_protect_running)
    audio = None
    revision = 0
    def release():
        nonlocal audio
        if audio is not None:
            close = getattr(audio, 'close', None)
            if close:
                close()
            audio = None
        gc.collect()
    try:
        while True:
            # Commands are serialized on this same audio thread.
            while connection.poll():
                command, revision, enabled = connection.recv()
                if command == 'stop':
                    return
                release()
                engine.set_enabled(enabled)
            if engine.enabled:
                try:
                    if audio is None:
                        if factory is None:
                            audio = ComAudio()
                        else:
                            audio = factory()
                    engine.poll(audio, time.monotonic(), allowed=lambda: not connection.poll())
                    if engine.error in ('snapshot-failed', 'cli-conflict'):
                        release()
                except Exception:
                    release()
                    engine.fault('audio-init-failed')
            connection.send((revision, engine.status()))
            connection.poll(interval)
    except (EOFError, BrokenPipeError, OSError):
        pass
    finally:
        release()
        connection.close()
        LOG.info('Audio worker stopped')
        logging.shutdown()


class TrayController:
    """One supervisor thread, one contained audio process, non-blocking UI commands."""
    def __init__(self, factory=None, interval=.2, timeout=12.0, log_dir=None,
                 conflict_check=None):
        from tray_platform import cli_protect_running
        self.factory, self.interval, self.timeout, self.log_dir = factory, interval, timeout, log_dir
        self.conflict_check = conflict_check or cli_protect_running
        self._lock = threading.Lock()
        self._commands = queue.Queue()
        self._closing = threading.Event()
        self._thread = None
        self._process = None
        self._revision = 0
        self._state = dict(enabled=False, recording=None, restored=0, error='',
                           ready=False, pending=False)
        self._stopped = False
        self._failed = threading.Event()
        self.on_update = None
        self._last_published = None

    def start(self):
        with self._lock:
            if self._thread is not None:
                return
            if self._stopped:
                raise RuntimeError('Controller already closed')
            self._thread = threading.Thread(target=self._supervise, name='WeTypeTraySupervisor')
            self._thread.start()

    def snapshot(self):
        with self._lock:
            return dict(self._state)

    def set_enabled(self, enabled):
        # Process inspection must not run in the UI callback; worker rechecks.
        with self._lock:
            if self._closing.is_set() or self._failed.is_set():
                return
            self._revision += 1
            self._state.update(enabled=bool(enabled), pending=True, ready=False, recording=None)
            self._commands.put((self._revision, bool(enabled)))
        LOG.info('Protection %s requested', 'enable' if enabled else 'pause')

    def _notify_if_changed(self):
        """Deliver only changed snapshots; avoid continuous idle PostMessage calls."""
        callback = self.on_update
        if callback is None:
            return
        state = self.snapshot()
        if state == self._last_published:
            return
        try:
            callback(state)
        except Exception:
            LOG.warning('Tray status refresh failed')
        else:
            self._last_published = state

    @staticmethod
    def _reap(process):
        if process is None:
            return
        if process.is_alive():
            process.terminate()
        process.join(1)
        if process.is_alive():
            process.kill()
            process.join()
        process.close()

    def _supervise(self):
        context = mp.get_context('spawn')
        connection = None
        process = None
        last_reply = time.monotonic()
        try:
            if self.conflict_check():
                with self._lock:
                    self._state['error'] = 'cli-conflict'
                LOG.warning('CLI protection conflict or process inspection unavailable')
            while not self._closing.is_set():
                if process is None:
                    parent, child = context.Pipe()
                    process = context.Process(target=_audio_child,
                        args=(child, self.factory, self.interval, self.log_dir), name='WeTypeAudioWorker')
                    process.start()
                    child.close()
                    connection = parent
                    self._process = process
                    last_reply = time.monotonic()
                latest = None
                while True:
                    try:
                        latest = self._commands.get_nowait()
                    except queue.Empty:
                        break
                if latest is not None:
                    revision, enabled = latest
                    if enabled and self.conflict_check():
                        enabled = False
                        with self._lock:
                            self._state.update(enabled=False, error='cli-conflict')
                    connection.send(('set', revision, enabled))
                while connection.poll():
                    revision, state = connection.recv()
                    last_reply = time.monotonic()
                    with self._lock:
                        if revision == self._revision:
                            # Preserve a parent-side conflict warning on pause ack.
                            if self._state['error'] == 'cli-conflict' and not state['enabled']:
                                state['error'] = 'cli-conflict'
                            self._state.update(state, pending=False)
                # Real Windows Core Audio enumeration may take several seconds
                # during WeType's session transitions. Do not confuse a slow
                # but functioning COM operation with a dead worker.
                if not process.is_alive():
                    LOG.error('Audio worker exited; exit code=%s', process.exitcode)
                    raise RuntimeError('Audio worker exited')
                elapsed = time.monotonic() - last_reply
                if elapsed > self.timeout:
                    LOG.error('Audio worker heartbeat late: %.2fs (limit %.1fs)',
                              elapsed, self.timeout)
                    raise TimeoutError('Audio worker heartbeat expired')
                self._notify_if_changed()
                self._closing.wait(.03)
        except Exception:
            self._failed.set()
            with self._lock:
                self._state.update(pending=True, ready=False,
                                   recording=None, error='worker-stopped')
            LOG.error('Audio worker stopped or timed out; restart tray to retry')
        finally:
            if connection:
                try:
                    connection.send(('stop', 0, False))
                    if process and not self._failed.is_set():
                        process.join(self.timeout)
                except (OSError, EOFError):
                    pass
                connection.close()
            self._reap(process)
            self._process = None
            with self._lock:
                self._state.update(enabled=False, pending=False, ready=False, recording=None)
            self._notify_if_changed()

    def close(self):
        self._closing.set()
        if self._thread:
            self._thread.join()
        self._stopped = True
        LOG.info('Tray controller stopped')
