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
)

from app.services.protocol_mount_service import ProtocolMountService


class ProtocolMountWindow(QWidget):
    def __init__(self, on_saved):
        super().__init__()
        self.on_saved = on_saved
        self.service = ProtocolMountService()
        self.init_ui()

    def init_ui(self):
        self.resize(620, 360)
        self.setWindowTitle("新建协议挂载")

        layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["smb", "sshfs", "webdav"])
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.remote_path_input = QLineEdit()
        self.local_path_input = QLineEdit()
        self.auto_start_check = QCheckBox("开机自动挂载")

        layout.addLayout(self._row("显示名称", self.name_input))
        layout.addLayout(self._row("协议", self.protocol_combo))
        layout.addLayout(self._row("主机/URL", self.host_input))
        layout.addLayout(self._row("端口(可选)", self.port_input))
        layout.addLayout(self._row("用户名", self.user_input))
        layout.addLayout(self._row("密码", self.password_input))
        layout.addLayout(self._row("远程路径", self.remote_path_input))
        layout.addLayout(self._row("本地盘符", self.local_path_input))
        layout.addWidget(self.auto_start_check)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_mount)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def _row(self, title, widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(title))
        row.addWidget(widget)
        return row

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
            "remote_name": "proto_{}".format(name.lower().replace(" ", "_")),
        }

        self.service.add_mount(mount_data)
        QMessageBox.information(self, "完成", "协议挂载配置已保存。")
        self.on_saved()
        self.close()
