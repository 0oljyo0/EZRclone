import json
from path import appdata_path
import os

class SettingManger():
    def __init__(self):
        self.setting_file_path = appdata_path()+"/qrclone/setting.json"
        if not os.path.exists(appdata_path()+"/qrclone"):
            os.makedirs(appdata_path()+"/qrclone")

        self.setting_dict = {
            "title": "QRcloneSetting",
            "RclonePath": "",
            "RcloneConfPath": "",
            "AutoStart": "False",
            "AutoMounts": [],
        }

        try:
            self.load()
        except FileNotFoundError:
            self.create()

    def save(self):
        with open(self.setting_file_path, "w") as setting_file:
            json.dump(self.setting_dict,setting_file)
    
    def load(self):
        with open(self.setting_file_path, "r") as setting_file:
            self.setting_dict = json.load(setting_file)
    
    def create(self):
        with open(self.setting_file_path, "w") as setting_file:
            json.dump(self.setting_dict,setting_file)

    def update(self,key,value):
        self.setting_dict[key] = value
        self.save()