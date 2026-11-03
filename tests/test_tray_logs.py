"""User-invoked diagnostic export must be bounded, readable, and local."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tray_logs import diagnostic_text, open_diagnostic_logs, copy_diagnostic_logs


class DiagnosticLogTests(unittest.TestCase):
    def test_combines_recent_lines_without_uploading(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'audio.log').write_text(
                'old\n' + '\n'.join('audio%d' % i for i in range(5)) + '\n',
                encoding='utf-8')
            (root / 'tray.log').write_text('托盘启动\n', encoding='utf-8')
            result = diagnostic_text(root, per_file_lines=2)
            self.assertNotIn('audio0', result)
            self.assertIn('audio4', result)
            self.assertIn('托盘启动', result)
            self.assertIn('audio.log', result)
            self.assertIn('tray.log', result)
            self.assertIn('不会自动发送', result)

    def test_no_logs_yet_is_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            text = diagnostic_text(directory)
            self.assertEqual(text.count('（尚未生成）'), 2)

    def test_view_opens_notepad_with_combined_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'audio.log').write_text('Audio marker\n', encoding='utf-8')
            with patch('tray_logs.subprocess.Popen') as launcher:
                path = open_diagnostic_logs(root)
                self.assertTrue(path.is_file())
                self.assertIn('Audio marker', path.read_text(encoding='utf-8'))
                launcher.assert_called_once_with(
                    ['notepad.exe', str(path)], close_fds=True)

    def test_clipboard_is_only_updated_on_explicit_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('tray_logs._copy_unicode_to_clipboard') as clipboard:
                diagnostic_text(directory)
                clipboard.assert_not_called()
                copied = copy_diagnostic_logs(directory)
                clipboard.assert_called_once()
                self.assertEqual(len(clipboard.call_args.args[0]), copied)
