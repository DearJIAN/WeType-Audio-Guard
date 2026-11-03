# 🐳 WeType Audio Guard 1.1

**Windows 10 / 11 x64 · 真实声音恢复修复与托盘体验更新**

这是本项目经过用户真实 Windows 复验后的正式更新。

## 下载

- **`WeTypeAudioGuard.exe`**：单文件便携 Windows 程序，无需安装 Python。
- **`WeTypeAudioGuard-1.1-windows-x64.zip`**：包含相同 EXE、README、版本历史、MIT 与第三方许可证全文。

## 1.1 有哪些变化？

- 修复旧版音频工作进程被 3 秒心跳超时误判为故障的问题。
- 去掉实时解除静音前逐个应用遍历 Windows 进程的检查。真实日志显示该检查原先每个会话耗时约 **2.06–2.08 秒**，可能导致整个录音期间依然无声；现在冲突检测在**启用保护阶段**进行。
- 录音期间恢复操作重新接近经过验证的原 CLI 路径；新增恢复延迟与下一轮静音回读日志。
- **程序打开后自动请求开启保护**（不是 Windows 开机自启），状态显示勾选标识。
- 菜单新增**查看日志**（记事本）与**复制日志**（剪贴板），无自动上传。
- 原 CLI 核心算法文件保持不变；移除仓库中已过期的临时 Windows 构建工作流。

## 真实测试与自动测试

用户在 2026-11-03 真实 Windows 系统完成三轮独立录音：
**6 次播放静音恢复调用**，每次从录音状态被检测到至恢复完成记录为
**0.00–0.02 秒**；3 次回读均为 `unmuted=2 muted=0 missing=0 recording=ON`，
用户确认实际声音正常、托盘不再报错，并认可新版操作体验。

此外，Windows GitHub Actions 已完成 **46 项自动测试**、CLI 自测、冻结 EXE 导入测试、模拟托盘与音频工作进程测试。自动化测试不代替所有硬件实测。

## 使用

1. 先退出旧 EXE 和旧 CLI `--protect`，不要同时运行多个保护程序。
2. 双击 `WeTypeAudioGuard.exe`，程序会自动请求开启保护；等待录音结束/稳定基线。
3. 正常播放视频或会议声音，再用微信输入法语音输入。右键鲸鱼图标可暂停/启用、查看恢复次数、查看或复制日志。
4. 关闭程序请在菜单选择「退出」。

**没有总运行时长限制。** 只要程序持续运行、保护未暂停且音频进程正常，就持续检测。
每轮新录音仅有独立的前 2 秒保护窗口，每个会话同轮最多尝试一次。
程序不开机自启、不更改麦克风静音、不读取语音内容。

**局限与提醒**：不能保证零瞬时中断，不保证被持续重复静音时能恢复，也不能保证所有 Windows 声卡和驱动兼容。新版本仍未签名，可能触发 SmartScreen；请仅从官方 GitHub 仓库获取，勿关闭安全软件。

完整说明见 [README](https://github.com/DearJIAN/WeType-Audio-Guard/blob/v1.1/README.md)、
[CHANGELOG](https://github.com/DearJIAN/WeType-Audio-Guard/blob/v1.1/CHANGELOG.md)、
[Windows 验收记录](https://github.com/DearJIAN/WeType-Audio-Guard/blob/v1.1/docs/windows-tray-validation.md)
及 [第三方许可声明](https://github.com/DearJIAN/WeType-Audio-Guard/blob/v1.1/THIRD_PARTY_NOTICES.md)。

原创的小鲸鱼图标由作者与未婚妻「鲸鲸」共同构思，愿它守护每一段不该突然消失的声音。🐳💙
