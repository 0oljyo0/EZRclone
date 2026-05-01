import configparser
import ctypes
import os
import subprocess
import time
from uuid import uuid4

from app.core.path import appdata_path
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
        mount_data["pid"] = 0
        mount_data["last_error"] = ""
        mount_data["log_file"] = ""
        mounts.append(mount_data)
        self.setting.setting_dict["ProtocolMounts"] = mounts
        self.setting.save()
        return mount_data

    def update_mount(self, mount_id, mount_data):
        self.stop_mount(mount_id)
        self.setting.load()
        mounts = self.setting.setting_dict.get("ProtocolMounts", [])
        old_mount = None
        for idx, item in enumerate(mounts):
            if item.get("id") != mount_id:
                continue
            old_mount = item
            updated = dict(item)
            updated.update(mount_data)
            updated["id"] = mount_id
            updated["status"] = "已停止"
            updated["pid"] = 0
            updated["last_error"] = ""
            mounts[idx] = updated
            self.setting.setting_dict["ProtocolMounts"] = mounts
            self.setting.save()
            if old_mount and old_mount.get("remote_name") != updated.get("remote_name"):
                self._remove_remote(old_mount)
            return updated
        raise ValueError("挂载配置不存在")

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
        if mount.get("pid"):
            self._kill_pid(mount.get("pid"))

        self._ensure_remote(mount)
        rclone_path = get_default_rclone_path()
        if not os.path.exists(rclone_path):
            raise FileNotFoundError("未找到 rclone.exe")
        if not is_winfsp_installed():
            raise RuntimeError("未检测到 WinFsp，请先安装 WinFsp。")

        conf_path = get_default_rclone_conf_path()
        log_file = self._build_mount_log_file(mount_id, mount.get("name", "mount"))
        extra_flags = []
        if mount.get("protocol") == "sshfs":
            extra_flags.append("--links")

        local_mountpoint = self._normalize_local_mountpoint(mount["local_path"])
        self._ensure_mountpoint_available(local_mountpoint)
        print("[ProtocolMountService] start mount: id={}, remote={}, target={}".format(
            mount_id,
            "{}:{}".format(mount["remote_name"], mount.get("remote_path", "")),
            local_mountpoint,
        ))
        cmd = [
            rclone_path,
            "mount",
            "{}:{}".format(mount["remote_name"], mount.get("remote_path", "")),
            local_mountpoint,
            "--volname",
            mount["name"],
            "--config",
            conf_path,
            "--log-file",
            log_file,
            "--log-level",
            "DEBUG",
        ] + extra_flags

        self._update_mount_runtime(mount_id, "启动中", 0, "", log_file)
        process = subprocess.Popen(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(5)
        if process.poll() is not None:
            _, stderr = process.communicate(timeout=1)
            log_tail = self._read_log_tail(log_file)
            err_text = (stderr or "").strip() or log_tail or "rclone 进程启动后立即退出"
            self._update_mount_runtime(mount_id, "启动失败", 0, err_text, log_file)
            raise RuntimeError("{}\n日志文件：{}".format(err_text, log_file))

        if not self._mountpoint_reachable(local_mountpoint):
            self._kill_pid(process.pid)
            self.processes.pop(mount_id, None)
            err_text = "挂载超时：{} 在 5 秒后仍未就绪".format(local_mountpoint)
            self._update_mount_runtime(mount_id, "启动失败", 0, err_text, log_file)
            raise RuntimeError("{}\n日志文件：{}".format(err_text, log_file))

        self.processes[mount_id] = process
        self._update_mount_runtime(mount_id, "已启动", process.pid, "", log_file)
        print("[ProtocolMountService] mount started: id={}, pid={}, log={}".format(mount_id, process.pid, log_file))

    def stop_mount(self, mount_id):
        process = self.processes.get(mount_id)
        mount = self._find_mount(mount_id)
        print("[ProtocolMountService] stop mount: id={}".format(mount_id))
        if process and process.poll() is None:
            self._kill_pid(process.pid)
        if mount and mount.get("pid"):
            self._kill_pid(mount.get("pid"))
        self.processes.pop(mount_id, None)
        self._update_mount_runtime(mount_id, "已停止", 0, "", mount.get("log_file", "") if mount else "")

    def stop_all_mounts(self):
        for item in self.list_mounts():
            mount_id = item.get("id")
            if mount_id:
                self.stop_mount(mount_id)

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
        self._update_mount_runtime(mount_id, status, None)

    def _update_mount_runtime(self, mount_id, status, pid, last_error=None, log_file=None):
        self.setting.load()
        changed = False
        for item in self.setting.setting_dict.get("ProtocolMounts", []):
            if item.get("id") == mount_id:
                item["status"] = status
                if pid is not None:
                    item["pid"] = pid
                if last_error is not None:
                    item["last_error"] = last_error
                if log_file is not None:
                    item["log_file"] = log_file
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
            parser.set(section, "pass", self._obscure_password(mount["password"]))
        elif protocol == "sshfs":
            parser.set(section, "type", "sftp")
            parser.set(section, "host", mount["host"])
            parser.set(section, "user", mount["username"])
            parser.set(section, "pass", self._obscure_password(mount["password"]))
            if mount.get("port"):
                parser.set(section, "port", str(mount["port"]))
        elif protocol == "webdav":
            parser.set(section, "type", "webdav")
            parser.set(section, "url", mount["host"])
            parser.set(section, "vendor", "other")
            parser.set(section, "user", mount["username"])
            parser.set(section, "pass", self._obscure_password(mount["password"]))
        elif protocol == "ftp":
            parser.set(section, "type", "ftp")
            parser.set(section, "host", mount["host"])
            parser.set(section, "user", mount["username"])
            parser.set(section, "pass", self._obscure_password(mount["password"]))
            if mount.get("port"):
                parser.set(section, "port", str(mount["port"]))
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

    def _obscure_password(self, password):
        if not password:
            return ""
        rclone_path = get_default_rclone_path()
        if not os.path.exists(rclone_path):
            raise FileNotFoundError("未找到 rclone.exe，无法加密协议密码")
        result = subprocess.run(
            [rclone_path, "obscure", password],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError("rclone 密码加密失败: {}".format(result.stderr.strip() or result.stdout.strip()))
        return result.stdout.strip()

    def _normalize_local_mountpoint(self, local_path):
        mountpoint = (local_path or "").strip()
        # Accept "P" from old configs and convert to Windows drive-letter mountpoint.
        if len(mountpoint) == 1 and mountpoint.isalpha():
            return "{}:".format(mountpoint.upper())
        return mountpoint

    def _kill_pid(self, pid):
        if not pid:
            return False
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                text=True,
                shell=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _mountpoint_reachable(self, mountpoint):
        path = (mountpoint or "").strip()
        if not path:
            return False
        if len(path) == 2 and path[1] == ":" and path[0].isalpha():
            path = path + "\\"
        return os.path.exists(path)

    def _ensure_mountpoint_available(self, mountpoint):
        path = (mountpoint or "").strip()
        if not path:
            raise ValueError("本地挂载点不能为空")

        # Drive letter mode: "U:" etc.
        if len(path) == 2 and path[1] == ":" and path[0].isalpha():
            drive_root = path.upper() + "\\"
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_root)
            # DRIVE_NO_ROOT_DIR(1) means the drive letter is free.
            if drive_type != 1:
                raise RuntimeError("盘符 {} 已存在，请重新指定盘符或路径".format(path.upper()))
            return

        # Directory mode: reject existing path to avoid "mountpoint path already exists".
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            raise RuntimeError("路径 {} 已存在，请重新指定盘符或路径".format(full_path))

    def _build_mount_log_file(self, mount_id, mount_name):
        base = appdata_path() or os.getcwd()
        log_dir = os.path.join(base, "qrclone", "logs")
        os.makedirs(log_dir, exist_ok=True)
        safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in (mount_name or "mount"))
        return os.path.join(log_dir, "{}_{}.log".format(safe_name, mount_id))

    def _read_log_tail(self, log_file, max_lines=20):
        if not log_file or not os.path.exists(log_file):
            return ""
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()
            return "".join(lines[-max_lines:]).strip()
        except Exception:
            return ""
