"""SQLite 配置持久化模块。

所有界面设置以 key-value 形式保存在项目根目录的 config.db 中，
无需额外的配置文件，便于分发与复用。
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "config.db")

# 默认配置项（首次运行或字段为空时使用）
DEFAULTS = {
    # 来源模式: url=直接网址 | ip_port=IP+端口 | local=本地启动
    "mode": "url",
    "url": "https://www.example.com",
    # IP + 端口模式
    "ip": "127.0.0.1",
    "port": "8000",
    # 本地启动子类型: static=静态文件目录 | command=命令启动(如 npm run dev)
    "local_type": "static",
    # 静态文件服务
    "static_dir": "",
    "static_port": "8000",
    # 命令启动
    "command_dir": "",
    "command": "npm run dev",
    "command_url": "http://127.0.0.1:5173",
    "command_timeout": "60",
    # 窗口
    "window_title": "PyQt6 WebEngine 模板",
    "window_icon": "",
    "window_width": "1200",
    "window_height": "800",
}


class ConfigDB:
    """基于 SQLite 的 key-value 配置存储，默认读写 config.db。"""

    def __init__(self, db_path=DB_PATH):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)"
        )
        self._conn.commit()

    def get(self, key, default=None):
        row = self._conn.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ).fetchone()
        return row[0] if row else default

    def get_default(self, key):
        """优先取数据库中的值，否则返回默认值。"""
        val = self.get(key)
        return val if val is not None else DEFAULTS.get(key)

    def get_int(self, key, default=0):
        """安全获取整数值：从数据库或默认值中取值并转为 int。"""
        raw = self.get_default(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except (ValueError, TypeError):
            return default

    def set(self, key, value):
        self._conn.execute(
            "INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)",
            (key, str(value)),
        )
        self._conn.commit()

    def all_settings(self):
        """返回所有已保存的设置（避免方法名覆盖内建 all()）。"""
        return dict(self._conn.execute("SELECT key, value FROM settings").fetchall())

    # 保留 all() 别名以兼容旧代码
    all = all_settings

    def close(self):
        self._conn.close()
