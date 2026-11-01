import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import Mock, patch

from launcher_utils import choose_port, ready, reopen_running


class LauncherTests(unittest.TestCase):
    def test_busy_port_and_excluded_database_port_are_skipped(self):
        with socket.socket() as occupied:
            occupied.bind(('127.0.0.1', 0))
            port = occupied.getsockname()[1]
            chosen = choose_port(port, 'Website', excluded=(port + 1,))
            self.assertGreater(chosen, port + 1)
            with socket.socket() as check:
                check.bind(('127.0.0.1', chosen))

    def test_invalid_port_is_rejected(self):
        for port in (0, 65536):
            with self.assertRaises(RuntimeError):
                choose_port(port, 'Website')

    @patch('launcher_utils.open_browser')
    def test_failed_server_never_opens_browser(self, browser):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, 'stopped during startup'):
                ready(Mock(poll=Mock(return_value=1)), Path(directory), 8000)
            self.assertFalse((Path(directory) / 'running-web.json').exists())
        browser.assert_not_called()

    @patch('launcher_utils.open_browser')
    @patch('launcher_utils.urlopen')
    def test_ready_server_publishes_actual_port_and_reopens(self, request, browser):
        request.return_value.__enter__.return_value.status = 200
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            ready(Mock(poll=Mock(return_value=None)), runtime, 8014)
            self.assertEqual(json.loads((runtime / 'running-web.json').read_text()), {'port': 8014})
            self.assertEqual(reopen_running(runtime), 0)
            self.assertEqual(browser.call_count, 2)
            browser.assert_called_with('http://127.0.0.1:8014/')

    @patch('launcher_utils.open_browser')
    def test_starting_instance_without_address_does_not_open_browser(self, browser):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, 'already starting'):
                reopen_running(Path(directory))
        browser.assert_not_called()


if __name__ == '__main__':
    unittest.main()
