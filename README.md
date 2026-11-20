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
| `config.yaml` | yes | three blocks `dev`, `staging`, `prod` with `DB_URL`, `API_KEY`, `DEBUG`. No secret: values are references such as `${DEV_DB_URL}` |
| `.env` | **no** (`.gitignore`) | `KEY=value` lines behind the references |
| `.env.example` | yes | same keys with placeholders (`<password>`); used automatically when `.env` is missing |
| `config_loader.py` | yes | `read_yaml_section()` = the single method that reads the YAML and resolves `${...}`; `load_config()` selects the block from `APP_ENV` (default `dev`) |
| `app.py` | yes | prints the mode banner and the database URL with the password masked |

Only fake values are used: there is no real database and no real API key.

## 2.1 Configuration by environment - terminal output

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
