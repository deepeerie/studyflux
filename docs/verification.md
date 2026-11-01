# Local release verification

The macOS setup was verified on Apple Silicon using a clean export of the files prepared for Git, without a personal database, existing virtual environment, or `node_modules`.

## Checked

- First `bash start.sh`: download uv and Python, install pinned dependencies, initialize bundled PostgreSQL, apply migrations, seed six articles and two non-administrator accounts, serve the compiled frontend.
- Restart: retain articles, a comment submitted in the browser, and the original demo credentials; do not reseed existing accounts.
- Shutdown and conflicts: Ctrl+C stops both services; occupied website and database ports are skipped automatically; repeating the command reuses the existing website without starting another database. Launcher tests also cover invalid port values and a server that exits before becoming ready.
- Django test suite: registration and confirmation, login, Cyrillic topic creation, article create/edit and cover upload, editor upload, root comments and replies, cross-article parent rejection, comment escaping, like/unlike, pagination, topic links, ownership checks, and idempotent demo seeding.
- Browser inspection: demo login, article feed and images, profile, topic selection/highlight/blur, nested comments, and submitting a reply.
- Cloud mode on two isolated runtimes with fictional data: restore a snapshot, export edits, restore those edits on the other runtime, return to the first runtime, reject a changed snapshot without overwriting it, retain a recovery dump, and refuse an unresolved conflict on restart.
- Frontend production build and Django migration consistency.

## Limits

Intel macOS was not tested on hardware. These checks cover the restored local workflows; they are not a production deployment test, a load test, an exhaustive browser compatibility matrix, or a completed security audit. Some legacy screens use external assets and contain unfinished UI elements, such as the password-reset link. Do not interpret the presence of those elements as a verified account-recovery feature.

The launchers use loopback-only PostgreSQL with local trust authentication. This is intended for a personal development machine, not an untrusted shared host. Production authentication and network isolation must be configured separately.
