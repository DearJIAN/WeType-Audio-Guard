#!/usr/bin/env python3
"""WeType Audio Guard — diagnostic + opt-in guarded playback unmute for Windows.

This is an independently written, experimental tool. It does NOT modify any
input device or microphone mute state. Initial Windows field validation passed;
see docs/field-test-2026-11-02.md for results and limitations.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, Optional, Sequence


@dataclass
class AudioItem:
    key: str
    label: str
    muted: bool
    controller: object  # Only used on Windows; SetMute(0, None) when protected.


class GuardPolicy:
    """Pure policy engine; no OS operations, suitable for standalone tests.

    It learns which playback endpoints/sessions were not muted just before the
    WeType capture session started. Only those may be unmuted, only once and
    only in a short window after WeType begins recording. New sessions and
    pre-muted sessions are never unmuted. No attempts outside voice input.
    """

    def __init__(self, guard_window: float = 2.0):
        self.guard_window = guard_window
        self.baseline: Dict[str, bool] = {}
        self.active = False
        self.active_since: Optional[float] = None
        self.attempted: set[str] = set()
        self.idle_ticks = 0

    def tick(self, recording: bool, items: Dict[str, AudioItem], now: float) -> list[AudioItem]:
        if recording and not self.active:
            self.active = True
            self.active_since = now
            self.attempted.clear()
            self.idle_ticks = 0
        elif not recording and self.active:
            self.active = False
            self.active_since = None
            self.idle_ticks = 0
            self.attempted.clear()

        if not recording:
            # Leave a couple of polls for WeType to restore its own mute states
            # after capture stops; do not learn that transient as a baseline.
            self.idle_ticks += 1
            if self.idle_ticks >= 3:
                self.baseline = {k: bool(item.muted) for k, item in items.items()}
            return []

        if (self.active_since is None or not self.baseline or
                now - self.active_since > self.guard_window):
            return []

        changes: list[AudioItem] = []
        for key, item in items.items():
            if (key in self.baseline and self.baseline[key] is False
                    and item.muted and key not in self.attempted):
                self.attempted.add(key)
                changes.append(item)
        return changes


def self_test() -> None:
    p = GuardPolicy(guard_window=2.0)
    initial = {
        'chrome': AudioItem('chrome', 'Chrome', False, None),
        'meeting': AudioItem('meeting', 'Tencent Meeting', False, None),
        'intentional': AudioItem('intentional', 'Muted music', True, None),
    }
    for t in [0.0, .2, .4]:
        assert p.tick(False, initial, t) == []
    changed = {
        'chrome': AudioItem('chrome', 'Chrome', True, None),
        'meeting': AudioItem('meeting', 'Tencent Meeting', True, None),
        'intentional': AudioItem('intentional', 'Muted music', True, None),
        'new': AudioItem('new', 'App opened during dictation', True, None),
    }
    assert {x.key for x in p.tick(True, changed, .6)} == {'chrome', 'meeting'}
    assert p.tick(True, changed, .8) == []  # once per app per recording
    assert p.tick(True, changed, 3.0) == []  # time window ended
    assert p.tick(False, initial, 3.2) == []
    assert p.tick(False, initial, 3.4) == []
    assert p.tick(False, initial, 3.6) == []
    assert p.baseline['intentional'] is True
    print('PASS: only previously-unmuted playback is protected, once, during WeType capture')


class WindowsAudio:
    """Enumerate all active Windows capture and render endpoints, read-only."""

    def __init__(self):
        from comtypes import CoCreateInstance, CLSCTX_ALL, GUID
        from pycaw.api.mmdeviceapi import IMMDeviceEnumerator
        from pycaw.api.audiopolicy import IAudioSessionManager2, IAudioSessionControl2
        from pycaw.api.endpointvolume import IAudioEndpointVolume
        from pycaw.utils import AudioSession
        import psutil

        self._create = CoCreateInstance
        self._clsctx = CLSCTX_ALL
        self._mgr_type = IAudioSessionManager2
        self._sc_type = IAudioSessionControl2
        self._endpoint_type = IAudioEndpointVolume
        self._audio_session = AudioSession
        self._psutil = psutil
        self._enum = CoCreateInstance(
            GUID('{BCDE0395-E52F-467C-8E3D-C4579291692E}'),
            IMMDeviceEnumerator, CLSCTX_ALL,
        )

    def _devices(self, flow: int):
        # eRender=0, eCapture=1, DEVICE_STATE_ACTIVE=1.
        collection = self._enum.EnumAudioEndpoints(flow, 1)
        for index in range(collection.GetCount()):
            yield collection.Item(index)

    def _sessions(self, dev):
        obj = dev.Activate(self._mgr_type._iid_, self._clsctx, None)
        mgr = obj.QueryInterface(self._mgr_type)
        sessions = mgr.GetSessionEnumerator()
        for index in range(sessions.GetCount()):
            control = sessions.GetSession(index)
            if control is None:
                continue
            sc2 = control.QueryInterface(self._sc_type)
            if sc2 is None:
                continue
            yield self._audio_session(sc2), index

    def _process_name(self, pid: int) -> str:
        if not pid:
            return 'System'
        try:
            return self._psutil.Process(pid).name()
        except (self._psutil.Error, OSError):
            return f'pid:{pid}'

    def wetype_recording(self, capture_executable: str) -> bool:
        """Look for a matching active capture session on ANY active mic."""
        for dev in self._devices(1):
            for session, _ in self._sessions(dev):
                if (int(session.State) == 1 and
                        self._process_name(session.ProcessId).casefold() == capture_executable.casefold()):
                    return True
        return False

    def playback(self) -> Dict[str, AudioItem]:
        items: Dict[str, AudioItem] = {}
        for dev in self._devices(0):
            dev_id = str(dev.GetId())
            ep = dev.Activate(self._endpoint_type._iid_, self._clsctx, None)
            endpoint = ep.QueryInterface(self._endpoint_type)
            key = 'endpoint:' + dev_id
            items[key] = AudioItem(key, 'Output device: ' + dev_id, bool(endpoint.GetMute()), endpoint)

            for session, index in self._sessions(dev):
                try:
                    volume = session.SimpleAudioVolume
                    if volume is None:
                        continue
                    identifier = str(session.InstanceIdentifier)
                    if not identifier:
                        identifier = str(session.Identifier)
                    session_key = 'session:' + dev_id + ':' + identifier
                    name = self._process_name(session.ProcessId)
                    items[session_key] = AudioItem(
                        session_key, f'{name} (PID {session.ProcessId})',
                        bool(volume.GetMute()), volume,
                    )
                except Exception as exc:
                    print(f'[WARN] Playback session {index}: {exc}', file=sys.stderr)
        return items


def run(args) -> int:
    if sys.platform != 'win32':
        print('This tool must run on Windows 10/11.', file=sys.stderr)
        return 2

    try:
        from comtypes import CoInitialize, CoUninitialize
        CoInitialize()
        audio = WindowsAudio()
    except Exception as exc:
        print(f'Unable to initialize Windows audio: {exc}', file=sys.stderr)
        print('Install prerequisites: py -m pip install pycaw comtypes psutil', file=sys.stderr)
        return 2

    policy = GuardPolicy(args.window)
    previous_rec: Optional[bool] = None
    previous_mutes: Dict[str, bool] = {}
    print(f'WeType Audio Guard: {"PROTECT" if args.protect else "DIAGNOSTIC ONLY"}')
    print('Only output (speaker/app) mute states are observed or changed; microphones are never modified.')
    print('Press Ctrl+C to stop. Start this tool BEFORE starting WeType dictation.')
    print(f'Capture executable: {args.capture_process}; polling every {args.interval:.2f}s')

    try:
        while True:
            now = time.monotonic()
            try:
                recording = audio.wetype_recording(args.capture_process)
                items = audio.playback()
            except Exception as exc:
                # Fail closed: never modify volume if audio state is unknown.
                print(f'[WARN] Cannot read audio state: {exc}', file=sys.stderr)
                time.sleep(args.interval)
                continue

            if recording != previous_rec:
                print('[VOICE] WeType recording ON' if recording else '[VOICE] WeType recording OFF', flush=True)
                previous_rec = recording
            for key, item in items.items():
                old = previous_mutes.get(key)
                if old is not None and old != item.muted:
                    print(f'[MUTE] {item.label}: {"ON" if item.muted else "OFF"}', flush=True)
            previous_mutes = {key: item.muted for key, item in items.items()}

            candidates = policy.tick(recording, items, now)
            for item in candidates:
                if args.protect:
                    try:
                        item.controller.SetMute(0, None)
                        print(f'[RESTORED] {item.label}', flush=True)
                    except Exception as exc:
                        print(f'[ERROR] Failed to restore {item.label}: {exc}', file=sys.stderr)
                else:
                    print(f'[WOULD RESTORE] {item.label} (read-only mode)', flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\nStopped. No sound settings changed at shutdown.')
        return 0
    finally:
        try:
            CoUninitialize()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description='WeType multi-app audio mute diagnostic/guard for Windows')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--diagnose', action='store_true', help='Read-only monitoring; default')
    modes.add_argument('--protect', action='store_true', help='Opt in to unmuting only newly muted playback sessions')
    parser.add_argument('--capture-process', default='wetype_update.exe',
                        help='Voice capture executable (default wetype_update.exe)')
    parser.add_argument('--interval', type=float, default=0.20, help='Polling seconds; default 0.2')
    parser.add_argument('--window', type=float, default=2.0, help='Max seconds after voice starts to recover once; default 2')
    parser.add_argument('--self-test', action='store_true', help='Test policy logic without audio hardware')
    args = parser.parse_args()
    if args.interval < 0.1 or args.window <= 0:
        parser.error('--interval must be >= 0.1, --window must be positive')
    if args.self_test:
        self_test()
        return 0
    return run(args)


if __name__ == '__main__':
    raise SystemExit(main())
