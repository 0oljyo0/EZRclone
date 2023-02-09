import sys
from PyQt5.QtWidgets import (
    QMainWindow, QAction, qApp, QApplication, 
    QHBoxLayout,QVBoxLayout,QLabel,QPushButton,
    QWidget,QTabWidget,QListWidget,QSpacerItem,QSizePolicy,QFileDialog,QLineEdit,QFormLayout,QCheckBox,
    QListWidgetItem
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

class SettingWidget(QWidget):
    def __init__(self):
        super().__init__()
        # self.setWindowTitle("我是子窗口啊")
        self.rclonePath = ''
        self.SystemSettingManger = SystemSettingManger()

        self.initAllWindow()

    def initAllWindow(self):    
        self.resize(640,320)

        self.initSettingWindow()

        self.setWindowTitle('Setting')
    
    def initSettingWindow(self):
        settingMainLayerout = QVBoxLayout()

        btnFindRclone = QPushButton("浏览")
        settingFindRcloneLable = QLabel("Rclone.exe 路径")
        self.settingFindRcloneLineEdit = QLineEdit(self.SystemSettingManger.setting_dict['RclonePath'])
        self.settingFindRcloneLineEdit.setReadOnly(True)
        settingFindRcloneLayerout = QHBoxLayout()
        btnFindRclone.clicked.connect(self.getRclonePath)
        settingFindRcloneLayerout.addWidget(settingFindRcloneLable)
        settingFindRcloneLayerout.addWidget(self.settingFindRcloneLineEdit)
        settingFindRcloneLayerout.addWidget(btnFindRclone)


        btnRcloneConf = QPushButton("浏览")
        settingRcloneConfLable = QLabel("Rclone.conf 路径")
        self.settingRcloneConfLineEdit = QLineEdit(self.SystemSettingManger.setting_dict['RcloneConfPath'])
        self.settingRcloneConfLineEdit.setReadOnly(True)
        settingRcloneConfLayerout = QHBoxLayout()
        btnRcloneConf.clicked.connect(self.getRcloneConfPath)
        settingRcloneConfLayerout.addWidget(settingRcloneConfLable)
        settingRcloneConfLayerout.addWidget(self.settingRcloneConfLineEdit)
        settingRcloneConfLayerout.addWidget(btnRcloneConf)

        self.autorunCheckBox = QCheckBox("开机启动")
        if self.SystemSettingManger.setting_dict['AutoStart'] == "True":
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
        self.SystemSettingManger.update('RclonePath', self.rclonePath)

    def getRcloneConfPath(self):
        self.rcloneConfPath, _ = QFileDialog.getOpenFileName(self, "打开文件", '.', '*.conf')
        self.settingRcloneConfLineEdit.setText(self.rcloneConfPath)
        self.SystemSettingManger.update('RcloneConfPath', self.rcloneConfPath)
    
    def autorunEvent(self):
        if self.autorunCheckBox.isChecked():
            self.SystemSettingManger.update('AutoStart', "True")
            check(1)
        else:
            self.SystemSettingManger.update('AutoStart', "False")
            check(0)



# class ChangeSettingWidget(QWidget):
#     def __init__(self, remoteName):
#         super().__init__()
#         # self.setWindowTitle("我是子窗口啊")
#         self.rclonePath = ''
#         self.SystemSettingManger = SystemSettingManger()
#         self.SystemSettingManger.load()

#         self.initAllWindow()

#     def initAllWindow(self):    
#         self.resize(640,320)

#         self.initSettingWindow()

#         self.setWindowTitle('Setting')
    
#     def initSettingWindow(self):
#         settingMainLayerout = QVBoxLayout()

#         btnFindRclone = QPushButton("浏览")
#         settingFindRcloneLable = QLabel("Rclone.exe 路径")
#         self.settingFindRcloneLineEdit = QLineEdit(self.SystemSettingManger.setting_dict['RclonePath'])
#         self.settingFindRcloneLineEdit.setReadOnly(True)
#         settingFindRcloneLayerout = QHBoxLayout()
#         btnFindRclone.clicked.connect(self.getRclonePath)
#         settingFindRcloneLayerout.addWidget(settingFindRcloneLable)
#         settingFindRcloneLayerout.addWidget(self.settingFindRcloneLineEdit)
#         settingFindRcloneLayerout.addWidget(btnFindRclone)


#         btnRcloneConf = QPushButton("浏览")
#         settingRcloneConfLable = QLabel("Rclone.conf 路径")
#         self.settingRcloneConfLineEdit = QLineEdit(self.SystemSettingManger.setting_dict['RcloneConfPath'])
#         self.settingRcloneConfLineEdit.setReadOnly(True)
#         settingRcloneConfLayerout = QHBoxLayout()
#         btnRcloneConf.clicked.connect(self.getRcloneConfPath)
#         settingRcloneConfLayerout.addWidget(settingRcloneConfLable)
#         settingRcloneConfLayerout.addWidget(self.settingRcloneConfLineEdit)
#         settingRcloneConfLayerout.addWidget(btnRcloneConf)

#         self.autorunCheckBox = QCheckBox("开机启动")
#         if self.SystemSettingManger.setting_dict['AutoStart'] == "True":
#             self.autorunCheckBox.setChecked(True)
#         else:
#             self.autorunCheckBox.setChecked(False)
#         self.autorunCheckBox.stateChanged.connect(self.autorunEvent)

#         settingMainLayerout.addLayout(settingFindRcloneLayerout)
#         settingMainLayerout.addLayout(settingRcloneConfLayerout)
#         settingMainLayerout.addWidget(self.autorunCheckBox)
#         self.setLayout(settingMainLayerout)
    
#     def getRclonePath(self):
#         self.rclonePath, _ = QFileDialog.getOpenFileName(self, "打开文件", '.', '*.exe')
#         self.settingFindRcloneLineEdit.setText(self.rclonePath)
#         self.SystemSettingManger.update('RclonePath', self.rclonePath)

#     def getRcloneConfPath(self):
#         self.rcloneConfPath, _ = QFileDialog.getOpenFileName(self, "打开文件", '.', '*.conf')
#         self.settingRcloneConfLineEdit.setText(self.rcloneConfPath)
#         self.SystemSettingManger.update('RcloneConfPath', self.rcloneConfPath)
    
#     def autorunEvent(self):
#         if self.autorunCheckBox.isChecked():
#             self.SystemSettingManger.update('AutoStart', "True")
#             check(1)
#         else:
#             self.SystemSettingManger.update('AutoStart', "False")
#             check(0)

#     def readInitSetting(self):
#         self.settingFindRcloneLineEdit.setText(self.SystemSettingManger.setting_dict['RclonePath'])
#         self.settingRcloneConfLineEdit.setText(self.SystemSettingManger.setting_dict['RcloneConfPath'])
#         # self.autorunCheckBox.setChecked(self.SystemSettingManger.setting_dict[''])
