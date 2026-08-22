"""主窗口：顶部工具栏（设置按钮）+ QtWebEngine 网页区域 + 命令执行日志面板。

应用启动时根据 SQLite 中的设置自动执行：
- 直接网址 / IP+端口：直接加载对应网页
- 本地启动（静态目录）：启动静态文件 HTTP 服务后加载
- 本地启动（命令）：执行 npm run dev 等命令，等待服务就绪后加载指定 URL；
  「就绪后加载」留空时，会自动从命令输出中识别地址（如 Vite 打印的 Local URL）

界面效果：网页加载动画遮罩、日志面板平滑展开/收起、统一 QSS 现代主题。
"""
import os
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit

from PyQt6.QtCore import (
    QEasingCurve,
    QTimer,
    Qt,
    QUrl,
    QVariantAnimation,
)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .dev_server import LocalDevServer
from .log_widget import LogPanel
from .settings_dialog import SettingsDialog

LOG_PANEL_WIDTH = 340  # 日志面板展开宽度


class LoadingOverlay(QWidget):
    """网页加载遮罩：半透明圆角卡片 + 旋转加载动画。"""

    _FRAMES = ["◐", "◓", "◑", "◒"]

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay = QVBoxLayout(self)
        lay.addStretch(1)
        self._label = QLabel("◐ 加载中...", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            "color:#e2e8f0; font-size:15px; font-weight:600;"
            "background:rgba(15,23,42,210); border-radius:14px;"
            "padding:18px 28px;"
        )
        lay.addWidget(self._label, 0, Qt.AlignmentFlag.AlignCenter)
        lay.addStretch(1)
        self._idx = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.hide()

    def _tick(self):
        self._idx = (self._idx + 1) % len(self._FRAMES)
        self._label.setText(f"{self._FRAMES[self._idx]} 加载中...")

    def start(self):
        self.setGeometry(self.parentWidget().rect())
        self.show()
        self.raise_()
        self._timer.start(130)

    def stop(self):
        self._timer.stop()
        self.hide()


