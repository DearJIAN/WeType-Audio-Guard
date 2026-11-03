import logging
import multiprocessing as mp
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
from unittest.mock import patch
from tests.fakes import QuietAudio, HungAudio, BrokenAudio, SlowAudio
from tray_runtime import TrayController
try:
    from tray_platform import SingleInstance, cli_protect_running, configure_logging
except ImportError:
    SingleInstance = cli_protect_running = configure_logging = None


def wait_for(predicate, timeout=6):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate(): return
        time.sleep(.02)
    raise AssertionError('Timed out waiting for observable state')


class LifecycleTests(unittest.TestCase):
    def make(self, factory=QuietAudio, **kwargs):
        c = TrayController(factory=factory, interval=.02, timeout=.8,
                           conflict_check=lambda: False, **kwargs)
        self.addCleanup(c.close)
        c.start()
        return c
    def test_default_paused_and_repeated_toggles_reuse_worker(self):
        c = self.make()
        wait_for(lambda: c._process is not None)
        pid = c._process.pid
        worker = c._thread
        self.assertFalse(c.snapshot()['enabled'])
        for _ in range(8):
            c.set_enabled(True)
            wait_for(lambda: not c.snapshot()['pending'])
            self.assertTrue(c.snapshot()['enabled'])
            c.set_enabled(False)
            wait_for(lambda: not c.snapshot()['pending'])
            self.assertFalse(c.snapshot()['enabled'])
        self.assertEqual(c._process.pid, pid)
        self.assertIs(c._thread, worker)
        c.close()
        self.assertFalse(worker.is_alive())
        self.assertNotIn(pid, [p.pid for p in mp.active_children()])
    def test_hung_audio_is_terminated_on_exit(self):
        c = self.make(HungAudio)
        c.set_enabled(True)
        wait_for(lambda: c._process is not None)
        pid = c._process.pid
        time.sleep(.3)
        start = time.monotonic()
        c.close()
        self.assertLess(time.monotonic() - start, 4)
        self.assertNotIn(pid, [p.pid for p in mp.active_children()])
    def test_hung_audio_watchdog_pauses_and_reaps_child(self):
        c = self.make(HungAudio)
        c.set_enabled(True)
        wait_for(lambda: c.snapshot()['error'] == 'worker-stopped')
        wait_for(lambda: not c._thread.is_alive())
        self.assertFalse(c.snapshot()['enabled'])
        self.assertIsNone(c._process)
    def test_audio_errors_keep_ui_responsive(self):
        c = self.make(BrokenAudio)
        c.set_enabled(True)
        wait_for(lambda: bool(c.snapshot()['error']))
        c.set_enabled(False)
        wait_for(lambda: not c.snapshot()['pending'])
        self.assertFalse(c.snapshot()['enabled'])


class PlatformTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(SingleInstance, 'platform helpers are not implemented')
    def test_named_mutex_blocks_another_process_and_releases(self):
        name = 'Local\\WeTypeAudioGuardTest-' + uuid.uuid4().hex
        code = ('from tray_platform import SingleInstance; import sys; '
                'lock=SingleInstance(sys.argv[1]); sys.exit(0 if lock.acquire() else 9)')
        with SingleInstance(name):
            r = subprocess.run([sys.executable, '-c', code, name], timeout=5)
            self.assertEqual(r.returncode, 9)
        r = subprocess.run([sys.executable, '-c', code, name], timeout=5)
        self.assertEqual(r.returncode, 0)
    def test_cli_detection_only_protection_not_diagnosis(self):
        class Proc:
            def __init__(self, args): self.info = dict(name='python.exe', cmdline=args)
        with patch('psutil.process_iter', return_value=[Proc(['python', 'wetype_audio_guard.py', '--protect'])]):
            self.assertTrue(cli_protect_running())
        with patch('psutil.process_iter', return_value=[Proc(['python', 'wetype_audio_guard.py', '--diagnose'])]):
            self.assertFalse(cli_protect_running())
    def test_inaccessible_python_fails_closed(self):
        class Proc:
            info = dict(name='python.exe', cmdline=None)
        with patch('psutil.process_iter', return_value=[Proc()]):
            self.assertTrue(cli_protect_running())
    def test_log_rotation_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = configure_logging(directory, max_bytes=128, backups=2)
            try:
                for _ in range(50): logger.info('Application lifecycle event')
                files = list(Path(directory).glob('tray.log*'))
                self.assertLessEqual(len(files), 3)
                self.assertGreater(len(files), 1)
            finally:
                for handler in logger.handlers[:]:
                    handler.close(); logger.removeHandler(handler)

