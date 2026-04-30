import json
import os

from app.core.path import appdata_path


class SystemSettingManger:
    def __init__(self):
        self.setting_file_path = os.path.join(appdata_path(), "qrclone", "setting.json")
        os.makedirs(os.path.dirname(self.setting_file_path), exist_ok=True)

        self.setting_dict = {
            "title": "QRcloneSetting",
            "RclonePath": "",
            "RcloneConfPath": "",
            "AutoStart": "False",
            "AutoMounts": [],
            "ProtocolMounts": [],
        }

        try:
            self.load()
        except FileNotFoundError:
            self.create()

    def save(self):
        with open(self.setting_file_path, "w", encoding="utf-8") as setting_file:
            json.dump(self.setting_dict, setting_file, ensure_ascii=False)

    def load(self):
        with open(self.setting_file_path, "r", encoding="utf-8") as setting_file:
            self.setting_dict = json.load(setting_file)
        if "ProtocolMounts" not in self.setting_dict:
            self.setting_dict["ProtocolMounts"] = []
            self.save()

    def create(self):
        with open(self.setting_file_path, "w", encoding="utf-8") as setting_file:
            json.dump(self.setting_dict, setting_file, ensure_ascii=False)

    def update(self, key, value):
        self.setting_dict[key] = value
        self.save()
