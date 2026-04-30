import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QMainWindow, QAction, qApp, QApplication, 
    QHBoxLayout,QVBoxLayout,QLabel,QPushButton,
    QWidget,QTabWidget,QListWidget,QSpacerItem,QSizePolicy,QFileDialog,QLineEdit,QFormLayout,QCheckBox,
    QListWidgetItem, QMessageBox, QTableWidget, QAbstractItemView, QDialog, QProgressBar
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
import json

from winds.settingWindow import SettingWidget
from winds.createNewMountWindow import CreateNewMountWidget
from winds.protocolMountWindow import ProtocolMountWindow
from app.services.protocol_mount_service import ProtocolMountService
from app.services.winfsp_installer import (
    ensure_winfsp,
    DownloadCancelledError as WinFspCancelledError,
)

import threading

import os
import subprocess

from PyQt5.QtWidgets import QFrame

# 导入 QHeaderView
from PyQt5.QtWidgets import QHeaderView
from app.services.rclone_installer import (
    ensure_rclone,
    download_rclone,
    DownloadCancelledError,
    get_default_rclone_path,
    get_default_rclone_conf_path,
)


class RcloneDownloadWorker(QtCore.QObject):
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


class DownloadProgressDialog(QDialog):
    cancel_requested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("下载 rclone")
        self.setModal(True)
        self.resize(420, 130)

        self.label = QLabel("准备下载...")
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.cancelButton = QPushButton("取消")
        self.cancelButton.clicked.connect(self._on_cancel_click)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.cancelButton)
        self.setLayout(layout)

    def _on_cancel_click(self):
        self.cancel_requested.emit()

    def set_progress(self, downloaded, total):
        if total > 0:
            percent = int(downloaded * 100 / total)
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(min(percent, 100))
            self.label.setText("正在下载 rclone（16线程）... {:.1f}MB / {:.1f}MB".format(downloaded / 1024 / 1024, total / 1024 / 1024))
        else:
            self.progressBar.setRange(0, 0)
            self.label.setText("正在下载 rclone（16线程）... 已下载 {:.1f}MB".format(downloaded / 1024 / 1024))

    def set_cancelling(self):
        self.label.setText("正在取消下载，请稍候...")
        self.cancelButton.setText("取消中...")
        self.cancelButton.setEnabled(False)


class WinFspDownloadWorker(QtCore.QObject):
    progress_changed = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal()
    failed = QtCore.pyqtSignal(str)
    cancelled = QtCore.pyqtSignal()

    def __init__(self, cancel_event):
        super().__init__()
        self.cancel_event = cancel_event

    @QtCore.pyqtSlot()
    def run(self):
        try:
            ensure_winfsp(download_if_missing=True, progress_cb=self._on_progress, cancel_event=self.cancel_event)
            self.finished.emit()
        except WinFspCancelledError:
            self.cancelled.emit()
        except Exception as err:
            self.failed.emit(str(err))

    def _on_progress(self, downloaded, total):
        self.progress_changed.emit(downloaded, total)

