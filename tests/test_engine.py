import unittest
from wetype_audio_guard import AudioItem, GuardPolicy
try:
    from tray_runtime import GuardEngine
except ImportError:
    GuardEngine = None


class Control:
    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail
    def SetMute(self, value, context):
        assert (value, context) == (0, None)
        self.calls += 1
        if self.fail:
            raise OSError('private device details must not be logged')


class Audio:
    def __init__(self):
        self.recording = False
        self.muted = False
        self.topology = ('mic', 'speaker')
        self.error = False
        self.extra = False
        self.control = Control()
        self.intentional = Control()
        self.new = Control()
    def snapshot(self):
        if self.error:
            raise OSError('private path')
        items = {'session:app': AudioItem('session:app', 'app.exe (PID 123)', self.muted, self.control),
                 'session:muted': AudioItem('session:muted', 'muted.exe', True, self.intentional)}
        if self.extra:
            items['session:new'] = AudioItem('session:new', 'new.exe', True, self.new)
        return self.recording, items, self.topology


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(GuardEngine, 'GuardEngine is not implemented')
        self.engine = GuardEngine()
        self.audio = Audio()
        self.now = 0
    def tick(self):
        self.now += .2
        return self.engine.poll(self.audio, self.now)
    def prime(self):
        self.engine.set_enabled(True)
        for _ in range(3): self.tick()
    def test_default_paused_never_writes(self):
        for _ in range(3): self.tick()
        self.audio.recording = self.audio.muted = True
        self.tick()
        self.assertFalse(self.engine.status()['enabled'])
        self.assertEqual(self.audio.control.calls, 0)
    def test_restores_once_and_preserves_intentional_and_new_mutes(self):
        self.prime()
        self.audio.recording = self.audio.muted = self.audio.extra = True
        self.tick(); self.tick()
        self.assertEqual(self.audio.control.calls, 1)
        self.assertEqual(self.audio.intentional.calls, 0)
        self.assertEqual(self.audio.new.calls, 0)
        self.assertEqual(self.engine.status()['restored'], 1)
    def test_enable_during_recording_waits_for_new_idle_baseline(self):
        self.audio.recording = self.audio.muted = True
        self.engine.set_enabled(True)
        for _ in range(5): self.tick()
        self.assertEqual(self.audio.control.calls, 0)
        self.audio.recording = self.audio.muted = False
        for _ in range(3): self.tick()
        self.audio.recording = self.audio.muted = True
        self.tick()
        self.assertEqual(self.audio.control.calls, 1)
    def test_pause_and_reenable_during_same_capture_does_not_repeat(self):
        self.prime(); self.audio.recording = self.audio.muted = True
        self.tick()
        self.engine.set_enabled(False); self.tick()
        self.engine.set_enabled(True)
        for _ in range(4): self.tick()
        self.assertEqual(self.audio.control.calls, 1)
    def test_error_invalidates_baseline_and_recovers_only_after_idle(self):
        self.prime(); self.audio.error = True
        self.tick()
        self.assertTrue(self.engine.status()['error'])
        self.audio.error = False
        self.audio.recording = self.audio.muted = True
        self.tick()
        self.assertEqual(self.audio.control.calls, 0)
        self.audio.recording = self.audio.muted = False
        for _ in range(3): self.tick()
        self.audio.recording = self.audio.muted = True
        self.tick()
        self.assertEqual(self.audio.control.calls, 1)
    def test_device_change_invalidates_baseline(self):
        self.prime()
        self.audio.topology = ('mic', 'other-speaker')
        self.audio.recording = self.audio.muted = True
        self.tick()
        self.assertEqual(self.audio.control.calls, 0)
    def test_failed_restore_not_retried_and_not_counted(self):
        self.prime(); self.audio.control.fail = True
        self.audio.recording = self.audio.muted = True
        self.tick(); self.tick()
        self.assertEqual(self.audio.control.calls, 1)
        self.assertEqual(self.engine.status()['restored'], 0)
    def test_outside_window_not_restored(self):
        self.prime(); self.audio.recording = True
        self.tick(); self.now += 3; self.audio.muted = True
        self.tick()
        self.assertEqual(self.audio.control.calls, 0)
    def test_idle_session_set_change_requires_three_new_polls(self):
        self.prime(); self.audio.extra = True
        self.tick(); self.audio.recording = self.audio.muted = True
        self.tick()
        self.assertEqual(self.audio.control.calls, 0)
    def test_two_candidate_restores_without_slow_process_enumeration(self):
        # The validated CLI calls SetMute directly. A simulated expensive
        # process scan must never enter the recording-time restore loop.
        from unittest.mock import patch
        self.prime()
        self.audio.extra = True
        self.audio.recording = self.audio.muted = True
        self.audio.extra = False
        with patch('tray_platform.cli_protect_running',
                   side_effect=AssertionError('Unexpected real-time process scan')) as check:
            self.tick()
        self.assertEqual(self.audio.control.calls, 1)
        check.assert_not_called()

    def test_post_restore_readback_reports_repeated_muting(self):
        from unittest.mock import patch
        self.prime()
        self.audio.recording = self.audio.muted = True
        with patch('tray_runtime.LOG') as logger:
            self.tick()
            self.assertEqual(self.audio.control.calls, 1)
            # Deliberately leave the fake app muted to mimic re-muting.
            self.tick()
            messages = [str(call) for call in logger.info.call_args_list]
        self.assertTrue(any('Restore readback:' in message and
                            'muted=%d' in message for message in messages))
        self.assertEqual(self.audio.control.calls, 1)

class PrivacyTests(unittest.TestCase):
    def test_error_payload_and_session_label_never_enter_log(self):
        import tempfile
        import logging
        from pathlib import Path
        from tray_platform import configure_logging
        with tempfile.TemporaryDirectory() as directory:
            logger=configure_logging(directory)
            try:
                engine=GuardEngine(); audio=Audio(); engine.set_enabled(True)
                for now in (.2,.4,.6): engine.poll(audio,now)
                audio.recording=audio.muted=True; audio.control.fail=True
                engine.poll(audio,.8)
                audio.error=True; engine.poll(audio,1.0)
                text=Path(directory,'tray.log').read_text(encoding='utf-8')
                self.assertIn('restore failed',text)
                for private in ('private device','private path','PID 123','app.exe'):
                    self.assertNotIn(private,text)
            finally:
                for handler in logger.handlers[:]:
                    handler.close(); logger.removeHandler(handler)

