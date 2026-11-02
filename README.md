# WeType Audio Guard · 微信输入法语音输入防静音

一个轻量的 Windows Python 工具，用于观察并尝试恢复微信输入法（WeType）语音输入期间被自动静音的**输出设备及应用播放会话**。支持多应用，而非只针对 Chrome。

> **项目阶段：已在一台 Windows 电脑上完成初步实测验证，仍是实验原型。** 目前没有托盘界面、独立 EXE、开机自启、后台服务或自动更新。暂不建议在正式会议中未经测试直接开启保护。

## 项目命名

项目名称保留为 **WeType-Audio-Guard**，意为“微信输入法音频守护工具”：

- **WeType**：微信输入法。
- **Audio**：音频。
- **Guard**：守护、防止意外静音。

## 现象与验证

实测环境中，Windows 的「通信 → 不执行任何操作」已设置，使用独立外置麦克风，Windows 录音机不会造成播放静音；但微信输入法开始语音转文字时，其他播放会话会被直接设为静音，输入结束后自动恢复。2026-11-02 的实测日志详见 [`docs/field-test-2026-11-02.md`](docs/field-test-2026-11-02.md)。

实测通过了**诊断**和**保护**：对 `ldremote.exe`、`wemeetapp.exe` 的输出音频会话观察到静音变化，启用保护后打印了 `[RESTORED]`，使用者确认声音恢复。尚未证明微信输入法内部如何实现静音，也尚未覆盖全部电脑、音频设备和软件。

## 原理及保护范围

- 通过 Windows Core Audio / WASAPI 枚举活跃的**输出设备及应用音频会话**，读取静音状态。
- 通过活跃录音会话中的 `wetype_update.exe` 进程判断微信输入法语音输入是否正在进行；不同 WeType 版本可能使用其他进程名。
- 默认诊断模式**只读**，不会修改音量。
- 仅在显式指定 `--protect` 后，尝试恢复语音输入开始前原本未静音、随后在短窗口内被静音的输出设备/会话。每次语音输入，每个会话最多尝试恢复一次。
- **不控制麦克风静音，不读取语音内容，不上传数据，不修改注册表或开机设置。**

限制：无法完全判断录音窗口内的一次静音是软件自动操作还是用户手动操作，因此仍存在误解除静音的风险；如果应用持续重复静音，保护可能无法维持。外放时还可能增加回声或影响识别准确率。

## 运行（Windows 10 / 11）

需要 Python 3.10+。在 PowerShell 中进入项目目录。若使用 Conda 虚拟环境，**优先使用 `python` 而不是 `py`**，确保使用当前环境的解释器：

```powershell
python -c "import sys; print(sys.executable)"
python -m pip install -r requirements.txt
python .\wetype_audio_guard.py --self-test
```

### 先诊断（安全、只读）

```powershell
python .\wetype_audio_guard.py --diagnose
```

保持程序运行后播放视频，启动微信输入法语音输入；观察 `[VOICE]`、`[MUTE]`、`[WOULD RESTORE]`。按 `Ctrl+C` 停止。

### 再保护（主动修改播放静音状态）

请先在**非正式会议环境**中确认诊断正确：

```powershell
python .\wetype_audio_guard.py --protect
```

常见日志：

```text
[VOICE] WeType recording ON
[MUTE] wemeetapp.exe (PID ...): ON
[RESTORED] wemeetapp.exe (PID ...)
[MUTE] wemeetapp.exe (PID ...): OFF
[VOICE] WeType recording OFF
```

用 `Ctrl+C` 结束。程序退出时不会自动重置任何已有声音设置。如语音识别未被检测到，可通过 `--capture-process` 修改录音进程名；轮询间隔及保护窗口也可通过 `--interval`、`--window` 调整。运行 `python .\wetype_audio_guard.py --help` 查看完整参数。

## 使用细节与已知局限

- 请在语音输入开始前启动程序，并留出至少 3 次空闲轮询建立基线（默认约 0.6 秒）。
- 默认轮询间隔为 0.2 秒，恢复窗口为录音开始后的 2 秒；原先已静音或录音期间新出现的会话不会被恢复。
- 每次录音周期、每个受影响输出设备或播放会话最多尝试恢复一次；即使恢复失败，也不会在同一周期重试。
- 读取音频状态失败时跳过本次操作；无法识别最初发出静音命令的进程，不能保证适配全部设备及软件。
- 旧版源码中的依赖错误提示仍提及 `py`；请以本文命令为准，使用当前环境的 `python` 安装依赖。
- 本次仓库初始化只运行编译检查、策略自测和导入检查，没有重新开启诊断或保护，也未更改当前音频设备设置；此前 Windows 实测成功结果见实测记录。

## 后续计划（尚未实现）

- Windows 托盘常驻与一键暂停
- 独立 EXE 打包与启动体验
- 可选开机自启、状态日志和更严格的防误解除静音策略

## 技术参考

- [Microsoft ISimpleAudioVolume::SetMute](https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nf-audioclient-isimpleaudiovolume-setmute)
- [Microsoft IAudioEndpointVolume::GetMute](https://learn.microsoft.com/en-us/windows/win32/api/endpointvolume/nf-endpointvolume-iaudioendpointvolume-getmute)
- [pycaw](https://github.com/AndreMiras/pycaw)

## Acknowledgements / 致谢

感谢 **SDS-CC** 公开的 [WeType Voice Tip](https://github.com/SDS-CC/wetype-voice-tip) 项目。该项目采用 [MIT License](https://github.com/SDS-CC/wetype-voice-tip/blob/b9c34c6c2dd46cb1a05f7db19c95c6239ac4bada/LICENSE)，原项目版权署名为 `Copyright (c) 2026 CYCYC-SDS`。

该项目公开了通过 Windows WASAPI 监听 `wetype_update.exe` 麦克风音频会话状态，从而判断微信输入法语音识别开始和结束的方法。WeType Audio Guard 在研发过程中参考了这一技术思路，用于识别语音录入状态，并围绕 Windows 播放应用的意外静音问题实现了诊断及恢复功能；录音状态检测思路的来源应归功于该项目。

本次对照上游提交 [`b9c34c6`](https://github.com/SDS-CC/wetype-voice-tip/tree/b9c34c6c2dd46cb1a05f7db19c95c6239ac4bada) 中的 `poc_mic_monitor.py`、`wetype_voice_tip.py` 及仓库文件清单，核查本仓库源码和全部已跟踪文件，未发现复制上游源码或素材。本项目仅参考上述技术思路；共有的 Windows 接口名称、接口标识符及目标进程名不代表复用了上游特有实现。本仓库未包含上游的图标、音频素材、打包配置或可执行文件。

WeType Voice Tip 的开始/结束提示音是上游功能，WeType Audio Guard 当前未实现提示音功能。两个项目保持独立；此致谢不表示官方合作、授权背书或隶属关系。

上述 MIT 许可证及版权署名属于上游项目，不代表本仓库整体采用 MIT 许可证。若后续实际复制或改编上游源码或素材，应随相应内容保留上游版权与许可声明。

本项目可作为实验原型公开展示和讨论，但目前尚未指定开源许可证；**公开可见不等于授权他人复制、修改或分发**。该工具并非微信输入法官方产品，也尚未经过充分的跨设备与长期稳定性验证。
