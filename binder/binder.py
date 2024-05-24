import sys
import os
from enum import Enum
from time import sleep
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QDialog, QComboBox,
    QFormLayout, QScrollArea, QScrollBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPalette, QColor
from webbrowser import open as webbrowser_open
from keyboard import add_hotkey, send
import pyperclip
import threading
import hashlib
import urllib.request
import subprocess

from ctypes import Structure, windll, pointer, cast, c_void_p, c_ulong, c_bool, c_int, WINFUNCTYPE, c_uint32, create_unicode_buffer, byref, wintypes
from json import dump as json_dump, load as json_load, loads as json_loads


__location__ = os.getcwd()
binder = None
mouse = None

user32 = windll.user32
EnumWindows = windll.user32.EnumWindows
EnumWindowsProc = WINFUNCTYPE(c_bool, c_int, c_int)
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowRect = windll.user32.GetWindowRect
OpenProcess = windll.kernel32.OpenProcess
CloseHandle = windll.kernel32.CloseHandle
GetWindowLong = user32.GetWindowLongW
GetWindowLong.restype = wintypes.LONG
GetWindowLong.argtypes = [wintypes.HWND, c_int]



PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
GWL_STYLE = -16
WS_BORDER = 0x00800000
WS_CAPTION = 0x00C00000
GW_HWNDNEXT = 2
MAX_COLS = 1
WINDOW_WIDTH, WINDOW_HEIGHT = 0, 0
LEFT, TOP, RIGHT, BOTTOM = 0, 0, 0, 0
DATE_FORMAT = "%d.%m.%Y"
UPDATE_FILE = 'Update.exe'
SECRET_FILE = 'data/configs/secret.json'
BUTTON_HOUSE_CONFIG_FILE = 'data/configs/house_info.json'
BUTTON_REPORT_CONFIG_FILE = 'data/configs/button_config.json'

# # neon
# TEXT_COLOR = "#e0e0e0"
# BORDER_COLOR = "#2E8B57"
# BACKGROUND_COLOR = "#1E1E1E"
# LINE_BACKGROUND_COLOR = "#345e37"


# # neon
# TEXT_COLOR = "#e0e0e0"
# BORDER_COLOR = "#4d425f"
# BACKGROUND_COLOR = "#241b35"
# LINE_BACKGROUND_COLOR = "#4d425f"


# # dark green
# TEXT_COLOR = "#fbfbfe"
# BORDER_COLOR = "#1acdb4"
# BACKGROUND_COLOR = "#222222"
# LINE_BACKGROUND_COLOR = "#1f5b53"

#blue
TEXT_COLOR = "#e0e0e0"
BORDER_COLOR = "#3D5A80"
BACKGROUND_COLOR = "#0f1c2e"
LINE_BACKGROUND_COLOR = "#4d648d"

VERSION_FILE = os.path.join(__location__, "version.json")
CLICK_DATA_FILE = os.path.join(__location__, "data/configs/click_data.json")
BUTTON_VIOLATION_CONFIG_FILE = os.path.join(__location__, "data/configs/violation_config.json")
BUTTON_REPORT_CONFIG_FILE = os.path.join(__location__, "data/configs/button_config.json")
BUTTON_HOUSE_CONFIG_FILE = os.path.join(__location__, "data/configs/house_info.json")
SECRET_FILE = os.path.join(__location__, "data/configs/secret.json")
CSS_STYLES_FILE = os.path.join(__location__, "data/styles.css")

pixel_conditions = {
    "should_show_violation_buttons": {
        (20, 370): (68, 68, 68),
        (70, 370): (68, 68, 68)
    },
    "should_show_buttons": {
        (250, 370): (68, 68, 68),
        (305, 338): (68, 68, 68)
    },
    "should_show_control_buttons": {
        (940, 360): (85, 85, 85),
        (940, 385): (85, 85, 85)
    },
    "should_show_teleport_buttons": {
        (340, 370): (68, 68, 68),
        (420, 370): (68, 68, 68)
    }
}

if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists("data/configs"):
    os.makedirs("data/configs")



class Mouse:
    """
    It simulates the mouse.

    Attributes:
    - MOUSEEVENTF_MOVE (int): Mouse move event flag.
    - MOUSEEVENTF_LEFTDOWN (int): Left button down event flag.
    - MOUSEEVENTF_LEFTUP (int): Left button up event flag.
    - MOUSEEVENTF_RIGHTDOWN (int): Right button down event flag.
    - MOUSEEVENTF_RIGHTUP (int): Right button up event flag.
    - MOUSEEVENTF_MIDDLEDOWN (int): Middle button down event flag.
    - MOUSEEVENTF_MIDDLEUP (int): Middle button up event flag.
    - MOUSEEVENTF_WHEEL (int): Wheel button rolled event flag.
    - MOUSEEVENTF_ABSOLUTE (int): Absolute move event flag.
    - SM_CXSCREEN (int): System metric for screen width.
    - SM_CYSCREEN (int): System metric for screen height.

    Methods:
    - _do_event(flags, x_pos, y_pos, data, extra_info): Generate a mouse event.
    - _get_button_value(button_name, button_up=False): Convert button name to the corresponding value.
    - move_mouse(pos): Move the mouse to the specified coordinates.
    - press_button(pos=(-1, -1), button_name="left", button_up=False): Push a mouse button.
    - click(pos=(-1, -1), button_name="left"): Click at the specified position.
    - get_position(): Get the current mouse position.
    """

    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_ABSOLUTE = 0x8000
    SM_CXSCREEN = 0
    SM_CYSCREEN = 1


    def _do_event(self, flags, x_pos, y_pos, data, extra_info):
        """
        Generate a mouse event.

        Args:
        - flags (int): Mouse event flags.
        - x_pos (int): X-coordinate for the event.
        - y_pos (int): Y-coordinate for the event.
        - data (int): Additional data for the event.
        - extra_info (int): Extra information for the event.

        Returns:
        - int: Result of the mouse event generation.
        """
        x_calc = int(65536 * x_pos / windll.user32.GetSystemMetrics(self.SM_CXSCREEN) + 1)
        y_calc = int(65536 * y_pos / windll.user32.GetSystemMetrics(self.SM_CYSCREEN) + 1)
        return windll.user32.mouse_event(flags, x_calc, y_calc, data, extra_info)


    def _get_button_value(self, button_name, button_up=False):
        """
        Convert the name of the button into the corresponding value.

        Args:
        - button_name (str): Name of the button.
        - button_up (bool): Whether the button is released.

        Returns:
        - int: Corresponding value of the button.
        """
        buttons = 0
        if button_name.find("right") >= 0:
            buttons = self.MOUSEEVENTF_RIGHTDOWN
        if button_name.find("left") >= 0:
            buttons = buttons + self.MOUSEEVENTF_LEFTDOWN
        if button_name.find("middle") >= 0:
            buttons = buttons + self.MOUSEEVENTF_MIDDLEDOWN
        if button_up:
            buttons = buttons << 1
        return buttons


    def move(self, pos):
        """
        Move the mouse to the specified coordinates.

        Args:
        - pos (tuple): Tuple containing X and Y coordinates.

        Returns:
        - None
        """
        (x, y) = pos
        old_pos = self.get_position()
        x = x if (x != -1) else old_pos[0]
        y = y if (y != -1) else old_pos[1]
        self._do_event(self.MOUSEEVENTF_MOVE + self.MOUSEEVENTF_ABSOLUTE, x, y, 0, 0)


    def press_button(self, pos=(-1, -1), button_name="left", button_up=False):
        """
        Push a button of the mouse.

        Args:
        - pos (tuple): Tuple containing X and Y coordinates.
        - button_name (str): Name of the button.
        - button_up (bool): Whether the button is released.

        Returns:
        - None
        """
        self.move(pos)
        self._do_event(self._get_button_value(button_name, button_up), 0, 0, 0, 0)


    def click(self, pos=(-1, -1), button_name="left"):
        """
        Click at the specified place.

        Args:
        - pos (tuple): Tuple containing X and Y coordinates.
        - button_name (str): Name of the button.

        Returns:
        - None
        """
        self.move(pos)
        self._do_event(self._get_button_value(button_name, False) + self._get_button_value(button_name, True), 0, 0, 0, 0)


    def get_position(self):
        """
        Get the mouse position.

        Returns:
        - tuple: Tuple containing X and Y coordinates of the mouse position.
        """
        point = POINT()
        windll.user32.GetCursorPos(pointer(point))
        return point.x, point.y


