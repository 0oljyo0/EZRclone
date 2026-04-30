import os
import sys


def app_path():
    """Return the executable/script directory."""
    if hasattr(sys, "frozen"):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


def appdata_path():
    return os.getenv("APPDATA")
