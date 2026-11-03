import unittest
try:
    from tray_icon import whale_icon
    from wetype_audio_tray import status_text, build_menu
except ImportError:
    whale_icon = status_text = build_menu = None

class IconMenuTests(unittest.TestCase):
    def test_original_whale_sizes_transparency_and_state_variants(self):
        self.assertIsNotNone(whale_icon, 'Whale icon is not implemented')
        for size in (16,24,32):
            enabled=whale_icon(size, True)
            paused=whale_icon(size, False)
            error=whale_icon(size, False, True)
            self.assertEqual(enabled.size,(size,size))
            self.assertEqual(enabled.mode,'RGBA')
            self.assertEqual(enabled.getpixel((0,0))[3],0)
            self.assertGreater(enabled.getchannel('A').getextrema()[1],0)
            self.assertNotEqual(enabled.tobytes(),paused.tobytes())
            self.assertNotEqual(paused.tobytes(),error.tobytes())
    def test_status_distinguishes_pause_recording_waiting_error_pending(self):
        self.assertIsNotNone(status_text, 'Tray status is not implemented')
        state=dict(enabled=False,recording=None,ready=False,error='',pending=False,restored=0)
        self.assertIn('暂停',status_text(state))
        state.update(enabled=True,recording=True)
        self.assertIn('录音',status_text(state))
        self.assertIn('等待',status_text(state))
        state.update(pending=True,enabled=False)
        self.assertIn('暂停中',status_text(state))
        state.update(pending=False,error='snapshot-failed')
        self.assertIn('错误',status_text(state))
    def test_menu_checked_state_and_log_actions(self):
        self.assertIsNotNone(build_menu, 'Tray menu is not implemented')
        class Controller:
            def __init__(self): self.actions=[]
            def snapshot(self):
                return dict(enabled=False,recording=None,ready=False,error='',pending=False,restored=0)
            def set_enabled(self,value): self.actions.append(value)
        from unittest.mock import patch
        c=Controller(); exits=[]
        menu=build_menu(c,lambda *args: exits.append(True))
        self.assertEqual(c.actions,[])
        items=list(menu.items)
        enable=next(item for item in items if item.text=='启用保护')
        pause=next(item for item in items if item.text=='暂停保护')
        self.assertFalse(enable.checked)
        self.assertTrue(enable.enabled)
        self.assertFalse(pause.enabled)
        enable(None)
        self.assertEqual(c.actions,[True])
        c.snapshot=lambda: dict(enabled=True,recording=False,ready=True,
                                error='',pending=False,restored=3)
        self.assertTrue(enable.checked)
        self.assertFalse(enable.enabled)
        self.assertTrue(pause.enabled)
        self.assertTrue(next(it for it in items if '保护已开启' in it.text).text.startswith('✓'))
        pause(None)
        self.assertEqual(c.actions,[True,False])
        with patch('wetype_audio_tray.open_diagnostic_logs') as view, \
             patch('wetype_audio_tray.copy_diagnostic_logs') as copy:
            next(it for it in items if it.text=='查看日志')(None)
            next(it for it in items if it.text=='复制日志')(None)
            view.assert_called_once()
            copy.assert_called_once()
        next(it for it in items if it.text=='退出')(None)
        self.assertEqual(exits,[True])

class WindowsDispatchTests(unittest.TestCase):
    def test_background_snapshot_is_only_rendered_on_ui_message(self):
        from unittest.mock import patch
        try:
            from tray_windows import WindowsTrayIcon
        except ImportError:
            self.fail('UI message dispatch is not implemented')
        icon=object.__new__(WindowsTrayIcon)
        icon._running=False; icon._icon_handle=None
        import threading
        icon._state_lock=threading.Lock(); icon._latest_state=None; icon._hwnd=123
        rendered=[]
        icon.apply_state=lambda state:rendered.append(state)
        with patch('tray_windows.win32.PostMessage') as post:
            icon.request_refresh({'enabled':False})
            self.assertEqual(rendered,[])
            self.assertEqual(post.call_count,1)
            icon._on_refresh(0,0)
        self.assertEqual(rendered,[{'enabled':False}])

class NativeTrayTests(unittest.TestCase):
    def test_full_entry_auto_enables_without_real_audio(self):
        import multiprocessing as mp
        import tempfile
        from tests.fakes import native_autoenable_probe
        with tempfile.TemporaryDirectory() as directory:
            ctx=mp.get_context('spawn'); parent,child=ctx.Pipe()
            process=ctx.Process(target=native_autoenable_probe,args=(child,directory))
            try:
                process.start(); child.close()
                self.assertTrue(parent.poll(10),'Tray startup did not return')
                code,observations=parent.recv()
                process.join(5)
                self.assertFalse(process.is_alive())
                self.assertEqual(process.exitcode,0)
                self.assertEqual(code,0)
                self.assertTrue(observations)
                self.assertTrue(all(on_owner and enabled for on_owner,enabled in observations))
            finally:
                if process.is_alive(): process.terminate(); process.join()
                process.close(); parent.close()

class PackagedStartupFailureTests(unittest.TestCase):
    def test_no_console_does_not_silence_frozen_startup_error(self):
        import sys
        from unittest.mock import patch
        from wetype_audio_tray import show_startup_failure
        with patch.object(sys, 'frozen', True, create=True), \
             patch.object(sys, 'stderr', None), \
             patch('ctypes.WinDLL') as loader:
            show_startup_failure('Test startup problem')
            loader.assert_called_once_with('user32', use_last_error=True)
            loader.return_value.MessageBoxW.assert_called_once()
    def test_console_version_still_writes_to_stderr(self):
        import io
        import sys
        from unittest.mock import patch
        from wetype_audio_tray import show_startup_failure
        output = io.StringIO()
        with patch.object(sys, 'frozen', False, create=True), patch.object(sys, 'stderr', output):
            show_startup_failure('Test problem')
        self.assertIn('Test problem', output.getvalue())
