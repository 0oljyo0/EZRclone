import sys
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QAction, qApp, QApplication, 
    QHBoxLayout,QVBoxLayout,QLabel,QPushButton,
    QWidget,QTabWidget,QListWidget,QSpacerItem,QSizePolicy,QFileDialog,QLineEdit,QFormLayout,QCheckBox,
    QListWidgetItem, QMessageBox, QDialog, QProgressBar
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5 import QtCore
from app.core.settings import SystemSettingManger
import os
from utils.autorun import check
from app.core.path import appdata_path
# coding=utf-8
import configparser
import os
from app.services.rclone_installer import (
    ensure_rclone,
    download_rclone,
    DownloadCancelledError,
    get_default_rclone_path,
    get_default_rclone_conf_path,
)


class DownloadWorker(QtCore.QObject):
    progress_changed = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(str)
    failed = QtCore.pyqtSignal(str)
    cancelled = QtCore.pyqtSignal()

    def __init__(self, cancel_event):
        super().__init__()
        self.cancel_event = cancel_event

    @QtCore.pyqtSlot()
    def run(self):
        try:
            path = download_rclone(progress_cb=self._on_progress, cancel_event=self.cancel_event)
            self.finished.emit(path)
        except DownloadCancelledError:
            self.cancelled.emit()
        except Exception as err:
            self.failed.emit(str(err))

    def _on_progress(self, downloaded, total):
        self.progress_changed.emit(downloaded, total)


