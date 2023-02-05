import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QMainWindow, QAction, qApp, QApplication, 
    QHBoxLayout,QVBoxLayout,QLabel,QPushButton,
    QWidget,QTabWidget,QListWidget,QSpacerItem,QSizePolicy,QFileDialog,QLineEdit,QFormLayout,QCheckBox,
    QListWidgetItem, QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5 import QtCore
from setting import SettingManger
import os
from autorun import check
from path import appdata_path
# coding=utf-8
import configparser
import os
import json

from winds.settingWindow import SettingWidget
from winds.createNewMountWindow import CreateNewMountWidget

import threading

import os
import subprocess

class BasicMenubar(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        
        self.setting = SettingManger()
        self.setting.load()
        self.tasks = []

        self.setWindowFlags(QtCore.Qt.SplashScreen | QtCore.Qt.FramelessWindowHint)
        
        self.initAllWindow()

        print(self.setting.setting_dict)

        self.mountAll()

        self.showMinimized()
    
    def mountAll(self):
        for mountInfo in self.setting.setting_dict['AutoMounts']:
            print(mountInfo)
            task = threading.Thread(target=self.mountSingle, args=(mountInfo,))
            task.setDaemon(True)
            task.start()
            self.tasks.append(task)

    def mountSingle(self, mountInfo):
        print("task",mountInfo)
        cmd = self.setting.setting_dict['RclonePath']+" "+"mount"+" "+mountInfo['name']+":"+mountInfo['RemoteAbsolutePath']+" "+mountInfo['LocalDeviceId']
        print(cmd)
        # os.system(cmd)
        res = subprocess.run(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    def initAllWindow(self):    
        self.resize(512,512)
        self.initMenuBar()
        self.initCentrolWindow()
        self.setWindowTitle('QRclone')    
        self.show()

    def initMenuBar(self):
        exitAction = QAction('&Exit', self)        
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        setAction = QAction('&Setting', self)        
        setAction.setShortcut('Ctrl+E')
        setAction.setStatusTip('Exit application')
        setAction.triggered.connect(self.settingEvent)

        cleanSetAction = QAction('&CleanSetting', self)        
        # cleanSetAction.setShortcut('Ctrl+E')
        cleanSetAction.setStatusTip('Exit application')
        cleanSetAction.triggered.connect(self.cleanSetting)


        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        fileMenu.addAction(setAction)
        fileMenu.addAction(cleanSetAction)

        setMenu = menubar.addMenu('&Help')

    def initCentrolWindow(self):
        remotesTab = self.buildRemotesTab()

        mountTab = self.buildMountsTab()
        cccTab = QWidget()

        tabWidget = QTabWidget()
        tabWidget.addTab(remotesTab, "Remotes")
        tabWidget.addTab(mountTab, "Mounts")
        tabWidget.addTab(cccTab, "ccc")
        self.setCentralWidget(tabWidget)

    def buildMountsTab(self):
        # baseWidget = QWidget()
        remotesTab = QWidget()
        remotesTabMainLayerout = QVBoxLayout()

        remotesTabBodyLayerout = QHBoxLayout()
        remotesTabButtonLayerout = QHBoxLayout()

        self.mountsListWidget = QListWidget()
        self.refreshMountsTab()

        btn_config = QPushButton("New Mount")
        btn_config.clicked.connect(self.createNewMountEvent)
        # btn_mount= QPushButton("Delet Mount")
        spacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_delet = QPushButton("Delet Mount")
        btn_delet.clicked.connect(self.deletMountEvent)
        remotesTabButtonLayerout.addWidget(btn_config)
        # remotesTabButtonLayerout.addWidget(btn_mount)
        remotesTabButtonLayerout.addItem(spacerItem)
        remotesTabButtonLayerout.addWidget(btn_delet)

        remotesTabMainLayerout.addWidget(self.mountsListWidget)
        remotesTabMainLayerout.addLayout(remotesTabButtonLayerout)

        remotesTab.setLayout(remotesTabMainLayerout)
        return remotesTab
    
    def deletMountEvent(self):
        # print(self.mountsListWidget.selectedItems())
        if len(self.mountsListWidget.selectedIndexes()) == 0:
            print("先选择一个mount")
            return
        print(self.mountsListWidget.selectedIndexes()[0].row())
        print("aaaaa")
        del_index = self.mountsListWidget.selectedIndexes()[0].row()

        self.settingManger = SettingManger()
        self.settingManger.load()
        del self.settingManger.setting_dict['AutoMounts'][del_index]
        self.settingManger.save()
        self.refreshMountsTab()
        # with open(appdata_path()+"/qrclone/setting.json") as qrclone_file:
        #     settings = json.load(qrclone_file)
        #     print(settings['AutoMounts'])
        #     print("settings")
        #     del settings['AutoMounts'][del_index]

    def createNewMountEvent(self):
        self.child_window = CreateNewMountWidget(self.refreshMountsTab)
        self.child_window.setWindowModality(Qt.ApplicationModal)
        self.child_window.show()

    def refreshMountsTab(self):
        with open(appdata_path()+"/qrclone/setting.json") as qrclone_file:
            settings = json.load(qrclone_file)
            print(settings['AutoMounts'])
            print("settings")

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

        text = QLabel("Remote Name:"+title['name'])
        remoteAbPathLable = QLabel("远程绝对路径："+title['RemoteAbsolutePath'])
        localDeviceIdLabel = QLabel("本地绝对路径："+title['LocalDeviceId'])

        mountItemMainLayerout.addWidget(text)
        mountItemMainLayerout.addWidget(remoteAbPathLable)
        mountItemMainLayerout.addWidget(localDeviceIdLabel)
        
        mountItem.setLayout(mountItemMainLayerout)
        return mountItem

    # def buildRemotesItem(self,title):
    #     print(title)
    #     mountItem = QWidget()
    #     # mountItemMainLayerout = QHBoxLayout()

    #     # text = QLabel(title)
    #     # remoteAbPathLable = QLabel("远程绝对路径：")
    #     # remoteAbPath = QLineEdit()
    #     # localDeviceIdLabel = QLabel("本地盘符：")
    #     # localDeviceId = QLineEdit()
    #     # autoMountCheckBox = QCheckBox("开启自动挂载")
    #     # autoMountCheckBox.stateChanged.connect(self.autoMountCheckBoxStateChangedEvent)
    #     # btn_config = QPushButton("Config")

    #     # mountItemMainLayerout.addWidget(text)
    #     # mountItemMainLayerout.addWidget(remoteAbPathLable)
    #     # mountItemMainLayerout.addWidget(remoteAbPath)
    #     # mountItemMainLayerout.addWidget(localDeviceIdLabel)
    #     # mountItemMainLayerout.addWidget(localDeviceId)
    #     # mountItemMainLayerout.addWidget(autoMountCheckBox)
    #     # mountItemMainLayerout.addWidget(btn_config)
        
    #     # mountItem.setLayout(mountItemMainLayerout)
    #     return mountItem

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

    def autoMountCheckBoxStateChangedEvent(self):
        # print("aaaa")
        pButton = self.sender() #取信号发射对象
        # print(pButton.parent().children())
        self.settingManger = SettingManger()
        self.settingManger.load()

        mate_info = {
            "name": pButton.parent().children()[1].text(),
            "RemoteAbsolutePath": pButton.parent().children()[3].text(),
            "LocalDeviceId": pButton.parent().children()[5].text(),
        }

        print(mate_info['RemoteAbsolutePath'].split(":")[-1])
        print(os.path.isdir(mate_info['RemoteAbsolutePath'].split(":")[-1]))

        self.settingManger.setting_dict["AutoMounts"].append(mate_info)
        print(self.settingManger.setting_dict["AutoMounts"])
        print(mate_info)
        new_mounts_list = list(self.deleteDuplicate(self.settingManger.setting_dict["AutoMounts"]))
        print(new_mounts_list)
        self.settingManger.update(
            "AutoMounts", 
            new_mounts_list
        )

    def buildRemotesTab(self):
        # # baseWidget = QWidget()
        # remotesTab = QWidget()
        # remotesTabMainLayerout = QVBoxLayout()

        # remotesTabBodyLayerout = QHBoxLayout()
        # remotesTabButtonLayerout = QHBoxLayout()

        # self.mountsListWidget = QListWidget()
        # self.refreshMountsTab()

        # btn_config = QPushButton("Config")
        # btn_mount= QPushButton("mount")
        # spacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # btn_ccc = QPushButton("ccc")
        # remotesTabButtonLayerout.addWidget(btn_config)
        # remotesTabButtonLayerout.addWidget(btn_mount)
        # remotesTabButtonLayerout.addItem(spacerItem)
        # remotesTabButtonLayerout.addWidget(btn_ccc)

        # remotesTabMainLayerout.addWidget(self.mountsListWidget)
        # remotesTabMainLayerout.addLayout(remotesTabButtonLayerout)

        # remotesTab.setLayout(remotesTabMainLayerout)
        # return remotesTab
        remotesTab = QWidget()
        remotesTabMainLayerout = QVBoxLayout()

        remotesTabBodyLayerout = QHBoxLayout()
        remotesTabButtonLayerout = QHBoxLayout()

        self.remotesListWidget = QListWidget()
        self.refreshRemotesTab()

        # btn_config = QPushButton("Config")
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refreshRemotesTab)
        spacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # btn_ccc = QPushButton("ccc")
        # remotesTabButtonLayerout.addWidget(btn_config)
        remotesTabButtonLayerout.addWidget(btn_refresh)
        remotesTabButtonLayerout.addItem(spacerItem)
        # remotesTabButtonLayerout.addWidget(btn_ccc)

        remotesTabMainLayerout.addWidget(self.remotesListWidget)
        remotesTabMainLayerout.addLayout(remotesTabButtonLayerout)

        remotesTab.setLayout(remotesTabMainLayerout)
        return remotesTab
    
    def refreshRemotesTab(self):
        rclone_config_file = appdata_path()+"/rclone/rclone.conf"
        rclone_conf = configparser.ConfigParser()
        filename = rclone_conf.read(rclone_config_file)

        self.remotesListWidget.clear()
        for remotesListWidgetItem in rclone_conf.sections():
            self.remotesListWidget.addItem(remotesListWidgetItem)


    def settingEvent(self):
        self.child_window = SettingWidget()
        self.child_window.setWindowModality(Qt.ApplicationModal)
        self.child_window.show()

    def cleanSetting(self):
        # print(appdata_path()+"\qrclone\setting.json")
        os.system("del "+appdata_path()+"\qrclone\setting.json")
    
    def closeEvent(self, event):
        result = QMessageBox.question(self, "标题", "确认退出吗？否则最小化到系统托盘", QMessageBox.Yes | QMessageBox.No)
        # print(result)
        # print(QMessageBox.Yes)
        # print(QMessageBox.No)
        if(result == QMessageBox.Yes):
            # self.setWindowFlags(QtCore.Qt.Window)
            self.setVisible(False)
            # os.system('taskkill /F /IM '+self.setting.setting_dict['RclonePath'].split("/")[-1])
            cmd = 'taskkill /F /IM '+self.setting.setting_dict['RclonePath'].split("/")[-1]
            res = subprocess.run(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            QtWidgets.qApp.quit()
            # event.accept()
        elif(result == QMessageBox.No):
            self.setWindowFlags(QtCore.Qt.SplashScreen | QtCore.Qt.FramelessWindowHint)
            event.ignore()
        else:
            event.ignore()
