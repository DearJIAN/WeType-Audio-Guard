# 2026-11-02 · 微信输入法防静音实测记录

## 环境与问题

- Windows、PowerShell 7、Conda Python 3.12.11。
- 微信输入法（WeType）语音转文字；使用独立外置麦克风。
- 正常视频播放持续进行，微信输入法启动语音识别时多个应用的**音量合成器静音状态**变为 ON，结束后变为 OFF。
- Windows 通信设置已改为「不执行任何操作」。Windows 录音机使用同一外置麦克风录音时，播放音频正常。

## 已完成的测试

### 纯策略自测

```text
PASS: only previously-unmuted playback is protected, once, during WeType capture
```

### `--diagnose`（只读）

```text
[VOICE] WeType recording OFF
[VOICE] WeType recording ON
[MUTE] ldremote.exe (PID <redacted>): ON
[MUTE] wemeetapp.exe (PID <redacted>): ON
[WOULD RESTORE] ldremote.exe (PID <redacted>) (read-only mode)
[WOULD RESTORE] wemeetapp.exe (PID <redacted>) (read-only mode)
[VOICE] WeType recording OFF
[MUTE] ldremote.exe (PID <redacted>): OFF
[MUTE] wemeetapp.exe (PID <redacted>): OFF
```

### `--protect`（用户确认实际有效）

```text
[VOICE] WeType recording OFF
[VOICE] WeType recording ON
[MUTE] ldremote.exe (PID <redacted>): ON
[MUTE] wemeetapp.exe (PID <redacted>): ON
[RESTORED] ldremote.exe (PID <redacted>)
[RESTORED] wemeetapp.exe (PID <redacted>)
[MUTE] ldremote.exe (PID <redacted>): OFF
[MUTE] wemeetapp.exe (PID <redacted>): OFF
[VOICE] WeType recording OFF
```

用户反馈「有用」，代表该机器上的初步防静音实测成功。此日志无法单独证明具体哪个进程执行了静音操作，也不意味着已通过长期稳定性或所有应用的测试。

## 项目状态

此记录针对原始 `wetype_audio_guard.py` 实验代码；后续托盘化、打包或其他开发应以**不破坏这次通过的真实防静音行为**为前提，并保持诊断模式默认只读。
