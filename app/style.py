"""全局 QSS 样式与主题常量。

在 main.py 中通过 app.setStyleSheet(QSS) 应用到整个应用，
主窗口、设置对话框、日志面板统一使用同一套现代主题。
"""

ACCENT = "#6366f1"        # indigo-500 主色
ACCENT_HOVER = "#818cf8"  # indigo-400 悬浮
ACCENT_DARK = "#4f46e5"   # indigo-600 按下
BG = "#f1f5f9"            # 页面底色
TERMINAL_BG = "#0f172a"   # 日志面板深色终端底色

QSS = f"""
/* ================= 全局 ================= */
QMainWindow, QDialog {{
    background: {BG};
}}
QToolTip {{
    background: #0f172a;
    color: #e2e8f0;
    border: 1px solid #334155;
    padding: 4px 8px;
    border-radius: 6px;
}}

/* ================= 工具栏 ================= */
QToolBar {{
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    padding: 6px 10px;
    spacing: 6px;
}}
QToolButton {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 6px 14px;
    color: #334155;
    font-size: 13px;
    font-weight: 500;
}}
QToolButton:hover {{
    background: #eef2ff;
    color: {ACCENT_DARK};
}}
QToolButton:pressed {{
    background: #e0e7ff;
}}
QToolButton:checked {{
    background: {ACCENT};
    color: #ffffff;
}}
QToolBar::separator {{
    width: 1px;
    background: #e2e8f0;
    margin: 6px 8px;
}}

/* ================= 状态栏 ================= */
QStatusBar {{
    background: #ffffff;
    border-top: 1px solid #e2e8f0;
    color: #64748b;
}}
QStatusBar::item {{ border: none; }}

/* ================= 按钮 ================= */
QPushButton {{
    background: {ACCENT};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 6px 16px;
    font-weight: 500;
}}
QPushButton:hover {{ background: {ACCENT_HOVER}; }}
QPushButton:pressed {{ background: {ACCENT_DARK}; }}
QPushButton:disabled {{ background: #cbd5e1; color: #f1f5f9; }}
QPushButton#GhostBtn {{
    background: transparent;
    color: #cbd5e1;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 400;
}}
QPushButton#GhostBtn:hover {{ background: #334155; color: #ffffff; border-color: #64748b; }}
QPushButton#GhostBtn:pressed {{ background: #475569; }}

/* 模式切换分段按钮 */
QPushButton#ModeTab {{
    background: #f8fafc;
    color: #475569;
    border: 1px solid #e2e8f0;
    border-radius: 9px;
    padding: 9px 12px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton#ModeTab:hover {{
    background: #eef2ff;
    color: {ACCENT_DARK};
    border-color: #c7d2fe;
}}
QPushButton#ModeTab:checked {{
    background: {ACCENT};
    color: #ffffff;
    border-color: {ACCENT};
}}
QPushButton#ModeTab:pressed {{ background: {ACCENT_DARK}; }}

/* ================= 输入控件 ================= */
QLineEdit, QSpinBox, QComboBox {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 6px 10px;
    color: #0f172a;
    min-height: 20px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{ border-color: #94a3b8; }}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 18px;
    border: none;
    background: transparent;
}}
QSpinBox::up-arrow {{
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 6px solid #64748b;
}}
QSpinBox::down-arrow {{
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #64748b;
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
    outline: none;
}}

/* ================= 单选按钮 ================= */
QRadioButton {{
    color: #334155;
    spacing: 8px;
    font-weight: 500;
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #cbd5e1;
    background: #ffffff;
}}
QRadioButton::indicator:hover {{ border-color: {ACCENT_HOVER}; }}
QRadioButton::indicator:checked {{
    border: 6px solid {ACCENT};
    background: #ffffff;
}}

/* ================= 分组框 ================= */
QGroupBox {{
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px 12px 10px;
    background: #ffffff;
    font-weight: 600;
    color: #1e293b;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}

/* ================= 日志面板（深色终端风格） ================= */
#LogPanel {{
    background: {TERMINAL_BG};
    border-left: 1px solid #1e293b;
}}
#LogHeader {{
    background: #1e293b;
}}
#LogTitle {{ color: #e2e8f0; font-size: 13px; font-weight: 600; }}
#StateBadge {{ color: #34d399; font-size: 11px; font-weight: 700; }}
#StateBadge[state="stopped"] {{ color: #f87171; }}
#LogInfo {{ background: #16213a; }}
#LogUrlLabel {{
    color: #7dd3fc;
    font-size: 12px;
    font-family: "Cascadia Code", Consolas, monospace;
}}
#LogLanLabel {{ color: #94a3b8; font-size: 12px; }}
#LogBody {{
    background: {TERMINAL_BG};
    color: #e2e8f0;
    border: none;
    font-family: "Cascadia Code", Consolas, "Courier New", monospace;
    font-size: 12px;
    padding: 8px;
}}
#LogBody QScrollBar:vertical {{
    background: #0b1220;
    width: 10px;
    border: none;
    border-radius: 5px;
}}
#LogBody QScrollBar::handle:vertical {{
    background: #334155;
    border-radius: 5px;
    min-height: 24px;
}}
#LogBody QScrollBar::handle:vertical:hover {{ background: #475569; }}
#LogBody QScrollBar::add-line, #LogBody QScrollBar::sub-line {{ height: 0; }}
"""
