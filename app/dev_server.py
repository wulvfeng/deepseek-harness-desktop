"""本地启动服务管理。

支持两种本地启动方式：
1. static   - 将指定文件夹作为静态文件根目录启动一个本地 HTTP 服务
2. command  - 在指定文件夹中执行外部命令（如 npm run dev），并等待服务就绪

所有启动的进程/服务在应用退出时会自动清理。
"""
import logging
import os
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

WINDOWS = os.name == "nt"

logger = logging.getLogger(__name__)


class LocalDevServer:
    """管理本地启动的进程与服务。"""

    def __init__(self, log_callback=None):
        self._httpd = None
        self._http_thread = None
        self._proc = None
        self._log = log_callback or (lambda msg: print(msg))

    # ---------- 静态文件目录服务 ----------
    def start_static(self, folder, port=8000):
        """以 folder 为根目录启动静态文件 HTTP 服务。"""
        folder = os.path.abspath(folder)
        if not os.path.isdir(folder):
            raise FileNotFoundError(f"静态目录不存在: {folder}")
        handler = partial(SimpleHTTPRequestHandler, directory=folder)
        self._httpd = ThreadingHTTPServer(("127.0.0.1", int(port)), handler)
        self._http_thread = threading.Thread(
            target=self._httpd.serve_forever, daemon=True
        )
        self._http_thread.start()
        self._log(f"[local] 静态服务已启动: http://127.0.0.1:{port}/ -> {folder}")

    # ---------- 命令启动（npm run dev 等） ----------
    def start_command(self, command, cwd):
        """在 cwd 目录中启动命令，输出通过日志回调转发。"""
        cwd = os.path.abspath(cwd)
        if not os.path.isdir(cwd):
            raise FileNotFoundError(f"命令工作目录不存在: {cwd}")
        kwargs = {
            "cwd": cwd,
            "shell": True,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }
        if WINDOWS:
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        self._proc = subprocess.Popen(command, **kwargs)
        self._log(f"[local] 已执行命令: {command} (cwd={cwd}, pid={self._proc.pid})")
        threading.Thread(target=self._pump_output, daemon=True).start()
        return self._proc

    def _pump_output(self):
        try:
            for line in iter(self._proc.stdout.readline, ""):
                if line:
                    self._log(f"[dev] {line.rstrip()}")
            self._proc.stdout.close()
        except (OSError, ValueError):
            # 进程已被终止，stdout 管道已关闭
            pass
        if self._proc is not None and self._proc.poll() is not None and self._proc.returncode != 0:
            self._log(f"[dev] 命令已退出，退出码: {self._proc.returncode}")

    @property
    def running(self):
        if self._httpd is not None:
            return True
        return self._proc is not None and self._proc.poll() is None

    # ---------- 清理 ----------
    def stop(self):
        """停止命令进程（含子进程树）与静态服务。"""
        self._stop_command()
        self._stop_http()

    def _stop_command(self):
        proc = self._proc
        if proc is None or proc.poll() is not None:
            if proc is not None:
                self._proc = None
            return

        pid = proc.pid
        try:
            if WINDOWS:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    timeout=10,
                )
            else:
                proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
            self._log("[local] 已停止命令进程")
        except Exception as exc:
            logger.warning("停止命令进程时出错: %s", exc)
            self._log(f"[error] 停止命令进程失败: {exc}")
        finally:
            self._proc = None

    def _stop_http(self):
        httpd = self._httpd
        if httpd is None:
            return
        try:
            httpd.shutdown()
            httpd.server_close()
            self._log("[local] 已停止静态服务")
        except Exception as exc:
            logger.warning("停止静态服务时出错: %s", exc)
        finally:
            self._httpd = None
            self._http_thread = None
