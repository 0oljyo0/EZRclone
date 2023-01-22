import sys
from PyQt5.QtWidgets import (
    QMainWindow, QAction, qApp, QApplication, 
    QHBoxLayout,QVBoxLayout,QLabel,QPushButton,
    QWidget,QTabWidget,QListWidget,QSpacerItem,QSizePolicy,QFileDialog,QLineEdit,QFormLayout,QCheckBox,
    QListWidgetItem
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from setting import SettingManger
import os
from autorun import check
from path import appdata_path
# coding=utf-8
import configparser
import os




class BasicMenubar(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        
        self.initMainWindow()

        self.setting = SettingManger()

    def initMainWindow(self):    
        self.resize(512,512)
        self.initMenu()
        self.initCentrolWindow()
        self.setWindowTitle('QRclone')    
        self.show()

    def initMenu(self):
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

        btn_config = QPushButton("Config")
        btn_mount= QPushButton("mount")
        spacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_ccc = QPushButton("ccc")
        remotesTabButtonLayerout.addWidget(btn_config)
        remotesTabButtonLayerout.addWidget(btn_mount)
        remotesTabButtonLayerout.addItem(spacerItem)
        remotesTabButtonLayerout.addWidget(btn_ccc)

        remotesTabMainLayerout.addWidget(self.mountsListWidget)
        remotesTabMainLayerout.addLayout(remotesTabButtonLayerout)

        remotesTab.setLayout(remotesTabMainLayerout)
        return remotesTab

    def refreshMountsTab(self):
        rclone_config_file = appdata_path()+"/rclone/rclone.conf"
        rclone_conf = configparser.ConfigParser()
        filename = rclone_conf.read(rclone_config_file)

        self.mountsListWidget.clear()
        for remotesListWidgetItem in rclone_conf.sections():
            # self.remotesListWidget.addItem(remotesListWidgetItem)
            item = QListWidgetItem() # 创建QListWidgetItem对象
            item.setSizeHint(QSize(0, 50)) # 设置QListWidgetItem大小
            widget = self.buileMountItem(remotesListWidgetItem)#QPushButton("bbbbbbb")
            self.mountsListWidget.addItem(item) # 添加item
            self.mountsListWidget.setItemWidget(item, widget) # 为item设置widget


    def buileMountItem(self,title):
        mountItem = QWidget()
        mountItemMainLayerout = QHBoxLayout()

        text = QLabel(title)
        autoMountCheckBox = QCheckBox("自动挂载")
        btn_config = QPushButton("Config")

        mountItemMainLayerout.addWidget(text)
        mountItemMainLayerout.addWidget(autoMountCheckBox)
        mountItemMainLayerout.addWidget(btn_config)
        
        mountItem.setLayout(mountItemMainLayerout)
        return mountItem


    def buildRemotesTab(self):
        remotesTab = QWidget()
        remotesTabMainLayerout = QVBoxLayout()

        remotesTabBodyLayerout = QHBoxLayout()
        remotesTabButtonLayerout = QHBoxLayout()

        self.remotesListWidget = QListWidget()
        self.refreshRemotesTab()

        btn_config = QPushButton("Config")
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refreshRemotesTab)
        spacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_ccc = QPushButton("ccc")
        remotesTabButtonLayerout.addWidget(btn_config)
        remotesTabButtonLayerout.addWidget(btn_refresh)
        remotesTabButtonLayerout.addItem(spacerItem)
        remotesTabButtonLayerout.addWidget(btn_ccc)

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
        
class SettingWidget(QWidget):
    def __init__(self):
        super().__init__()
        # self.setWindowTitle("我是子窗口啊")
        self.rclonePath = ''
        self.settingManger = SettingManger()

        self.initMainWindow()

    def initMainWindow(self):    
        self.resize(640,320)

        self.initSettingWindow()

        self.setWindowTitle('Setting')
    
    def initSettingWindow(self):
        settingMainLayerout = QVBoxLayout()

        btnFindRclone = QPushButton("浏览")
        settingFindRcloneLable = QLabel("Rclone.exe 路径")
        self.settingFindRcloneLineEdit = QLineEdit(self.settingManger.setting_dict['RclonePath'])
        self.settingFindRcloneLineEdit.setReadOnly(True)
        settingFindRcloneLayerout = QHBoxLayout()
        btnFindRclone.clicked.connect(self.getRclonePath)
        settingFindRcloneLayerout.addWidget(settingFindRcloneLable)
        settingFindRcloneLayerout.addWidget(self.settingFindRcloneLineEdit)
        settingFindRcloneLayerout.addWidget(btnFindRclone)


        btnRcloneConf = QPushButton("浏览")
        settingRcloneConfLable = QLabel("Rclone.conf 路径")
        self.settingRcloneConfLineEdit = QLineEdit(self.settingManger.setting_dict['RcloneConfPath'])
        self.settingRcloneConfLineEdit.setReadOnly(True)
        settingRcloneConfLayerout = QHBoxLayout()
        btnRcloneConf.clicked.connect(self.getRcloneConfPath)
        settingRcloneConfLayerout.addWidget(settingRcloneConfLable)
        settingRcloneConfLayerout.addWidget(self.settingRcloneConfLineEdit)
        settingRcloneConfLayerout.addWidget(btnRcloneConf)

        self.autorunCheckBox = QCheckBox("开机启动")
        if self.settingManger.setting_dict['AutoStart'] == "True":
            self.autorunCheckBox.setChecked(True)
        else:
            self.autorunCheckBox.setChecked(False)
        self.autorunCheckBox.stateChanged.connect(self.autorunEvent)

        settingMainLayerout.addLayout(settingFindRcloneLayerout)
        settingMainLayerout.addLayout(settingRcloneConfLayerout)
        settingMainLayerout.addWidget(self.autorunCheckBox)
        self.setLayout(settingMainLayerout)
    
    def getRclonePath(self):
        self.rclonePath, _ = QFileDialog.getOpenFileName(self, "打开文件", '.', '*.exe')
        self.settingFindRcloneLineEdit.setText(self.rclonePath)
        self.settingManger.update('RclonePath', self.rclonePath)

    def getRcloneConfPath(self):
        self.rcloneConfPath, _ = QFileDialog.getOpenFileName(self, "打开文件", '.', '*.conf')
        self.settingRcloneConfLineEdit.setText(self.rcloneConfPath)
        self.settingManger.update('RcloneConfPath', self.rcloneConfPath)
    
    def autorunEvent(self):
        if self.autorunCheckBox.isChecked():
            self.settingManger.update('AutoStart', "True")
            check(1)
        else:
            self.settingManger.update('AutoStart', "False")
            check(0)
