"""Loopback port selection and browser handoff shared by the macOS launchers."""
import json
import os
import socket
import subprocess
import time
from urllib.error import URLError
from urllib.request import urlopen


def choose_port(preferred, label, excluded=()):
    if not 1024 <= preferred <= 65535:
        raise RuntimeError(f'{label} port must be between 1024 and 65535.')
    for port in range(preferred, min(preferred + 100, 65536)):
        if port in excluded:
            continue
        with socket.socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(('127.0.0.1', port))
            except OSError:
                continue
        if port != preferred:
            print(f'{label}: port {preferred} is busy; using {port}.', flush=True)
        return port
    raise RuntimeError(f'No free {label} port near {preferred}. Set STUDYFLUX_DB_PORT or STUDYFLUX_WEB_PORT to another range.')


def open_browser(url):
    if os.environ.get('STUDYFLUX_OPEN_BROWSER', '1') == '0':
        return
    try:
        subprocess.run(['open', url], check=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        print(f'Open this address in your browser: {url}', flush=True)


def ready(server, runtime, port):
    url = f'http://127.0.0.1:{port}/'
    print('Waiting for the website to be ready…', flush=True)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError('The web server stopped during startup. See the error above.')
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200 and server.poll() is None:
                    (runtime / 'running-web.json').write_text(json.dumps({'port': port}))
                    print(f'\nStudyFlux is ready: {url}\nKeep this terminal open. Ctrl+C stops StudyFlux.\n', flush=True)
                    open_browser(url)
                    return
        except (URLError, OSError):
            pass
        time.sleep(0.2)
    raise RuntimeError('The website did not become ready within 60 seconds. See the server output above.')


def reopen_running(runtime):
    # Called only while another launcher holds this runtime's lock.
    try:
        port = json.loads((runtime / 'running-web.json').read_text())['port']
        if not isinstance(port, int) or not 1024 <= port <= 65535:
            raise ValueError('Invalid port')
        url = f'http://127.0.0.1:{port}/'
        with urlopen(url, timeout=2) as response:
            if response.status != 200:
                raise ValueError('Not ready')
    except (OSError, ValueError, KeyError, URLError):
        raise RuntimeError('This copy is already starting or is running with an older launcher. Check its original terminal for the website address; do not start a second database.')
    print(f'StudyFlux is already running: {url}\nReopening it; use the original terminal to stop it.', flush=True)
    open_browser(url)
    return 0
