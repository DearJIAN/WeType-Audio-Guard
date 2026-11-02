<p align="center">
  <img src="docs/whale-preview.png" width="330" alt="原创小鲸鱼：暂停、启用与异常状态" />
</p>

<h1 align="center">🐳 WeType Audio Guard</h1>
<p align="center"><strong>微信输入法语音输入防静音 · 让其他应用的声音继续播放</strong></p>
<p align="center">A lightweight Windows utility to restore playback muted during WeType voice dictation.</p>

<p align="center">
  <a href="https://github.com/DearJIAN/WeType-Audio-Guard/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/DearJIAN/WeType-Audio-Guard?label=Release"></a>
  <a href="https://github.com/DearJIAN/WeType-Audio-Guard/actions/workflows/windows-release.yml"><img alt="Windows Build" src="https://github.com/DearJIAN/WeType-Audio-Guard/actions/workflows/windows-release.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/DearJIAN/WeType-Audio-Guard"></a>
  <a href="https://github.com/DearJIAN/WeType-Audio-Guard/releases"><img alt="Downloads" src="https://img.shields.io/github/downloads/DearJIAN/WeType-Audio-Guard/total?label=Downloads"></a>
  <img alt="Windows 10/11" src="https://img.shields.io/badge/Windows-10%20%7C%2011-0078D4?logo=windows">
</p>
<p align="center">
  <a href="https://github.com/DearJIAN/WeType-Audio-Guard/releases/latest"><strong>⬇️ 下载便携 EXE</strong></a>
  · <a href="CHANGELOG.md">更新日志</a>
  · <a href="docs/windows-tray-validation.md">验收文档</a>
</p>

## 💡 它解决什么问题？

部分 Windows 电脑使用微信输入法（WeType）语音转文字时，会把其他应用**直接设为静音**，包括视频、音乐和会议软件；结束录音后声音才恢复。

**WeType Audio Guard** 监测微信输入法的录音状态，并在用户**主动启用**后，尝试把识别期间意外静音的播放应用恢复正常。它支持多个播放应用，而非只针对 Chrome。

**注意：** 本工具是检测后尝试解除静音，不能阻止最初的静音动作，因此仍可能出现短暂声音中断；不能保证所有设备与版本兼容。

> **当前版本：1.0.1（Git tag `v1.0.1`）**。原命令行工具已完成真实 Windows 防静音实测；托盘版与 EXE 已通过自动化构建、自测；1.0.1 进一步加入冻结 EXE 启动与子进程的模拟验收，但**真实音频防护仍需在用户桌面验证**。

## ✨ 功能亮点

- 🐳 **原创鲸鱼托盘图标**：灰鲸表示暂停，蓝鲸表示保护启用，异常状态有提示。
- 🔊 **多应用防意外静音**：检查已建立基线的 Windows 播放设备和应用会话。
- 🛡️ **默认暂停**：每次启动需要手动「启用保护」；可随时暂停或退出。
- 🎙️ **录音状态识别**：通过 `wetype_update.exe` 的活跃录音会话检测微信输入法。
- 🔐 **保守恢复策略**：只处理原本未静音、之后异常静音的会话，每轮每会话最多尝试一次。
- 🪵 **稳定性与隐私**：单实例、音频子进程、异常后重新建立基线、本地滚动日志。
- 📦 **独立 Windows EXE**：无需安装 Python / Conda，没有安装器或自动更新。

## 🚀 快速开始