class POINT(Structure):
    _fields_ = [("x", c_ulong), ("y", c_ulong)]


class NotificationType(Enum):
    ERROR = "error"
    DEFAULT = "default"

    def get_color(self) -> str:
        colors = {
            self.__class__.ERROR: "red",
            self.__class__.DEFAULT: "#00aaff",
        }
        return colors.get(self, "white")

    def get_icon(self) -> QMessageBox:
        colors = {
            self.__class__.ERROR: QMessageBox.Icon.Critical,
            self.__class__.DEFAULT: QMessageBox.Icon.Information,
        }
        return colors.get(self, QMessageBox.Icon.Information)


class Notification(QMessageBox):
    def __init__(self, text: str, notification_type: NotificationType=NotificationType.DEFAULT):
        super().__init__()

        self.setIcon(notification_type.get_icon())
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setText(text)

        color = notification_type.get_color()
        self.setStyleSheet(f"""
            QMessageBox {{
                background-color: {BACKGROUND_COLOR};
                border: 2px solid {color};
            }}
            QPushButton {{
                background-color: {color};
                color: white;
                border: 1px solid {color};
                padding: 5px;
                width: 100%;
            }}
            QLabel {{
                color: {color};
                font-size: 14px;
                font-weight: bold;
            }}
        """)

class MainApp(QDialog):
    def __init__(self):
        super(MainApp, self).__init__()
        self.binder_running = False
        self.check_update()
        self.setWindowTitle('Настройки биндера')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")
        self.setup_labels_and_edits()
        self.setup_buttons()
        self.init_ui()

    def mousePressEvent(self, event):
        self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'dragPos'):
            self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos )
            self.dragPos = event.globalPosition().toPoint()
            event.accept()

    def setup_labels_and_edits(self):
        text_style = f"""
            font-weight: 600;
            font-size: 17px;
            color: {TEXT_COLOR};
        """
        line_style = f"""
            font-size: 15px;
            font-weight: 600;
            color: {TEXT_COLOR};
            background-color: {LINE_BACKGROUND_COLOR};
            border: 2px solid {BORDER_COLOR};
        """

        secret_data = load_secret_config()
        self.id_on_launch = str(secret_data.get("id", ""))
        password_edit = secret_data.get("password", "")

        self.id_label, self.password_label, self.id_edit, self.password_edit, self.footer_settings_label = (
            create_label(text="GID:", style=text_style),
            create_label(text="Пароль:", style=text_style),
            create_line(text=self.id_on_launch, style=line_style),
            create_line(text=password_edit, style=line_style),
            create_label(text="Управление настройками окон:", style=text_style),
        )

        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def setup_buttons(self):
        control_button_style = f"""
            font-weight: 600;
            font-size: 16px;
            color: {TEXT_COLOR};
            background-color: {BORDER_COLOR};
            border: 2px solid {BORDER_COLOR};
        """
        footer_button_style = f"""
            margin-top: 5px;
            font-weight: 600;
            font-size: 16px;
            color: {TEXT_COLOR};
            background-color: {BORDER_COLOR};
            border: 5px solid {BORDER_COLOR};
        """
        header_buttons_style = f"""
            width: 40px;
            background-color: {BACKGROUND_COLOR};
            border: none;
        """

        self.show_password_button = create_button(on_click_handler=self.toggle_password_visibility, text="Показать пароль")
        self.about_button, self.save_button, self.show_password_button, self.change_violation_button, self.change_pastes_button, self.change_properties_button, self.toggle_button = (
            create_button(on_click_handler=self.show_about_page, icon_name="about.svg", style=header_buttons_style),
            create_button(on_click_handler=self.save_secret_data, text="Сохранить", style=control_button_style),
            create_button(on_click_handler=self.toggle_password_visibility, text="Показать пароль", style=control_button_style),
            create_button(on_click_handler=self.show_violation_settings, text="Наказания", style=footer_button_style),
            create_button(on_click_handler=self.show_buttons_settings, text="Репорты", style=footer_button_style),
            create_button(on_click_handler=self.show_house_settings, text="Особняки", style=footer_button_style),
            create_button(on_click_handler=self.toggle_binder, text="Запустить биндер", style=footer_button_style),
        )

    def init_ui(self):
        layout = QVBoxLayout()

        control_layout = create_control_layout(self)
        control_layout.insertWidget(0, self.about_button)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        control_widget = QWidget()
        control_widget.setFixedHeight(30)
        control_widget.setStyleSheet(f"background-color: {BACKGROUND_COLOR}")
        control_widget.setLayout(control_layout)
        layout.addWidget(control_widget)

        input_row1_layout = QHBoxLayout()
        input_row1_layout.addWidget(self.id_label)
        input_row1_layout.addWidget(self.id_edit)
        input_row1_layout.addWidget(self.password_label)
        input_row1_layout.addWidget(self.password_edit)
        input_row2_layout = QHBoxLayout()
        input_row2_layout.addWidget(self.save_button)
        input_row2_layout.addWidget(self.show_password_button)
        input_layout = QVBoxLayout()
        input_layout.addLayout(input_row1_layout)
        input_layout.addLayout(input_row2_layout)
        input_widget = QWidget()
        input_widget.setFixedHeight(70)
        input_widget.setStyleSheet(f"background-color: {BACKGROUND_COLOR}")
        input_widget.setLayout(input_layout)
        layout.addWidget(input_widget)

        footer_setting_buttons_layout = QHBoxLayout()
        footer_setting_buttons_layout.addWidget(self.change_violation_button)
        footer_setting_buttons_layout.addWidget(self.change_pastes_button)
        footer_setting_buttons_layout.addWidget(self.change_properties_button)
        footer_setting_layout = QVBoxLayout()
        self.footer_settings_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footer_setting_layout.addWidget(self.footer_settings_label)
        footer_setting_layout.addLayout(footer_setting_buttons_layout)
        footer_layout = QVBoxLayout()
        footer_layout.addLayout(footer_setting_layout)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        footer_layout.addWidget(self.toggle_button)
        footer_widget = QWidget()
        footer_widget.setFixedHeight(130)
        footer_widget.setStyleSheet(f"background-color: {BACKGROUND_COLOR}")
        footer_widget.setLayout(footer_layout)
        layout.addWidget(footer_widget)

        self.setLayout(layout)

    def check_update(self):
        data = json_loads(urllib.request.urlopen("https://raw.githubusercontent.com/JudeDM/binder/main/info.json").read().decode())
        mismatched_files = [fp for fp, exp_hash in data["hashes"].items() if calculate_md5(fp) != exp_hash]
        if mismatched_files:
            updater_path = os.path.join(os.getcwd(), "..", "updater.exe")
            if not os.path.exists(updater_path):
                url = "https://github.com/JudeDM/binder/raw/main/updater.exe"
                urllib.request.urlretrieve(url, updater_path)
            subprocess.run(["taskkill", "/F", "/PID", str(os.getpid()), "&", "start", "cmd", "/c", updater_path], cwd=os.path.dirname(updater_path), shell=True)

    def toggle_password_visibility(self):
        if self.password_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_button.setText("Скрыть пароль")
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_button.setText("Показать пароль")

    def show_violation_settings(self):
        violation_settings_window = ViolationSettingsWindow(title="Кнопки для наказаний")
        violation_settings_window.exec()

    def show_buttons_settings(self):
        report_settings_window = ReportSettingsWindow(title="Кнопки для репортов")
        report_settings_window.exec()

    def show_house_settings(self):
        house_settings_window = HouseSettingsWindow(title="Телепорты к особнякам")
        house_settings_window.exec()

    def close_app(self):
        if binder:
            self.stop_binder()
        if hasattr(self, "about_page"):
            self.about_page.close()
        self.close()

    def toggle_binder(self):
        if self.binder_running:
            self.stop_binder()
        else:
            self.start_binder()

    def start_binder(self):
        if not hasattr(self, "isWarned"):
            self.isWarned = True
            secret_data = load_secret_config()
            user_id = str(secret_data.get("id", ""))
            if self.id_on_launch == user_id:
                return self.show_notification("Вы не поменяли ID после запуска биндера!\nНе забудьте его поменять, иначе можете помешать игрокам.")
        self.toggle_button.setText("Выключить биндер")
        self.toggle_button.clicked.disconnect()
        self.toggle_button.clicked.connect(self.stop_binder)
        self.binder_running = True
        global binder
        binder = Binder()
        binder.start_window()

    def stop_binder(self):
        self.toggle_button.setText("Запустить биндер")
        self.toggle_button.clicked.disconnect()
        self.toggle_button.clicked.connect(self.start_binder)
        self.binder_running = False
        if binder:
            binder.close_window()

    def show_about_page(self):
        if hasattr(self, "about_page"):
            if not self.about_page.isHidden():
                return
        self.about_page = AboutWindow()
        self.about_page.show()

    def save_secret_data(self):
        try:
            int(self.id_edit.text())
        except (ValueError, TypeError):
            return self.show_notification("ID должен быть целочисленным значением!", NotificationType.ERROR)
        data = {
            "password": self.password_edit.text(),
            "id": int(self.id_edit.text())
        }
        self.show_notification("Данные успешно сохранены!")
        save_secret_data(data)

    def show_notification(self, text: str, notification_type: NotificationType=NotificationType.DEFAULT):
        self.notification = Notification(text, notification_type)
        self.notification.show()


