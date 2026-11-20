# bookride-releases

Book&Ride release pipeline - assessment DEVOP2 (Part 2).
Author: François Lange (`lanfr144`).

## How to run

```bash
pip install -r requirements.txt     # PyYAML (already present on most systems)
cp .env.example .env                # optional: without .env the app uses .env.example
python app.py
```

## How the configuration works

| File | In git? | Role |
|---|---|---|
| `config.yaml` | yes | three blocks `dev`, `staging`, `prod` with `DATABASE_URL` (named `DB_URL` before v2.0.0), `API_KEY`, `DEBUG`. No secret: values are references such as `${DEV_DATABASE_URL}` |
| `.env` | **no** (`.gitignore`) | `KEY=value` lines behind the references |
| `.env.example` | yes | same keys with placeholders (`<password>`); used automatically when `.env` is missing |
| `config_loader.py` | yes | `read_yaml_section()` = the single method that reads the YAML and resolves `${...}`; `load_config()` selects the block from `APP_ENV` (default `dev`) |
| `app.py` | yes | writes one JSON log line (since v1.1.0), then prints the mode banner and the database URL with the password masked; since v3.0.0 also checks and prints the photo path |
| `assets/photo.jpg` | yes | the photo required since v3.0.0 (key `PHOTO_PATH`) |

Only fake values are used: there is no real database and no real API key.

## 2.1 Configuration by environment - terminal output

Output captured at v1.0.0.

```text
$ python app.py
bookride 1.0.0 - environment: dev
[DEBUG MODE] Verbose logs enabled
Connecting to DB: postgresql://dev_user:****@localhost:5432/bookride_dev

$ APP_ENV=staging python app.py
bookride 1.0.0 - environment: staging
[DEBUG MODE] Verbose logs enabled
Connecting to DB: postgresql://staging_user:****@staging-db:5432/bookride_staging

$ APP_ENV=prod python app.py
bookride 1.0.0 - environment: prod
[PRODUCTION MODE] Logging minimal
Connecting to DB: postgresql://prod_user:****@prod-db:5432/bookride_prod

$ APP_ENV=test python app.py
ERROR: APP_ENV=test : value not known. Choose one of: dev, staging, prod
$ echo $?
1
```

## Start-up log line (since v1.1.0)

The application writes one log line in JSON on standard output when it starts.
The first four fields (`@timestamp`, `service`, `level`, `message`) are the ones
used later in Elasticsearch; the password of the database URL is masked.

```text
$ python app.py
{"@timestamp": "2026-11-20T15:42:54Z", "service": "bookride", "level": "INFO", "message": "app_started", "version": "1.1.0", "app_env": "dev", "debug": true, "db_url": "postgresql://dev_user:****@localhost:5432/bookride_dev"}
bookride 1.1.0 - environment: dev
[DEBUG MODE] Verbose logs enabled
Connecting to DB: postgresql://dev_user:****@localhost:5432/bookride_dev

$ APP_ENV=test python app.py
{"@timestamp": "2026-11-20T15:42:54Z", "service": "bookride", "level": "ERROR", "message": "app_start_failed", "version": "1.1.0", "app_env": "test", "reason": "APP_ENV=test : value not known. Choose one of: dev, staging, prod"}
ERROR: APP_ENV=test : value not known. Choose one of: dev, staging, prod
```

## Breaking change in v2.0.0: `DB_URL` renamed `DATABASE_URL`

The key is renamed in `config.yaml`, in the code and in `.env` / `.env.example`
(see `RELEASE_NOTES.md` for the migration). Output at v2.0.0:

```text
$ python app.py
{"@timestamp": "2026-11-20T15:54:39Z", "service": "bookride", "level": "INFO", "message": "app_started", "version": "2.0.0", "app_env": "dev", "debug": true, "database_url": "postgresql://dev_user:****@localhost:5432/bookride_dev"}
bookride 2.0.0 - environment: dev
[DEBUG MODE] Verbose logs enabled
Connecting to DB: postgresql://dev_user:****@localhost:5432/bookride_dev
```

## Breaking change in v3.0.0: a photo is required

New file `assets/photo.jpg` and new key `PHOTO_PATH` in every block of `config.yaml`.
The app prints the photo path and stops with a clear error when the key or the file is missing.

```text
$ python app.py
{"@timestamp": "2026-11-20T16:01:23Z", "service": "bookride", "level": "INFO", "message": "app_started", "version": "3.0.0", "app_env": "dev", "debug": true, "database_url": "postgresql://dev_user:****@localhost:5432/bookride_dev", "photo_path": "assets/photo.jpg"}
bookride 3.0.0 - environment: dev
[DEBUG MODE] Verbose logs enabled
Connecting to DB: postgresql://dev_user:****@localhost:5432/bookride_dev
Photo: assets/photo.jpg

$ python app.py     # when assets/photo.jpg is missing
{"@timestamp": "2026-11-20T16:01:23Z", "service": "bookride", "level": "ERROR", "message": "app_start_failed", "version": "3.0.0", "app_env": "dev", "reason": "photo file not found: assets/photo.jpg (key PHOTO_PATH, environment 'dev')"}
ERROR: photo file not found: assets/photo.jpg (key PHOTO_PATH, environment 'dev')
```

## 2.2 Release strategy: canary (simulated with files)

The three production servers are simulated by three files, as in Unit 04b:
`servers/server1/version.txt`, `servers/server2/version.txt`, `servers/server3/version.txt`.
Each file contains the version that the server runs. One commit = one deployment step.

| Step | Commit | server1 | server2 | server3 |
|---|---|---|---|---|
| 0 | `Canary step 0: all servers run v2.0.0` | v2.0.0 | v2.0.0 | v2.0.0 |
| 1 | `Canary step 1: server1 runs v3.0.0` | **v3.0.0 (canary)** | v2.0.0 | v2.0.0 |
| 2 | `Canary step 2: promoted, all servers run v3.0.0` | v3.0.0 | v3.0.0 | v3.0.0 |

Why canary: v3.0.0 is a breaking change (photo required). Only one server out of three
(about a third of the traffic) receives it first; the two others keep v2.0.0. If the canary
shows errors, one `git revert` of step 1 brings server1 back to v2.0.0 and no other server is touched.

**What is live after the last step: v3.0.0 runs on all three servers (server1, server2, server3); v2.0.0 is not served any more.**