**系统：Windows 10 / 11 x64。** 前往 [GitHub Releases](https://github.com/DearJIAN/WeType-Audio-Guard/releases/latest)，下载 `WeTypeAudioGuard.exe`，或下载包含校验文件和许可证说明的 `WeTypeAudioGuard-1.0.1-windows-x64.zip`。

1. 关闭先前运行的 `python wetype_audio_guard.py --protect`，避免两个程序同时修改音频会话。
2. 双击 `WeTypeAudioGuard.exe`，任务栏通知区出现**灰色鲸鱼**（可能在隐藏图标中）。
3. 右键鲸鱼 → **启用保护**；等待录音结束并建立稳定基线，图标变为蓝色。
4. 播放视频/音乐，再使用微信输入法语音输入。右键菜单显示状态与本次恢复次数。
5. 不需要时右键 **暂停保护**或**退出**。暂停只有在音频工作进程确认后才生效；已进行中的系统调用无法撤回。

默认不会开机自启，也不会自动开启保护。**请先在普通视频场景测试，不要在重要会议中第一次启用。**

### 安全提示与校验

目前 EXE **未进行代码签名**，Windows 可能显示未知发布者或 SmartScreen 提示。请只从本项目 Release 下载，对照附带 SHA-256 检查文件完整性；不需要关闭安全软件。

```powershell
Get-FileHash .\WeTypeAudioGuard.exe -Algorithm SHA256
```

日志只保存在 `%LOCALAPPDATA%\WeTypeAudioGuard\logs`，不上传语音、会议内容或遥测。

## ⚙️ 从源码运行与打包

安装 Python 3.10+（开发实测环境为 Windows + Python 3.12.11）：

```powershell
git clone https://github.com/DearJIAN/WeType-Audio-Guard.git
cd WeType-Audio-Guard
python -m pip install -r requirements-tray.txt
python .\wetype_audio_tray.py
```

保留的 CLI（不带托盘）：

```powershell
python -m pip install -r requirements.txt
python .\wetype_audio_guard.py --self-test
python .\wetype_audio_guard.py --diagnose
# 仅在确定需要修改音频状态时：
python .\wetype_audio_guard.py --protect
```

Windows 本机重新构建 EXE：

```powershell
python -m pip install -r requirements-build.txt
python tools\build_windows_exe.py
```

产物为 `dist\WeTypeAudioGuard.exe`。GitHub Actions 在 Windows runner 上运行原 CLI 自测、托盘单元测试、PyInstaller 打包导入自检及 SHA-256 校验；**不会自动触发真实音频保护**。详见 [托盘验收说明](docs/windows-tray-validation.md)。

## 🔬 原理与安全边界

通过 Windows Core Audio / WASAPI，监听录音会话中的 `wetype_update.exe`，在无录音的稳定状态建立输出静音基线；录音开始后的短窗口内，仅对**此前未静音**而后被静音的既有输出会话尝试 `SetMute(FALSE)`。每次录音每个会话最多恢复一次，异常后重新建立基线。

- **不读取语音内容，不修改麦克风静音状态**；不更改音量数值、通信设置、系统服务或开机自启项。
- 无法可靠分辨录音期间的用户主动静音与软件自动静音，存在误解除静音风险；重复静音可能无法持续抵御。
- CLI 已真实验证 `ldremote.exe`、`wemeetapp.exe` 的播放会话恢复：[现场记录](docs/field-test-2026-11-02.md)。
- 托盘已有 **36 项自动测试**，1.0.1 又补充启动报错与事件去重回归测试；EXE 的 Windows 打包、导入自检及冻结托盘/模拟工作进程验收均纳入构建门禁。**真实 EXE 音频恢复、设备热插拔、显示缩放及长期运行仍待验证**。

## 🐋 为什么是鲸鱼？

因为项目作者的美丽未婚妻「**鲸鲸**」是一只喜欢深海蓝的小鲸鱼。💙

这只音频守护小鲸鱼由我们共同构思：**鲸鲸提出形象与配色创意，图标使用原创 Pillow 绘制代码实现**。希望它安静地待在你的任务栏里，守护那些不该突然消失的声音。

## 致谢与许可

感谢 [SDS-CC / WeType Voice Tip](https://github.com/SDS-CC/wetype-voice-tip)（MIT，原版权署名 © 2026 CYCYC-SDS）公开了通过 WASAPI 监测 `wetype_update.exe` 录音会话的技术思路。本项目在此基础上**独立实现另一种音频防静音功能**，未复制上游独特代码、图标或提示音素材，也并非微信输入法官方产品。

自主编写的项目源码采用 **[MIT License](LICENSE)**（© 2026 DearJIAN）。打包组件仍适用各自许可，例如 `pystray` 为 LGPLv3；请阅读 [第三方许可声明](THIRD_PARTY_NOTICES.md) 和 [许可原文](licenses/)。项目 MIT 不会覆盖第三方代码。

[查看版本变更](CHANGELOG.md) · [提出 Issue](https://github.com/DearJIAN/WeType-Audio-Guard/issues) · [下载 Release](https://github.com/DearJIAN/WeType-Audio-Guard/releases)
