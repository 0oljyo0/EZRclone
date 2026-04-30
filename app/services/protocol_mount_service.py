import configparser
import os
import subprocess
from uuid import uuid4

from app.core.settings import SystemSettingManger
from app.services.rclone_installer import get_default_rclone_conf_path, get_default_rclone_path
from app.services.winfsp_installer import is_winfsp_installed


class ProtocolMountService:
    def __init__(self):
        self.setting = SystemSettingManger()
        self.processes = {}

    def list_mounts(self):
        self.setting.load()
        return self.setting.setting_dict.get("ProtocolMounts", [])

    def add_mount(self, mount_data):
        self.setting.load()
        mounts = self.setting.setting_dict.get("ProtocolMounts", [])
        mount_data["id"] = mount_data.get("id") or str(uuid4())
        mount_data["status"] = "未启动"
        mounts.append(mount_data)
        self.setting.setting_dict["ProtocolMounts"] = mounts
        self.setting.save()
        return mount_data

    def delete_mount(self, mount_id):
        self.stop_mount(mount_id)
        self.setting.load()
        mounts = self.setting.setting_dict.get("ProtocolMounts", [])
        target = None
        new_mounts = []
        for item in mounts:
            if item.get("id") == mount_id:
                target = item
                continue
            new_mounts.append(item)
        self.setting.setting_dict["ProtocolMounts"] = new_mounts
        self.setting.save()
        if target:
            self._remove_remote(target)

    def start_mount(self, mount_id):
        mount = self._find_mount(mount_id)
        if not mount:
            raise ValueError("挂载配置不存在")
        if mount_id in self.processes and self.processes[mount_id].poll() is None:
            return

        self._ensure_remote(mount)
        rclone_path = get_default_rclone_path()
        if not os.path.exists(rclone_path):
            raise FileNotFoundError("未找到 rclone.exe")
        if not is_winfsp_installed():
            raise RuntimeError("未检测到 WinFsp，请先安装 WinFsp。")

        cmd = '"{}" mount "{}:{}" "{}" --volname "{}"'.format(
            rclone_path,
            mount["remote_name"],
            mount.get("remote_path", ""),
            mount["local_path"],
            mount["name"],
        )
        process = subprocess.Popen(cmd, shell=True)
        self.processes[mount_id] = process
        self._update_mount_status(mount_id, "运行中")

    def stop_mount(self, mount_id):
        process = self.processes.get(mount_id)
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except Exception:
                process.kill()
        self.processes.pop(mount_id, None)
        self._update_mount_status(mount_id, "已停止")

    def start_autostart_mounts(self):
        for item in self.list_mounts():
            if item.get("auto_start"):
                try:
                    self.start_mount(item["id"])
                except Exception:
                    self._update_mount_status(item["id"], "启动失败")

    def _find_mount(self, mount_id):
        for item in self.list_mounts():
            if item.get("id") == mount_id:
                return item
        return None

    def _update_mount_status(self, mount_id, status):
        self.setting.load()
        changed = False
        for item in self.setting.setting_dict.get("ProtocolMounts", []):
            if item.get("id") == mount_id:
                item["status"] = status
                changed = True
                break
        if changed:
            self.setting.save()

    def _ensure_remote(self, mount):
        conf_path = get_default_rclone_conf_path()
        conf_dir = os.path.dirname(conf_path)
        os.makedirs(conf_dir, exist_ok=True)
        parser = configparser.ConfigParser()
        parser.read(conf_path, encoding="utf-8")

        section = mount["remote_name"]
        if not parser.has_section(section):
            parser.add_section(section)

        protocol = mount["protocol"]
        if protocol == "smb":
            parser.set(section, "type", "smb")
            parser.set(section, "host", mount["host"])
            parser.set(section, "user", mount["username"])
            parser.set(section, "pass", mount["password"])
        elif protocol == "sshfs":
            parser.set(section, "type", "sftp")
            parser.set(section, "host", mount["host"])
            parser.set(section, "user", mount["username"])
            parser.set(section, "pass", mount["password"])
            if mount.get("port"):
                parser.set(section, "port", str(mount["port"]))
        elif protocol == "webdav":
            parser.set(section, "type", "webdav")
            parser.set(section, "url", mount["host"])
            parser.set(section, "vendor", "other")
            parser.set(section, "user", mount["username"])
            parser.set(section, "pass", mount["password"])
        else:
            raise ValueError("不支持的协议")

        with open(conf_path, "w", encoding="utf-8") as fp:
            parser.write(fp)

    def _remove_remote(self, mount):
        conf_path = get_default_rclone_conf_path()
        if not os.path.exists(conf_path):
            return
        parser = configparser.ConfigParser()
        parser.read(conf_path, encoding="utf-8")
        section = mount.get("remote_name")
        if section and parser.has_section(section):
            parser.remove_section(section)
            with open(conf_path, "w", encoding="utf-8") as fp:
                parser.write(fp)
