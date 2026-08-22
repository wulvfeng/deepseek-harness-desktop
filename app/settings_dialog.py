"""设置对话框：配置网页来源。

支持三种模式（分段按钮切换）：
1. 直接网址 (URL)        - 例如 https://example.com
2. IP + 端口             - 例如 127.0.0.1:8000
3. 本地启动              - 又分为：
   - 静态文件目录：将指定文件夹作为静态站点启动本地 HTTP 服务
   - 命令启动：在指定文件夹执行命令（如 npm run dev）后加载指定 URL
"""
import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

MODE_URL = "url"
MODE_IP_PORT = "ip_port"
MODE_LOCAL = "local"
LOCAL_STATIC = "static"
LOCAL_COMMAND = "command"

_MODE_ORDER = (MODE_URL, MODE_IP_PORT, MODE_LOCAL)
_MODE_BUTTON = {"url": "btn_url", "ip_port": "btn_ip", "local": "btn_local"}


def _browse_dir(line_edit, parent):
    """弹出文件夹选择框并填入输入框。"""
    path = QFileDialog.getExistingDirectory(parent, "选择文件夹", line_edit.text())
    if path:
        line_edit.setText(os.path.normpath(path))


def _browse_file(line_edit, parent):
    """弹出文件选择框并填入输入框。"""
    path, _ = QFileDialog.getOpenFileName(
        parent,
        "选择图标",
        line_edit.text(),
        "图片文件 (*.png *.ico *.jpg *.jpeg *.bmp *.svg);;所有文件 (*)",
    )
    if path:
        line_edit.setText(os.path.normpath(path))


