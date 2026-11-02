# Third-party notices / 第三方许可声明

项目自主编写代码采用 [MIT License](LICENSE)；**Windows EXE 同时包含受其他许可约束的第三方组件**。仓库所列 MIT 许可不取代这些依赖自己的版权与授权条件。

| 组件 | 项目使用的版本 | 许可证原文 |
| --- | --- | --- |
| [pystray](https://github.com/moses-palmer/pystray) | 0.19.5 | [LGPLv3](licenses/pystray-LGPL-3.0.txt)，其引用的 [GPLv3](licenses/GPL-3.0.txt) |
| [Pillow](https://github.com/python-pillow/Pillow) | 13.0.0（构建锁定） | [MIT-CMU / PIL](licenses/Pillow-MIT-CMU.txt) |
| [pycaw](https://github.com/AndreMiras/pycaw) | 20260927 | [MIT](licenses/pycaw-MIT.txt) |
| [comtypes](https://github.com/enthought/comtypes) | 1.4.17 | [MIT](licenses/comtypes-MIT.txt) |
| [psutil](https://github.com/giampaolo/psutil) | 7.2.2 | [BSD-3-Clause](licenses/psutil-BSD-3-Clause.txt) |
| [six](https://github.com/benjaminp/six) | 1.17.0（pystray 的依赖） | [MIT](licenses/six-MIT.txt) |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) | 6.22.3（构建工具及嵌入式 bootloader） | [GPL 与 Bootloader Exception](licenses/PyInstaller-COPYING.txt) |

这些文件保留了第三方版权和许可全文。直接从 GitHub Release 下载单个 EXE 的用户也可以在本仓库、同版本源码及完整 ZIP 中查阅和获取这些声明。

**pystray 的 LGPLv3**：该库的版权属于 Moses Palmér 等贡献者。遵守其修改、替换和再分发权利；本仓库提供可修改的应用完整源码、依赖清单和 [Windows 重新构建命令](README.md#从源码运行与打包)。原始 pystray 以 LGPLv3 授权，本项目没有宣称修改其代码。请在二次分发时保留适用许可和源代码/重新构建信息。

**构建说明**：对外正式 EXE 由 GitHub Actions 的 Windows 构建机从对应标签源码生成，构建约束位于 `requirements-build.txt`，完整的许可证原文位于 `licenses/`。实际传递性依赖仍需以构建锁定版本及 PyInstaller 清单为准；若改变打包依赖，需重新审视其附带许可。

### 技术思路致谢

感谢 [SDS-CC / WeType Voice Tip](https://github.com/SDS-CC/wetype-voice-tip)（MIT，原版权 © 2026 CYCYC-SDS）公开了使用 WASAPI 判断微信输入法录音会话的技术思路；本项目没有复制上游特有代码、图标或提示音素材。
