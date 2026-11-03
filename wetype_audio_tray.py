"""Windows tray entry point. Auto-enables protection on every launch."""
from __future__ import annotations
import argparse
import logging
import multiprocessing
import sys
from tray_logs import copy_diagnostic_logs, open_diagnostic_logs
from tray_icon import whale_icon
from tray_platform import SingleInstance, configure_logging, default_log_dir
from tray_runtime import TrayController

ERRORS = {
    'cli-conflict': '检测到 CLI 保护或无法检查进程，请停止 CLI 后重试',
    'snapshot-failed': '音频读取失败，等待重连与新基线',
    'audio-init-failed': '音频初始化失败，等待重连',
    'restore-failed': '恢复失败，本轮不重试',
    'worker-stopped': '音频进程无响应或已停止，请退出后重启',
}


def status_text(state):
    if state['pending']:
        return '正在启用保护' if state['enabled'] else '正在暂停中（等待音频确认）'
    if state['error']:
        return '错误：' + ERRORS.get(state['error'], '未知错误')
    if not state['enabled']:
        return '保护已暂停 · 录音状态未监测'
    recording = '微信输入法正在录音' if state['recording'] else '未检测到录音'
    if state['recording'] is None:
        recording = '录音状态未知'
    guard = '保护已开启' if state['ready'] else '保护已开启 · 等待录音结束/稳定基线'
    return guard + ' · ' + recording


def build_menu(controller, exit_action):
    import pystray
    item = pystray.MenuItem
    def active():
        state = controller.snapshot()
        return bool(state['enabled']) and not state['pending'] and not state['error']

    def actionable():
        return not controller.snapshot()['pending']

    def launch_logs(opener):
        try:
            opener()
        except (OSError, RuntimeError, ValueError):
            logging.getLogger('wetype_audio_guard.tray').warning(
                'Diagnostic log action failed')
            show_user_warning('无法查看或复制日志，请检查日志目录。')

    return pystray.Menu(
        item(lambda _: ('✓ ' if active() else '') + status_text(controller.snapshot()),
             None, enabled=False),
        item(lambda _: '本次成功恢复：%d 次' % controller.snapshot()['restored'], None, enabled=False),
        pystray.Menu.SEPARATOR,
        item('启用保护', lambda icon, entry: controller.set_enabled(True),
             checked=lambda _: active(),
             enabled=lambda _: actionable() and not controller.snapshot()['enabled']),
        item('暂停保护', lambda icon, entry: controller.set_enabled(False),
             enabled=lambda _: actionable() and controller.snapshot()['enabled']),
        pystray.Menu.SEPARATOR,
        item('查看日志', lambda icon, entry: launch_logs(open_diagnostic_logs)),
        item('复制日志', lambda icon, entry: launch_logs(copy_diagnostic_logs)),
        pystray.Menu.SEPARATOR,
        item('退出', exit_action),
    )


def show_user_warning(message):
    """Show a short native warning without disclosing private paths."""
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                None, message, 'WeType Audio Guard', 0x30)
            return
        except Exception:
            pass
    show_startup_failure(message)


def show_startup_failure(message):
    """Show errors in windowed EXE builds where sys.stderr may be None."""
    if getattr(sys, 'frozen', False) and sys.platform == 'win32':
        try:
            import ctypes
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            user32.MessageBoxW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p,
                                          ctypes.c_wchar_p, ctypes.c_uint]
            user32.MessageBoxW.restype = ctypes.c_int
            user32.MessageBoxW(None, message, 'WeType Audio Guard', 0x10)
            return
        except Exception:
            pass
    stream = getattr(sys, 'stderr', None)
    if stream is not None:
        try:
            stream.write(message + '\n')
        except (OSError, ValueError):
            pass


def main():
    argparse.ArgumentParser(description='WeType Audio Guard Windows tray (auto-enables on start)').parse_args()
    if sys.platform != 'win32':
        print('This tray prototype requires Windows 10/11.', file=sys.stderr)
        return 2
    from tray_windows import WindowsTrayIcon
    try:
        with SingleInstance():
            directory = default_log_dir()
            logger = configure_logging(directory)
            logger.info('Tray starting with automatic protection enabled')
            controller = TrayController(log_dir=str(directory))
            icon = WindowsTrayIcon('WeTypeAudioGuard', whale_icon(), 'WeType Audio Guard · 保护已暂停')
            previous = None
            def refresh(state):
                nonlocal previous
                if state == previous:
                    return
                previous = state
                icon.title = ('WeType Audio Guard · ' + status_text(state))[:127]
                icon.icon = whale_icon(32, state['enabled'] and not state['pending'], bool(state['error']))
            icon.apply_state = refresh
            controller.on_update = icon.request_refresh
            def exit_action(icon, entry):
                controller.close()
                icon.stop()
            icon.menu = build_menu(controller, exit_action)
            try:
                controller.start()
                def setup(icon):
                    icon.visible = True
                    # The supervisor checks CLI conflicts before enabling;
                    # audio must establish a safe idle baseline first.
                    controller.set_enabled(True)
                    icon.request_refresh(controller.snapshot())
                icon.run(setup=setup)
            finally:
                controller.close()
                icon.stop()
                logger.info('Tray exited; no audio settings changed at shutdown')
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
            return 0
    except Exception as exc:
        # Avoid disclosing paths, usernames or raw exception details.
        already_running = (isinstance(exc, RuntimeError) and
                           str(exc) == 'Tray is already running in this user session')
        reason = 'already-running' if already_running else 'startup-failed'
        logging.getLogger('wetype_audio_guard.tray').error('Startup error: %s', reason)
        message = ('WeType Audio Guard 已在运行，请检查系统托盘。' if already_running else
                   'WeType Audio Guard 启动失败。请检查本地日志和依赖。')
        show_startup_failure(message)
        return 2


if __name__ == '__main__':
    multiprocessing.freeze_support()
    raise SystemExit(main())