class GTAModal(QWidget):
    def __init__(self, modal_type: str = "punish", time = None, reason = None):
        super().__init__()
        self.modal_type = modal_type
        self.time = time
        self.reason = reason
        self.setStyleSheet("background:transparent;")
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Информация о приложении:")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedWidth(290)
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.setup_title()
        self.setup_middle()
        self.setup_footer()
        self.setLayout(self.main_layout)

    def setup_title(self):
        title_style = """
            font-family: 'Verdana';
            font-weight: 500;
            font-size: 26px;
            color: #fdfdfd
        """
        title_widget = QWidget()
        title_widget.setFixedHeight(66)
        title_widget.setStyleSheet("background-color: #1d1f23")
        title_text = create_label(text=self.modal_type, style=title_style)
        title_layout = QHBoxLayout()
        title_layout.addWidget(title_text)
        title_widget.setLayout(title_layout)
        self.main_layout.addWidget(title_widget)

    def setup_middle(self):
        text_style = f"""
            margin-top: 10px;
            font-family: 'Verdana';
            font-weight: 500;
            font-size: 14px;
            color: {TEXT_COLOR};
        """
        line_style = """
            padding-left: 10px;
            height: 39px;
            font-family: 'Verdana';
            font-size: 16px;
            color: #6a6f75;
            background-color: #15181b;
            border: 2px solid #84491e;
        """
        middle_layout = QVBoxLayout()
        if self.modal_type in ["prison", "mute", "ban"]:
            gid_label, time_label, reason_label, self.gid_edit, self.time_edit, self.reason_edit = (
                create_label(text="ID:", style=text_style),
                create_label(text="Время:", style=text_style),
                create_label(text="Причина:", style=text_style),
                create_line(style=line_style),
                create_line(text=self.time, style=line_style),
                create_line(text=self.reason, style=line_style),
            )

            middle_layout.addWidget(gid_label)
            middle_layout.addWidget(self.gid_edit)
            middle_layout.addWidget(time_label)
            middle_layout.addWidget(self.time_edit)
            middle_layout.addWidget(reason_label)
            middle_layout.addWidget(self.reason_edit)

        elif self.modal_type == "car_sync":
            car_gid_label, self.car_gid_edit = (
                create_label(text="Car GID:", style=text_style),
                create_line(style=line_style),
            )

            middle_layout.addWidget(car_gid_label)
            middle_layout.addWidget(self.car_gid_edit)

        elif self.modal_type == "uncuff":
            gid_label, self.gid_edit, reason_label, self.reason_edit = (
                create_label(text="GID:", style=text_style),
                create_line(style=line_style),
                create_label(text="Причина:", style=text_style),
                create_line(text=self.reason, style=line_style),
            )

            middle_layout.addWidget(gid_label)
            middle_layout.addWidget(self.gid_edit)
            middle_layout.addWidget(reason_label)
            middle_layout.addWidget(self.reason_edit)

        elif self.modal_type == "uo_delete":
            uo_id_label, self.uo_id_edit = (
                create_label(text="UO ID:", style=text_style),
                create_line(style=line_style),
            )

            middle_layout.addWidget(uo_id_label)
            middle_layout.addWidget(self.uo_id_edit)

        middle_widget = QWidget()
        middle_widget.setStyleSheet("background-color: #1b1e22")
        middle_widget.setLayout(middle_layout)
        self.main_layout.addWidget(middle_widget)

    def setup_footer(self):
        send_button_style = f"""
            font-family: 'Verdana';
            font-weight: 600;
            font-size: 15px;
            color: {TEXT_COLOR};
            background-color: #f0233c;
        """
        cancel_button_style = f"""
            font-family: 'Verdana';
            font-weight: 600;
            font-size: 15px;
            color: {TEXT_COLOR};
            background-color: #2f3843
        """
        footer_widget = QWidget()
        footer_widget.setFixedHeight(66)
        footer_widget.setStyleSheet("background-color: #1e2327")
        footer_layout = QHBoxLayout()
        if self.modal_type in ["prison", "mute", "ban"]:
            send_button = create_button(on_click_handler=self.punish_user, text="Отправить", style=send_button_style)
        elif self.modal_type == "car_sync":
            send_button = create_button(on_click_handler=self.car_sync, text="Отправить", style=send_button_style)
        elif self.modal_type == "uncuff":
            send_button = create_button(on_click_handler=self.uncuff, text="Отправить", style=send_button_style)
        elif self.modal_type == "uo_delete":
            send_button = create_button(on_click_handler=self.uo_delete, text="Отправить", style=send_button_style)
        else:
            send_button = create_button(on_click_handler=self.close, text="Отправить", style=send_button_style)
        cancel_button = create_button(on_click_handler=self.close, text="Отмена", style=cancel_button_style)
        send_button.setFixedSize(130, 37)
        cancel_button.setFixedSize(110, 37)
        footer_layout.addWidget(send_button)
        footer_layout.addWidget(cancel_button)
        footer_widget.setLayout(footer_layout)
        self.main_layout.addWidget(footer_widget)

    def punish_user(self):
        try:
            int(self.gid_edit.text())
        except (ValueError, TypeError):
            return self.show_notification("ID должен быть целочисленным значением!", NotificationType.ERROR)
        gid = self.gid_edit.text()
        time = self.time_edit.text()
        reason = self.reason_edit.text()
        paste_to_console(f"{self.modal_type} {gid} {time} {reason}")
        self.close()

    def uncuff(self):
        try:
            int(self.gid_edit.text())
        except (ValueError, TypeError):
            return self.show_notification("ID должен быть целочисленным значением!", NotificationType.ERROR)
        gid = self.gid_edit.text()
        reason = self.reason_edit.text()
        paste_to_console(f"{self.modal_type} {gid} {reason}")
        self.close()

    def uo_delete(self):
        try:
            int(self.uo_id_edit.text())
        except (ValueError, TypeError):
            return self.show_notification("ID должен быть целочисленным значением!", NotificationType.ERROR)
        uo_id = self.uo_id_edit.text()
        paste_to_console(f"{self.modal_type} {uo_id}")
        self.close()

    def car_sync(self):
        user_gid = load_secret_config().get('id', '')
        car_gid = self.car_gid_edit.text()
        actions = [
            f"dimension {user_gid} 1",
            f"tpcar {car_gid}",
            f"veh_repair {car_gid}",
            f"dimension {user_gid} 0",
            f"tpcar {car_gid}"
        ]
        for action in actions:
            paste_to_console(action)
            sleep(2.5)
        self.close()

    def show_notification(self, text: str, notification_type: NotificationType=NotificationType.DEFAULT):
        self.notification = Notification(text, notification_type)
        self.notification.show()


class AboutWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.text_style = f"""
            font-weight: 600;
            font-size: 15px;
            color: {TEXT_COLOR};
        """
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Информация о приложении")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")
        self.main_layout = QVBoxLayout(self)
        control_layout = create_control_layout(self)
        self.main_layout.addLayout(control_layout)
        self.init_about_area()
        self.init_footer()

    def init_about_area(self):
        title_style = f"""
            font-weight: 700;
            font-size: 17px;
            color: {TEXT_COLOR};
        """
        text_area = QVBoxLayout()
        title = create_label(text="Основная информация:", style=title_style)
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        text = "F8 - Автологин.\n\nБиндер для GTA 5 RP, обеспечивающий администраторам удобство в модерировании.\nПросьба сообщать о возникающих проблемах через контактные данные, указанные ниже."
        about = create_label(text=text, style=self.text_style)
        text_area.addWidget(title)
        text_area.addWidget(about)
        self.main_layout.addLayout(text_area)

    def init_footer(self):
        button_style = f"""
            height: 40px;
            background-color:{BACKGROUND_COLOR};
            border: none;
        """
        footer_layout = QVBoxLayout()
        developer_label = create_label(text="Разработано: JudeDM (Dmitriy Win)", style=self.text_style)
        footer_layout.addWidget(developer_label)

        footer_icons_layout = QHBoxLayout()
        github_button = create_button(on_click_handler=self.open_github, icon_name='github.svg', style=button_style)
        discord_button = create_button(on_click_handler=self.open_discord, icon_name='discord.svg', style=button_style)

        footer_icons_layout.addWidget(github_button)
        footer_icons_layout.addWidget(discord_button)
        footer_layout.addLayout(footer_icons_layout)
        self.main_layout.addLayout(footer_layout)

    def open_github(self):
        webbrowser_open("https://github.com/JudeDM/binder/tree/main")

    def open_discord(self):
        webbrowser_open("discord://-/users/208575718093750276")

    def mousePressEvent(self, event):
        self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos )
        self.dragPos = event.globalPosition().toPoint()
        event.accept()


