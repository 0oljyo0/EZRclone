import os
import shutil
import threading
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor

from app.core.path import appdata_path
from app.core.settings import SystemSettingManger

RCLONE_ZIP_URL = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
DOWNLOAD_THREADS = 16


class DownloadCancelledError(Exception):
    pass


def get_default_rclone_dir():
    base = appdata_path() or os.getcwd()
    target_dir = os.path.join(base, "qrclone", "bin")
    os.makedirs(target_dir, exist_ok=True)
    return target_dir


def get_default_rclone_path():
    return os.path.join(get_default_rclone_dir(), "rclone.exe")


def get_default_rclone_conf_path():
    base = appdata_path() or os.getcwd()
    return os.path.join(base, "rclone", "rclone.conf")


def detect_existing_rclone(setting=None):
    setting = setting or SystemSettingManger()
    rclone_path = setting.setting_dict.get("RclonePath", "")
    if rclone_path and os.path.exists(rclone_path):
        return rclone_path

    default_path = get_default_rclone_path()
    if os.path.exists(default_path):
        return default_path
    return ""


def ensure_rclone(download_if_missing=True):
    setting = SystemSettingManger()
    setting.load()

    existing_path = detect_existing_rclone(setting)
    if existing_path:
        if setting.setting_dict.get("RclonePath", "") != existing_path:
            setting.update("RclonePath", existing_path)
        return existing_path, False

    if not download_if_missing:
        return "", False

    return download_rclone(setting=setting), True


def download_rclone(setting=None, progress_cb=None, cancel_event=None):
    setting = setting or SystemSettingManger()
    target_path = get_default_rclone_path()
    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)

    zip_path = os.path.join(target_dir, "rclone-current-windows-amd64.zip")
    extract_dir = os.path.join(target_dir, "_extract_tmp")

    try:
        _download_file(RCLONE_ZIP_URL, zip_path, progress_cb=progress_cb, cancel_event=cancel_event)

        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)
        os.makedirs(extract_dir, exist_ok=True)
        _check_cancel(cancel_event)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            members = zip_ref.namelist()
            exe_member = next((item for item in members if item.lower().endswith("rclone.exe")), "")
            if not exe_member:
                raise FileNotFoundError("Zip 包内未找到 rclone.exe")
            zip_ref.extract(exe_member, extract_dir)
            extracted_path = os.path.join(extract_dir, exe_member)
            _check_cancel(cancel_event)
            shutil.copy2(extracted_path, target_path)
    finally:
        _safe_remove_file(zip_path)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)

    setting.update("RclonePath", target_path)
    return target_path


def _download_file(url, output_path, progress_cb=None, cancel_event=None):
    _check_cancel(cancel_event)
    req = urllib.request.Request(url, headers={"User-Agent": "EZRclone/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        total_size = response.headers.get("Content-Length")
        accept_ranges = response.headers.get("Accept-Ranges", "")
        total_size = int(total_size) if total_size else 0

    if total_size > 0 and "bytes" in accept_ranges.lower():
        _download_file_multi_thread(url, output_path, total_size, progress_cb, cancel_event)
    else:
        _download_file_single_thread(url, output_path, progress_cb, cancel_event)


def _download_file_single_thread(url, output_path, progress_cb=None, cancel_event=None):
    req = urllib.request.Request(url, headers={"User-Agent": "EZRclone/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response, open(output_path, "wb") as out_file:
        total_size = response.headers.get("Content-Length")
        total_size = int(total_size) if total_size else 0
        downloaded = 0
        chunk_size = 64 * 1024

        while True:
            _check_cancel(cancel_event)
            chunk = response.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if progress_cb:
                progress_cb(downloaded, total_size)


def _download_file_multi_thread(url, output_path, total_size, progress_cb=None, cancel_event=None):
    part_paths = []
    part_size = total_size // DOWNLOAD_THREADS
    progress_lock = threading.Lock()
    downloaded_total = {"value": 0}

    def _report(add_bytes):
        if not progress_cb:
            return
        with progress_lock:
            downloaded_total["value"] += add_bytes
            progress_cb(downloaded_total["value"], total_size)

    def _download_part(index, start, end):
        _check_cancel(cancel_event)
        headers = {
            "User-Agent": "EZRclone/1.0",
            "Range": "bytes={}-{}".format(start, end),
        }
        req = urllib.request.Request(url, headers=headers)
        part_path = "{}.part{}".format(output_path, index)
        part_paths.append(part_path)

        with urllib.request.urlopen(req, timeout=30) as response, open(part_path, "wb") as part_file:
            while True:
                _check_cancel(cancel_event)
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                part_file.write(chunk)
                _report(len(chunk))

    ranges = []
    for idx in range(DOWNLOAD_THREADS):
        start = idx * part_size
        if idx == DOWNLOAD_THREADS - 1:
            end = total_size - 1
        else:
            end = (start + part_size) - 1
        ranges.append((idx, start, end))

    try:
        with ThreadPoolExecutor(max_workers=DOWNLOAD_THREADS) as pool:
            futures = [pool.submit(_download_part, idx, start, end) for idx, start, end in ranges]
            for future in futures:
                future.result()

        _check_cancel(cancel_event)
        with open(output_path, "wb") as final_file:
            for idx in range(DOWNLOAD_THREADS):
                _check_cancel(cancel_event)
                part_path = "{}.part{}".format(output_path, idx)
                with open(part_path, "rb") as part_file:
                    shutil.copyfileobj(part_file, final_file)
    finally:
        for idx in range(DOWNLOAD_THREADS):
            _safe_remove_file("{}.part{}".format(output_path, idx))


def _safe_remove_file(path):
    if not os.path.exists(path):
        return
    try:
        os.remove(path)
    except OSError:
        pass


def _check_cancel(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise DownloadCancelledError("用户取消下载")
