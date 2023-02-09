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
from utils.setting import SystemSettingManger
import os
from utils.autorun import check
from utils.path import appdata_path
# coding=utf-8
import configparser
import os
import json

from winds.settingWindow import SystemSettingManger
from winds.createNewMountWindow import CreateNewMountWidget

import threading

import os
import subprocess

class MainUI(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        
        self.setting = SystemSettingManger()
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
        self.setWindowTitle('EZRclone')    
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
        # cccTab = QWidget()

        tabWidget = QTabWidget()
        tabWidget.addTab(remotesTab, "Remotes")
        tabWidget.addTab(mountTab, "Mounts")
        # tabWidget.addTab(cccTab, "ccc")
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
        # print(self.mountsListWidget.selectedIndexes()[0].row())
        # print("aaaaa")
        del_index = self.mountsListWidget.selectedIndexes()[0].row()

        self.SystemSettingManger = SystemSettingManger()
        self.SystemSettingManger.load()
        del self.SystemSettingManger.setting_dict['AutoMounts'][del_index]
        self.SystemSettingManger.save()
        self.refreshMountsTab()

    def createNewMountEvent(self):
        self.child_window = CreateNewMountWidget(self.refreshMountsTab)
        self.child_window.setWindowModality(Qt.ApplicationModal)
        self.child_window.show()

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

        text = QLabel("Remote Name:"+title['name'])
        remoteAbPathLable = QLabel("远程绝对路径："+title['RemoteAbsolutePath'])
        localDeviceIdLabel = QLabel("本地绝对路径："+title['LocalDeviceId'])

        mountItemMainLayerout.addWidget(text)
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
        btn_refresh = QPushButton("Refresh")
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
        rclone_config_file = appdata_path()+"/rclone/rclone.conf"
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
        rclone_config_file = appdata_path()+"/rclone/rclone.conf"
        rclone_conf = configparser.ConfigParser()
        filename = rclone_conf.read(rclone_config_file)

        self.remotesListWidget.clear()
        for remotesListWidgetItem in rclone_conf.sections():
            # print(remotesListWidgetItem)
            self.remotesListWidget.addItem(remotesListWidgetItem)


    def settingEvent(self):
        self.child_window = SystemSettingManger()
        self.child_window.setWindowModality(Qt.ApplicationModal)
        self.child_window.show()

    def cleanSetting(self):
        # print(appdata_path()+"\qrclone\setting.json")
        os.system("del "+appdata_path()+"\qrclone\setting.json")
    
    def closeEvent(self, event):

        self.setWindowFlags(QtCore.Qt.SplashScreen | QtCore.Qt.FramelessWindowHint)
        event.ignore()

