# Release notes

Newest version first. Versions follow MAJOR.MINOR.PATCH:
MAJOR = breaking change, MINOR = new feature, PATCH = fix.

## v1.0.0 - first version

- `config.yaml` with three environments (`dev`, `staging`, `prod`): `DB_URL`, `API_KEY`, `DEBUG`.
- `config_loader.py` selects the block from `APP_ENV` (default `dev`), clear error for an unknown environment.
- `app.py` prints the mode banner and the database URL with the password masked.
- No secret in git: values come from `.env` (ignored); `.env.example` gives the keys with placeholders.