class MainUI(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        
        self.setting = SystemSettingManger()
        self.setting.load()
        self.tasks = []
        self.protocol_service = ProtocolMountService()
        self.winfspThread = None
        self.winfspWorker = None
        self.winfspDialog = None
        self.winfspCancelEvent = None
        self.winfspCancelledByUser = False
        self.winfspTargetMountId = None

        # self.setWindowFlags(QtCore.Qt.SplashScreen | QtCore.Qt.FramelessWindowHint)
        
        self.initAllWindow()
        self.ensureRcloneAtStartup()

        print(self.setting.setting_dict)

        self.mountAll()
        self.protocol_service.start_autostart_mounts()
        
        


    
    def mountAll(self):
        self.setting.load()
        if not self.setting.setting_dict.get('RclonePath'):
            self.statusBar().showMessage("未检测到 rclone.exe，无法自动挂载。", 5000)
            return

        for mountInfo in self.setting.setting_dict['AutoMounts']:
            print(mountInfo)
            task = threading.Thread(target=self.mountSingle, args=(mountInfo,))
            task.setDaemon(True)
            task.start()
            self.tasks.append(task)

    def mountSingle(self, mountInfo):
        print("task",mountInfo)
        cmd = '"{}" mount "{}:{}" "{}" --volname "{}"'.format(
            self.setting.setting_dict['RclonePath'],
            mountInfo['name'],
            mountInfo['RemoteAbsolutePath'],
            mountInfo['LocalDeviceId'],
            mountInfo['DeviceName'],
        )
        print(cmd)
        # os.system(cmd)
        res = subprocess.run(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    def initAllWindow(self):    
        self.resize(900,620)
        self.initMenuBar()
        self.initCentrolWindow()
        self.applyStyle()
        self.statusBar().showMessage("EZRclone 就绪", 3000)
        self.setWindowTitle('EZRclone')    
        self.show()

    def applyStyle(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #f7f8fb; color: #222; }
            QTabWidget::pane { border: 1px solid #d8dde8; border-radius: 8px; background: white; }
            QTabBar::tab { padding: 8px 16px; margin-right: 4px; border: 1px solid #d8dde8; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: white; font-weight: 600; }
            QPushButton { background-color: #2f6fed; color: white; border: none; border-radius: 6px; padding: 8px 12px; min-width: 110px; }
            QPushButton:hover { background-color: #245ad0; }
            QTableWidget, QListWidget { border: 1px solid #d8dde8; border-radius: 6px; background: white; }
            QLabel { font-size: 13px; }
        """)

    def initMenuBar(self):
        exitAction = QAction('&Exit', self)        
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('退出应用')
        exitAction.triggered.connect(qApp.quit)

        setAction = QAction('&Setting', self)        
        setAction.setShortcut('Ctrl+E')
        setAction.setStatusTip('打开设置')
        setAction.triggered.connect(self.settingEvent)

        cleanSetAction = QAction('&CleanSetting', self)        
        # cleanSetAction.setShortcut('Ctrl+E')
        cleanSetAction.setStatusTip('清理设置')
        cleanSetAction.triggered.connect(self.cleanSetting)


        menubar = self.menuBar()
        fileMenu = menubar.addMenu('文件')
        fileMenu.addAction(exitAction)
        fileMenu.addAction(setAction)
        fileMenu.addAction(cleanSetAction)

        setMenu = menubar.addMenu('帮助')

    def initCentrolWindow(self):
        remotesTab = self.buildRemotesTab()
        protocolMountTab = self.buildProtocolMountTab()
        # cccTab = QWidget()

        tabWidget = QTabWidget()
        tabWidget.addTab(remotesTab, "远程配置")
        tabWidget.addTab(protocolMountTab, "协议挂载")
        # tabWidget.addTab(cccTab, "ccc")
        self.setCentralWidget(tabWidget)

    def buildProtocolMountTab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()

        self.protocolTable = QTableWidget()
        self.protocolTable.setColumnCount(6)
        self.protocolTable.setHorizontalHeaderLabels(["名称", "协议", "主机/URL", "本地盘符", "自启动", "状态"])
        self.protocolTable.verticalHeader().setVisible(False)
        self.protocolTable.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.protocolTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.protocolTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.protocolTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.protocolTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.refreshProtocolMountTab()

        btn_new = QPushButton("新增")
        btn_new.clicked.connect(self.createProtocolMountEvent)
        btn_start = QPushButton("启动")
        btn_start.clicked.connect(self.startProtocolMountEvent)
        btn_stop = QPushButton("停止")
        btn_stop.clicked.connect(self.stopProtocolMountEvent)
        btn_delete = QPushButton("删除")
        btn_delete.clicked.connect(self.deleteProtocolMountEvent)
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refreshProtocolMountTab)

        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_start)
        btn_layout.addWidget(btn_stop)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_refresh)

        layout.addWidget(self.protocolTable)
        layout.addLayout(btn_layout)
        tab.setLayout(layout)
        return tab

    def refreshProtocolMountTab(self):
        mounts = self.protocol_service.list_mounts()
        self.protocolTable.setRowCount(len(mounts))
        for idx, mount in enumerate(mounts):
            values = [
                mount.get("name", ""),
                mount.get("protocol", ""),
                mount.get("host", ""),
                mount.get("local_path", ""),
                "是" if mount.get("auto_start") else "否",
                mount.get("status", "未启动"),
            ]
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.protocolTable.setItem(idx, col, item)

    def _current_protocol_mount(self):
        row = self.protocolTable.currentRow()
        if row < 0:
            return None
        mounts = self.protocol_service.list_mounts()
        if row >= len(mounts):
            return None
        return mounts[row]

    def createProtocolMountEvent(self):
        self.protocolMountWindow = ProtocolMountWindow(self.refreshProtocolMountTab)
        self.protocolMountWindow.setWindowModality(Qt.ApplicationModal)
        self.protocolMountWindow.show()

    def startProtocolMountEvent(self):
        mount = self._current_protocol_mount()
        if not mount:
            QMessageBox.information(self, "提示", "请先选择一个协议挂载项。")
            return
        try:
            self.protocol_service.start_mount(mount["id"])
            self.statusBar().showMessage("协议挂载已启动。", 3000)
        except Exception as err:
            if "WinFsp" in str(err):
                ret = QMessageBox.question(
                    self,
                    "缺少 WinFsp",
                    "检测到未安装 WinFsp，是否现在下载并安装？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if ret == QMessageBox.Yes:
                    self._startWinFspDownload(mount["id"])
                    return
            QMessageBox.critical(self, "启动失败", str(err))
        self.refreshProtocolMountTab()

    def stopProtocolMountEvent(self):
        mount = self._current_protocol_mount()
        if not mount:
            QMessageBox.information(self, "提示", "请先选择一个协议挂载项。")
            return
        self.protocol_service.stop_mount(mount["id"])
        self.statusBar().showMessage("协议挂载已停止。", 3000)
        self.refreshProtocolMountTab()

    def deleteProtocolMountEvent(self):
        mount = self._current_protocol_mount()
        if not mount:
            QMessageBox.information(self, "提示", "请先选择一个协议挂载项。")
            return
        self.protocol_service.delete_mount(mount["id"])
        self.statusBar().showMessage("协议挂载已删除。", 3000)
        self.refreshProtocolMountTab()

    def buildNewMountsTab(self):
        mountsTab = QWidget()
        mountsTabMainLayerout = QVBoxLayout()
        btnLayerout = QHBoxLayout()
        
        
        self.newMountTab = QTableWidget()
        self.newMountTab.setColumnCount(4)
        self.newMountTab.setHorizontalHeaderLabels(['设备名称','远程名称','远程绝对路径','本地盘符'])
        
        # self.newMountTab.setShowGrid(False)
        # 隐藏行表头
        self.newMountTab.verticalHeader().setVisible(False)
        # 所有内容居中显示
        self.newMountTab.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        # 去掉表格所有边框
        # self.newMountTab.setFrameShape(QFrame.NoFrame)
        # self.newMountTab.setFrameShape(QFrame.NoFrame)
        # 设置不可编辑
        self.newMountTab.setEditTriggers(QTableWidget.NoEditTriggers)
        # 设置不获取焦点
        self.newMountTab.setFocusPolicy(Qt.NoFocus)
        self.newMountTab.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.newMountTab.setSelectionMode(QAbstractItemView.SingleSelection)
        # 表格自适应伸缩
        self.newMountTab.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.refreshNewMountsTab()
        
        
        mountsTabMainLayerout.addWidget(self.newMountTab)
        
        btn_config = QPushButton("新建挂载")
        btn_config.clicked.connect(self.createNewMountEvent)
        # btn_mount= QPushButton("Delet Mount")
        spacerItem1 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacerItem2 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_delet = QPushButton("删除挂载")
        btn_delet.clicked.connect(self.deletNewMountEvent)
        
        btn_remount = QPushButton("重新挂载全部")
        btn_remount.clicked.connect(self.remountAll)
        
        btnLayerout.addWidget(btn_config)
        # remotesTabButtonLayerout.addWidget(btn_mount)
        btnLayerout.addItem(spacerItem1)
        btnLayerout.addWidget(btn_remount)
        btnLayerout.addItem(spacerItem2)
        btnLayerout.addWidget(btn_delet)
        mountsTabMainLayerout.addLayout(btnLayerout)
        
        mountsTab.setLayout(mountsTabMainLayerout)
        return mountsTab

    def deletNewMountEvent(self):
        
        # 获取选中行序号
        index = self.newMountTab.currentRow()
        if index<0:
            QMessageBox.information(self, "提示", "请先选择一个挂载项。")
            return
        
        self.SystemSettingManger = SystemSettingManger()
        self.SystemSettingManger.load()
        del self.SystemSettingManger.setting_dict['AutoMounts'][index]
        self.SystemSettingManger.save()
        self.refreshNewMountsTab()
        self.statusBar().showMessage("挂载项已删除。", 3000)
        
        # # 删除选中行
        # self.newMountTab.removeRow(self.newMountTab.currentRow())
    
    def refreshNewMountsTab(self):
        with open(appdata_path()+"/qrclone/setting.json") as qrclone_file:
            settings = json.load(qrclone_file)

        self.newMountTab.clearContents()
        print(len(settings['AutoMounts']))
        self.newMountTab.setRowCount(len(settings['AutoMounts']))
        for mountSettingItem in settings['AutoMounts']:
            deviceNameItem = QtWidgets.QTableWidgetItem(mountSettingItem['DeviceName'])
            remoteNameItem = QtWidgets.QTableWidgetItem(mountSettingItem['name'])
            remoteAbsolutePathItem = QtWidgets.QTableWidgetItem(mountSettingItem['RemoteAbsolutePath'])
            localDeviceIdItem = QtWidgets.QTableWidgetItem(mountSettingItem['LocalDeviceId'])
            deviceNameItem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            remoteNameItem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            remoteAbsolutePathItem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            localDeviceIdItem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            
            self.newMountTab.setItem(settings['AutoMounts'].index(mountSettingItem), 0, deviceNameItem)
            self.newMountTab.setItem(settings['AutoMounts'].index(mountSettingItem), 1, remoteNameItem)
            self.newMountTab.setItem(settings['AutoMounts'].index(mountSettingItem), 2, remoteAbsolutePathItem)
            self.newMountTab.setItem(settings['AutoMounts'].index(mountSettingItem), 3, localDeviceIdItem)
            # self.newMountTab.setItem(settings['AutoMounts'].index(mountSettingItem), 0, QtWidgets.QTableWidgetItem(mountSettingItem['DeviceName']))
            # self.newMountTab.setItem(settings['AutoMounts'].index(mountSettingItem), 1, QtWidgets.QTableWidgetItem(mountSettingItem['name']))
            # self.newMountTab.setItem(settings['AutoMounts'].index(mountSettingItem), 2, QtWidgets.QTableWidgetItem(mountSettingItem['RemoteAbsolutePath']))
            # self.newMountTab.setItem(settings['AutoMounts'].index(mountSettingItem), 3, QtWidgets.QTableWidgetItem(mountSettingItem['LocalDeviceId']))
        #     # self.remotesListWidget.addItem(remotesListWidgetItem)
        #     item = QListWidgetItem() # 创建QListWidgetItem对象
        #     item.setSizeHint(QSize(0, 50)) # 设置QListWidgetItem大小
        #     widget = self.buildRemotesItem(mountSettingItem)#QPushButton("bbbbbbb")
        #     self.mountsListWidget.addItem(item) # 添加item
        #     self.mountsListWidget.setItemWidget(item, widget) # 为item设置widget


    def buildMountsTab(self):
        # baseWidget = QWidget()
        remotesTab = QWidget()
        remotesTabMainLayerout = QVBoxLayout()

        remotesTabBodyLayerout = QHBoxLayout()
        remotesTabButtonLayerout = QHBoxLayout()

        self.mountsListWidget = QListWidget()
        self.refreshMountsTab()

        btn_config = QPushButton("新建挂载")
        btn_config.clicked.connect(self.createNewMountEvent)
        # btn_mount= QPushButton("Delet Mount")
        spacerItem1 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacerItem2 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_delet = QPushButton("删除挂载")
        btn_delet.clicked.connect(self.deletMountEvent)
        
        btn_remount = QPushButton("重新挂载全部")
        btn_remount.clicked.connect(self.remountAll)
        
        remotesTabButtonLayerout.addWidget(btn_config)
        # remotesTabButtonLayerout.addWidget(btn_mount)
        remotesTabButtonLayerout.addItem(spacerItem1)
        remotesTabButtonLayerout.addWidget(btn_remount)
        remotesTabButtonLayerout.addItem(spacerItem2)
        remotesTabButtonLayerout.addWidget(btn_delet)

        remotesTabMainLayerout.addWidget(self.mountsListWidget)
        remotesTabMainLayerout.addLayout(remotesTabButtonLayerout)

        remotesTab.setLayout(remotesTabMainLayerout)
        return remotesTab
    
   
    def remountAll(self):
        if not self.setting.setting_dict.get('RclonePath'):
            QMessageBox.warning(self, "提示", "请先配置或下载 rclone.exe。")
            return
        cmd = 'taskkill /F /IM '+self.setting.setting_dict['RclonePath'].split("/")[-1]
        res = subprocess.run(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(res.stdout.decode('gbk'))
        self.mountAll()
        self.statusBar().showMessage("已重新挂载全部配置。", 4000)

    def deletMountEvent(self):
        # print(self.mountsListWidget.selectedItems())
        if len(self.mountsListWidget.selectedIndexes()) == 0:
            print("先选择一个mount")
            return
        # print(self.mountsListWidget.selectedIndexes()[0].row())
        # print("aaaaa")
        del_index = self.mountsListWidget.selectedIndexes()[0].row()

        self.SystemSettingManger = SystemSettingManger()
        self.SystemSettingManger.load()
        del self.SystemSettingManger.setting_dict['AutoMounts'][del_index]
        self.SystemSettingManger.save()
        self.refreshMountsTab()

    def createNewMountEvent(self):
        self.newMountWindow = CreateNewMountWidget(self.refreshNewMountsTab)
        self.newMountWindow.setWindowModality(Qt.ApplicationModal)
        self.newMountWindow.show()

    def refreshMountsTab(self):
        with open(appdata_path()+"/qrclone/setting.json") as qrclone_file:
            settings = json.load(qrclone_file)

        self.mountsListWidget.clear()
        for mountSettingItem in settings['AutoMounts']:
            # self.remotesListWidget.addItem(remotesListWidgetItem)
            item = QListWidgetItem() # 创建QListWidgetItem对象
            item.setSizeHint(QSize(0, 50)) # 设置QListWidgetItem大小
            widget = self.buildRemotesItem(mountSettingItem)#QPushButton("bbbbbbb")
            self.mountsListWidget.addItem(item) # 添加item
            self.mountsListWidget.setItemWidget(item, widget) # 为item设置widget

    def buildRemotesItem(self,title):
        mountItem = QWidget()
        mountItemMainLayerout = QHBoxLayout()

        # text = QLabel("Remote Name:"+title['name'])
        text = QLabel(title['name'])
        volNameLable = QLabel("volname:"+title['DeviceName'])
        remoteAbPathLable = QLabel("远程绝对路径："+title['RemoteAbsolutePath'])
        localDeviceIdLabel = QLabel("本地绝对路径："+title['LocalDeviceId'])

        mountItemMainLayerout.addWidget(text)
        mountItemMainLayerout.addWidget(volNameLable)
        mountItemMainLayerout.addWidget(remoteAbPathLable)
        mountItemMainLayerout.addWidget(localDeviceIdLabel)
        
        mountItem.setLayout(mountItemMainLayerout)
        return mountItem

    def deleteDuplicate(self, li):
        l = li
        seen = set()
        new_l = []
        for d in l:
            t = tuple(d.items())
            if t not in seen:
                seen.add(t)
                new_l.append(d)
        
        return new_l

    def buildRemotesTab(self):
        remotesTab = QWidget()
        remotesTabMainLayerout = QVBoxLayout()

        remotesTabBodyLayerout = QHBoxLayout()
        remotesTabButtonLayerout = QHBoxLayout()

        self.remotesListWidget = QListWidget()
        self.refreshRemotesTab()

        self.remotesListWidget.itemClicked.connect(self.showRemoteInfo)
        # self.remotesListWidget.itemDoubleClicked.connect(self.changeSettingEvent)#.DoubleClicked.connect(MainWindow.btnDoub_click)
        self.remotesInfoLable = QLabel("")

        # btn_config = QPushButton("Config")
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refreshRemotesTab)
        spacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # btn_ccc = QPushButton("ccc")
        # remotesTabButtonLayerout.addWidget(btn_config)
        remotesTabButtonLayerout.addWidget(btn_refresh)
        remotesTabButtonLayerout.addItem(spacerItem)
        # remotesTabButtonLayerout.addWidget(btn_ccc)

        remotesTabMainLayerout.addWidget(self.remotesListWidget)
        remotesTabMainLayerout.addWidget(self.remotesInfoLable)
        remotesTabMainLayerout.addLayout(remotesTabButtonLayerout)

        remotesTab.setLayout(remotesTabMainLayerout)
        return remotesTab

    # def changeSettingEvent(self):
    #     item = self.remotesListWidget.selectedItems()[0]
    #     self.child_window = ChangeSystemSettingManger(item.text())
    #     self.child_window.setWindowModality(Qt.ApplicationModal)
    #     self.child_window.show()

    #     item = self.remotesListWidget.selectedItems()[0]

    #     self.refreshRemotesTab()

    def showRemoteInfo(self):
        rclone_config_file = get_default_rclone_conf_path()
        rclone_conf = configparser.ConfigParser()
        filename = rclone_conf.read(rclone_config_file)

        item = self.remotesListWidget.selectedItems()[0]
        show_text = ''
        for ite in rclone_conf.items(item.text()):
            show_text+=(ite[0]+":"+ite[1]+"\n")
        # print(rclone_conf.items(item.text()))
        # print(item.text())
        self.remotesInfoLable.setText(show_text)
    
    def refreshRemotesTab(self):
        rclone_config_file = get_default_rclone_conf_path()
        rclone_conf = configparser.ConfigParser()
        filename = rclone_conf.read(rclone_config_file)

        self.remotesListWidget.clear()
        for remotesListWidgetItem in rclone_conf.sections():
            # print(remotesListWidgetItem)
            self.remotesListWidget.addItem(remotesListWidgetItem)
        self.statusBar().showMessage("Remotes 已刷新。", 2500)


    def settingEvent(self):
        self.settingWindow = SettingWidget()#SystemSettingManger()
        self.settingWindow.setWindowModality(Qt.ApplicationModal)
        self.settingWindow.show()

    def cleanSetting(self):
        # print(appdata_path()+"\qrclone\setting.json")
        os.system("del "+appdata_path()+"\qrclone\setting.json")

    def ensureRcloneAtStartup(self):
        rclone_path, _ = ensure_rclone(download_if_missing=False)
        if rclone_path:
            self.setting.load()
            return

        msg = (
            "未检测到 rclone.exe。\n\n"
            "是否现在下载到默认路径？\n"
            "{}"
        ).format(get_default_rclone_path())
        ret = QMessageBox.question(self, "下载 rclone", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ret != QMessageBox.Yes:
            self.statusBar().showMessage("已跳过下载 rclone.exe，可在设置页手动触发。", 6000)
            return

        self._startRcloneDownload()

    def _startRcloneDownload(self):
        if hasattr(self, "downloadThread") and self.downloadThread is not None and self.downloadThread.isRunning():
            self.statusBar().showMessage("下载任务已在进行中。", 3000)
            return

        self.downloadCancelledByUser = False
        self.downloadCancelEvent = threading.Event()
        self.downloadDialog = DownloadProgressDialog(self)

        self.downloadThread = QtCore.QThread(self)
        self.downloadWorker = RcloneDownloadWorker(self.downloadCancelEvent)
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
        self.downloadThread.finished.connect(self.downloadThread.deleteLater)

        self.downloadDialog.cancel_requested.connect(self._cancelDownload)
        self.downloadThread.start()
        self.downloadDialog.show()

    def _onDownloadProgress(self, downloaded, total):
        self.downloadDialog.set_progress(downloaded, total)

    def _onDownloadSuccess(self, rclone_path):
        if self.downloadCancelledByUser:
            return
        self.downloadDialog.progressBar.setValue(100)
        self.downloadDialog.close()
        self.setting.load()
        QMessageBox.information(self, "完成", "rclone 下载成功：\n{}".format(rclone_path))
        self.statusBar().showMessage("rclone 已就绪。", 4000)

    def _onDownloadFailed(self, err_text):
        if self.downloadCancelledByUser:
            return
        self.downloadDialog.close()
        QMessageBox.critical(self, "下载失败", "下载 rclone 失败：{}".format(err_text))
        self.statusBar().showMessage("rclone 下载失败。", 6000)

    def _cancelDownload(self):
        self.downloadCancelledByUser = True
        if hasattr(self, "downloadCancelEvent") and self.downloadCancelEvent:
            self.downloadCancelEvent.set()
        if hasattr(self, "downloadDialog") and self.downloadDialog:
            self.downloadDialog.set_cancelling()
        self.statusBar().showMessage("已请求取消下载。", 6000)

    def _onDownloadCancelled(self):
        if hasattr(self, "downloadDialog") and self.downloadDialog:
            self.downloadDialog.close()
        self.statusBar().showMessage("下载已取消。", 5000)

    def _startWinFspDownload(self, mount_id):
        if self.winfspThread is not None and self.winfspThread.isRunning():
            QMessageBox.information(self, "提示", "WinFsp 下载任务已在进行中。")
            return

        self.winfspTargetMountId = mount_id
        self.winfspCancelledByUser = False
        self.winfspCancelEvent = threading.Event()
        self.winfspDialog = DownloadProgressDialog(self)
        self.winfspDialog.setWindowTitle("下载 WinFsp")
        self.winfspDialog.label.setText("正在下载 WinFsp（16线程）...")

        self.winfspThread = QtCore.QThread(self)
        self.winfspWorker = WinFspDownloadWorker(self.winfspCancelEvent)
        self.winfspWorker.moveToThread(self.winfspThread)

        self.winfspThread.started.connect(self.winfspWorker.run)
        self.winfspWorker.progress_changed.connect(self.winfspDialog.set_progress)
        self.winfspWorker.finished.connect(self._onWinFspDownloadSuccess)
        self.winfspWorker.failed.connect(self._onWinFspDownloadFailed)
        self.winfspWorker.cancelled.connect(self._onWinFspDownloadCancelled)

        self.winfspWorker.finished.connect(self.winfspThread.quit)
        self.winfspWorker.failed.connect(self.winfspThread.quit)
        self.winfspWorker.cancelled.connect(self.winfspThread.quit)
        self.winfspWorker.finished.connect(self.winfspWorker.deleteLater)
        self.winfspWorker.failed.connect(self.winfspWorker.deleteLater)
        self.winfspWorker.cancelled.connect(self.winfspWorker.deleteLater)
        self.winfspThread.finished.connect(self._cleanupWinFspTask)
        self.winfspThread.finished.connect(self.winfspThread.deleteLater)

        self.winfspDialog.cancel_requested.connect(self._cancelWinFspDownload)
        self.winfspThread.start()
        self.winfspDialog.show()

    def _cancelWinFspDownload(self):
        self.winfspCancelledByUser = True
        if self.winfspCancelEvent is not None:
            self.winfspCancelEvent.set()
        if self.winfspDialog is not None:
            self.winfspDialog.set_cancelling()
        self.statusBar().showMessage("已请求取消 WinFsp 下载。", 4000)

    def _onWinFspDownloadSuccess(self):
        if self.winfspCancelledByUser:
            return
        if self.winfspDialog is not None:
            self.winfspDialog.close()
        QMessageBox.information(self, "完成", "WinFsp 安装完成，正在重试启动挂载。")
        try:
            self.protocol_service.start_mount(self.winfspTargetMountId)
            self.statusBar().showMessage("协议挂载已启动。", 3000)
        except Exception as err:
            QMessageBox.critical(self, "启动失败", str(err))
        self.refreshProtocolMountTab()

    def _onWinFspDownloadFailed(self, err_text):
        if self.winfspCancelledByUser:
            return
        if self.winfspDialog is not None:
            self.winfspDialog.close()
        QMessageBox.critical(self, "WinFsp 下载失败", err_text)

    def _onWinFspDownloadCancelled(self):
        if self.winfspDialog is not None:
            self.winfspDialog.close()
        self.statusBar().showMessage("WinFsp 下载已取消。", 4000)

    def _cleanupWinFspTask(self):
        self.winfspThread = None
        self.winfspWorker = None
        self.winfspCancelEvent = None
        self.winfspDialog = None
    
    def closeEvent(self, event):

        # print("main ui close")

        # self.setWindowFlags(QtCore.Qt.SplashScreen | QtCore.Qt.FramelessWindowHint)
        # event.ignore()
        event.accept()

