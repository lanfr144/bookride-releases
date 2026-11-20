# Release notes

Newest version first. Versions follow MAJOR.MINOR.PATCH:
MAJOR = breaking change, MINOR = new feature, PATCH = fix.

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
