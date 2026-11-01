# Cloud transfer between Macs

This mode is for one person's private StudyFlux library, used on **one Mac at a time**. It is not a multi-user database synchronization service or a substitute for a server.

## Existing cloud-synchronized copies

Keep the project folder, `sync/database.dump`, and `media/` together in your cloud-synchronized Documents folder. On each Mac, wait until all files are downloaded, open Terminal in the project folder, and run:

```sh
bash start-cloud.sh
```

The first launch installs the managed runtime automatically. It restores the snapshot into machine-local PostgreSQL and applies migrations. Your existing accounts and passwords are retained; it does not add demo accounts or reset passwords. Registration messages appear in the terminal instead of being sent by email.

The default runtime remains:

```text
~/Library/Application Support/StudyFlux/
```

This is intentionally the same path used by the earlier cloud launcher. The runtime and live PostgreSQL directory stay outside Documents. Images remain in the project's `media/` directory so the cloud service can carry them between Macs.

When finished:

1. Press **Ctrl+C** and wait for the message that the snapshot was saved and the database stopped.
2. Wait for the cloud service to finish uploading `sync/database.dump` and `media/`.
3. On the other Mac, wait for those files to finish downloading before launching.

The default website and database ports are `8000` and `55432`, both on localhost. Occupied ports are skipped automatically. The launcher prints the chosen address and opens the browser after the website is ready. Repeating the command for the same runtime reopens the running site. Set `STUDYFLUX_WEB_PORT` and `STUDYFLUX_DB_PORT` to prefer another pair, or `STUDYFLUX_OPEN_BROWSER=0` to skip opening the browser.

## What the protection does

The launcher records a snapshot hash and whether the local session has unfinished changes. Incoming snapshots are first restored into a separate database; a previous local database is retained when it is replaced. On shutdown, a local `recovery.dump` is written before the cloud file is updated.

If the cloud snapshot changed during a session, the launcher refuses to overwrite it. If an unfinished local session and a changed cloud snapshot are both detected at startup, it refuses to choose one automatically.

These checks detect conflicts visible on the current Mac. A cloud provider can deliver a remote change late, so they cannot guarantee protection against concurrent use or merge two databases. Always finish and synchronize one session before opening another.

## If a conflict is reported

Keep both the cloud snapshot and the local runtime, especially `recovery.dump`, `sync-state.json`, and `pgdata/`. Stop other sessions and make separate backup copies before recovery. Decide which version to restore, or arrange a deliberate merge with database tools. Do not delete the state file merely to silence the error: it records that local changes may still need recovery.

The database dump includes account records, password hashes, articles, and comments. Media files are separate. Treat both as private backups; neither belongs in a public Git repository. Both locations are ignored by Git.

## Starting a cloud copy from the normal local demo

Normal `bash start.sh` data is intentionally separate and is not exported automatically. If you want to move that library into cloud mode, first make a backup and use a new cloud project folder with no existing `sync/database.dump` or private `media/` data.

While the normal local app is running, note its printed data directory. In a second Terminal window, from the new cloud project folder, export from that running database (replace the runtime path and port if needed):

```sh
runtime='/absolute/path/printed/by/the/local/launcher'
pg_bin="$runtime/venv/lib/python3.9/site-packages/pgserver/pginstall/bin"
mkdir -p sync
# Stop here if this folder already has a snapshot: do not overwrite it.
test ! -e sync/database.dump && \
  "$pg_bin/pg_dump" -h 127.0.0.1 -p 55432 -U studyflux \
    -d studyflux_local --format=custom --no-owner --no-acl \
    --file=sync/database.dump
```

Copy that runtime's `media/` directory into the new cloud project's `media/` directory as well. Stop the normal local app without making further edits, let the cloud files synchronize, then start cloud mode. Keep the original runtime as a backup until the restored account, articles, and images have been checked.

For a separate cloud library on a Mac that already has one, choose another machine-local runtime explicitly on every launch:

```sh
STUDYFLUX_RUNTIME="$HOME/Library/Application Support/StudyFlux/cloud-second" \
  bash start-cloud.sh
```

Do not point cloud mode at a normal local runtime: the two modes have different snapshot and media semantics. Sharing the project code in Documents alone does not transfer the database used by normal local mode.