class SettingsWindow(QDialog):
    def __init__(self, title: str, settings_type: str, calling_instance):
        super().__init__()
        self.setStyleSheet(f"""
            QScrollBar:horizontal
            {{
                height: 15px;
                margin: 3px 15px 3px 15px;
                border: 1px transparent #2A2929;
                border-radius: 4px;
                background-color: {BORDER_COLOR};
            }}

            QScrollBar::handle:horizontal
            {{
                background-color: {BORDER_COLOR};
                min-width: 5px;
                border-radius: 4px;
            }}

            QScrollBar::add-line:horizontal
            {{
                margin: 0px 3px 0px 3px;
                border-image: url(:/qss_icons/rc/right_arrow_disabled.png);
                width: 10px;
                height: 10px;
                subcontrol-position: right;
                subcontrol-origin: margin;
            }}

            QScrollBar::sub-line:horizontal
            {{
                margin: 0px 3px 0px 3px;
                border-image: url(:/qss_icons/rc/left_arrow_disabled.png);
                height: 10px;
                width: 10px;
                subcontrol-position: left;
                subcontrol-origin: margin;
            }}

            QScrollBar::add-line:horizontal:hover,QScrollBar::add-line:horizontal:on
            {{
                border-image: url(:/qss_icons/rc/right_arrow.png);
                height: 10px;
                width: 10px;
                subcontrol-position: right;
                subcontrol-origin: margin;
            }}


            QScrollBar::sub-line:horizontal:hover, QScrollBar::sub-line:horizontal:on
            {{
                border-image: url(:/qss_icons/rc/left_arrow.png);
                height: 10px;
                width: 10px;
                subcontrol-position: left;
                subcontrol-origin: margin;
            }}

            QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal
            {{
                background: none;
            }}

            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal
            {{
                background: none;
            }}

            QPushButton
            {{
                font-weight: bold;
                font-size: 16px;
                color: {TEXT_COLOR};
                background-color: {BORDER_COLOR};
                border: 4px solid {BORDER_COLOR};
            }}
        """)
        palette = self.palette()
        palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Window, QColor(BACKGROUND_COLOR))
        self.setPalette(palette)

        self.config = []
        self.calling_instance = calling_instance
        self.settings_type = settings_type
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(1200, 470)
        self.main_layout = QVBoxLayout(self)
        control_layout = create_control_layout(self)
        self.main_layout.addLayout(control_layout)
        control_panel_layout = QHBoxLayout()
        add_column_button = create_button(on_click_handler=self.add_item, text="Добавить кнопку")
        save_button = create_button(on_click_handler=self.save_config, text="Сохранить")
        control_panel_layout.addWidget(add_column_button)
        control_panel_layout.addWidget(save_button)

        if settings_type == "house":
            self.config = [item for sublist in load_house_button_config() for item in sublist]
        elif settings_type == "report":
            self.config = [item for sublist in load_report_button_config() for item in sublist]
        elif settings_type == "violation":
            self.config = [item for sublist in load_violation_button_config() for item in sublist]

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.horizontal_scrollbar = QScrollBar(Qt.Orientation.Horizontal)
        scroll_area.setHorizontalScrollBar(self.horizontal_scrollbar)
        self.main_layout.addWidget(scroll_area)

        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")

        self.main_scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setMaximumWidth(1200)

        self.main_layout.addLayout(control_panel_layout)


    def mousePressEvent(self, event):
        self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos )
        self.dragPos = event.globalPosition().toPoint()
        event.accept()

    def add_item(self):
        if len(self.config) >= MAX_COLS * 10:
            return

        new_item = {"name": ""}
        if self.settings_type == "report":
            new_item["text"] = ""
        elif self.settings_type == "violation":
            new_item.update({"time": "", "reason": "", "type": "prison"})

        self.config.append(new_item)
        self.calling_instance.update_layout()


    def remove_item(self, item_index):
        del self.config[item_index]
        self.calling_instance.update_layout()


    def move_item(self, index, action):
        lst = self.config
        if action == 'down' and index < len(lst) - 1:
            lst[index], lst[index + 1] = lst[index + 1], lst[index]
        elif action == 'up' and index > 0:
            lst[index], lst[index - 1] = lst[index - 1], lst[index]
        self.calling_instance.update_layout()


    @classmethod
    def clear_layout(cls, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()

            if widget:
                widget.setParent(None)
            else:
                cls.clear_layout(item.layout())


    def item_control_buttons(self, item_index):
        button_style = """
            min-height: 30px;
            min-width: 30px;
            border: none;
        """
        item_control_buttons = QHBoxLayout()

        delete_button, moveup_button, movedown_button = (
            create_button(on_click_handler=lambda: self.remove_item(item_index), icon_name="delete.svg", style=button_style),
            create_button(on_click_handler=lambda: self.move_item(item_index, "up"), icon_name="arrow_up.svg", style=button_style),
            create_button(on_click_handler=lambda: self.move_item(item_index, "down"), icon_name="arrow_down.svg", style=button_style),
        )
        delete_button.setFixedWidth(20)
        moveup_button.setFixedWidth(20)
        movedown_button.setFixedWidth(20)
        item_control_buttons.addWidget(delete_button)
        item_control_buttons.addWidget(moveup_button)
        item_control_buttons.addWidget(movedown_button)
        item_control_buttons.setSpacing(3)
        return item_control_buttons


    def save_config(self):
        self.show_notification("Конфиг успешно сохранён.")
        if self.settings_type == "house":
            save_house_button_config([self.config[i:i+10] for i in range(0, len(self.config), 10)])
        elif self.settings_type == "report":
            save_report_button_config([self.config[i:i+10] for i in range(0, len(self.config), 10)])
        elif self.settings_type == "violation":
            save_violation_button_config([self.config[i:i+10] for i in range(0, len(self.config), 10)])
        self.accept()


    def show_notification(self, text: str, notification_type: NotificationType=NotificationType.DEFAULT):
        self.notification = Notification(text, notification_type)
        self.notification.show()


class ViolationSettingsWindow(SettingsWindow):
    def __init__(self, title):
        super().__init__(title=title, settings_type="violation", calling_instance=self)
        self.update_layout()


    def update_layout(self):
        current_scroll_position = self.horizontal_scrollbar.value()
        if hasattr(self, 'violation_manager_layout'):
            self.clear_layout(self.violation_manager_layout)


        self.violation_manager_layout = QHBoxLayout()
        for group_index, violation_group in enumerate([self.config[i:i+10] for i in range(0, len(self.config), 10)]):
            self.create_violation_group_layout(violation_group, group_index)


        self.main_scroll_layout.addLayout(self.violation_manager_layout)
        self.horizontal_scrollbar.setValue(current_scroll_position)


    def create_violation_group_layout(self, violation_group, group_index):
        short_style = f"""
            min-width: 100px;
            max-width: 100px;
            font-size: 14px;
            font-weight: 500;
            color: {TEXT_COLOR};
            background-color: {LINE_BACKGROUND_COLOR};
            border: 2px solid {BORDER_COLOR};
        """
        long_style = f"""
            min-width: 300px;
            max-width: 300px;
            font-size: 14px;
            font-weight: 500;
            color: {TEXT_COLOR};
            background-color: {LINE_BACKGROUND_COLOR};
            border: 2px solid {BORDER_COLOR};
        """

        group_layout = QVBoxLayout()
        group_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        for index, violation in enumerate(violation_group):
            violation_index = group_index * 10 + index
            row = QHBoxLayout()
            form_layout = QFormLayout()
            type_edit = QComboBox()
            type_edit.addItems(['prison', 'mute', 'ban'])
            type_edit.setStyleSheet(short_style)
            type_edit.setCurrentText(violation["type"] if "type" in violation else None)
            type_edit.activated.connect(lambda index, type_edit=type_edit, violation_index=violation_index: self.update_violation_field(violation_index, "type", type_edit.currentText()))
            name_edit = create_line(text=violation["name"], style=short_style)
            name_edit.textChanged.connect(lambda text, index=violation_index: self.update_violation_field(index, "name", text))
            time_edit = create_line(text=violation["time"], style=short_style)
            time_edit.textChanged.connect(lambda text, index=violation_index: self.update_violation_field(index, "time", text))
            reason_edit = create_line(text=violation["reason"], style=long_style)
            reason_edit.textChanged.connect(lambda text, index=violation_index: self.update_violation_field(index, "reason", text))
            row.addWidget(type_edit)
            row.addWidget(name_edit)
            row.addWidget(time_edit)
            row.addWidget(reason_edit)
            row.addLayout(self.item_control_buttons(violation_index))
            form_layout.addRow(row)
            group_layout.addLayout(form_layout)
        self.violation_manager_layout.addLayout(group_layout)


    def update_violation_field(self, item_index, field, new_name):
        self.config[item_index][field] = new_name


class ReportSettingsWindow(SettingsWindow):
    def __init__(self, title):
        super().__init__(title=title, settings_type="report", calling_instance=self)
        self.update_layout()


    def update_layout(self):
        current_scroll_position = self.horizontal_scrollbar.value()
        if hasattr(self, 'report_manager_layout'):
            self.clear_layout(self.report_manager_layout)


        self.report_manager_layout = QHBoxLayout()
        for group_index, report_group in enumerate([self.config[i:i+10] for i in range(0, len(self.config), 10)]):
            self.create_report_group_layout(report_group, group_index)


        self.main_scroll_layout.addLayout(self.report_manager_layout)
        self.horizontal_scrollbar.setValue(current_scroll_position)

    def create_report_group_layout(self, report_group, group_index):
        name_style = f"""
            min-width: 140px;
            font-size: 14px;
            font-weight: 500;
            color: {TEXT_COLOR};
            background-color: {LINE_BACKGROUND_COLOR};
            border: 2px solid {BORDER_COLOR};
        """
        text_style = f"""
            min-width: 300px;
            font-size: 14px;
            font-weight: 500;
            color: {TEXT_COLOR};
            background-color: {LINE_BACKGROUND_COLOR};
            border: 2px solid {BORDER_COLOR};
        """
        group_layout = QVBoxLayout()
        group_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for index, report in enumerate(report_group):
            report_index = group_index * 10 + index
            row = QHBoxLayout()
            form_layout = QFormLayout()
            name_edit = QLineEdit(text=report["name"])
            name_edit.textChanged.connect(lambda text, index=report_index: self.update_report_field(index, "name", text))
            text_edit = QLineEdit(text=report["text"])
            text_edit.textChanged.connect(lambda text, index=report_index: self.update_report_field(index, "text", text))
            name_edit.setStyleSheet(name_style)
            text_edit.setStyleSheet(text_style)
            row.addWidget(name_edit)
            row.addWidget(text_edit)
            row.addLayout(self.item_control_buttons(report_index))
            form_layout.addRow(row)
            group_layout.addLayout(form_layout)
        self.report_manager_layout.addLayout(group_layout)

    def update_report_field(self, item_index, field, new_name):
        self.config[item_index][field] = new_name


class HouseSettingsWindow(SettingsWindow):
    def __init__(self, title):
        super().__init__(title=title, settings_type="house", calling_instance=self)
        self.update_layout()

    def update_layout(self):
        current_scroll_position = self.horizontal_scrollbar.value()
        if hasattr(self, 'house_manager_layout'):
            self.clear_layout(self.house_manager_layout)

        self.house_manager_layout = QHBoxLayout()
        for group_index, house_group in enumerate([self.config[i:i+10] for i in range(0, len(self.config), 10)]):
            self.create_house_group_layout(house_group, group_index)

        self.main_scroll_layout.insertLayout(0, self.house_manager_layout)
        self.horizontal_scrollbar.setValue(current_scroll_position)


    def create_house_group_layout(self, house_group, group_index):
        name_style = f"""
            min-width: 140px;
            font-size: 14px;
            font-weight: 500;
            color: {TEXT_COLOR};
            background-color: {LINE_BACKGROUND_COLOR};
            border: 2px solid {BORDER_COLOR};
        """
        group_layout = QVBoxLayout()
        group_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for index, house in enumerate(house_group):
            house_index = group_index * 10 + index
            form_layout = QFormLayout()
            name_edit = QLineEdit(text=house["name"])
            name_edit.textChanged.connect(lambda text, index=house_index: self.update_house_name(index, text))
            name_edit.setStyleSheet(name_style)
            form_layout.addRow(name_edit, self.item_control_buttons(house_index))
            group_layout.addLayout(form_layout)

        self.house_manager_layout.addLayout(group_layout)

    def update_house_name(self, item_index, new_name):
        self.config[item_index]['name'] = new_name


class Binder(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(WINDOW_WIDTH-1000, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.violation_buttons, self.buttons, self.house_buttons, self.report_labels = {}, {}, {}, []
        self.is_violation_ui, self.is_report_ui, self.is_teleport_ui, self.is_additional_ui = False, False, False, False
        self.init_ui()
        timer = QTimer(self, timeout=self.update_buttons)
        timer.start(100)


    def init_violations_ui(self):
        self.violation_buttons_layout = QGridLayout()
        self.violation_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.violation_buttons_layout.setHorizontalSpacing(10)
        self.violation_buttons_layout.setVerticalSpacing(5)
        violation_config = load_violation_button_config()
        for col, col_config in enumerate(violation_config):
            if col >= MAX_COLS:
                continue
            for row, button_config in enumerate(col_config):
                button_number = row * len(violation_config) + col + 1
                button = create_button(on_click_handler=self.handle_punish_button_click, text=button_config['name'], style=admin_button_stylesheet())
                self.violation_buttons[button_number] = (button, button_config['type'], button_config['time'], button_config['reason'])
                self.violation_buttons_layout.addWidget(button, row, col)
        self.main_layout.insertLayout(0, self.violation_buttons_layout)


    def init_reports_ui(self):
        self.report_buttons_layout = QGridLayout()
        self.report_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.report_buttons_layout.setHorizontalSpacing(10)
        self.report_buttons_layout.setVerticalSpacing(5)
        button_configs = load_report_button_config()
        for col, col_config in enumerate(button_configs):
            if col >= MAX_COLS:
                continue
            for row, button_config in enumerate(col_config):
                button_number = row * len(button_configs) + col + 1
                button = create_button(on_click_handler=self.handle_report_button_click, text=button_config['name'], style=admin_button_stylesheet())
                self.buttons[button_number] = (button, button_config['text'])
                self.report_buttons_layout.addWidget(button, row, col)
        self.main_layout.insertLayout(0, self.report_buttons_layout)


    def init_house_ui(self):
        self.house_layout = QGridLayout()
        self.house_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.house_layout.setHorizontalSpacing(10)
        self.house_layout.setVerticalSpacing(5)
        house_button_configs = load_house_button_config()

        def teleport_closure(name):
            return lambda: self.teleport_to_house(name)

        for col, col_config in enumerate(house_button_configs):
            if col >= MAX_COLS:
                continue
            for row, house_button_config in enumerate(col_config):
                button_number = row * len(house_button_configs) + col + 1
                name = house_button_config['name']

                button = create_button(on_click_handler=teleport_closure(name), text=name, style=admin_button_stylesheet())
                self.house_buttons[button_number] = (button, name)
                self.house_layout.addWidget(button, row, col)

        self.main_layout.insertLayout(0, self.house_layout)


    def init_additional_ui(self):
        self.additional_layout = QVBoxLayout()
        self.additional_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.additional_layout.setContentsMargins(0, 31, 0 ,0)
        self.init_reports_counter()
        self.init_sync_buttons()
        self.main_layout.addLayout(self.additional_layout)


    def init_reports_counter(self):
        self.reports_counter = QVBoxLayout()
        self.reports_counter.setSpacing(5)
        title = create_label(text="Статистика:", style=admin_button_stylesheet())
        title.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.reports_counter.addWidget(title)
        labels = ["За день:", "За неделю:", "За месяц:"]

        for label_text in labels:
            label = create_label(text=label_text, style=admin_button_stylesheet())
            label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            self.reports_counter.addWidget(label)
            self.report_labels.append(label)

        self.additional_layout.addLayout(self.reports_counter)
        self.update_report_labels()


    def init_sync_buttons(self):
        # mute_button = create_button(on_click_handler=lambda: self.handle_punish_button_click("mute"), text="mute", style=admin_button_stylesheet())
        # prison_button = create_button(on_click_handler=lambda: self.handle_punish_button_click("prison"), text="prison", style=admin_button_stylesheet())
        # ban_button = create_button(on_click_handler=lambda: self.handle_punish_button_click("ban"), text="ban", style=admin_button_stylesheet())
        uncuff_button = create_button(on_click_handler=self.handle_uncuff_button_click, text="uncuff", style=admin_button_stylesheet())
        dimension_sync_button = create_button(on_click_handler=self.handle_sync_button_click, text="dimension_sync", style=admin_button_stylesheet())
        car_sync_button = create_button(on_click_handler=self.handle_car_sync_button_click, text="car_sync", style=admin_button_stylesheet())
        # uo_delete_button = create_button(on_click_handler=self.handle_uo_delete_button_click, text="uo_delete", style=admin_button_stylesheet())
        reof_button = create_button(on_click_handler=self.handle_reof_button_click, text="reof", style=admin_button_stylesheet())
        buttons_box = QHBoxLayout()
        buttons_box_col1 = QVBoxLayout()
        buttons_box_col2 = QVBoxLayout()
        # buttons_box_col1.addWidget(mute_button)
        # buttons_box_col1.addWidget(prison_button)
        # buttons_box_col1.addWidget(ban_button)
        buttons_box_col1.addWidget(dimension_sync_button)
        buttons_box_col1.addWidget(car_sync_button)
        buttons_box_col1.addWidget(uncuff_button)
        # buttons_box_col1.addWidget(uo_delete_button)
        buttons_box_col1.addWidget(reof_button)
        buttons_box_col1.setContentsMargins(0, 0, 4 ,0)
        buttons_box.addLayout(buttons_box_col1)
        buttons_box.addLayout(buttons_box_col2)
        self.additional_layout.addLayout(buttons_box)


    def init_ui(self):
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)


    def handle_uncuff_button_click(self):
        if hasattr(self, "gta_modal"):
            if not self.gta_modal.isHidden():
                return
        self.gta_modal = GTAModal(modal_type="uncuff", reason="Поблизости никого нет")
        self.gta_modal.show()


    def handle_uo_delete_button_click(self):
        if hasattr(self, "gta_modal"):
            if not self.gta_modal.isHidden():
                return
        self.gta_modal = GTAModal(modal_type="uo_delete")
        self.gta_modal.show()


    def handle_punish_button_click(self, punish_type: str | None = None):
        if punish_type:
            self.modal = GTAModal(modal_type=punish_type)
            return self.modal.show()
        for button, button_punish_type, time, reason in self.violation_buttons.values():
            if button is self.sender():
                if hasattr(self, "gta_modal"):
                    if not self.gta_modal.isHidden():
                        return
                self.modal = GTAModal(modal_type=button_punish_type, time=time, reason=reason)
                return self.modal.show()


    def handle_report_button_click(self, text_to_copy=None):
        text_to_copy = text_to_copy or next(text for button, text in self.buttons.values() if button is self.sender())
        position = mouse.get_position()
        now = datetime.now()
        start_date = datetime(now.year, 4, 1, 7)
        end_date = datetime(now.year, 4, 2, 7)
        mouse.click((LEFT+245, (TOP+345 if start_date <= now < end_date else TOP+330)))
        pyperclip.copy(text_to_copy)
        send('ctrl+v')
        send('enter')
        mouse.move(position)
        self.update_click_data()


    def handle_car_sync_button_click(self):
        if hasattr(self, "car_sync_modal"):
            if not self.car_sync_modal.isHidden():
                return
        self.car_sync_modal = GTAModal(modal_type="car_sync")
        self.car_sync_modal.show()


    def handle_sync_button_click(self):
        position = mouse.get_position()
        paste_to_console(f"dimension_sync {load_secret_config().get('id', '')}")
        mouse.click((LEFT+185, TOP+365))
        mouse.move(position)


    def handle_reof_button_click(self):
        position = mouse.get_position()
        paste_to_console("reof")
        mouse.click((LEFT+185, TOP+365))
        mouse.move(position)


    @classmethod
    def clear_layout(cls, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                else:
                    cls.clear_layout(item.layout())


    def update_report_labels(self):
        today_date = datetime.now().strftime(DATE_FORMAT)
        week_ago_date = (datetime.now() - timedelta(days=datetime.now().weekday() + 1)).strftime(DATE_FORMAT)
        month_ago_date = (datetime.now() - timedelta(days=30)).strftime(DATE_FORMAT)
        report_data = load_click_data()
        daily_reports = report_data.get(today_date, 0)
        week_ago_date_dt = datetime.strptime(week_ago_date, DATE_FORMAT)
        today_date_dt = datetime.strptime(today_date, DATE_FORMAT)
        month_ago_date_dt = datetime.strptime(month_ago_date, DATE_FORMAT)
        weekly_reports = sum(report_data[date] for date in report_data if week_ago_date_dt <= datetime.strptime(date, DATE_FORMAT) <= today_date_dt)
        monthly_reports = sum(report_data[date] for date in report_data if month_ago_date_dt <= datetime.strptime(date, DATE_FORMAT) <= today_date_dt)
        for label, count in zip(self.report_labels[-3:], [daily_reports, weekly_reports, monthly_reports]):
            label.setText(f"{label.text()[:label.text().index(':')]}: {count}")


    def remove_report_buttons(self):
        if hasattr(self, 'report_buttons_widget'):
            item = self.main_layout.itemAt(self.main_layout.indexOf(self.report_buttons_widget))
            if item is not None:
                self.report_buttons_widget.deleteLater()
                self.main_layout.removeItem(item)
                del self.report_buttons_widget


    def teleport_to_house(self, name):
        house_number = name.split('.')[0]
        paste_to_console(f"family_house_info {house_number}")
        sleep(0.1)
        mouse.click(TELEPORT_TO_HOUSE)


    def update_buttons(self):
        if self.x() != LEFT+1000 or self.y() != TOP+4:
            self.setFixedSize(WINDOW_WIDTH-1000, 400)
            self.move(LEFT+1000, TOP+4)
        is_console_open = all(is_within_range(get_pixel_color(*coord), color) for coord, color in pixel_conditions["should_show_violation_buttons"].items())
        is_report_open = all(is_within_range(get_pixel_color(*coord), color) for coord, color in pixel_conditions["should_show_buttons"].items())
        is_teleport_open = all(is_within_range(get_pixel_color(*coord), color) for coord, color in pixel_conditions["should_show_teleport_buttons"].items())
        is_panel_open = all(is_within_range(get_pixel_color(*coord), color) for coord, color in pixel_conditions["should_show_control_buttons"].items())

        if is_console_open and not self.is_violation_ui:
            self.is_violation_ui = True
            self.init_violations_ui()
        elif not is_console_open and self.is_violation_ui:
            self.is_violation_ui = False
            self.clear_layout(self.violation_buttons_layout)

        if is_report_open and not self.is_report_ui:
            self.is_report_ui = True
            self.init_reports_ui()
        elif not is_report_open and self.is_report_ui:
            self.is_report_ui = False
            self.clear_layout(self.report_buttons_layout)

        if is_teleport_open and not self.is_teleport_ui:
            self.is_teleport_ui = True
            self.init_house_ui()
        elif not is_teleport_open and self.is_teleport_ui:
            self.is_teleport_ui = False
            self.clear_layout(self.house_layout)

        if is_panel_open and not self.is_additional_ui:
            self.is_additional_ui = True
            self.init_additional_ui()
        elif not is_panel_open and self.is_additional_ui:
            self.is_additional_ui = False
            self.clear_layout(self.additional_layout)


    def start_window(self):
        self.show()


    def close_window(self):
        self.destroy()


    def update_click_data(self):
        today_date = datetime.now().strftime(DATE_FORMAT)
        click_data = load_click_data()
        click_data[today_date] = click_data.get(today_date, 0) + 1
        save_click_data(click_data)
        self.update_report_labels()

def create_control_layout(instance):
    control_buttons_style = f"width: 40px; background-color: {BACKGROUND_COLOR}; border: none;"

    control_layout = QHBoxLayout()
    minimize_button = create_button(on_click_handler=instance.showMinimized, icon_name='minimize.svg', style=control_buttons_style)
    close_button = create_button(on_click_handler=instance.close_app if isinstance(instance, MainApp) else instance.close, icon_name='delete.svg', style=control_buttons_style)

    control_layout.addWidget(minimize_button)
    control_layout.addWidget(close_button)
    control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
    return control_layout

def create_line(text=None, style=None):
    """
    Create a QLineEdit with specified properties.

    Args:
        text (int | str, optional): Text to display on the line.
        style (str, optional): Custom stylesheet for the label.

    Returns:
        QLineEdit: Created button object.
    """
    line = QLineEdit()
    if text:
        line.setText(str(text))
    if style:
        line.setStyleSheet(style)
    return line

def create_label(text=None, style=None):
    """
    Create a QLabel with specified properties.

    Args:
        text (str, optional): Text to display on the label.
        style (str, optional): Custom stylesheet for the label.

    Returns:
        QLabel: Created button object.
    """
    label = QLabel()
    if text:
        label.setText(text)
    if style:
        label.setStyleSheet(style)
    return label

def create_button(on_click_handler=None, text=None, icon_name=None, style=None):
    """
    Create a QPushButton with specified properties.

    Args:
        on_click_handler (callable, optional): Function to call when the button is clicked.
        text (str, optional): Text to display on the button.
        icon_name (str, optional): Icon name to display on the button.
        style (str, optional): Custom stylesheet for the button.

    Returns:
        QPushButton: Created button object.
    """
    button = QPushButton()
    if text:
        button.setText(text)
    if on_click_handler:
        button.clicked.connect(on_click_handler)
    if icon_name:
        button.setIcon(QIcon("data/icons/" + icon_name))
    if style:
        button.setStyleSheet(style)
    return button


def is_within_range(color1: tuple, color2: tuple, tolerance=5) -> bool:
    return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))


def paste_to_console(text: str):
    mouse.click((LEFT+55, TOP+375))
    sleep(0.1)
    mouse.click((LEFT+500, TOP+335))
    send('ctrl+a, backspace')
    pyperclip.copy(text)
    send('ctrl+v')
    send('enter')


# def get_local_version():
#     return json_load(open(VERSION_FILE, "r", encoding="utf-8"))["version"] if os.path.exists(VERSION_FILE) else {}


def admin_button_stylesheet():
    return """
    QPushButton {
        border-radius: 0px;
        background-color: #555555;
        color: #ffffff;
        font-weight: 450;
        font-family: "Columbia";
        font-size: 13px;
        width: 153px;
        height: 33px;
    }

    QPushButton:hover {
        background-color: #666666;
    }

    QLabel {
        color: #ffffff;
        font-family: "Arial";
        font-size: 20px;
    }"""


def load_click_data():
    return json_load(open(CLICK_DATA_FILE, "r", encoding="utf-8")) if os.path.exists(CLICK_DATA_FILE) else {}


def save_click_data(click_data):
    with open(CLICK_DATA_FILE, "w", encoding="utf8") as f:
        json_dump(click_data, f, indent=4)


def load_violation_button_config():
    return json_load(open(BUTTON_VIOLATION_CONFIG_FILE, "r", encoding="utf-8")) if os.path.exists(BUTTON_VIOLATION_CONFIG_FILE) else {}


def save_violation_button_config(data):
    with open(BUTTON_VIOLATION_CONFIG_FILE, 'w', encoding="utf-8") as json_file:
        json_dump(data, json_file, indent=4, ensure_ascii=False)


def load_report_button_config():
    return json_load(open(BUTTON_REPORT_CONFIG_FILE, "r", encoding="utf-8")) if os.path.exists(BUTTON_REPORT_CONFIG_FILE) else {}


def save_report_button_config(data):
    with open(BUTTON_REPORT_CONFIG_FILE, 'w', encoding="utf-8") as json_file:
        json_dump(data, json_file, indent=4, ensure_ascii=False)


def load_secret_config():
    return json_load(open(SECRET_FILE, "r", encoding="utf-8")) if os.path.exists(SECRET_FILE) else {}


def save_secret_data(data):
    with open(SECRET_FILE, 'w', encoding="utf8") as json_file:
        json_dump(data, json_file, indent=4)


def load_house_button_config():
    return json_load(open(BUTTON_HOUSE_CONFIG_FILE, "r", encoding="utf-8")) if os.path.exists(BUTTON_HOUSE_CONFIG_FILE) else {}


def save_house_button_config(data):
    with open(BUTTON_HOUSE_CONFIG_FILE, 'w', encoding="utf-8") as json_file:
        json_dump(data, json_file, indent=4, ensure_ascii=False)


def get_pixel_color(x: int, y: int) -> tuple:
    hdc = user32.GetDC(0)
    pixel = windll.gdi32.GetPixel(hdc, x + LEFT, y + TOP)
    user32.ReleaseDC(0, hdc)

    red = pixel & 0xFF
    green = (pixel >> 8) & 0xFF
    blue = (pixel >> 16) & 0xFF

    return red, green, blue


def get_monitor_coordinates():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def change_to_english_layout(layout_id=0x04090409):
    window_handle = user32.GetForegroundWindow()
    user32.SendMessageW(window_handle, 0x0050, 0, cast(layout_id, c_void_p))


def get_process(process_name: str) -> tuple[int, int] | None:
    """
    Get the window handle and process ID of the first window with the given process name.

    Args:
        process_name (str): The name of the process.

    Returns:
        tuple[int, int] | None: A tuple containing the window handle (int) and process ID (int) of the first matching window,
            or None if no matching window is found.
    """
    return next(((hwnd, pid) for hwnd, pid in get_process_handles() if process_name == get_process_name(pid)), None)

def get_process_handles() -> list[tuple[int, int]]:
    """
    Get handles of all windows and their corresponding process IDs.

    Returns:
        list[tuple[int, int]]: A list of tuples, where each tuple contains a window handle
            (int) and the process ID (int) of the window.
    """
    handles = []
    try:
        def enum_windows_callback(hwnd: int, _: int) -> bool:
            process_id = c_ulong()
            result = user32.GetWindowThreadProcessId(hwnd, byref(process_id))
            if result is not None:
                handles.append((hwnd, process_id.value))
            return True

        EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
    except Exception:
        handles = []
    return handles

def get_window_coordinates(hwnd: int) -> tuple[int, int, int, int] | None:
    """
    Get the window coordinates of the given window handle.

    Args:
        hwnd (int): The window handle.

    Returns:
        tuple[int, int, int, int] | None: The left, top, right, and bottom coordinates of the window,
            or None if the window handle is invalid.
    """
    rect = wintypes.RECT()
    try:
        result = user32.GetWindowRect(hwnd, byref(rect))
        if not result:
            return None
    except Exception:
        return None
    return rect.left, rect.top, rect.right, rect.bottom

def calculate_md5(file_path: str) -> str | None:
    """
    Calculate the MD5 hash of the file located at the given file_path.

    Args:
        file_path (str): The path to the file.

    Returns:
        str | None: The MD5 hash of the file, or None if the file is not found or an error occurs.
    """
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
            if file_data is None:
                return None
            return hashlib.md5(file_data).hexdigest()
    except FileNotFoundError:
        return None
    except Exception:
        return None


def get_process_name(pid: int) -> str | None:
    """
    Get the name of the process with the given process ID.

    Args:
        pid (int): The process ID.

    Returns:
        str | None: The name of the process, or None if the process does not exist or cannot be accessed.
    """
    kernel32 = windll.kernel32

    try:
        hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not hProcess:
            return None

        buffer = create_unicode_buffer(260)
        buffer_size = c_uint32(260)
        success = kernel32.QueryFullProcessImageNameW(hProcess, 0, byref(buffer), byref(buffer_size))
        kernel32.CloseHandle(hProcess)

        if success:
            return os.path.basename(buffer.value) if buffer.value else None
    except Exception:
        pass

    return None

def has_border(hwnd: wintypes.HWND) -> bool:
    """
    Check if a window has a border or caption.

    Args:
        hwnd (ctypes.wintypes.HWND): The window handle.

    Returns:
        bool: True if the window has a border or caption, False otherwise.
    """
    style = GetWindowLong(hwnd, c_int(GWL_STYLE))
    has_border = bool(style & WS_BORDER)
    has_caption = bool(style & WS_CAPTION)
    return has_border or has_caption


def autologin():
    secret_file = load_secret_config()
    change_to_english_layout()
    pyperclip.copy("/alogin13")
    send('t')
    sleep(0.5)
    send('ctrl+v')
    send('enter')
    sleep(0.5)
    send('~')
    sleep(0.5)
    mouse.click((LEFT+80, TOP+380))
    pyperclip.copy(secret_file["password"])
    send('ctrl+v')
    send('enter')
    sleep(0.5)
    paste_to_console("hp")
    sleep(1.5)
    paste_to_console("fly")
    sleep(0.5)
    send('~')


add_hotkey('F8', autologin)

def update_coordinates():
    global WINDOW_WIDTH
    global WINDOW_HEIGHT
    global TELEPORT_TO_HOUSE
    global MAX_COLS
    global LEFT, TOP, RIGHT, BOTTOM
    while True:
        process = get_process("GTA5.exe")
        if process is not None:
            LEFT, TOP, RIGHT, BOTTOM = get_window_coordinates(process[0])
            if has_border(process[0]):
                LEFT += 8
                TOP += 31
                RIGHT -= 9
                BOTTOM -= 9
            WINDOW_WIDTH = RIGHT - LEFT
            WINDOW_HEIGHT = BOTTOM - TOP
            TELEPORT_TO_HOUSE = (LEFT+WINDOW_WIDTH/2 - 50, TOP+WINDOW_HEIGHT/2 + 101)
            MAX_COLS = (WINDOW_WIDTH - 1170) // 163
        sleep(0.5)

if __name__ == '__main__':
    mouse = Mouse()
    thread = threading.Thread(target=update_coordinates)
    thread.start()
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())
