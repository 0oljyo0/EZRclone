import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QMainWindow, QAction, qApp, QApplication, 
    QHBoxLayout,QVBoxLayout,QLabel,QPushButton,
    QWidget,QTabWidget,QListWidget,QSpacerItem,QSizePolicy,QFileDialog,QLineEdit,QFormLayout,QCheckBox,
    QListWidgetItem, QMessageBox, QTableWidget
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

from winds.settingWindow import SettingWidget
from winds.createNewMountWindow import CreateNewMountWidget

import threading

import os
import subprocess

from PyQt5.QtWidgets import QFrame

# 导入 QHeaderView
from PyQt5.QtWidgets import QHeaderView

class MainUI(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        
        self.setting = SystemSettingManger()
        self.setting.load()
        self.tasks = []

        # self.setWindowFlags(QtCore.Qt.SplashScreen | QtCore.Qt.FramelessWindowHint)
        
        self.initAllWindow()

        print(self.setting.setting_dict)

        self.mountAll()
        
        


    
    def mountAll(self):
        self.setting.load()
        for mountInfo in self.setting.setting_dict['AutoMounts']:
            print(mountInfo)
            task = threading.Thread(target=self.mountSingle, args=(mountInfo,))
            task.setDaemon(True)
            task.start()
            self.tasks.append(task)

    def mountSingle(self, mountInfo):
        print("task",mountInfo)
        cmd = self.setting.setting_dict['RclonePath']+" "+"mount"+" "+mountInfo['name']+":"+mountInfo['RemoteAbsolutePath']+" "+mountInfo['LocalDeviceId']+" "+"--volname"+" "+mountInfo['DeviceName']
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
        # mountTab = self.buildMountsTab()
        newMountTab = self.buildNewMountsTab()
        # cccTab = QWidget()

        tabWidget = QTabWidget()
        tabWidget.addTab(remotesTab, "Remotes")
        # tabWidget.addTab(mountTab, "Mounts")
        tabWidget.addTab(newMountTab, "Mounts")
        # tabWidget.addTab(cccTab, "ccc")
        self.setCentralWidget(tabWidget)

    def buildNewMountsTab(self):
        mountsTab = QWidget()
        mountsTabMainLayerout = QVBoxLayout()
        btnLayerout = QHBoxLayout()
        
        
        self.newMountTab = QTableWidget()
        self.newMountTab.setColumnCount(4)
        self.newMountTab.setHorizontalHeaderLabels(['DeviceName','RemoteName','RemoteAbsolutePath','LocalDeviceId'])
        
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
        # 表格自适应伸缩
        self.newMountTab.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.refreshNewMountsTab()
        
        
        mountsTabMainLayerout.addWidget(self.newMountTab)
        
        btn_config = QPushButton("New Mount")
        btn_config.clicked.connect(self.createNewMountEvent)
        # btn_mount= QPushButton("Delet Mount")
        spacerItem1 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacerItem2 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_delet = QPushButton("Delet Mount")
        btn_delet.clicked.connect(self.deletNewMountEvent)
        
        btn_remount = QPushButton("Remount All")
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
            print("先选择一个mount")
            return
        
        self.SystemSettingManger = SystemSettingManger()
        self.SystemSettingManger.load()
        del self.SystemSettingManger.setting_dict['AutoMounts'][index]
        self.SystemSettingManger.save()
        self.refreshNewMountsTab()
        
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

        btn_config = QPushButton("New Mount")
        btn_config.clicked.connect(self.createNewMountEvent)
        # btn_mount= QPushButton("Delet Mount")
        spacerItem1 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacerItem2 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_delet = QPushButton("Delet Mount")
        btn_delet.clicked.connect(self.deletMountEvent)
        
        btn_remount = QPushButton("Remount All")
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
        cmd = 'taskkill /F /IM '+self.setting.setting_dict['RclonePath'].split("/")[-1]
        res = subprocess.run(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(res.stdout.decode('gbk'))
        self.mountAll()

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
        self.settingWindow = SettingWidget()#SystemSettingManger()
        self.settingWindow.setWindowModality(Qt.ApplicationModal)
        self.settingWindow.show()

    def cleanSetting(self):
        # print(appdata_path()+"\qrclone\setting.json")
        os.system("del "+appdata_path()+"\qrclone\setting.json")
    
    def closeEvent(self, event):

        # print("main ui close")

        # self.setWindowFlags(QtCore.Qt.SplashScreen | QtCore.Qt.FramelessWindowHint)
        # event.ignore()
        event.accept()

