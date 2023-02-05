import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtCore
from gui import BasicMenubar
from path import app_path

if __name__=='__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    print(app_path())
    app = QApplication(sys.argv)
    ex = BasicMenubar()
    print(ex)
    sys.exit(app.exec_())
