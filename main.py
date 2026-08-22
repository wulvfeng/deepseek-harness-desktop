"""PyQt6 WebEngine 通用模板 - 程序入口。

用法：
    python main.py
启动后会自动根据 config.db 中的设置加载网页；
本地启动方式（静态目录 / npm run dev 等命令）会在界面启动时自动运行。
"""
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from app.config_db import ConfigDB
from app.main_window import MainWindow
from app.style import QSS


def main():
    # Qt6 高分屏缩放策略
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("DeepSeek Harness Desktop")
    app.setStyleSheet(QSS)  # 应用全局主题

    cfg = ConfigDB()  # 默认使用项目根目录下的 config.db (SQLite)
    window = MainWindow(cfg)
    window.show()
    window.start()  # 自动启动本地服务并加载网页

    exit_code = app.exec()
    cfg.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
