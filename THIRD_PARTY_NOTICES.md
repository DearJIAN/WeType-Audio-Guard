# Third-party notices / 第三方许可声明

[MIT License](LICENSE) 适用于 WeType Audio Guard 自主编写的代码；**打包 EXE 中的第三方依赖仍由各自许可约束**，不受本项目 MIT 许可证替代。

| 组件 | 用途 | 上游与许可 |
| --- | --- | --- |
| [pystray 0.19.5](https://github.com/moses-palmer/pystray) | 系统托盘 | **LGPLv3**（[COPYING.LGPL](https://github.com/moses-palmer/pystray/blob/master/COPYING.LGPL)） |
| [Pillow](https://github.com/python-pillow/Pillow) | 绘制原创鲸鱼图标 | [PIL/HPND 类及附带许可声明](https://github.com/python-pillow/Pillow/blob/main/LICENSE) |
| [pycaw](https://github.com/AndreMiras/pycaw) | Windows 音频 | 以对应发行包的 LICENSE 为准 |
| [comtypes](https://github.com/enthought/comtypes) | Windows COM | [MIT](https://github.com/enthought/comtypes/blob/main/LICENSE.txt) |
| [psutil](https://github.com/giampaolo/psutil) | 进程检测 | [BSD-3-Clause](https://github.com/giampaolo/psutil/blob/master/LICENSE) |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) | 发行包构建工具 | GPL + 专门的 bootloader exception |

### 关于 pystray / LGPLv3

pystray 的版权归 Moses Palmér 及原项目贡献者所有；本项目未声称修改该库。使用者仍享有 LGPL 规定的修改、更换、重新链接与重新分发等权利。

本仓库附带 `licenses/pystray-LGPL-3.0.txt`（原项目 `COPYING.LGPL`）与 `licenses/GPL-3.0.txt`（LGPLv3 引用的 GNU GPLv3 条款），并公开完整应用源码、[构建说明](README.md#从源码运行与打包)和构建工作流，便于替换依赖后重新生成 EXE。

发行包应与适用的第三方许可声明和重建信息一同分发。不能用本项目的 MIT 声明替代 pystray 或其他上游组件的许可条件。

### 致谢（非代码复用）

[SDS-CC / WeType Voice Tip](https://github.com/SDS-CC/wetype-voice-tip)（MIT，© 2026 CYCYC-SDS）分享了可用于识别微信输入法录音状态的 WASAPI 技术思路；本项目未复制上游独特实现、图标或提示音。
