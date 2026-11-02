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

class StrictCaptureTests(unittest.TestCase):
    def test_uninspectable_active_capture_invalidates_snapshot(self):
        class Audio(StrictWindowsAudio):
            def __init__(self): pass
            def _devices(self,flow):
                self._seen[flow].append('device')
                yield object()
            def _sessions(self,device):
                yield types.SimpleNamespace(State=1,ProcessId=42),0
            def _process_name(self,pid): return 'pid:42'
            def playback(self):
                self._seen[0].append('speaker')
                return {}
        with self.assertRaises(RuntimeError): Audio().snapshot()

    def test_missing_volume_is_rejected_by_tray_session_adapter(self):
        audio=object.__new__(StrictWindowsAudio)
        class Control:
            def QueryInterface(self,kind): return self
        class Sessions:
            def GetCount(self):return 1
            def GetSession(self,index):return Control()
        class Manager:
            def GetSessionEnumerator(self):return Sessions()
            def QueryInterface(self,kind):return self
        class Device:
            def Activate(self,*args):return Manager()
        audio._mgr_type=types.SimpleNamespace(_iid_='fake');audio._sc_type=object();audio._clsctx=0
        audio._audio_session=lambda _:types.SimpleNamespace(SimpleAudioVolume=None)
        session,_=next(audio._sessions(Device()))
        with self.assertRaises(RuntimeError): _=session.SimpleAudioVolume

class SimulatedComAudio(StrictWindowsAudio):
    """COM-shaped fake backend exercising inherited playback and strict snapshots."""
    def __init__(self):
        self.recording=False; self.lookup=True; self.missing_volume=False
        self._seen={0:[],1:[]}
        self._mgr_type=types.SimpleNamespace(_iid_='manager')
        self._endpoint_type=types.SimpleNamespace(_iid_='endpoint')
        self._sc_type=object(); self._clsctx=0; self._audio_session=lambda control:control
        self.output=Volume(); self.a=Volume(); self.b=Volume()
    def _process_name(self,pid):
        if pid==42: return 'wetype_update.exe' if self.lookup else 'pid:42'
        return 'app.exe'
    def _devices(self,flow):
        self._seen[flow].append('capture' if flow else 'output')
        outer=self
        class Session:
            def __init__(self,pid,key,volume):
                self.ProcessId=pid; self.InstanceIdentifier=key; self.Identifier=key
                self.State=1 if outer.recording else 0
                self.SimpleAudioVolume=volume
            def QueryInterface(self,kind):return self
        class Sessions:
            def __init__(self):
                self.items=([Session(42,'capture',None)] if flow else
                            [Session(7,'a',outer.a),Session(8,'b',None if outer.missing_volume else outer.b)])
            def GetCount(self):return len(self.items)
            def GetSession(self,index):return self.items[index]
        class Manager:
            def QueryInterface(self,kind):return self
            def GetSessionEnumerator(self):return Sessions()
        class Device:
            def GetId(self):return 'capture' if flow else 'output'
            def Activate(self,kind,*args):return Manager() if kind=='manager' else outer.output
        yield Device()

class Volume:
    def __init__(self):self.muted=False;self.calls=0
    def QueryInterface(self,kind):return self
    def GetMute(self):return self.muted
    def SetMute(self,value,context):
        assert (value,context)==(0,None)
        self.calls+=1;self.muted=False

class StrictSnapshotRecoveryTests(unittest.TestCase):
    def setUp(self):
        from tray_runtime import GuardEngine
        self.engine=GuardEngine();self.engine.set_enabled(True)
        self.audio=SimulatedComAudio();self.now=0
    def poll(self):
        self.now+=.2;self.engine.poll(self.audio,self.now)
    def idle(self):
        self.audio.recording=False;self.audio.a.muted=self.audio.b.muted=False
        for _ in range(3):self.poll()
    def test_capture_lookup_recovery_during_same_recording_cannot_establish_baseline(self):
        self.audio.recording=True;self.audio.lookup=False
        for _ in range(3):self.poll()
        self.assertTrue(self.engine.status()['error'])
        self.audio.lookup=True;self.audio.a.muted=True
        self.poll()
        self.assertEqual(self.audio.a.calls,0)
        self.assertFalse(self.engine.status()['ready'])
        self.idle();self.audio.recording=self.audio.a.muted=True;self.poll()
        self.assertEqual(self.audio.a.calls,1)
    def test_missing_playback_volume_invalidates_entire_snapshot_until_fresh_idle(self):
        self.idle();self.assertTrue(self.engine.status()['ready'])
        self.audio.recording=self.audio.a.muted=True;self.audio.missing_volume=True
        self.poll()
        self.assertEqual(self.audio.a.calls,0)
        self.assertFalse(self.engine.status()['ready'])
        self.audio.missing_volume=False;self.poll()
        self.assertEqual(self.audio.a.calls,0)
        self.idle();self.audio.recording=self.audio.a.muted=True;self.poll()
        self.assertEqual(self.audio.a.calls,1)
