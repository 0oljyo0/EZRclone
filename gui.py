import sys
from PyQt5.QtWidgets import (
    QMainWindow, QAction, qApp, QApplication, 
    QHBoxLayout,QVBoxLayout,QLabel,QPushButton,
    QWidget,QTabWidget,QListWidget,QSpacerItem,QSizePolicy,QFileDialog,QLineEdit,QFormLayout,QCheckBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from setting import SettingManger
import os
from autorun import check
class BasicMenubar(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        
        self.initMainWindow()

        self.setting = SettingManger()
    
    def initMenu(self):
        exitAction = QAction('&Exit', self)        
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        setAction = QAction('&Setting', self)        
        setAction.setShortcut('Ctrl+E')
        setAction.setStatusTip('Exit application')
        setAction.triggered.connect(self.settingEvent)


        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        fileMenu.addAction(setAction)

        setMenu = menubar.addMenu('&Help')

    def initCentrolWindow(self):
        remotesTab = self.buildRemotesTab()

        bbbTab = QWidget()
        cccTab = QWidget()

        tabWidget = QTabWidget()
        tabWidget.addTab(remotesTab, "Remotes")
        tabWidget.addTab(bbbTab, "bbb")
        tabWidget.addTab(cccTab, "ccc")
        self.setCentralWidget(tabWidget)

    def buildRemotesTab(self):
        remotesTab = QWidget()
        remotesTabMainLayerout = QVBoxLayout()

        remotesTabBodyLayerout = QHBoxLayout()
        remotesTabButtonLayerout = QHBoxLayout()

        remotesListWidget = QListWidget()
        remotesListWidget.addItem("remote1")
        remotesListWidget.addItem("remote2")
        remotesListWidget.addItem("remote3")

        btn_config = QPushButton("Config")
        btn_bbb= QPushButton("bbb")
        spacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_ccc = QPushButton("ccc")
        remotesTabButtonLayerout.addWidget(btn_config)
        remotesTabButtonLayerout.addWidget(btn_bbb)
        remotesTabButtonLayerout.addItem(spacerItem)
        remotesTabButtonLayerout.addWidget(btn_ccc)

        remotesTabMainLayerout.addWidget(remotesListWidget)
        remotesTabMainLayerout.addLayout(remotesTabButtonLayerout)

        remotesTab.setLayout(remotesTabMainLayerout)
        return remotesTab
    
    def initMainWindow(self):    
        self.resize(512,512)
        self.initMenu()
        self.initCentrolWindow()
        self.setWindowTitle('QRclone')    
        self.show()
    
    # def showSettingWindow(self):
    #     self.child_window = SettingWidget()
    #     self.child_window.setWindowModality(Qt.ApplicationModal)
    #     self.child_window.show()
    
    def settingEvent(self):
        self.child_window = SettingWidget()
        self.child_window.setWindowModality(Qt.ApplicationModal)
        self.child_window.show()

        
class SettingWidget(QWidget):
    def __init__(self):
        super().__init__()
        # self.setWindowTitle("我是子窗口啊")
        self.initMainWindow()
        self.rclonePath = ''
        self.settingManger = SettingManger()

    def initMainWindow(self):    
        self.resize(640,320)

        self.initSettingWindow()

        self.setWindowTitle('Setting')
    
    def initSettingWindow(self):
        settingMainLayerout = QVBoxLayout()

        btnFindRclone = QPushButton("浏览")
        settingFindRcloneLable = QLabel("Rclone.exe 路径")
        self.settingFindRcloneLineEdit = QLineEdit()
        self.settingFindRcloneLineEdit.setReadOnly(True)
        settingFindRcloneLayerout = QHBoxLayout()
        btnFindRclone.clicked.connect(self.getRclonePath)
        settingFindRcloneLayerout.addWidget(settingFindRcloneLable)
        settingFindRcloneLayerout.addWidget(self.settingFindRcloneLineEdit)
        settingFindRcloneLayerout.addWidget(btnFindRclone)


        btnRcloneConf = QPushButton("浏览")
        settingRcloneConfLable = QLabel("Rclone.conf 路径")
        self.settingRcloneConfLineEdit = QLineEdit()
        self.settingRcloneConfLineEdit.setReadOnly(True)
        settingRcloneConfLayerout = QHBoxLayout()
        btnRcloneConf.clicked.connect(self.getRcloneConfPath)
        settingRcloneConfLayerout.addWidget(settingRcloneConfLable)
        settingRcloneConfLayerout.addWidget(self.settingRcloneConfLineEdit)
        settingRcloneConfLayerout.addWidget(btnRcloneConf)

        self.autorunCheckBox = QCheckBox("开机启动")
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
            check(1)
        else:
            check(0)
