# workers/config.py
import os
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_DIR = os.path.join(ROOT, "config")

def _load_yaml(path):
    f = open(path, "r")
    data = yaml.safe_load(f)
    f.close()
    return data

def load_all():
    cfg = {}
    cfg["sources"] = _load_yaml(os.path.join(CONFIG_DIR, "sources.yaml"))
    cfg["scoring"] = _load_yaml(os.path.join(CONFIG_DIR, "scoring.yaml"))
    cfg["norm"] = _load_yaml(os.path.join(CONFIG_DIR, "normalization.yaml"))
    cfg["app"] = _load_yaml(os.path.join(CONFIG_DIR, "app.settings.yaml"))
    return cfg
