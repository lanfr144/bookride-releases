"""
app.py - Book&Ride demo application (version 1.1.0)

What it does when it starts
---------------------------
1. reads the 'app' block of config.yaml (name and version of the application);
2. loads the configuration block selected by APP_ENV (dev when APP_ENV is not set);
   then writes ONE log line in JSON on standard output (same shape as a logger
   record: @timestamp, service, level, message). Later these lines are loaded
   into Elasticsearch;
   and prints the mode banner and the database URL with the password masked.

Usage
-----
    python app.py                    # dev (default)
    APP_ENV=staging python app.py
    APP_ENV=prod python app.py
    APP_ENV=test python app.py       # unknown environment -> clear error, exit code 1

Both this file and config_loader.py read config.yaml with the same method:
config_loader.read_yaml_section().
"""
import json
import re
import sys
from datetime import datetime, timezone

from config_loader import ConfigError, current_env, load_config, read_yaml_section


def mask_url(url):
    """Hide the password of a URL: scheme://user:secret@host/db -> scheme://user:****@host/db"""
    return re.sub(r"(://[^:/@]+:)[^@]+@", r"\1****@", url)


def require(cfg, key):
    """Return cfg[key] or stop with a clear message when the key is missing."""
    if key not in cfg or cfg[key] in (None, ""):
        raise ConfigError(f"key {key} is missing in config.yaml for environment '{current_env()}'")
    return cfg[key]


def log_event(app, level, message, **fields):
    """Write ONE JSON log line on standard output (no logging module: a simple print).

    The four first fields are the ones used in Elasticsearch (index bookride-logs):
    @timestamp, service, level, message. The other fields give the context.
    """
    record = {
        "@timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "service": app.get("name", "bookride"),
        "level": level,
        "message": message,
        "version": str(app.get("version", "unknown")),
        **fields,
    }
    print(json.dumps(record), flush=True)


def main():
    env = current_env()
    app = {}
    try:
        app = read_yaml_section("app")          # common method, 'app' block
        cfg = load_config()                     # common method, block of APP_ENV
        database_url = require(cfg, "DB_URL")
        debug = require(cfg, "DEBUG") is True      # YAML true -> debug mode
    except ConfigError as error:
        log_event(app, "ERROR", "app_start_failed", app_env=env, reason=str(error))
        print(f"ERROR: {error}")
        return 1

    log_event(app, "INFO", "app_started", app_env=env, debug=debug,
              db_url=mask_url(database_url))
    print(f"{app['name']} {app['version']} - environment: {env}")
    if debug:
        print("[DEBUG MODE] Verbose logs enabled")
    else:
        print("[PRODUCTION MODE] Logging minimal")
    print(f"Connecting to DB: {mask_url(database_url)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