class SettingsDialog(QDialog):
    """网页来源设置对话框。"""

    # 保存成功后发出，主窗口据此重新加载网页来源
    settings_saved = pyqtSignal()

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle("设置 - 网页来源")
        self.setMinimumWidth(580)
        self._build_ui()
        self._load_values()
        self._apply_saved_mode()

    # ---------- UI 构建 ----------
    def _build_ui(self):
        root = QVBoxLayout(self)

        # 模式切换：分段按钮（选中高亮）
        mode_box = QGroupBox("网页来源模式")
        mode_row = QHBoxLayout(mode_box)
        mode_row.setSpacing(8)
        self.btn_url = QPushButton("直接网址 (URL)", objectName="ModeTab")
        self.btn_ip = QPushButton("IP + 端口", objectName="ModeTab")
        self.btn_local = QPushButton("本地启动", objectName="ModeTab")
        self._mode_group = QButtonGroup(self)
        for btn in (self.btn_url, self.btn_ip, self.btn_local):
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._mode_group.addButton(btn)
            mode_row.addWidget(btn, 1)
        self._mode_group.buttonClicked.connect(self._sync_ui)
        root.addWidget(mode_box)

        # 各模式面板
        cfg_box = QGroupBox("配置")
        cfg_lay = QVBoxLayout(cfg_box)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_url_panel())
        self.stack.addWidget(self._build_ip_panel())
        self.stack.addWidget(self._build_local_panel())
        cfg_lay.addWidget(self.stack)
        root.addWidget(cfg_box)

        # 窗口外观
        win_box = QGroupBox("窗口外观")
        win_lay = QFormLayout(win_box)
        self.edt_title = QLineEdit()
        self.edt_title.setPlaceholderText("PyQt6 WebEngine 模板")
        win_lay.addRow("窗口标题：", self.edt_title)
        self.edt_icon = QLineEdit()
        self.edt_icon.setPlaceholderText("选择 .png / .ico 图标文件")
        btn_icon = QPushButton("浏览...")
        btn_icon.clicked.connect(lambda: _browse_file(self.edt_icon, self))
        icon_row = QHBoxLayout()
        icon_row.addWidget(self.edt_icon, 1)
        icon_row.addWidget(btn_icon)
        win_lay.addRow("窗口图标：", icon_row)
        root.addWidget(win_box)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _build_url_panel(self):
        panel = QWidget()
        form = QFormLayout(panel)
        self.edt_url = QLineEdit()
        self.edt_url.setPlaceholderText("https://example.com")
        form.addRow("网址：", self.edt_url)
        return panel

    def _build_ip_panel(self):
        panel = QWidget()
        form = QFormLayout(panel)
        self.edt_ip = QLineEdit()
        self.edt_ip.setPlaceholderText("127.0.0.1")
        self.spn_port = QSpinBox()
        self.spn_port.setRange(1, 65535)
        form.addRow("IP：", self.edt_ip)
        form.addRow("端口：", self.spn_port)
        return panel

    def _build_local_panel(self):
        panel = QWidget()
        form = QFormLayout(panel)

        self.cb_local_type = QComboBox()
        self.cb_local_type.addItem("静态文件目录", LOCAL_STATIC)
        self.cb_local_type.addItem("命令启动 (如 npm run dev)", LOCAL_COMMAND)
        form.addRow("启动方式：", self.cb_local_type)

        self.local_stack = QStackedWidget()
        self.local_stack.addWidget(self._build_static_panel())
        self.local_stack.addWidget(self._build_command_panel())
        form.addRow(self.local_stack)

        self.cb_local_type.currentIndexChanged.connect(self.local_stack.setCurrentIndex)
        return panel

    def _build_static_panel(self):
        panel = QWidget()
        form = QFormLayout(panel)
        self.edt_static_dir = QLineEdit()
        btn_dir = QPushButton("浏览...")
        btn_dir.clicked.connect(lambda: _browse_dir(self.edt_static_dir, self))
        row = QHBoxLayout()
        row.addWidget(self.edt_static_dir, 1)
        row.addWidget(btn_dir)
        form.addRow("静态目录：", row)
        self.spn_static_port = QSpinBox()
        self.spn_static_port.setRange(1, 65535)
        self.spn_static_port.setValue(8000)
        form.addRow("服务端口：", self.spn_static_port)
        return panel

    def _build_command_panel(self):
        panel = QWidget()
        form = QFormLayout(panel)
        self.edt_cmd_dir = QLineEdit()
        btn_dir = QPushButton("浏览...")
        btn_dir.clicked.connect(lambda: _browse_dir(self.edt_cmd_dir, self))
        row = QHBoxLayout()
        row.addWidget(self.edt_cmd_dir, 1)
        row.addWidget(btn_dir)
        form.addRow("项目目录：", row)
        self.edt_command = QLineEdit()
        self.edt_command.setPlaceholderText("npm run dev")
        form.addRow("启动命令：", self.edt_command)
        self.edt_cmd_url = QLineEdit()
        self.edt_cmd_url.setPlaceholderText("http://127.0.0.1:5173")
        form.addRow("就绪后加载(留空自动识别)：", self.edt_cmd_url)
        self.spn_cmd_timeout = QSpinBox()
        self.spn_cmd_timeout.setRange(5, 600)
        self.spn_cmd_timeout.setValue(60)
        self.spn_cmd_timeout.setSuffix(" 秒")
        form.addRow("就绪超时：", self.spn_cmd_timeout)
        return panel

    # ---------- 取值 / 回填 ----------
    def _load_values(self):
        g = self.cfg.get_default
        self.edt_url.setText(g("url"))
        self.edt_ip.setText(g("ip"))
        self.spn_port.setValue(self.cfg.get_int("port", 8000))
        self.edt_static_dir.setText(g("static_dir"))
        self.spn_static_port.setValue(self.cfg.get_int("static_port", 8000))
        self.edt_cmd_dir.setText(g("command_dir"))
        self.edt_command.setText(g("command"))
        self.edt_cmd_url.setText(g("command_url"))
        self.spn_cmd_timeout.setValue(self.cfg.get_int("command_timeout", 60))
        self.edt_title.setText(g("window_title"))
        self.edt_icon.setText(g("window_icon"))

    def _apply_saved_mode(self):
        """打开对话框时，根据已保存的配置勾选对应模式与启动方式。"""
        mode = self.cfg.get_default("mode")
        getattr(self, _MODE_BUTTON.get(mode, "btn_url")).setChecked(True)
        idx = self.cb_local_type.findData(self.cfg.get_default("local_type"))
        self.cb_local_type.setCurrentIndex(idx if idx >= 0 else 0)
        self._sync_ui()

    def _sync_ui(self):
        self.stack.setCurrentIndex(_MODE_ORDER.index(self._current_mode()))

    def _current_mode(self):
        if self.btn_url.isChecked():
            return MODE_URL
        if self.btn_ip.isChecked():
            return MODE_IP_PORT
        return MODE_LOCAL

    # ---------- 保存 ----------
    def _save(self):
        g = self.cfg.get_default
        setter = self.cfg.set
        setter("mode", self._current_mode())
        setter("local_type", self.cb_local_type.currentData() or LOCAL_STATIC)
        setter("url", self.edt_url.text().strip())
        setter("ip", self.edt_ip.text().strip() or "127.0.0.1")
        setter("port", self.spn_port.value())
        setter("static_dir", self.edt_static_dir.text().strip())
        setter("static_port", self.spn_static_port.value())
        setter("command_dir", self.edt_cmd_dir.text().strip())
        setter("command", self.edt_command.text().strip() or g("command"))
        setter("command_url", self.edt_cmd_url.text().strip() or g("command_url"))
        setter("command_timeout", self.spn_cmd_timeout.value())
        setter("window_title", self.edt_title.text().strip() or g("window_title"))
        setter("window_icon", self.edt_icon.text().strip())
        self.settings_saved.emit()
        self.accept()
