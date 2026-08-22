"""命令执行日志面板。

功能：
- 实时显示本地启动命令（npm run dev 等）的标准输出/错误
- 顶部展示当前访问地址与局域网访问地址（自动提取端口）
- 自动从命令输出中识别 URL（如 Vite 打印的 Local 地址），通过信号通知主窗口
- 深色终端风格，日志按前缀着色，自动滚动到底部

说明：append() 可能从后台线程调用，通过 Qt 信号转发到 UI 线程，保证线程安全。
"""
import re
import socket
from urllib.parse import urlparse

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_URL_RE = re.compile(r"https?://[^\s\"'<>）)】]+")

# 日志行前缀 → 颜色（深色终端风格）
_TAG_COLOR = {
    "[error]": "#f87171",   # 红
    "[local]": "#38bdf8",   # 天蓝
    "[web]":   "#c084fc",   # 紫
    "[dev]":   "#94a3b8",   # 灰蓝
    "[ready]": "#34d399",   # 绿
}
_DEFAULT_COLOR = "#e2e8f0"


def lan_ips():
    """返回本机所有 IPv4 局域网地址（不含回环地址）。"""
    ips = set()
    try:
        hostname = socket.gethostname()
        # 先尝试通过 UDP 连接确定主网卡 IP（不会实际发送数据）
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(0.1)
                s.connect(("8.8.8.8", 80))
                ips.add(s.getsockname()[0])
        except (OSError, socket.timeout):
            pass
        # 再通过 getaddrinfo 补充
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ips.add(info[4][0])
    except (OSError, socket.gaierror):
        pass
    ips.discard("127.0.0.1")
    return sorted(ips)


class LogPanel(QWidget):
    """命令执行日志面板。"""

    # 从命令输出中识别到 URL 时发出
    url_detected = pyqtSignal(str)
    _append = pyqtSignal(str)  # 后台线程 → UI 线程转发

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogPanel")
        self._last_url = ""
        self._build_ui()
        self.set_state("stopped")
        self._append.connect(self._append_local)

    # ---------- UI ----------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 头部
        header = QFrame(objectName="LogHeader")
        h = QHBoxLayout(header)
        h.setContentsMargins(12, 10, 12, 10)
        title = QLabel("命令执行日志", objectName="LogTitle")
        self.badge = QLabel("未运行", objectName="StateBadge")
        self.btn_copy = QPushButton("复制地址", objectName="GhostBtn")
        self.btn_clear = QPushButton("清空", objectName="GhostBtn")
        self.btn_copy.clicked.connect(self._copy_url)
        self.btn_clear.clicked.connect(self.clear)
        h.addWidget(title)
        h.addStretch(1)
        h.addWidget(self.badge)
        h.addWidget(self.btn_copy)
        h.addWidget(self.btn_clear)
        root.addWidget(header)

        # 地址信息条
        info = QFrame(objectName="LogInfo")
        inf = QVBoxLayout(info)
        inf.setContentsMargins(12, 8, 12, 8)
        inf.setSpacing(4)
        self.lbl_url = QLabel("访问地址: --", objectName="LogUrlLabel")
        self.lbl_lan = QLabel("局域网访问: --", objectName="LogLanLabel")
        inf.addWidget(self.lbl_url)
        inf.addWidget(self.lbl_lan)
        root.addWidget(info)

        # 日志正文
        self.body = QPlainTextEdit(objectName="LogBody")
        self.body.setReadOnly(True)
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.body.setFont(font)
        self.body.setMaximumBlockCount(2000)
        root.addWidget(self.body, 1)

    # ---------- 日志 ----------
    def append(self, text):
        """追加一行日志（线程安全，可从后台线程调用）。"""
        self._append.emit(text)

    def _append_local(self, text):
        line = text.rstrip()
        if not line:
            return
        color = _DEFAULT_COLOR
        for tag, c in _TAG_COLOR.items():
            if line.startswith(tag):
                color = c
                break
        body = self._highlight_urls(self._esc(line))
        self.body.appendHtml(f'<span style="color:{color};">{body}</span>')

        # 状态变化
        if "已执行命令" in line or "已启动" in line:
            self.set_state("running")
        elif "已停止" in line or "退出码" in line or "失败" in line or "超时" in line:
            self.set_state("stopped")

        # 自动识别地址
        m = _URL_RE.search(line)
        if m:
            url = m.group(0).rstrip(")>,.;，。；：")
            self.set_access_url(url)
            self.url_detected.emit(url)

    def clear(self):
        self.body.clear()

    @staticmethod
    def _esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _highlight_urls(esc_text):
        def repl(m):
            return f'<span style="color:#7dd3fc;">{m.group(0)}</span>'

        return _URL_RE.sub(repl, esc_text)

    # ---------- 地址展示 ----------
    def set_access_url(self, url):
        self._last_url = url
        self.lbl_url.setText(f"访问地址: {url}")
        port = None
        try:
            port = urlparse(url).port
        except ValueError:
            port = None
        if port:
            lan = "  ".join(f"http://{ip}:{port}" for ip in lan_ips())
            self.lbl_lan.setText("局域网访问: " + (lan or "--"))
        else:
            self.lbl_lan.setText("局域网访问: --")

    def set_state(self, state):
        """state: "running" | "stopped"（通过属性切换徽标颜色）。"""
        self.badge.setProperty("state", state)
        self.badge.setText("运行中" if state == "running" else "未运行")
        self.badge.style().unpolish(self.badge)
        self.badge.style().polish(self.badge)

    def _copy_url(self):
        if self._last_url:
            QApplication.clipboard().setText(self._last_url)
