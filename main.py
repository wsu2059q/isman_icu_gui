import sys
import sqlite3
import os
import winreg
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, 
                            QPushButton, QMessageBox, QSystemTrayIcon, QMenu,
                            QVBoxLayout, QHBoxLayout, QWidget, QComboBox,
                            QListWidget, QInputDialog, QDialog, QDialogButtonBox,
                            QCheckBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
import win32gui
import requests
import time
import re
import shutil

def copy_icon_to_root():
    try:
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            icon_src = os.path.join(base_path, 'icon.ico')
            icon_dst = os.path.join(os.getcwd(), 'icon.ico')
            if not os.path.exists(icon_dst):
                shutil.copy(icon_src, icon_dst)
                print("图标文件已复制到程序目录")
                
    except Exception as e:
        print(f"图标复制失败: {str(e)}")

def fetch_data(url, check_string, patterns):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"请求失败，状态码: {response.status_code}")
    
    result = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, response.text)
        if match:
            result[key] = match.group(1)
        else:
            result[key] = None
    return result

class CreateAccountWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowTitle('新建账号')
        self.setGeometry(300, 300, 400, 200)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        self.new_id_input = QLineEdit()
        self.new_id_input.setPlaceholderText("输入新云湖ID")
        layout.addWidget(self.new_id_input)
        
        btn_layout = QHBoxLayout()
        self.create_btn = QPushButton("创建")
        self.create_btn.clicked.connect(self.create_account)
        btn_layout.addWidget(self.create_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
    def create_account(self):
        new_id = self.new_id_input.text()
        if not new_id:
            QMessageBox.warning(self, '错误', '请输入云湖ID')
            return
        
        self.parent().start_main_window(new_id)
        self.close()

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('icon.ico'))
        self.initUI()
        self.init_db()
        self.load_users()
        
    def initUI(self):
        self.setWindowTitle('云湖登录')
        self.setGeometry(300, 300, 450, 300)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
                border-radius: 12px;
            }
            QLabel {
                font-size: 14px;
                color: #495057;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
                min-height: 40px;
            }
            QLineEdit:focus {
                border: 2px solid #6c757d;
            }
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                min-width: 120px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #4e555b;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                min-width: 240px;
                min-height: 40px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #ced4da;
                border-left-style: solid;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignCenter)
        
        self.user_combo = QComboBox()
        self.user_combo.setPlaceholderText("选择已有账号")
        layout.addWidget(self.user_combo)
        
        self.login_btn = QPushButton('登录', self)
        layout.addWidget(self.login_btn, 0, Qt.AlignHCenter)
        self.login_btn.clicked.connect(self.handle_login)
        
        self.new_btn = QPushButton('新建账号', self)
        layout.addWidget(self.new_btn, 0, Qt.AlignHCenter)
        self.new_btn.clicked.connect(self.show_create_account)
        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
    def show_create_account(self):
        self.create_account_window = CreateAccountWindow(self)
        self.create_account_window.show()
        
    def init_db(self):
        self.conn = sqlite3.connect('users.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS users
                         (id TEXT PRIMARY KEY, 
                         username TEXT, 
                         userid TEXT, 
                         words TEXT)''')
        self.conn.commit()
        
    def load_users(self):
        self.c.execute("SELECT id, username FROM users")
        users = self.c.fetchall()
        self.user_combo.clear()
        
        if len(users) == 1:
            self.user_combo.addItem(f"{users[0][1]} ({users[0][0]})", users[0][0])
            self.user_combo.setCurrentIndex(0)
        elif len(users) > 1:
            for user in users:
                self.user_combo.addItem(f"{user[1]} ({user[0]})", user[0])
            self.user_combo.setCurrentIndex(0)
        else:
            self.user_combo.hide()
            self.login_btn.hide()
            self.new_btn.setText('创建账号')
            self.new_btn.clicked.disconnect()
            self.new_btn.clicked.connect(self.show_create_account)

    @staticmethod
    def get_executable_path():
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
            return os.path.abspath(sys.argv[0])

    @staticmethod
    def set_autostart(enabled):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "是个人 - ICU奸视器"
        executable_path = LoginWindow.get_executable_path()

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{executable_path}"')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            QMessageBox.warning(None, '自启动设置错误', f'无法修改注册表: {str(e)}')

    @staticmethod
    def check_autostart():
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "是个人 - ICU奸视器"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, app_name)
                executable_path = LoginWindow.get_executable_path()
                return value == f'"{executable_path}"'
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    def handle_login(self):
        if self.user_combo.isVisible():
            if self.user_combo.currentIndex() == -1:
                QMessageBox.warning(self, '错误', '请选择或输入账号')
                return
            
            selected_id = self.user_combo.currentData()
            self.start_main_window(selected_id)
        else:
            self.show_create_account()

    def start_main_window(self, user_id):
        self.hide()
        self.main_window = MainWindow(user_id, self.conn, self.c)
        self.main_window.closed.connect(self.show)
        self.main_window.closed.connect(self.load_users)
        self.main_window.show()
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowIcon(QIcon('icon.ico'))
        self.initUI()

    def initUI(self):
        self.setWindowTitle("设置")
        self.setGeometry(400, 400, 400, 300)
        layout = QVBoxLayout()

        # 自启动设置
        self.autostart_checkbox = QCheckBox("开机自动启动")
        self.autostart_checkbox.setChecked(LoginWindow.check_autostart())
        layout.addWidget(self.autostart_checkbox)

        # 屏蔽词列表
        layout.addWidget(QLabel("屏蔽词列表:"))
        self.word_list = QListWidget()
        self.word_list.addItems(self.parent.words)
        layout.addWidget(self.word_list)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self.add_word)
        btn_layout.addWidget(self.add_btn)

        self.del_btn = QPushButton("删除")
        self.del_btn.clicked.connect(self.del_word)
        btn_layout.addWidget(self.del_btn)

        layout.addLayout(btn_layout)

        watermark_label = QLabel("由 艾莉丝·格雷拉特 创建，开源地址: <a href='https://github.com/wsu2059q/isman_icu_gui'>是个人ICU_第三方</a>")
        watermark_label.setOpenExternalLinks(True)
        watermark_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        layout.addWidget(watermark_label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def add_word(self):
        word, ok = QInputDialog.getText(self, '添加屏蔽词', '输入新屏蔽词:')
        if ok and word:
            self.word_list.addItem(word)
            self.parent.words = [self.word_list.item(i).text() for i in range(self.word_list.count())]

    def del_word(self):
        row = self.word_list.currentRow()
        if row >= 0:
            self.word_list.takeItem(row)
            self.parent.words = [self.word_list.item(i).text() for i in range(self.word_list.count())]

    def accept(self):
        LoginWindow.set_autostart(self.autostart_checkbox.isChecked())
        super().accept()

class MainWindow(QMainWindow):
    closed = pyqtSignal()
    
    def __init__(self, user_id, conn, c):
        super().__init__()
        self.setWindowIcon(QIcon('icon.ico'))
        self.user_id = user_id
        self.conn = conn
        self.c = c
        self.username = None
        self.userid = None
        self.avatar_url = None
        self.words = []
        self.current_window = None
        self.initUI()
        self.init_tray()
        self.load_user_info()
        
    def initUI(self):
        self.setWindowTitle('是个人 - ICU奸视器')
        self.setGeometry(300, 300, 500, 400)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
                border-radius: 12px;
            }
            QLabel {
                font-size: 14px;
                color: #495057;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
                min-height: 40px;
            }
            QLineEdit:focus {
                border: 2px solid #6c757d;
            }
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                min-width: 120px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #4e555b;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(24)
        main_layout.setAlignment(Qt.AlignCenter)
        user_info_layout = QHBoxLayout()
        info_layout = QVBoxLayout()
        self.info_label = QLabel(self)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                font-size: 14px;
            }
        """)
        info_layout.addWidget(self.info_label)
        self.monitor_label = QLabel("当前监视窗口：无")
        self.monitor_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                font-size: 13px;
                color: #666;
            }
        """)
        info_layout.addWidget(self.monitor_label)
        
        user_info_layout.addLayout(info_layout)
        main_layout.addLayout(user_info_layout)
        
        btn_layout = QHBoxLayout()
        
        self.switch_btn = QPushButton('切换账号', self)
        self.switch_btn.clicked.connect(self.switch_account)
        btn_layout.addWidget(self.switch_btn)
        
        self.settings_btn = QPushButton('设置', self)
        self.settings_btn.clicked.connect(self.open_settings)
        btn_layout.addWidget(self.settings_btn)
        
        main_layout.addLayout(btn_layout)
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.monitor_window)
        self.timer.start(10000)
        
    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icon.ico'))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.close_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def load_user_info(self):
        self.get_user_info()
            
    def get_user_info(self):
        url = f"https://www.yhchat.com/user/homepage/{self.user_id}"
        patterns = {
            "userId": r'userId:"(.*?)"',
            "nickname": r'nickname:"(.*?)"',
            "avatarUrl": r'avatarUrl:"(.*?)"',
            "registerTime": r'registerTime:(\d+)',
            "registerTimeText": r'registerTimeText:"(.*?)"',
            "onLineDay": r'在线天数<\/span> <span[^>]*>(\d+)天<\/span>',
            "continuousOnLineDay": r'连续在线<\/span> <span[^>]*>(\d+)天<\/span>',
            "isVip": r'isVip:(.*?)}/',
            "medal": r'<div class="medal-container"[^>]*>\s*(.*?)\s*<\/div>'
        }
        try:
            data = fetch_data(url, "", patterns)
            print("获取到的用户信息：", data)
            self.username = data['nickname']
            self.userid = data['userId']
            self.avatar_url = data['avatarUrl']
            self.registerTime = int(data['registerTime'])
            self.registerTimeText = data['registerTimeText']
            self.onLineDay = int(data['onLineDay'])
            self.continuousOnLineDay = int(data['continuousOnLineDay'])
            self.isVip = data['isVip']
            self.medal = data['medal']
            self.save_user_info()
            self.update_info()
        except Exception as e:
            QMessageBox.warning(self, '错误', f'获取用户信息失败: {str(e)}')
            
    def save_user_info(self):
        self.c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)",
                      (self.user_id, self.username, self.userid, ' '.join(self.words)))
        self.conn.commit()
        
    def update_info(self):
        info = f"用户名: {self.username}\n\n用户ID: {self.userid}\n\n注册时间: {self.registerTimeText}\n\n在线天数: {self.onLineDay}\n\n连续在线: {self.continuousOnLineDay}\n\nVIP状态: {'是' if self.isVip == 'true' else '否'}"
        self.info_label.setText(info)
            
    def monitor_window(self):
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)
        for word in self.words:
            if word in window_title:
                window_title = "(小孩子不准看)"
        self.monitor_label.setText(f"当前监视窗口：{window_title}")
        self.send_name(window_title, hwnd)
        
    def send_name(self, name, hwnd=0):
        try:
            requests.post("http://de8.spaceify.eu:25660/sub", json={
                "header": {
                    "eventTime": int(time.time() * 1000),
                    "eventType": "message.receive.instruction"
                },
                "event": {
                    "sender": {
                        "senderId": self.userid,
                        "senderType": "user",
                        "senderUserLevel": "member",
                        "senderNickname": self.username,
                    },
                    "chat": {
                        "chatType": "bot"
                    },
                    "message": {
                        "msgId": str(int(time.time() * 1000)),
                        "contentType": "text",
                        "content": {
                            "text": name
                        },
                        "commandName": "NowOpening"
                    }
                }
            }, timeout=(15, 30))

            if hwnd:
                try:
                    win32gui.SetWindowText(hwnd, name)
                except Exception as e:
                    print(f"修改窗口标题失败: {str(e)}")
                    
        except requests.exceptions.Timeout:
            QMessageBox.warning(self, "连接超时", "正在尝试重新连接...")
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            QMessageBox.warning(self, "发送错误", f"数据发送失败: {str(e)}")

    def switch_account(self):
        self.closed.emit()
        self.hide()
        
    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.save_user_info()
            self.update_info()
        
    def close_app(self):
        try:
            self.send_name("空气")
        finally:
            self.tray_icon.hide()
            QApplication.quit()
            
    def closeEvent(self, event):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowIcon(QIcon('icon.ico'))
        msg.setWindowTitle('关闭确认')
        msg.setText('请选择操作：')
        msg.setStandardButtons(
            QMessageBox.Yes | 
            QMessageBox.No
        )
        msg.button(QMessageBox.Yes).setText('最小化到托盘')
        msg.button(QMessageBox.No).setText('完全退出')
        
        reply = msg.exec_()

        if reply == QMessageBox.Yes:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "后台运行",
                "程序将继续在后台运行\n双击托盘图标可恢复窗口",
                QSystemTrayIcon.Information,
                3000
            )
        elif reply == QMessageBox.No:
            self.close_app()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    copy_icon_to_root()
    app.setWindowIcon(QIcon('icon.ico'))
    app.setApplicationName("是个人 - ICU奸视器")
    if win32gui.FindWindow(None, "云湖登录"):
        QMessageBox.warning(None, "警告", "程序已经在运行中！")
        sys.exit(1)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
