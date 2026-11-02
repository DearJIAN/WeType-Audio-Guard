import gc
import threading
import types
import unittest
from unittest.mock import patch
from tray_runtime import StrictWindowsAudio, TrayController
try:
    from tray_runtime import ComAudio
except ImportError:
    ComAudio = None

class ComOwnershipTests(unittest.TestCase):
    def test_create_use_release_and_uninitialize_on_owner_thread(self):
        self.assertIsNotNone(ComAudio, 'COM owner is not implemented')
        events = []
        class Backend:
            def __init__(self): events.append(('create', threading.get_ident()))
            def snapshot(self):
                events.append(('read', threading.get_ident()))
                return False, {}, ()
            def __del__(self): events.append(('release', threading.get_ident()))
        fake = types.SimpleNamespace(
            CoInitialize=lambda: events.append(('init', threading.get_ident())),
            CoUninitialize=lambda: events.append(('uninit', threading.get_ident())))
        def run():
            with patch.dict('sys.modules', {'comtypes': fake}), patch('tray_runtime.StrictWindowsAudio', Backend):
                audio = ComAudio(); audio.snapshot(); audio.close()
        worker = threading.Thread(target=run); worker.start(); worker.join()
        self.assertEqual([x[0] for x in events], ['init','create','read','release','uninit'])
        self.assertEqual(len({x[1] for x in events}), 1)
        self.assertNotEqual(events[0][1], threading.get_ident())
    def test_factory_failure_balances_com_initialization(self):
        self.assertIsNotNone(ComAudio, 'COM owner is not implemented')
        events=[]
        fake=types.SimpleNamespace(CoInitialize=lambda: events.append('init'),
                                  CoUninitialize=lambda: events.append('uninit'))
        with patch.dict('sys.modules', {'comtypes': fake}), patch('tray_runtime.StrictWindowsAudio', side_effect=OSError()):
            with self.assertRaises(OSError): ComAudio()
        self.assertEqual(events, ['init','uninit'])

class PartialSnapshotTests(unittest.TestCase):
    def test_missing_control_is_not_silently_accepted(self):
        audio = object.__new__(StrictWindowsAudio)
        class Sessions:
            def GetCount(self): return 1
            def GetSession(self, index): return None
        class Manager:
            def GetSessionEnumerator(self): return Sessions()
            def QueryInterface(self, interface): return self
        class Device:
            def Activate(self, *args): return Manager()
        audio._mgr_type=types.SimpleNamespace(_iid_='fake')
        audio._clsctx=0
        with self.assertRaises(RuntimeError): list(audio._sessions(Device()))