class DownloadDialog(QDialog):
    cancel_requested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("下载 rclone")
        self.setModal(True)
        self.resize(420, 130)

        self.label = QLabel("准备下载...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.cancel_requested.emit)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.cancel_button)
        self.setLayout(layout)

    def set_progress(self, downloaded, total):
        if total > 0:
            percent = int(downloaded * 100 / total)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(min(percent, 100))
            self.label.setText("正在下载 rclone（16线程）... {:.1f}MB / {:.1f}MB".format(downloaded / 1024 / 1024, total / 1024 / 1024))
        else:
            self.progress_bar.setRange(0, 0)
            self.label.setText("正在下载 rclone（16线程）... 已下载 {:.1f}MB".format(downloaded / 1024 / 1024))

    def set_cancelling(self):
        self.label.setText("正在取消下载，请稍候...")
        self.cancel_button.setText("取消中...")
        self.cancel_button.setEnabled(False)


class SettingWidget(QWidget):
    def __init__(self):
        super().__init__()
        # self.setWindowTitle("我是子窗口啊")
        self.rclonePath = ''
        self.SystemSettingManger = SystemSettingManger()
        self.downloadThread = None
        self.downloadWorker = None
        self.downloadDialog = None
        self.downloadCancelEvent = None
        self.downloadCancelledByUser = False

        self.initAllWindow()

    def initAllWindow(self):    
        self.resize(760,320)

        self.initSettingWindow()
        self.applyStyle()

        self.setWindowTitle('设置')

    def applyStyle(self):
        self.setStyleSheet("""
            QWidget { background-color: #f7f8fb; color: #222; }
            QPushButton { background-color: #2f6fed; color: white; border: none; border-radius: 6px; padding: 8px 12px; min-width: 84px; }
            QPushButton:hover { background-color: #245ad0; }
            QLineEdit { background-color: white; border: 1px solid #d8dde8; border-radius: 6px; padding: 6px 8px; }
            QCheckBox { margin-top: 10px; }
        """)
    
    def initSettingWindow(self):
        settingMainLayerout = QVBoxLayout()

        self.rclonePathLabel = QLabel("rclone.exe 默认路径：{}".format(get_default_rclone_path()))
        self.rcloneConfPathLabel = QLabel("rclone.conf 默认路径：{}".format(get_default_rclone_conf_path()))
        btnAutoDownload = QPushButton("下载 rclone")
        btnAutoDownload.clicked.connect(self.autoDownloadRclone)

        self.autorunCheckBox = QCheckBox("开机启动")
        if self.SystemSettingManger.setting_dict['AutoStart'] == "True":
            self.autorunCheckBox.setChecked(True)
        else:
            self.autorunCheckBox.setChecked(False)
        self.autorunCheckBox.stateChanged.connect(self.autorunEvent)

        settingMainLayerout.addWidget(self.rclonePathLabel)
        settingMainLayerout.addWidget(self.rcloneConfPathLabel)
        settingMainLayerout.addWidget(btnAutoDownload)
        settingMainLayerout.addWidget(self.autorunCheckBox)
        self.setLayout(settingMainLayerout)

    def autoDownloadRclone(self):
        rclone_path, downloaded = ensure_rclone(download_if_missing=False)
        if rclone_path:
            self.rclonePathLabel.setText("rclone.exe 默认路径：{}".format(rclone_path))
            QMessageBox.information(self, "提示", "已检测到本地 rclone.exe，无需下载。")
            return

        if self.downloadThread is not None and self.downloadThread.isRunning():
            QMessageBox.information(self, "提示", "下载任务已在进行中。")
            return

        self.downloadCancelledByUser = False
        self.downloadCancelEvent = threading.Event()
        self.downloadDialog = DownloadDialog(self)
        self.downloadThread = QtCore.QThread(self)
        self.downloadWorker = DownloadWorker(self.downloadCancelEvent)
        self.downloadWorker.moveToThread(self.downloadThread)

        self.downloadThread.started.connect(self.downloadWorker.run)
        self.downloadWorker.progress_changed.connect(self._onDownloadProgress)
        self.downloadWorker.finished.connect(self._onDownloadSuccess)
        self.downloadWorker.failed.connect(self._onDownloadFailed)
        self.downloadWorker.cancelled.connect(self._onDownloadCancelled)

        self.downloadWorker.finished.connect(self.downloadThread.quit)
        self.downloadWorker.failed.connect(self.downloadThread.quit)
        self.downloadWorker.cancelled.connect(self.downloadThread.quit)
        self.downloadWorker.finished.connect(self.downloadWorker.deleteLater)
        self.downloadWorker.failed.connect(self.downloadWorker.deleteLater)
        self.downloadWorker.cancelled.connect(self.downloadWorker.deleteLater)
        self.downloadThread.finished.connect(self._cleanupDownloadTask)
        self.downloadThread.finished.connect(self.downloadThread.deleteLater)

        self.downloadDialog.cancel_requested.connect(self._cancelDownload)
        self.downloadThread.start()
        self.downloadDialog.show()

    def _onDownloadProgress(self, downloaded, total):
        if self.downloadDialog is not None:
            self.downloadDialog.set_progress(downloaded, total)

    def _onDownloadSuccess(self, rclone_path):
        if self.downloadCancelledByUser:
            return
        if self.downloadDialog is not None:
            self.downloadDialog.close()
        self.rclonePathLabel.setText("rclone.exe 默认路径：{}".format(rclone_path))
        QMessageBox.information(self, "完成", "已下载并配置 rclone.exe。")

    def _onDownloadFailed(self, err_text):
        if self.downloadCancelledByUser:
            return
        if self.downloadDialog is not None:
            self.downloadDialog.close()
        QMessageBox.critical(self, "下载失败", "自动下载 rclone 失败：{}".format(err_text))

    def _cancelDownload(self):
        self.downloadCancelledByUser = True
        if self.downloadCancelEvent is not None:
            self.downloadCancelEvent.set()
        if self.downloadDialog is not None:
            self.downloadDialog.set_cancelling()

    def _onDownloadCancelled(self):
        if self.downloadDialog is not None:
            self.downloadDialog.close()
        QMessageBox.information(self, "提示", "下载已取消。")

    def _cleanupDownloadTask(self):
        self.downloadThread = None
        self.downloadWorker = None
        self.downloadCancelEvent = None
    
    def autorunEvent(self):
        if self.autorunCheckBox.isChecked():
            self.SystemSettingManger.update('AutoStart', "True")
            check(1)
        else:
            self.SystemSettingManger.update('AutoStart', "False")
            check(0)
