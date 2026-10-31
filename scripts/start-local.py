"""Run a fresh local demo, with no dependency on cloud snapshots or SMTP."""
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys

import pgserver
import psycopg2

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ['STUDYFLUX_RUNTIME']).resolve()
BIN = Path(pgserver.__file__).parent / 'pginstall/bin'
DATA = RUNTIME / 'pgdata'
DB_PORT = int(os.environ.get('STUDYFLUX_DB_PORT', '55432'))
WEB_PORT = int(os.environ.get('STUDYFLUX_WEB_PORT', '8000'))


def run(name, *args, **kwargs):
    return subprocess.run([str(BIN / name), *map(str, args)], **kwargs)


def interrupt(signum, frame):
    raise KeyboardInterrupt


def main():
    os.chdir(ROOT)
    os.umask(0o077)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    lock = (RUNTIME / 'launcher.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError('This checkout is already running. Stop it with Ctrl+C first.')
    manage = sys.argv[1:2] == ['--manage']
    if sys.argv[1:] and not manage:
        raise RuntimeError('Usage: bash start.sh [--manage <Django command> ...]')
    if manage and len(sys.argv) < 3:
        raise RuntimeError('Provide a Django command after --manage.')
    # A stale pid file after a crash must not prevent PostgreSQL recovery.
    if (DATA / 'PG_VERSION').exists():
        running = run('pg_ctl', '-D', DATA, 'status', stdout=subprocess.DEVNULL).returncode == 0
        if running:
            run('pg_ctl', '-D', DATA, '-m', 'fast', '-w', 'stop', check=True)
    for port in ([DB_PORT] if manage else [DB_PORT, WEB_PORT]):
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1', port)) == 0:
                raise RuntimeError(f'Port {port} is busy. Stop the other app, or set STUDYFLUX_DB_PORT and STUDYFLUX_WEB_PORT.')
    if not (DATA / 'PG_VERSION').exists():
        run('initdb', '-D', DATA, '-U', 'studyflux', '--auth=trust', '--encoding=UTF8', '--locale=C', check=True)
    env = os.environ.copy()
    env.update(DJANGO_SETTINGS_MODULE='my_portfolio.settings_local', PYTHONUNBUFFERED='1',
               STUDYFLUX_MEDIA_ROOT=str(RUNTIME / 'media'),
               DATABASE_URL=f'postgres://studyflux@127.0.0.1:{DB_PORT}/studyflux_local')
    started = False
    server = None
    signal.signal(signal.SIGTERM, interrupt)
    try:
        run('pg_ctl', '-D', DATA, '-l', RUNTIME / 'postgres.log', '-o',
            f'-h 127.0.0.1 -p {DB_PORT} -k /tmp', '-w', 'start', check=True)
        started = True
        conn = psycopg2.connect(host='127.0.0.1', port=DB_PORT, user='studyflux', dbname='postgres')
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname='studyflux_local'")
            if not cur.fetchone():
                cur.execute('CREATE DATABASE studyflux_local')
        conn.close()
        subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], env=env, check=True)
        subprocess.run([sys.executable, 'manage.py', 'seed_demo'], env=env, check=True)
        if manage:
            return subprocess.call([sys.executable, 'manage.py', *sys.argv[2:]], env=env)
        credentials = RUNTIME / 'demo-credentials.json'
        if credentials.exists():
            login = json.loads(credentials.read_text())
            print(f"\nDemo login: {login['username']}\nDemo password: {login['password']}", flush=True)
        print(f'\nStudyFlux: http://127.0.0.1:{WEB_PORT}/\nData: {RUNTIME}\nRegistration codes appear here (no email is sent).\nCtrl+C stops the app and database.\n', flush=True)
        server = subprocess.Popen([sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{WEB_PORT}', '--noreload'], env=env)
        return server.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        if started:
            run('pg_ctl', '-D', DATA, '-m', 'fast', '-w', 'stop', check=True)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(f'\nStudyFlux: {error}', file=sys.stderr)
        sys.exit(1)
