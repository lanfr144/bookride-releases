"""
config_loader.py - reads config.yaml for the Book&Ride application.

How the configuration works (read this first)
---------------------------------------------
1. config.yaml  : describes the environments (dev, staging, prod).
                  It contains NO secret, only references such as ${DEV_DB_URL}.
2. .env         : KEY=value lines with the values behind the references.
                  This file is NOT in git (see .gitignore).
3. .env.example : same keys as .env but with placeholders (<password>).
                  This file IS in git. It is used automatically when .env
                  does not exist, so the project runs right after a clone.

ONE common method reads the YAML file and resolves the ${...} references:

    read_yaml_section("app")                   -> used by app.py
    read_yaml_section("environments", "dev")   -> used by load_config() below

Run this file alone to see which block is selected:
    python config_loader.py
    APP_ENV=prod python config_loader.py
"""
import os
import re
import sys
from pathlib import Path

import yaml  # PyYAML, see requirements.txt

HERE = Path(__file__).resolve().parent
CONFIG_FILE = HERE / "config.yaml"
ENV_FILE = HERE / ".env"
ENV_EXAMPLE_FILE = HERE / ".env.example"
DEFAULT_ENV = "dev"

# ${NAME} : NAME starts with a letter or "_" and continues with letters, digits or "_"
_PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_warned = False  # the ".env not found" warning is shown only once per run


class ConfigError(ValueError):
    """Any configuration problem: unknown environment, missing key, missing variable."""


def load_env_file():
    """Load KEY=value lines into os.environ. Return the file used (or None).

    - .env is used when it exists, otherwise .env.example (with a warning on stderr).
    - A variable that already exists in the real environment is NOT replaced,
      so `DEV_API_KEY=xyz python app.py` always wins over the file.
    """
    if ENV_FILE.exists():
        path = ENV_FILE
    elif ENV_EXAMPLE_FILE.exists():
        path = ENV_EXAMPLE_FILE
        global _warned
        if not _warned:
            _warned = True
            print("[config] .env not found -> using .env.example (placeholders only). "
                  "Create your own with: cp .env.example .env", file=sys.stderr)
    else:
        return None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue  # empty line, comment, or not a KEY=value line
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return path


def _expand(value, where):
    """Replace every ${NAME} found in value (string, dict or list) with os.environ[NAME]."""
    if isinstance(value, dict):
        return {key: _expand(item, where) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand(item, where) for item in value]
    if not isinstance(value, str):
        return value  # true/false, numbers: nothing to replace

    def replace(match):
        name = match.group(1)
        if name not in os.environ:
            raise ConfigError(f"variable {name} is not defined (needed by '{where}' in "
                              f"{CONFIG_FILE.name}): add it to .env, see .env.example")
        return os.environ[name]

    return _PLACEHOLDER.sub(replace, value)


def read_yaml_section(*keys, expand=True):
    """THE common method: read config.yaml and return one section of it.

    read_yaml_section("app")                  -> the 'app' block
    read_yaml_section("environments", "dev")  -> the 'dev' block
    Only the section that is returned gets its ${...} references resolved:
    running in dev does not require the prod variables to exist.
    expand=False returns the section as written in the file (no .env needed).
    """
    load_env_file()
    with open(CONFIG_FILE, encoding="utf-8") as handle:
        section = yaml.safe_load(handle) or {}
    for depth, key in enumerate(keys):
        if not isinstance(section, dict) or key not in section:
            where = ".".join(keys[:depth + 1])
            raise ConfigError(f"'{where}' not found in {CONFIG_FILE.name}")
        section = section[key]
    return _expand(section, ".".join(keys)) if expand else section


def current_env():
    """Name of the environment asked with APP_ENV (dev when APP_ENV is not set)."""
    return os.getenv("APP_ENV", DEFAULT_ENV).strip().lower() or DEFAULT_ENV


def load_config():
    """Return the configuration block selected by APP_ENV (default: dev)."""
    env = current_env()
    known = list(read_yaml_section("environments", expand=False))
    if env not in known:
        raise ConfigError(f"APP_ENV={env} : value not known. Choose one of: {', '.join(known)}")
    return read_yaml_section("environments", env)


def mask_secret(key, value):
    """Hide what must not be shown on screen: URL passwords and API keys."""
    if not isinstance(value, str):
        return value
    if "KEY" in key or "PASSWORD" in key or "TOKEN" in key:
        return value[:4] + "****"
    return re.sub(r"(://[^:/@]+:)[^@]+@", r"\1****@", value)  # scheme://user:secret@host


if __name__ == "__main__":
    # Small self-test: print the selected block as  KEY = value  (secrets masked).
    try:
        block = load_config()
    except ConfigError as error:
        print(f"ERROR: {error}")
        sys.exit(1)
    print(f"# environment: {current_env()}")
    for key, value in block.items():
        print(f"{key} = {mask_secret(key, value)}")
