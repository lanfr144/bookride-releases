# Release notes

Newest version first. Versions follow MAJOR.MINOR.PATCH:
MAJOR = breaking change, MINOR = new feature, PATCH = fix.

## v2.0.0 - BREAKING CHANGE: `DB_URL` renamed `DATABASE_URL`

**Breaking change: an existing `config.yaml` or `.env` written for v1.x does not work any more.**

- In `config.yaml` the key `DB_URL` is renamed `DATABASE_URL` in every block (`dev`, `staging`, `prod`).
- In the code, `app.py` reads `DATABASE_URL`; the JSON log line has the field `database_url` (was `db_url`).
- In `.env` / `.env.example` the variables are renamed the same way:
  `DEV_DB_URL` -> `DEV_DATABASE_URL`, `STAGING_DB_URL` -> `STAGING_DATABASE_URL`, `PROD_DB_URL` -> `PROD_DATABASE_URL`.
- How to migrate: rename the three variables in your `.env`
  (`sed -i 's/_DB_URL=/_DATABASE_URL=/' .env`). With the old names the app stops with
  "variable DEV_DATABASE_URL is not defined".

## v1.1.0 - new feature: start-up log line

- `app.py` writes ONE log line in JSON on standard output when it starts
  (`@timestamp`, `service`, `level`, `message`, plus `version`, `app_env`, `debug`, `db_url` with the password masked).
- When the start fails (unknown `APP_ENV`, missing key or variable) the line has level `ERROR` and a `reason`.
- No logging module: a simple `print` of a JSON record. These lines are meant to be loaded into Elasticsearch later.
- Nothing to change in `config.yaml` or `.env`: compatible with v1.0.0.

## v1.0.0 - first version

- `config.yaml` with three environments (`dev`, `staging`, `prod`): `DB_URL`, `API_KEY`, `DEBUG`.
- `config_loader.py` selects the block from `APP_ENV` (default `dev`), clear error for an unknown environment.
- `app.py` prints the mode banner and the database URL with the password masked.
- No secret in git: values come from `.env` (ignored); `.env.example` gives the keys with placeholders.
