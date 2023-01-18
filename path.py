import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget
from gui import BasicMenubar


def app_path():
    """Returns the base application path."""
    if hasattr(sys, 'frozen'):
        # Handles PyInstaller
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)

# if __name__=='__main__':
#     print(app_path())
