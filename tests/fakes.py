"""Spawn-safe fake audio backends: never import or access audio hardware."""
import threading
import time

class QuietAudio:
    def __init__(self):
        self.owner = threading.get_ident()
    def snapshot(self):
        assert self.owner == threading.get_ident()
        return False, {}, ('fake-mic', 'fake-output')

class HungAudio:
    def snapshot(self):
        time.sleep(60)
        return False, {}, ()

class BrokenAudio:
    def snapshot(self):
        raise OSError('simulated unplug')

class SharedAudio:
    def __init__(self, recording, muted, block, entered, release, calls):
        self.recording,self.muted,self.block=recording,muted,block
        self.entered,self.release,self.calls=entered,release,calls
    def snapshot(self):
        from wetype_audio_guard import AudioItem
        recording,muted=self.recording.value,self.muted.value
        if self.block.is_set():
            self.entered.set(); self.release.wait(10)
        return bool(recording), {'app':AudioItem('app','private label',bool(muted),self)}, ('mic','speaker')
    def SetMute(self,value,context):
        assert (value,context)==(0,None)
        with self.calls.get_lock(): self.calls.value+=1

def native_paused_probe(connection, directory):
    """Full entry smoke test: actual tray, always paused, automatic UI-thread exit."""
    import sys
    import threading
    from unittest.mock import patch
    from pathlib import Path
    from tray_windows import WindowsTrayIcon
    import wetype_audio_tray
    owner=threading.get_ident()
    observations=[]
    class ProbeIcon(WindowsTrayIcon):
        def _on_refresh(self,wparam,lparam):
            super()._on_refresh(wparam,lparam)
            observations.append((threading.get_ident()==owner,self._latest_state['enabled']))
            self.stop()
    with patch('tray_windows.WindowsTrayIcon',ProbeIcon), \
         patch('wetype_audio_tray.default_log_dir',lambda:Path(directory)), \
         patch.object(sys,'argv',['wetype_audio_tray.py']):
        code=wetype_audio_tray.main()
    connection.send((code,observations))
    connection.close()
