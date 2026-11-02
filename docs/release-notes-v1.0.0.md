# 🐳 WeType Audio Guard 1.00

首次公开版本 · Windows 10/11 x64 · Tag `v1.0.0`

微信输入法语音转文字时，其他应用可能意外静音。这个轻量 Windows 工具会在用户启用后观察录音状态，尝试恢复受影响的播放会话。

## 下载资产

- **`WeTypeAudioGuard.exe`**：可直接双击运行的单文件便携版。
- **`WeTypeAudioGuard-1.00-windows-x64.zip`**：包含 EXE、SHA-256 校验、README、MIT 许可证与第三方许可说明。
- **`WeTypeAudioGuard.exe.sha256`**：用于验证 EXE 文件完整性。

## 使用

先关闭旧 CLI `--protect`。双击 EXE 后，托盘出现**灰色小鲸鱼（默认暂停）**；右键选择「启用保护」，等待建立正常声音基线后再开启微信输入法语音识别。可随时暂停或退出，无需安装 Python。

## 首发亮点

- 多应用播放会话防意外静音
- 默认暂停、单实例、恢复计数、安全退出
- 原创蓝色鲸鱼图标及本地滚动日志
- 独立音频子进程与异常后的基线重建
- 公开源码与 MIT 许可证，致谢 [WeType Voice Tip](https://github.com/SDS-CC/wetype-voice-tip)

## 测试与风险说明

✅ 原 CLI 已在真实 Windows 环境验证两款应用的异常静音可以恢复。

✅ 托盘 36 项自动测试、Windows EXE 构建和打包导入自检通过，校验值一致。

⚠️ **EXE 尚未完成用户真实 Windows 桌面的完整音频保护、设备插拔、显示缩放及长期运行验收。** 请先用普通视频/音乐测试，避免在重要会议中第一次启用。

⚠️ EXE 未签名，Windows 可能显示未知发布者。只从此仓库下载并对照 SHA-256；不需要关闭系统安全软件。

项目原创代码为 [MIT](https://github.com/DearJIAN/WeType-Audio-Guard/blob/v1.0.0/LICENSE)，打包依赖有各自许可（`pystray` 为 LGPLv3），请见 [第三方许可说明](https://github.com/DearJIAN/WeType-Audio-Guard/blob/v1.0.0/THIRD_PARTY_NOTICES.md)。

**为什么是鲸鱼？** 因为这是作者与美丽的未婚妻「鲸鲸」共同构思的小鲸鱼，想在任务栏里一直守护你的声音。🐳💙

更多变更：[CHANGELOG.md](https://github.com/DearJIAN/WeType-Audio-Guard/blob/v1.0.0/CHANGELOG.md)
