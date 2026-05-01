from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QGridLayout,
    QFrame,
)
from PyQt5.QtCore import Qt

from app.services.protocol_mount_service import ProtocolMountService


class ProtocolMountWindow(QWidget):
    def __init__(self, on_saved, mount_data=None):
        super().__init__()
        self.on_saved = on_saved
        self.mount_data = mount_data
        self.service = ProtocolMountService()
        self.init_ui()

    def init_ui(self):
        self.resize(680, 420)
        self.setWindowTitle("编辑协议挂载" if self.mount_data else "新建协议挂载")

        self.setStyleSheet(
            """
            QWidget { background-color: #f7f8fb; color: #1f2937; font-size: 13px; }
            QFrame#card { background: white; border: 1px solid #d9e2ef; border-radius: 10px; }
            QLabel#title { font-size: 17px; font-weight: 600; padding: 4px 2px; }
            QLineEdit, QComboBox {
                background: white;
                border: 1px solid #d0d9e5;
                border-radius: 6px;
                padding: 4px 8px;
                min-height: 24px;
            }
            QPushButton {
                background-color: #2f6fed;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                min-width: 96px;
            }
            QPushButton:hover { background-color: #245ad0; }
            QPushButton#secondary {
                background-color: #eef2f7;
                color: #1f2937;
            }
            QPushButton#secondary:hover { background-color: #e2e8f0; }
            """
        )

        layout = QVBoxLayout()
        title = QLabel("编辑协议挂载" if self.mount_data else "新建协议挂载")
        title.setObjectName("title")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(18, 16, 18, 16)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：开发机 root 目录")
        self._normalize_field(self.name_input)
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["smb", "sshfs", "ftp", "webdav"])
        self._normalize_field(self.protocol_combo)
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("例如：192.168.1.10 或 https://dav.example.com")
        self._normalize_field(self.host_input)
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("例如：22（可留空）")
        self._normalize_field(self.port_input)
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("例如：root")
        self._normalize_field(self.user_input)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入对应账号密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self._normalize_field(self.password_input)
        self.remote_path_input = QLineEdit()
        self.remote_path_input.setPlaceholderText("例如：/root 或 /data")
        self._normalize_field(self.remote_path_input)
        self.local_path_input = QLineEdit()
        self.local_path_input.setPlaceholderText("例如 P:（盘符）或 mount\\data（相对路径）或 D:\\mounts\\test（绝对路径）")
        self.local_path_input.setToolTip("带 : 视为盘符（如 P:）；不带 : 视为路径，默认按当前工作目录解析。")
        self._normalize_field(self.local_path_input)
        self.auto_start_check = QCheckBox("开机自动挂载")

        form = QGridLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)
        form.setColumnStretch(0, 0)
        form.setColumnStretch(1, 1)
        rows = [
            ("显示名称", self.name_input),
            ("协议", self.protocol_combo),
            ("主机/URL", self.host_input),
            ("端口（可选）", self.port_input),
            ("用户名", self.user_input),
            ("密码", self.password_input),
            ("远程路径", self.remote_path_input),
            ("本地挂载点", self.local_path_input),
        ]
        for idx, (text, widget) in enumerate(rows):
            form.addWidget(self._make_label(text), idx, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)
            form.addWidget(widget, idx, 1, alignment=Qt.AlignVCenter)
        card_layout.addLayout(form)
        card_layout.addWidget(self.auto_start_check)

        save_btn = QPushButton("更新" if self.mount_data else "保存")
        save_btn.clicked.connect(self.save_mount)
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.close)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        card_layout.addLayout(btn_row)

        card.setLayout(card_layout)
        layout.addWidget(card)

        self.setLayout(layout)
        self._load_mount_data()

    def _make_label(self, text):
        label = QLabel(text)
        label.setFixedWidth(96)
        label.setFixedHeight(28)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return label

    def _normalize_field(self, widget):
        widget.setFixedHeight(28)

    def _load_mount_data(self):
        if not self.mount_data:
            return
        self.name_input.setText(self.mount_data.get("name", ""))
        self.protocol_combo.setCurrentText(self.mount_data.get("protocol", "smb"))
        self.host_input.setText(self.mount_data.get("host", ""))
        self.port_input.setText(str(self.mount_data.get("port", "")))
        self.user_input.setText(self.mount_data.get("username", ""))
        self.password_input.setText(self.mount_data.get("password", ""))
        self.remote_path_input.setText(self.mount_data.get("remote_path", ""))
        self.local_path_input.setText(self.mount_data.get("local_path", ""))
        self.auto_start_check.setChecked(bool(self.mount_data.get("auto_start")))

    def save_mount(self):
        name = self.name_input.text().strip()
        protocol = self.protocol_combo.currentText()
        host = self.host_input.text().strip()
        port = self.port_input.text().strip()
        username = self.user_input.text().strip()
        password = self.password_input.text().strip()
        remote_path = self.remote_path_input.text().strip()
        local_path = self.local_path_input.text().strip()

        if not all([name, protocol, host, username, password, local_path]):
            QMessageBox.warning(self, "提示", "请完整填写必填字段。")
            return

        mount_data = {
            "name": name,
            "protocol": protocol,
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "remote_path": remote_path,
            "local_path": local_path,
            "auto_start": self.auto_start_check.isChecked(),
        }
        if self.mount_data:
            mount_data["remote_name"] = self.mount_data.get("remote_name") or "proto_{}".format(name.lower().replace(" ", "_"))
            self.service.update_mount(self.mount_data["id"], mount_data)
            QMessageBox.information(self, "完成", "协议挂载配置已更新。")
        else:
            mount_data["remote_name"] = "proto_{}".format(name.lower().replace(" ", "_"))
            self.service.add_mount(mount_data)
            QMessageBox.information(self, "完成", "协议挂载配置已保存。")
        self.on_saved()
        self.close()
