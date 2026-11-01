"""macOS launcher: machine-local PostgreSQL, portable cloud-synced snapshots."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import uuid

from launcher_utils import choose_port, ready as website_ready, reopen_running

import pgserver
import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('STUDYFLUX_RUNTIME', Path.home() / 'Library/Application Support/StudyFlux'))
RUNTIME.mkdir(parents=True, exist_ok=True)
BIN = Path(pgserver.__file__).parent / 'pginstall/bin'
DATA = RUNTIME / 'pgdata'
SNAPSHOT = ROOT / 'sync/database.dump'
STATE = RUNTIME / 'sync-state.json'
DB = 'studyflux_local'
PORT = int(os.environ.get('STUDYFLUX_DB_PORT', '55432'))
WEBPORT = int(os.environ.get('STUDYFLUX_WEB_PORT', '8000'))
USER = 'studyflux'
os.chdir(ROOT)
os.umask(0o077)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def state_write(value):
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(value))
    temporary.replace(STATE)


def run(name, *args):
    subprocess.run([str(BIN / name), *map(str, args)], check=True)


def connection():
    conn = psycopg2.connect(host='127.0.0.1', port=PORT, user=USER, dbname='postgres')
    conn.autocommit = True
    return conn


def restore_snapshot():
    # Restore to a new database first. Keep the previous database as recovery data.
    local_dump = RUNTIME / 'incoming.dump'
    shutil.copyfile(SNAPSHOT, local_dump)
    expected = digest(local_dump)
    stage = 'restore_' + uuid.uuid4().hex[:12]
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(stage)))
        run('pg_restore', '-h', '127.0.0.1', '-p', PORT, '-U', USER,
            '--no-owner', '--no-acl', '--exit-on-error', '-d', stage, local_dump)
        if digest(SNAPSHOT) != expected:
            raise RuntimeError('Облачная копия изменилась при восстановлении. Дождитесь синхронизации и повторите запуск.')
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (DB,))
            if cur.fetchone():
                previous = 'previous_' + uuid.uuid4().hex[:12]
                cur.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(DB), sql.Identifier(previous)))
            cur.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(stage), sql.Identifier(DB)))
    finally:
        conn.close()
    return expected


def save_snapshot(expected):
    local_dump = RUNTIME / 'recovery.dump'
    run('pg_dump', '-h', '127.0.0.1', '-p', PORT, '-U', USER, '-d', DB,
        '--format=custom', '--no-owner', '--no-acl', '--file', local_dump)
    if digest(SNAPSHOT) != expected:
        raise RuntimeError(f'КОНФЛИКТ: облачная база изменилась на другом Mac. Она НЕ перезаписана. Ваши данные сохранены в {local_dump}.')
    temporary = SNAPSHOT.with_name('database.' + uuid.uuid4().hex + '.tmp')
    shutil.copyfile(local_dump, temporary)
    temporary.replace(SNAPSHOT)
    state_write({'hash': digest(SNAPSHOT), 'dirty': False})
    print('Данные сохранены в sync/database.dump. Дождитесь синхронизации облака перед запуском другого Mac.', flush=True)


def interrupt(signum, frame):
    raise KeyboardInterrupt


def main():
    global PORT, WEBPORT
    lock = (RUNTIME / 'launcher.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return reopen_running(RUNTIME)
    (RUNTIME / 'running-web.json').unlink(missing_ok=True)
    if not SNAPSHOT.is_file():
        raise RuntimeError('Нет sync/database.dump. Скачайте всю папку StudyFlux из облака, затем повторите запуск.')
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    remote_hash = digest(SNAPSHOT)
    if state.get('dirty') and remote_hash != state.get('hash'):
        raise RuntimeError('После незавершённого сеанса изменилась облачная база. Локальные данные сохранены; автоматическое объединение невозможно.')
    # If a previous launcher crashed, stop only our own PostgreSQL before restarting.
    if (DATA / 'PG_VERSION').exists():
        status = subprocess.run([str(BIN / 'pg_ctl'), '-D', str(DATA), 'status'], stdout=subprocess.DEVNULL)
        if status.returncode == 0:
            run('pg_ctl', '-D', DATA, '-m', 'fast', '-w', 'stop')
    PORT = choose_port(PORT, 'PostgreSQL')
    WEBPORT = choose_port(WEBPORT, 'Website', excluded=(PORT,))
    fresh_database = not (DATA / 'PG_VERSION').exists()
    if fresh_database:
        run('initdb', '-D', DATA, '-U', USER, '--auth=trust', '--encoding=UTF8', '--locale=C')
    server = None
    started = False
    ready = False
    code = 0
    signal.signal(signal.SIGTERM, interrupt)
    try:
        run('pg_ctl', '-D', DATA, '-l', RUNTIME / 'postgres.log', '-o',
            f'-h 127.0.0.1 -p {PORT} -k /tmp', '-w', 'start')
        started = True
        if fresh_database or not state or remote_hash != state.get('hash'):
            remote_hash = restore_snapshot()
            print('Облачная копия базы восстановлена.', flush=True)
        state_write({'hash': remote_hash, 'dirty': True})
        ready = True
        env = os.environ.copy()
        env.update(DJANGO_SETTINGS_MODULE='my_portfolio.settings_local', PYTHONUNBUFFERED='1',
                   PYTHONDONTWRITEBYTECODE='1', DATABASE_URL=f'postgres://{USER}@127.0.0.1:{PORT}/{DB}')
        subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], check=True, env=env)
        print(f'\nStudyFlux: http://127.0.0.1:{WEBPORT}/\nCtrl+C — сохранить данные для другого Mac и остановить приложение.\nКоды регистрации выводятся сюда.\n', flush=True)
        server = subprocess.Popen([sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{WEBPORT}', '--noreload'], env=env)
        website_ready(server, RUNTIME, WEBPORT)
        code = server.wait()
    except KeyboardInterrupt:
        pass
    finally:
        (RUNTIME / 'running-web.json').unlink(missing_ok=True)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        try:
            if ready:
                save_snapshot(remote_hash)
        finally:
            if started:
                run('pg_ctl', '-D', DATA, '-m', 'fast', '-w', 'stop')
    return code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(f'\nОшибка: {error}', file=sys.stderr)
        sys.exit(1)
