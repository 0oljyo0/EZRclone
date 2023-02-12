import sys
from PyQt5.QtWidgets import (
    QMainWindow, QAction, qApp, QApplication, 
    QHBoxLayout,QVBoxLayout,QLabel,QPushButton,
    QWidget,QTabWidget,QListWidget,QSpacerItem,QSizePolicy,QFileDialog,QLineEdit,QFormLayout,QCheckBox,
    QListWidgetItem, QComboBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from utils.setting import SystemSettingManger
import os
from utils.autorun import check
from utils.path import appdata_path
# coding=utf-8
import configparser
import os

class CreateNewMountWidget(QWidget):
    def __init__(self, closeCallBack):
        super().__init__()
        # self.setWindowTitle("我是子窗口啊")
        # self.rclonePath = ''
        self.settingManger = SystemSettingManger()

        self.closeCallBack = closeCallBack

        self.initAllWindow()

    def initAllWindow(self):    
        self.resize(640,320)

        self.initWindow()

        self.setWindowTitle('New Mount')
    
    def initWindow(self):
        mainLayerout = QVBoxLayout()

        remoteNameLayerout = QHBoxLayout()
        deviceNameLayerout = QHBoxLayout()
        remotePathLayerout = QHBoxLayout()
        LocalPathLayerout = QHBoxLayout()
        buttonLayerout = QHBoxLayout()


        
            
        
            
        remoteNameLable = QLabel("Remote Name")
        # self.remoteNameInput = QLineEdit()
        self.remoteNameComboBox = QComboBox()
        rclone_config_file = appdata_path()+"/rclone/rclone.conf"
        rclone_conf = configparser.ConfigParser()
        filename = rclone_conf.read(rclone_config_file)

        for remotesListWidgetItem in rclone_conf.sections():
            print(remotesListWidgetItem)
            self.remoteNameComboBox.addItem(remotesListWidgetItem)
            
        remoteNameLayerout.addWidget(remoteNameLable)
        remoteNameLayerout.addWidget(self.remoteNameComboBox)

        deviceNameLable = QLabel("Device Name")
        self.deviceNameInput = QLineEdit()
        deviceNameLayerout.addWidget(deviceNameLable)
        deviceNameLayerout.addWidget(self.deviceNameInput)

        remotePathLable = QLabel("Remote Path")
        self.remotePathInput = QLineEdit()
        remotePathLayerout.addWidget(remotePathLable)
        remotePathLayerout.addWidget(self.remotePathInput)

        
        LocalPathLable = QLabel("Local Path")
        self.LocalPathInput = QLineEdit()
        LocalPathLayerout.addWidget(LocalPathLable)
        LocalPathLayerout.addWidget(self.LocalPathInput)

        btnFindRclone = QPushButton("保存")
        btnFindRclone.clicked.connect(self.saveEvent)
        buttonLayerout.addWidget(btnFindRclone)



        mainLayerout.addLayout(remoteNameLayerout)
        mainLayerout.addLayout(deviceNameLayerout)
        mainLayerout.addLayout(remotePathLayerout)
        mainLayerout.addLayout(LocalPathLayerout)
        mainLayerout.addLayout(buttonLayerout)
        self.setLayout(mainLayerout)
    
    def saveEvent(self):
        remoteName = self.remoteNameComboBox.currentText()
        remotePath = self.remotePathInput.text()
        localPath = self.LocalPathInput.text()
        deviceName = self.deviceNameInput.text()


        self.settingManger.load()

        self.settingManger.setting_dict['AutoMounts'].append({
            'name': remoteName,
            'RemoteAbsolutePath':remotePath,
            'LocalDeviceId':localPath,
            'DeviceName':deviceName
        })

        self.settingManger.save()
        # print(remoteName)
        # print(remotePath)
        # print(localPath)
        self.closeCallBack()

        self.close()
