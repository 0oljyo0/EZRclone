"""Backward-compatible import bridge for legacy utils.path."""

from app.core.path import app_path, appdata_path


if __name__ == "__main__":
    print(appdata_path())
