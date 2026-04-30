import sys
from PyQt5.QtWidgets import (
    QMainWindow, QAction, qApp, QApplication, 
    QHBoxLayout,QVBoxLayout,QLabel,QPushButton,
    QWidget,QTabWidget,QListWidget,QSpacerItem,QSizePolicy,QFileDialog,QLineEdit,QFormLayout,QCheckBox,
    QListWidgetItem, QComboBox, QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from app.core.settings import SystemSettingManger
import os
from utils.autorun import check
from app.core.path import appdata_path
# coding=utf-8
import configparser
import os
from app.services.rclone_installer import get_default_rclone_conf_path

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
        self.applyStyle()

        self.setWindowTitle('新建挂载')

    def applyStyle(self):
        self.setStyleSheet("""
            QWidget { background-color: #f7f8fb; color: #222; }
            QPushButton { background-color: #2f6fed; color: white; border: none; border-radius: 6px; padding: 8px 12px; min-width: 84px; }
            QPushButton:hover { background-color: #245ad0; }
            QLineEdit, QComboBox { background-color: white; border: 1px solid #d8dde8; border-radius: 6px; padding: 6px 8px; }
        """)
    
    def initWindow(self):
        mainLayerout = QVBoxLayout()

        remoteNameLayerout = QHBoxLayout()
        deviceNameLayerout = QHBoxLayout()
        remotePathLayerout = QHBoxLayout()
        LocalPathLayerout = QHBoxLayout()
        buttonLayerout = QHBoxLayout()


        
            
        
            
        remoteNameLable = QLabel("远程名称")
        # self.remoteNameInput = QLineEdit()
        self.remoteNameComboBox = QComboBox()
        rclone_config_file = get_default_rclone_conf_path()
        rclone_conf = configparser.ConfigParser()
        filename = rclone_conf.read(rclone_config_file)

        for remotesListWidgetItem in rclone_conf.sections():
            print(remotesListWidgetItem)
            self.remoteNameComboBox.addItem(remotesListWidgetItem)
            
        remoteNameLayerout.addWidget(remoteNameLable)
        remoteNameLayerout.addWidget(self.remoteNameComboBox)

        deviceNameLable = QLabel("设备名称")
        self.deviceNameInput = QLineEdit()
        deviceNameLayerout.addWidget(deviceNameLable)
        deviceNameLayerout.addWidget(self.deviceNameInput)

        remotePathLable = QLabel("远程路径")
        self.remotePathInput = QLineEdit()
        remotePathLayerout.addWidget(remotePathLable)
        remotePathLayerout.addWidget(self.remotePathInput)

        
        LocalPathLable = QLabel("本地盘符")
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
        remotePath = self.remotePathInput.text().strip()
        localPath = self.LocalPathInput.text().strip()
        deviceName = self.deviceNameInput.text().strip()

        if not remoteName or not remotePath or not localPath or not deviceName:
            QMessageBox.warning(self, "提示", "请完整填写所有挂载参数。")
            return


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
        QMessageBox.information(self, "完成", "挂载项保存成功。")

        self.close()