class FailureStateTests(unittest.TestCase):
    def test_dead_worker_cannot_be_reenabled_and_final_status_notifies_ui(self):
        updates=[]
        c=TrayController(factory=HungAudio,interval=.02,timeout=.4,conflict_check=lambda:False)
        self.addCleanup(c.close)
        c.on_update=lambda state: updates.append(state)
        c.start(); c.set_enabled(True)
        wait_for(lambda:not c._thread.is_alive())
        self.assertTrue(any(s['error']=='worker-stopped' and not s['enabled'] for s in updates))
        c.set_enabled(True)
        self.assertFalse(c.snapshot()['enabled'])
        self.assertFalse(c.snapshot()['pending'])

    def test_default_sid_mutex_name_is_stable(self):
        a,b=SingleInstance(),SingleInstance()
        self.assertEqual(a.name,b.name)
        self.assertTrue(a.acquire())
        try: self.assertFalse(b.acquire())
        finally: a.close(); b.close()

class RaceTests(unittest.TestCase):
    def test_pause_invalidates_inflight_snapshot_before_restore(self):
        from functools import partial
        from tests.fakes import SharedAudio
        ctx=mp.get_context('spawn')
        rec,muted,calls=ctx.Value('i',0),ctx.Value('i',0),ctx.Value('i',0)
        block,entered,release=ctx.Event(),ctx.Event(),ctx.Event()
        factory=partial(SharedAudio,rec,muted,block,entered,release,calls)
        c=TrayController(factory=factory,interval=.03,timeout=2,conflict_check=lambda:False)
        self.addCleanup(c.close); self.addCleanup(release.set)
        c.start(); c.set_enabled(True)
        wait_for(lambda:c.snapshot()['ready'])
        rec.value=muted.value=1; block.set()
        self.assertTrue(entered.wait(3))
        c.set_enabled(False)
        self.assertTrue(c.snapshot()['pending'])
        # Ensure the supervisor has delivered pause while the read is blocked.
        time.sleep(.15)
        release.set()
        wait_for(lambda:not c.snapshot()['pending'])
        self.assertFalse(c.snapshot()['enabled'])
        self.assertEqual(calls.value,0)

class ProcessAvailabilityTests(unittest.TestCase):
    def test_unidentified_non_python_process_does_not_block_every_enable(self):
        class Proc:
            info=dict(name=None,cmdline=None)
        with patch('psutil.process_iter',return_value=[Proc()]):
            self.assertFalse(cli_protect_running())

class StatusNotificationTests(unittest.TestCase):
    def test_repeated_idle_snapshots_do_not_repost(self):
        controller = TrayController(factory=QuietAudio, conflict_check=lambda: False)
        updates = []
        controller.on_update = lambda value: updates.append(value)
        controller._notify_if_changed()
        controller._notify_if_changed()
        self.assertEqual(len(updates), 1)
        controller._state['pending'] = True
        controller._notify_if_changed()
        controller._notify_if_changed()
        self.assertEqual(len(updates), 2)
        controller._state['pending'] = False
        controller._notify_if_changed()
        self.assertEqual(len(updates), 3)
    def test_failed_refresh_is_retried(self):
        controller = TrayController(factory=QuietAudio, conflict_check=lambda: False)
        calls = []
        def flaky(value):
            calls.append(value)
            if len(calls) == 1:
                raise RuntimeError('simulated refresh failure')
        controller.on_update = flaky
        controller._notify_if_changed()
        controller._notify_if_changed()
        self.assertEqual(len(calls), 2)

class SlowAudioWatchdogTests(unittest.TestCase):
    def test_default_watchdog_allows_realistic_slow_but_live_scans(self):
        # Previous default 3.0s incorrectly terminated a responsive worker.
        c = TrayController(factory=SlowAudio, interval=.02,
                           conflict_check=lambda: False)
        self.addCleanup(c.close)
        self.assertGreaterEqual(c.timeout, 10.0)
        c.start()
        c.set_enabled(True)
        wait_for(lambda: not c.snapshot()['pending'] and
                 c.snapshot()['enabled'], timeout=9)
        # An entire snapshot takes >3s, but must not be treated as a crash.
        time.sleep(3.9)
        self.assertFalse(c._failed.is_set())
        self.assertTrue(c._thread.is_alive())
        self.assertTrue(c.snapshot()['enabled'])
        c.set_enabled(False)
        wait_for(lambda: not c.snapshot()['pending'] and
                 not c.snapshot()['enabled'], timeout=12)
        self.assertFalse(c._failed.is_set())
        c.close()
        self.assertFalse(c._thread.is_alive())
        self.assertIsNone(c._process)

class ExplicitEnableConflictTests(unittest.TestCase):
    def test_cli_conflict_prevents_enable_without_audio_writes(self):
        checks = []
        def blocked():
            checks.append(True)
            return True
        c = TrayController(factory=QuietAudio, interval=.02,
                           timeout=2.0, conflict_check=blocked)
        self.addCleanup(c.close)
        c.start()
        c.set_enabled(True)
        wait_for(lambda: not c.snapshot()['pending'], timeout=6)
        self.assertFalse(c.snapshot()['enabled'])
        self.assertEqual(c.snapshot()['error'], 'cli-conflict')
        self.assertGreaterEqual(len(checks), 1)

