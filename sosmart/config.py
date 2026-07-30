import json
import os

try:
    from kivy.app import App
except ImportError:
    App = None


DEFAULT_CONFIG = {
    "keyword": "auxilio",
    "contacts": [],
    "volume_trigger_enabled": True,
    "shake_trigger_enabled": True,
    "listen_seconds": 8,
    "countdown_seconds": 5,
    "live_tracking_enabled": True,
    "live_tracking_interval_seconds": 180,
    "live_tracking_duration_minutes": 15,
}


def _config_path():
    running_app = App.get_running_app() if App is not None else None
    if running_app is not None:
        base = running_app.user_data_dir
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "config.json")


def load_config():
    path = _config_path()
    if not os.path.exists(path):
        return dict(DEFAULT_CONFIG)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    return merged


def save_config(config):
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
