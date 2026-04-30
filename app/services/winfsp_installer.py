import os
import subprocess
import threading
import time
import urllib.request
from urllib.error import URLError
from concurrent.futures import ThreadPoolExecutor

WINFSP_MSI_URL = "https://github.com/winfsp/winfsp/releases/download/v2.1/winfsp-2.1.25156.msi"
DOWNLOAD_THREADS = 16


class DownloadCancelledError(Exception):
    pass


def is_winfsp_installed():
    candidates = [
        r"C:\Program Files (x86)\WinFsp\bin\winfsp-x64.dll",
        r"C:\Program Files\WinFsp\bin\winfsp-x64.dll",
    ]
    for path in candidates:
        if os.path.exists(path):
            return True
    return False


def ensure_winfsp(download_if_missing=True, progress_cb=None, cancel_event=None):
    if is_winfsp_installed():
        return True, False
    if not download_if_missing:
        return False, False
    download_winfsp(progress_cb=progress_cb, cancel_event=cancel_event)
    return is_winfsp_installed(), True


def download_winfsp(progress_cb=None, cancel_event=None):
    temp_dir = os.getenv("TEMP") or os.getcwd()
    msi_path = os.path.join(temp_dir, "winfsp-latest.msi")
    _download_file(WINFSP_MSI_URL, msi_path, progress_cb=progress_cb, cancel_event=cancel_event)
    _check_cancel(cancel_event)
    try:
        _install_winfsp(msi_path, cancel_event=cancel_event)
    finally:
        _safe_remove_file(msi_path)


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
    while True:
        try:
            with urllib.request.urlopen(req, timeout=2) as response, open(output_path, "wb") as out_file:
                total_size = response.headers.get("Content-Length")
                total_size = int(total_size) if total_size else 0
                downloaded = 0
                while True:
                    _check_cancel(cancel_event)
                    chunk = response.read(32 * 1024)
                    if not chunk:
                        return
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb:
                        progress_cb(downloaded, total_size)
        except (TimeoutError, URLError):
            _check_cancel(cancel_event)
            continue


def _download_file_multi_thread(url, output_path, total_size, progress_cb=None, cancel_event=None):
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
        headers = {"User-Agent": "EZRclone/1.0", "Range": "bytes={}-{}".format(start, end)}
        req = urllib.request.Request(url, headers=headers)
        part_path = "{}.part{}".format(output_path, index)
        while True:
            try:
                with urllib.request.urlopen(req, timeout=2) as response, open(part_path, "wb") as part_file:
                    while True:
                        _check_cancel(cancel_event)
                        chunk = response.read(32 * 1024)
                        if not chunk:
                            return
                        part_file.write(chunk)
                        _report(len(chunk))
            except (TimeoutError, URLError):
                _check_cancel(cancel_event)
                continue

    ranges = []
    for idx in range(DOWNLOAD_THREADS):
        start = idx * part_size
        end = total_size - 1 if idx == DOWNLOAD_THREADS - 1 else (start + part_size - 1)
        ranges.append((idx, start, end))

    pool = None
    try:
        pool = ThreadPoolExecutor(max_workers=DOWNLOAD_THREADS)
        futures = [pool.submit(_download_part, idx, start, end) for idx, start, end in ranges]
        while True:
            _check_cancel(cancel_event)
            if all(f.done() for f in futures):
                break
            time.sleep(0.05)
        for future in futures:
            future.result()
        _check_cancel(cancel_event)
        with open(output_path, "wb") as final_file:
            for idx in range(DOWNLOAD_THREADS):
                _check_cancel(cancel_event)
                part_path = "{}.part{}".format(output_path, idx)
                with open(part_path, "rb") as part_file:
                    final_file.write(part_file.read())
    except DownloadCancelledError:
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)
        for idx in range(DOWNLOAD_THREADS):
            _safe_remove_file("{}.part{}".format(output_path, idx))


def _safe_remove_file(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _check_cancel(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise DownloadCancelledError("用户取消下载")


def _install_winfsp(msi_path, cancel_event=None):
    cmd = 'msiexec /i "{}" /passive /norestart'.format(msi_path)
    process = subprocess.Popen(cmd, shell=True)
    while process.poll() is None:
        if cancel_event is not None and cancel_event.is_set():
            subprocess.run(
                "taskkill /PID {} /T /F".format(process.pid),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            raise DownloadCancelledError("用户取消下载")
        time.sleep(0.2)
    if process.returncode != 0:
        raise RuntimeError("WinFsp 安装失败，返回码：{}".format(process.returncode))
