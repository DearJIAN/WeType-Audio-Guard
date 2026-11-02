# 🐳 WeType Audio Guard v1.0.1

**Windows 10 / 11 x64 · 稳定性与发行合规修补版**

本次更新保留 v1.0.0 已验证的防静音算法，重点完善 Windows 便携 EXE 的失败提示、托盘状态刷新、冻结后启动验证及许可证材料。

### 下载

- **`WeTypeAudioGuard.exe`**：单文件便携程序，双击后默认**灰鲸（保护暂停）**。
- **`WeTypeAudioGuard-1.0.1-windows-x64.zip`**：EXE、SHA-256、README、CHANGELOG、MIT 和第三方许可证全文。
- **`WeTypeAudioGuard.exe.sha256`**：用于完整性校验。

### 修复内容

- 无控制台 EXE 启动异常或重复打开时使用 Windows 消息框显示清晰、脱敏的错误。
- 仅在托盘状态实际变化时发送刷新事件，减少后台空闲唤醒。
- 新增冻结 EXE 原生托盘与模拟音频子进程启停测试，覆盖打包独有风险而不读取或改变真实声音。
- 补充 Pillow、pycaw、comtypes、psutil、six 等第三方许可证全文，并固定 Windows 打包依赖版本。

### 使用与限制

请先关闭旧 CLI `--protect` 或旧版本托盘，双击 EXE，右键鲸鱼图标选择「启用保护」，等待稳定基线后开始微信输入法语音输入；不需要 Python。可以随时暂停或退出。

✅ 原 CLI 已在真实 Windows 环境完成微信输入法的多应用声音恢复实测；该核心文件在本次补丁中保持不变。

✅ v1.0.1 发布前 Windows CI 运行源码自测、托盘单元测试、冻结 EXE 导入与模拟托盘/音频子进程自检、文件校验。

⚠️ **仍未在用户真实 Windows 设备上完整验收 EXE 的防静音、设备插拔和长时间运行。** 初次使用请在普通视频/音乐环境测试，不要在重要会议中首次开启。

⚠️ 未签署代码签名证书，Windows 可能显示未知发布者。只从此 GitHub Release 下载并验证 SHA-256；不需要关闭安全防护。

项目自主源码采用 [MIT](https://github.com/DearJIAN/WeType-Audio-Guard/blob/v1.0.1/LICENSE)；第三方组件适用各自许可证，完整说明见 [THIRD_PARTY_NOTICES.md](https://github.com/DearJIAN/WeType-Audio-Guard/blob/v1.0.1/THIRD_PARTY_NOTICES.md)。

这只鲸鱼来自作者与美丽的未婚妻「鲸鲸」共同构思的原创小鲸鱼。🐳💙

[完整版本变更](https://github.com/DearJIAN/WeType-Audio-Guard/blob/v1.0.1/CHANGELOG.md)
