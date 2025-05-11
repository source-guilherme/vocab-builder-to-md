import os
import json

DEFAULT_THEME = "darkly"
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")


def load_theme():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                return config.get("theme", DEFAULT_THEME)
    except (json.JSONDecodeError, IOError):
        pass
    return DEFAULT_THEME


def save_theme(theme):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"theme": theme}, f, indent=4)