class MainWindow(QMainWindow):
    """通用 WebEngine 主窗口模板。"""

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self._base_title = cfg.get_default("window_title") or "PyQt6 WebEngine 模板"
        self.setWindowTitle(self._base_title)
        self._apply_window_icon()
        self.resize(
            cfg.get_int("window_width", 1200),
            cfg.get_int("window_height", 800),
        )

        # 日志面板 + 本地启动管理（日志回调直接进入面板，线程安全）
        self.log_panel = LogPanel()
        self.log_panel.url_detected.connect(self._on_url_detected)
        self.server = LocalDevServer(log_callback=self.log_panel.append)

        # 命令启动就绪轮询
        self._ready_timer = QTimer(self)
        self._ready_timer.timeout.connect(self._check_ready)
        self._ready_elapsed = 0
        self._ready_timeout = 0
        self._pending_url = None     # 配置的就绪检测地址；None 表示等待自动识别
        self._detected_url = ""      # 从命令输出识别到的地址

        self._build_central()
        self._build_toolbar()
        self._build_log_anim()
        self._log_collapsing = False

        # F12 切换命令日志面板（类似 DevTools）
        self._log_visible = False
        self._f12 = QShortcut(QKeySequence(Qt.Key.Key_F12), self)
        self._f12.activated.connect(self._toggle_log_by_hotkey)

        self.statusBar().showMessage("就绪")

    # ---------- 中央区域 ----------
    def _build_central(self):
        self.view_container = QWidget()
        vlay = QVBoxLayout(self.view_container)
        vlay.setContentsMargins(0, 0, 0, 0)

        self.view = QWebEngineView()
        self.view.titleChanged.connect(self._on_title_changed)
        self.view.loadStarted.connect(self._on_load_started)
        self.view.loadFinished.connect(self._on_load_finished)
        vlay.addWidget(self.view)

        self._overlay = LoadingOverlay(self.view_container)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.addWidget(self.view_container)
        self.splitter.addWidget(self.log_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.setCentralWidget(self.splitter)

    # ---------- 工具栏 ----------
    def _build_toolbar(self):
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(toolbar)

        act_back = QAction("后退", self)
        act_back.triggered.connect(self.view.back)
        act_forward = QAction("前进", self)
        act_forward.triggered.connect(self.view.forward)
        act_reload = QAction("刷新", self)
        act_reload.triggered.connect(self.view.reload)
        for act in (act_back, act_forward, act_reload):
            toolbar.addAction(act)

        toolbar.addSeparator()

        act_settings = QAction("设置", self)
        act_settings.triggered.connect(self.open_settings)
        toolbar.addAction(act_settings)

    # ---------- 日志面板动画 ----------
    def _build_log_anim(self):
        self.log_panel.hide()
        self._log_anim = QVariantAnimation(self)
        self._log_anim.setDuration(220)
        self._log_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._log_anim.valueChanged.connect(self._on_log_anim_value)
        self._log_anim.finished.connect(self._on_log_anim_finished)

    def _toggle_log_by_hotkey(self):
        """F12 快捷键切换日志面板显示/隐藏。"""
        self._log_visible = not self._log_visible
        self.toggle_log(self._log_visible)

    def toggle_log(self, show):
        """切换日志面板显示状态。show=True 展开，show=False 收起。"""
        self._log_anim.stop()
        current = self.log_panel.width() if self.log_panel.isVisible() else 0
        if show:
            self.log_panel.setVisible(True)
            self._log_collapsing = False
            self._log_anim.setStartValue(current)
            self._log_anim.setEndValue(LOG_PANEL_WIDTH)
        else:
            self._log_collapsing = True
            self._log_anim.setStartValue(current)
            self._log_anim.setEndValue(0)
        self._log_anim.start()

    def _on_log_anim_value(self, width):
        sizes = self.splitter.sizes()
        total = sum(sizes)
        self.splitter.setSizes([max(120, total - int(width)), int(width)])

    def _on_log_anim_finished(self):
        if self._log_collapsing:
            self.log_panel.hide()
            self._log_collapsing = False

    # ---------- 启动流程 ----------
    def start(self):
        """应用启动 / 设置保存后调用：先停止旧本地服务，再按模式加载网页。"""
        self.server.stop()
        self._stop_ready_poll()
        self._detected_url = ""
        mode = self.cfg.get_default("mode")

        if mode == "local":
            self._start_local()
        else:
            url = self._resolve_remote_url()
            self.log_panel.set_access_url(url)
            self._navigate(url)

    def _resolve_remote_url(self):
        mode = self.cfg.get_default("mode")
        if mode == "ip_port":
            ip = self.cfg.get_default("ip") or "127.0.0.1"
            port = self.cfg.get_default("port") or "8000"
            return f"http://{ip}:{port}"
        return self.cfg.get_default("url")

    def _start_local(self):
        local_type = self.cfg.get_default("local_type")
        try:
            if local_type == "static":
                folder = self.cfg.get_default("static_dir")
                port = self.cfg.get_int("static_port", 8000)
                self.server.start_static(folder, port)
                url = f"http://127.0.0.1:{port}/"
                self.log_panel.set_access_url(url)
                self._navigate(url)
            else:  # 命令启动
                cwd = self.cfg.get_default("command_dir")
                command = self.cfg.get_default("command")
                url = (self.cfg.get_default("command_url") or "").strip()
                timeout = self.cfg.get_int("command_timeout", 60)
                self.server.start_command(command, cwd)
                if url:
                    self.log_panel.set_access_url(url)
                    self._wait_ready(url, timeout)
                else:
                    # 未指定地址：等待从命令输出中自动识别
                    self.log_panel.set_access_url("等待从命令输出识别地址...")
                    self._wait_ready(None, timeout)
        except Exception as exc:  # 目录不存在、端口占用等
            self._log(f"[error] 本地启动失败: {exc}")
            QMessageBox.warning(self, "本地启动失败", str(exc))

    def _navigate(self, url):
        self._log(f"[web] 加载 {url}")
        self.statusBar().showMessage(f"加载中: {url}")
        self.view.load(QUrl(url))

    # ---------- 命令就绪轮询 ----------
    def _wait_ready(self, url, timeout):
        self._pending_url = url
        self._ready_elapsed = 0
        self._ready_timeout = timeout
        self.statusBar().showMessage(
            "等待服务就绪..." if url is None else f"等待服务就绪: {url} ..."
        )
        self._ready_timer.start(1000)

    def _stop_ready_poll(self):
        self._ready_timer.stop()
        self._pending_url = None

    def _check_ready(self):
        self._ready_elapsed += 1
        target = self._pending_url or self._detected_url
        if target:
            ready = self._probe_ready(target)
            if ready:
                self._ready_timer.stop()
                self.statusBar().showMessage(f"服务已就绪: {ready}", 5000)
                self._navigate(ready)
                self._pending_url = None
                return
        if self._ready_elapsed >= self._ready_timeout:
            self._ready_timer.stop()
            self.statusBar().clearMessage()
            QMessageBox.warning(
                self,
                "启动超时",
                f"服务在 {self._ready_timeout} 秒内未就绪:\n{target or '未能从命令输出识别地址'}",
            )
            self._pending_url = None

    def _probe_ready(self, url):
        """探测服务是否就绪；部分开发服务器只绑定 IPv6(::/::1)，此时把主机名换成 localhost 再试。"""
        if self._url_ok(url):
            return url
        parts = urlsplit(url)
        host = parts.hostname
        if host and host not in ("localhost", "::1"):
            alt = urlunsplit(
                (parts.scheme, f"localhost:{parts.port or 80}", parts.path, parts.query, parts.fragment)
            )
            if self._url_ok(alt):
                return alt
        return None

    @staticmethod
    def _url_ok(url, timeout=1.0):
        """返回 True 表示服务已响应（能连上即可，不要求 200）。"""
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout):
                return True
        except urllib.error.HTTPError:
            return True  # 返回了 HTTP 状态码即视为服务已启动
        except Exception:
            return False

    # ---------- 日志识别与展示 ----------
    def _on_url_detected(self, url):
        self._detected_url = url

    def _on_load_started(self):
        self._overlay.start()

    def _on_load_finished(self, ok):
        self._overlay.stop()
        self.statusBar().showMessage("加载完成" if ok else "加载失败", 3000)

    # ---------- 设置 ----------
    def open_settings(self):
        dlg = SettingsDialog(self.cfg, self)
        dlg.settings_saved.connect(self._apply_window_identity)
        dlg.settings_saved.connect(self.start)
        dlg.exec()

    def _apply_window_identity(self):
        """设置保存后，应用窗口标题与图标。"""
        self._base_title = self.cfg.get_default("window_title") or "PyQt6 WebEngine 模板"
        self.setWindowTitle(self._base_title)
        self._apply_window_icon()

    def _apply_window_icon(self):
        icon = self.cfg.get_default("window_icon")
        if icon and os.path.isfile(icon):
            self.setWindowIcon(QIcon(icon))

    # ---------- 辅助 ----------
    def _log(self, msg):
        print(msg)
        self.log_panel.append(msg)

    def _on_title_changed(self, title):
        if title:
            self.setWindowTitle(f"{title} - {self._base_title}")

    # ---------- 退出清理 ----------
    def closeEvent(self, event):
        self._stop_ready_poll()
        self.server.stop()
        self.cfg.set("window_width", self.width())
        self.cfg.set("window_height", self.height())
        super().closeEvent(event)
