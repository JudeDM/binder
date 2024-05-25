import sys
import os
import threading
import subprocess
from enum import Enum
import time
from datetime import datetime
from PyQt6.QtWidgets import (
	QApplication, QWidget, QLineEdit,
	QVBoxLayout, QHBoxLayout, QGridLayout, QDialog, QComboBox,
	QFormLayout, QScrollArea, QScrollBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor, QMouseEvent
import webbrowser
import keyboard
import pyperclip
import utils
import config


binder = None
mouse = None

MAX_COLS = 1
WINDOW_WIDTH, WINDOW_HEIGHT = 0, 0
LEFT, TOP, RIGHT, BOTTOM = 0, 0, 0, 0

pixel_conditions = {
	"should_show_violation_buttons": {
		(20, 370): (68, 68, 68),
		(70, 370): (68, 68, 68)
	},
	"should_show_report_buttons": {
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
				background-color: {config.BACKGROUND_COLOR};
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
		utils.check_update()
		self.binder_running = False
		self.setWindowTitle('Настройки')
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.setStyleSheet(config.BACKGROUND_COLOR_STYLE)
		self.setup_labels_and_edits()
		self.setup_buttons()
		self.init_ui()

	def mousePressEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse press event.

		Args:
			event (QMouseEvent): The mouse event.

		Returns:
			None
		"""
		if event is None:
			raise ValueError("Event cannot be None")
		self.dragPos = event.globalPosition()
		if self.dragPos is None:
			raise ValueError("Drag position cannot be None")
		self.dragPos = self.dragPos.toPoint()

	def mouseMoveEvent(self, event: QMouseEvent) -> None:
		"""
		Moves the window when dragging the mouse.

		Args:
			event (QMouseEvent): The mouse event.

		Returns:
			None
		"""
		if event is None or not hasattr(self, 'dragPos'):
			return
		drag_pos = event.globalPosition().toPoint()
		if drag_pos is None:
			raise ValueError("Drag position cannot be None")
		self.move(self.pos() + drag_pos - self.dragPos)
		self.dragPos = drag_pos
		event.accept()

	def setup_labels_and_edits(self) -> None:
		"""
		Setup labels and edits for the main app.

		Returns:
		- None
		"""
		secret_data = utils.load_secret_config()
		self.id_on_launch= str(secret_data.get("id", ""))
		password_edit = secret_data.get("password", "")
		self.id_label = utils.create_label(text="GID:", style=config.MAIN_APP_LABEL_TEXT_STYLE)
		self.password_label = utils.create_label(text="Пароль:", style=config.MAIN_APP_LABEL_TEXT_STYLE)
		self.id_edit = utils.create_line(text=self.id_on_launch, style=config.MAIN_APP_LINE_STYLE)
		self.password_edit = utils.create_line(text=password_edit, style=config.MAIN_APP_LINE_STYLE)
		self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
		self.footer_settings_label = utils.create_label(text="Изменение настроек окон:", style=config.MAIN_APP_LABEL_TEXT_STYLE)

	def setup_buttons(self) -> None:
		"""
		Setup buttons for the main app.

		Returns:
		- None
		"""
		self.show_password_button = utils.create_button(on_click_handler=self.toggle_password_visibility, text="Показать пароль")
		self.about_button, self.save_button, self.show_password_button, self.change_violation_button, self.change_pastes_button, self.change_properties_button, self.toggle_button = (
			utils.create_button(on_click_handler=self.show_about_page, icon_name="about.svg", style=config.MAIN_APP_HEADER_BUTTON_STYLE),
			utils.create_button(on_click_handler=self.save_secret_data, text="Сохранить", style=config.MAIN_APP_CONTROL_BUTTON_STYLE),
			utils.create_button(on_click_handler=self.toggle_password_visibility, text="Показать пароль", style=config.MAIN_APP_CONTROL_BUTTON_STYLE),
			utils.create_button(on_click_handler=self.show_violation_settings, text="Наказания", style=config.MAIN_APP_FOOTER_BUTTON_STYLE),
			utils.create_button(on_click_handler=self.show_buttons_settings, text="Репорты", style=config.MAIN_APP_FOOTER_BUTTON_STYLE),
			utils.create_button(on_click_handler=self.show_house_settings, text="Особняки", style=config.MAIN_APP_FOOTER_BUTTON_STYLE),
			utils.create_button(on_click_handler=self.toggle_binder, text="Запустить биндер", style=config.MAIN_APP_FOOTER_BUTTON_STYLE),
		)

	def init_ui(self):
		layout = QVBoxLayout()

		control_layout = create_control_layout(self)
		control_layout.insertWidget(0, self.about_button)
		control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
		control_widget = QWidget()
		control_widget.setFixedHeight(30)
		control_widget.setStyleSheet(config.BACKGROUND_COLOR_STYLE)
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
		input_widget.setStyleSheet(config.BACKGROUND_COLOR_STYLE)
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
		footer_widget.setStyleSheet(config.BACKGROUND_COLOR_STYLE)
		footer_widget.setLayout(footer_layout)
		layout.addWidget(footer_widget)

		self.setLayout(layout)

	def toggle_password_visibility(self) -> None:
		"""
		Toggles the password visibility of the password edit line.

		Returns:
		- None
		"""
		if self.password_edit.echoMode() == QLineEdit.EchoMode.Password:
			self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
			self.show_password_button.setText("Скрыть пароль")
		else:
			self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
			self.show_password_button.setText("Показать пароль")

	def show_violation_settings(self) -> None:
		"""
		Shows the Violation Settings window.

		Returns:
		- None
		"""
		violation_settings_window = ViolationSettingsWindow(title="Наказания")
		violation_settings_window.exec()

	def show_buttons_settings(self) -> None:
		"""
		Shows the Report Settings window.

		Returns:
		- None
		"""
		report_settings_window = ReportSettingsWindow(title="Репорты")
		report_settings_window.exec()

	def show_house_settings(self) -> None:
		"""
		Shows the House Settings window.

		Returns:
		- None
		"""
		house_settings_window = HouseSettingsWindow(title="Особняки")
		house_settings_window.exec()

	def close_app(self) -> None:
		"""
		Close the application using the taskkill command.

		Returns:
		- None
		"""
		subprocess.run(
			["taskkill", "/F", "/PID", str(os.getpid())],
			shell=True,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL
		)

	def toggle_binder(self) -> None:
		"""
		Toggle the binder running state.

		Returns:
		- None
		"""
		if self.binder_running:
			self.stop_binder()
		else:
			self.start_binder()

	def start_binder(self):
		if not hasattr(self, "isWarned"):
			self.isWarned = True
			secret_data = utils.load_secret_config()
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
		utils.save_secret_data(data)

	def show_notification(self, text: str, notification_type: NotificationType=NotificationType.DEFAULT):
		self.notification = Notification(text, notification_type)
		self.notification.show()


class GTAModal(QWidget):
	def __init__(self, modal_type: str = "punish", time = None, reason = None):
		super().__init__()
		self.modal_type = modal_type
		self.time = time
		self.reason = reason
		self.setup_ui()

	def setup_ui(self):
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
		title_widget = QWidget()
		title_widget.setFixedHeight(66)
		title_widget.setStyleSheet(config.GTA_MODAL_TITLE_BACKGROUND_COLOR_STYLE)
		title_text = utils.create_label(text=self.modal_type, style=config.GTA_MODAL_TITLE_STYLE)
		title_layout = QHBoxLayout()
		title_layout.addWidget(title_text)
		title_widget.setLayout(title_layout)
		self.main_layout.addWidget(title_widget)

	def setup_middle(self):
		middle_layout = QVBoxLayout()
		if self.modal_type in ["prison", "mute", "ban"]:
			gid_label, time_label, reason_label, self.gid_edit, self.time_edit, self.reason_edit = (
				utils.create_label(text="ID:", style=config.GTA_MODAL_TEXT_STYLE),
				utils.create_label(text="Время:", style=config.GTA_MODAL_TEXT_STYLE),
				utils.create_label(text="Причина:", style=config.GTA_MODAL_TEXT_STYLE),
				utils.create_line(style=config.GTA_MODAL_LINE_STYLE),
				utils.create_line(text=self.time, style=config.GTA_MODAL_LINE_STYLE),
				utils.create_line(text=self.reason, style=config.GTA_MODAL_LINE_STYLE),
			)

			middle_layout.addWidget(gid_label)
			middle_layout.addWidget(self.gid_edit)
			middle_layout.addWidget(time_label)
			middle_layout.addWidget(self.time_edit)
			middle_layout.addWidget(reason_label)
			middle_layout.addWidget(self.reason_edit)

		elif self.modal_type == "car_sync":
			car_gid_label, self.car_gid_edit = (
				utils.create_label(text="Car GID:", style=config.GTA_MODAL_TEXT_STYLE),
				utils.create_line(style=config.GTA_MODAL_LINE_STYLE),
			)

			middle_layout.addWidget(car_gid_label)
			middle_layout.addWidget(self.car_gid_edit)

		elif self.modal_type == "uncuff":
			gid_label, self.gid_edit, reason_label, self.reason_edit = (
				utils.create_label(text="GID:", style=config.GTA_MODAL_TEXT_STYLE),
				utils.create_line(style=config.GTA_MODAL_LINE_STYLE),
				utils.create_label(text="Причина:", style=config.GTA_MODAL_TEXT_STYLE),
				utils.create_line(text=self.reason, style=config.GTA_MODAL_LINE_STYLE),
			)

			middle_layout.addWidget(gid_label)
			middle_layout.addWidget(self.gid_edit)
			middle_layout.addWidget(reason_label)
			middle_layout.addWidget(self.reason_edit)

		elif self.modal_type == "uo_delete":
			uo_id_label, self.uo_id_edit = (
				utils.create_label(text="UO ID:", style=config.GTA_MODAL_TEXT_STYLE),
				utils.create_line(style=config.GTA_MODAL_LINE_STYLE),
			)

			middle_layout.addWidget(uo_id_label)
			middle_layout.addWidget(self.uo_id_edit)

		middle_widget = QWidget()
		middle_widget.setStyleSheet(config.GTA_MODAL_MIDDLE_BACKGROUND_COLOR_STYLE)
		middle_widget.setLayout(middle_layout)
		self.main_layout.addWidget(middle_widget)

	def setup_footer(self):
		footer_widget = QWidget()
		footer_widget.setFixedHeight(66)
		footer_widget.setStyleSheet(config.GTA_MODAL_FOOTER_BACKGROUND_COLOR_STYLE)
		footer_layout = QHBoxLayout()
		if self.modal_type in ["prison", "mute", "ban"]:
			send_button = utils.create_button(on_click_handler=self.punish_user, text="Отправить", style=config.GTA_MODAL_SEND_BUTTON_STYLE)
		elif self.modal_type == "car_sync":
			send_button = utils.create_button(on_click_handler=self.car_sync, text="Отправить", style=config.GTA_MODAL_SEND_BUTTON_STYLE)
		elif self.modal_type == "uncuff":
			send_button = utils.create_button(on_click_handler=self.uncuff, text="Отправить", style=config.GTA_MODAL_SEND_BUTTON_STYLE)
		elif self.modal_type == "uo_delete":
			send_button = utils.create_button(on_click_handler=self.uo_delete, text="Отправить", style=config.GTA_MODAL_SEND_BUTTON_STYLE)
		else:
			send_button = utils.create_button(on_click_handler=self.close, text="Отправить", style=config.GTA_MODAL_SEND_BUTTON_STYLE)
		cancel_button = utils.create_button(on_click_handler=self.close, text="Отмена", style=config.GTA_MODAL_CANCEL_BUTTON_STYLE)
		send_button.setFixedSize(130, 37)
		cancel_button.setFixedSize(110, 37)
		footer_layout.addWidget(send_button)
		footer_layout.addWidget(cancel_button)
		footer_widget.setLayout(footer_layout)
		self.main_layout.addWidget(footer_widget)

	def punish_user(self) -> None:
		"""
		Punishes a user with the specified GID, time, and reason.
		
		Args:
			self (GTAModal): The current instance of GTAModal.
		
		Returns:
			None
		"""
		try:
			gid: int = int(self.gid_edit.text())
		except (ValueError, TypeError):
			return self.show_notification("GID должен быть целым числом!", NotificationType.ERROR)
		time: str = self.time_edit.text()
		reason: str = self.reason_edit.text()
		paste_to_console(f"{self.modal_type} {gid} {time} {reason}")
		self.close()

	def uncuff(self) -> None:
		"""
		Uncuffs a player with the specified GID and reason.

		Args:
			self (GTAModal): The current instance of GTAModal.

		Returns:
			None
		"""
		try:
			gid = int(self.gid_edit.text())
		except (ValueError, TypeError):
			return self.show_notification("ID должен быть целочисленным значением!", NotificationType.ERROR)
		reason: str = self.reason_edit.text()
		paste_to_console(f"{self.modal_type} {gid} {reason}")
		self.close()

	def uo_delete(self) -> None:
		"""
		Deletes the item with the specified UO ID.

		Args:
			self (GTAModal): The current instance of GTAModal.

		Returns:
			None
		"""
		try:
			uo_id: int = int(self.uo_id_edit.text())
		except (ValueError, TypeError):
			return self.show_notification("ID должен быть целочисленным значением!", NotificationType.ERROR)
		paste_to_console(f"{self.modal_type} {uo_id}")
		self.close()

	def car_sync(self):
		user_gid = utils.load_secret_config().get('id', '')
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
			time.sleep(2.5)
		self.close()

	def show_notification(self, text: str, notification_type: NotificationType=NotificationType.DEFAULT):
		self.notification = Notification(text, notification_type)
		self.notification.show()


class AboutWindow(QWidget):
	def __init__(self):
		super().__init__()
		self.setup_ui()

	def setup_ui(self):
		self.setWindowTitle("О приложении")
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.setStyleSheet(config.BACKGROUND_COLOR_STYLE)
		self.main_layout = QVBoxLayout(self)
		control_layout = create_control_layout(self)
		self.main_layout.addLayout(control_layout)
		self.init_about_area()
		self.init_footer()

	def init_about_area(self):
		text_area = QVBoxLayout()
		reports_area = QVBoxLayout()
		reports_area_info = QHBoxLayout()
		STATS_title = utils.create_label(text="Статистика по репортам:", style=config.ABOUT_WINDOW_TITLE_STYLE)
		STATS_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		FAQ_title = utils.create_label(text="Немного о приложении:", style=config.ABOUT_WINDOW_TITLE_STYLE)
		FAQ_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		text = "F8 - Автологин.\n\nБиндер для GTA 5 RP, обеспечивающий администраторам удобство в модерировании.\nПросьба сообщать о возникающих проблемах через контактные данные, указанные ниже."
		FAQ_text = utils.create_label(text=text, style=config.ABOUT_WINDOW_TEXT_STYLE)
		reports_data = utils.get_reports_info()
		daily_reports, weekly_reports, monthly_reports, all_reports = utils.get_reports_count(reports_data=reports_data)
		daily_text = f"За сегодня: {daily_reports}\n({next(iter(reports_data["daily_reports"]))})"
		weekly_text = f"За неделю: {weekly_reports}\n({next(iter(reports_data["weekly_reports"]))})"
		monthly_text = f"За месяц: {monthly_reports}\n({next(iter(reports_data["monthly_reports"]))})"
		all_text = f"За всё время: {all_reports}\n({next(iter(reports_data["all_reports"]))})"
		daily_label = utils.create_label(text=daily_text, style=config.ABOUT_WINDOW_TEXT_STYLE)
		weekly_label = utils.create_label(text=weekly_text, style=config.ABOUT_WINDOW_TEXT_STYLE)
		monthly_label = utils.create_label(text=monthly_text, style=config.ABOUT_WINDOW_TEXT_STYLE)
		all_label = utils.create_label(text=all_text, style=config.ABOUT_WINDOW_TEXT_STYLE)
		daily_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		weekly_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		monthly_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		all_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		show_more_weekly_button = utils.create_button(
			on_click_handler=lambda: self.show_reports_info_page(period_type="weekly_reports"), 
			text="Подробнее за неделю", 
			style=config.ABOUT_WINDOW_BUTTON_STYLE
		)
		show_more_monthly_button = utils.create_button(
			on_click_handler=lambda: self.show_reports_info_page(period_type="monthly_reports"), 
			text="Подробнее за месяц", 
			style=config.ABOUT_WINDOW_BUTTON_STYLE
		)
		reports_area_info.addWidget(daily_label)
		reports_area_info.addWidget(weekly_label)
		reports_area_info.addWidget(monthly_label)
		reports_area_info.addWidget(all_label)
		reports_buttons_area = QHBoxLayout()
		reports_buttons_area.addWidget(show_more_weekly_button)
		reports_buttons_area.addWidget(show_more_monthly_button)
		reports_area.addLayout(reports_area_info)
		reports_area.addLayout(reports_buttons_area)
		text_area.addWidget(STATS_title)
		text_area.addLayout(reports_area)
		text_area.addWidget(FAQ_title)
		text_area.addWidget(FAQ_text)
		self.main_layout.addLayout(text_area)

	def show_reports_info_page(self, period_type: str) -> None:
		"""
		Show the information page for the specified period type.

		Args:
		- period_type (str): The type of period for which to show the information.

		Returns:
		- None
		"""
		if hasattr(self, "reports_info_page"):
			if not self.reports_info_page.isHidden():
				return
		self.reports_info_page = ReporsInfoWindow(period_type=period_type)
		self.reports_info_page.show()
		self.reports_info_page.show()

	def init_footer(self):
		footer_layout = QVBoxLayout()
		developer_label = utils.create_label(text="Начало разработки: 25 декабря 2023 года\nРазработчик: JudeDM (Dmitriy Win)", style=config.ABOUT_WINDOW_TEXT_STYLE)
		developer_label.setAlignment(Qt.AlignmentFlag.AlignRight)
		footer_layout.addWidget(developer_label)
		footer_icons_layout = QHBoxLayout()
		github_button = utils.create_button(on_click_handler=self.open_github, icon_name='github.svg', style=config.ABOUT_WINDOW_ICONS_BUTTON_STYLE)
		discord_button = utils.create_button(on_click_handler=self.open_discord, icon_name='discord.svg', style=config.ABOUT_WINDOW_ICONS_BUTTON_STYLE)
		footer_icons_layout.addWidget(github_button)
		footer_icons_layout.addWidget(discord_button)
		footer_layout.addLayout(footer_icons_layout)
		self.main_layout.addLayout(footer_layout)

	def open_github(self) -> None:
		"""
		Opens the GitHub repository page in the default web browser.

		:return: None
		"""
		webbrowser.open(url="https://github.com/JudeDM/binder/tree/main")

	def open_discord(self) -> None:
		"""
		Opens the Discord profile page in the default web browser.

		:return: None
		"""
		webbrowser.open(url="discord://-/users/208575718093750276")

	def mousePressEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse press event.

		Args:
			event (QMouseEvent): The mouse event.

		Returns:
			None
		"""
		if event is None:
			raise ValueError("Event cannot be None")
		self.dragPos = event.globalPosition()
		if self.dragPos is None:
			raise ValueError("Drag position cannot be None")
		self.dragPos = self.dragPos.toPoint()

	def mouseMoveEvent(self, event: QMouseEvent) -> None:
		"""
		Moves the window when dragging the mouse.

		Args:
			event (QMouseEvent): The mouse event.

		Returns:
			None
		"""
		if event is None or not hasattr(self, 'dragPos'):
			return
		drag_pos = event.globalPosition().toPoint()
		if drag_pos is None:
			raise ValueError("Drag position cannot be None")
		self.move(self.pos() + drag_pos - self.dragPos)
		self.dragPos = drag_pos
		event.accept()


class ReporsInfoWindow(QWidget):
	def __init__(self, period_type: int):
		super().__init__()
		self.period_type = period_type
		self.setup_ui()

	def setup_ui(self):
		self.setWindowTitle("Статистика по репортам")
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.setMinimumSize(400, 200)
		self.setStyleSheet(config.BACKGROUND_COLOR_STYLE)
		self.main_layout = QVBoxLayout(self)
		control_layout = create_control_layout(self)
		self.main_layout.addLayout(control_layout)
		self.init_report_area()

	def init_report_area(self):
		reports_data = utils.get_reports_info()[self.period_type]
		text_area = QVBoxLayout()
		STATS_title = utils.create_label(text="Статистика по репортам:", style=config.ABOUT_WINDOW_TITLE_STYLE)
		STATS_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		text = "	" + "	".join(f"{key} - {value}\n" for key, value in reports_data.items())
		text_label = utils.create_label(text=text, style=config.ABOUT_WINDOW_TEXT_STYLE)
		text_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		text_area.addWidget(STATS_title)
		text_area.addWidget(text_label)
		self.main_layout.addLayout(text_area)

	def mousePressEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse press event.

		Args:
			event (QMouseEvent): The mouse event.

		Returns:
			None
		"""
		if event is None:
			raise ValueError("Event cannot be None")
		self.dragPos = event.globalPosition()
		if self.dragPos is None:
			raise ValueError("Drag position cannot be None")
		self.dragPos = self.dragPos.toPoint()

	def mouseMoveEvent(self, event: QMouseEvent) -> None:
		"""
		Moves the window when dragging the mouse.

		Args:
			event (QMouseEvent): The mouse event.

		Returns:
			None
		"""
		if event is None or not hasattr(self, 'dragPos'):
			return
		drag_pos = event.globalPosition().toPoint()
		if drag_pos is None:
			raise ValueError("Drag position cannot be None")
		self.move(self.pos() + drag_pos - self.dragPos)
		self.dragPos = drag_pos
		event.accept()


class SettingsWindow(QDialog):
	def __init__(self, title: str, settings_type: str, calling_instance):
		super().__init__()
		self.setStyleSheet(config.SETTINGS_WINDOW_STYLE)
		palette = self.palette()
		palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Window, QColor(config.BACKGROUND_COLOR))
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
		add_column_button = utils.create_button(on_click_handler=self.add_item, text="Добавить кнопку")
		save_button = utils.create_button(on_click_handler=self.save_config, text="Сохранить")
		control_panel_layout.addWidget(add_column_button)
		control_panel_layout.addWidget(save_button)

		if settings_type == "house":
			self.config = [item for sublist in utils.load_house_button_config() for item in sublist]
		elif settings_type == "report":
			self.config = [item for sublist in utils.load_report_button_config() for item in sublist]
		elif settings_type == "violation":
			self.config = [item for sublist in utils.load_violation_button_config() for item in sublist]

		scroll_area = QScrollArea(self)
		scroll_area.setWidgetResizable(True)
		scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
		self.horizontal_scrollbar = QScrollBar(Qt.Orientation.Horizontal)
		scroll_area.setHorizontalScrollBar(self.horizontal_scrollbar)
		self.main_layout.addWidget(scroll_area)

		scroll_widget = QWidget()
		scroll_area.setWidget(scroll_widget)
		scroll_area.setStyleSheet(config.BACKGROUND_COLOR_STYLE)

		self.main_scroll_layout = QVBoxLayout(scroll_widget)
		scroll_area.setMaximumWidth(1200)

		self.main_layout.addLayout(control_panel_layout)

	def mousePressEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse press event.

		Args:
			event (QMouseEvent): The mouse event.

		Returns:
			None
		"""
		if event is None:
			raise ValueError("Event cannot be None")
		self.dragPos = event.globalPosition()
		if self.dragPos is None:
			raise ValueError("Drag position cannot be None")
		self.dragPos = self.dragPos.toPoint()

	def mouseMoveEvent(self, event: QMouseEvent) -> None:
		"""
		Moves the window when dragging the mouse.

		Args:
			event (QMouseEvent): The mouse event.

		Returns:
			None
		"""
		if event is None or not hasattr(self, 'dragPos'):
			return
		drag_pos = event.globalPosition().toPoint()
		if drag_pos is None:
			raise ValueError("Drag position cannot be None")
		self.move(self.pos() + drag_pos - self.dragPos)
		self.dragPos = drag_pos
		event.accept()

	def add_item(self):
		if len(self.config) > 200:
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
		item_control_buttons = QHBoxLayout()
		delete_button, moveup_button, movedown_button = (
			utils.create_button(on_click_handler=lambda: self.remove_item(item_index), icon_name="delete.svg", style=config.SETTINGS_BUTTON_STYLE),
			utils.create_button(on_click_handler=lambda: self.move_item(item_index, "up"), icon_name="arrow_up.svg", style=config.SETTINGS_BUTTON_STYLE),
			utils.create_button(on_click_handler=lambda: self.move_item(item_index, "down"), icon_name="arrow_down.svg", style=config.SETTINGS_BUTTON_STYLE),
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
			utils.save_house_button_config([self.config[i:i+10] for i in range(0, len(self.config), 10)])
		elif self.settings_type == "report":
			utils.save_report_button_config([self.config[i:i+10] for i in range(0, len(self.config), 10)])
		elif self.settings_type == "violation":
			utils.save_violation_button_config([self.config[i:i+10] for i in range(0, len(self.config), 10)])
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
		group_layout = QVBoxLayout()
		group_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

		for index, violation in enumerate(violation_group):
			violation_index = group_index * 10 + index
			row = QHBoxLayout()
			form_layout = QFormLayout()
			type_edit = QComboBox()
			type_edit.addItems(['prison', 'mute', 'ban'])
			type_edit.setStyleSheet(config.VIOLATION_SETTINGS_SHORT_STYLE)
			type_edit.setCurrentText(violation["type"] if "type" in violation else None)
			type_edit.activated.connect(lambda index, type_edit=type_edit, violation_index=violation_index: self.update_violation_field(violation_index, "type", type_edit.currentText()))
			name_edit = utils.create_line(text=violation["name"], style=config.VIOLATION_SETTINGS_SHORT_STYLE)
			name_edit.textChanged.connect(lambda text, index=violation_index: self.update_violation_field(index, "name", text))
			time_edit = utils.create_line(text=violation["time"], style=config.VIOLATION_SETTINGS_SHORT_STYLE)
			time_edit.textChanged.connect(lambda text, index=violation_index: self.update_violation_field(index, "time", text))
			reason_edit = utils.create_line(text=violation["reason"], style=config.VIOLATION_SETTINGS_LONG_STYLE)
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
			name_edit.setStyleSheet(config.REPORT_SETTINGS_SHORT_STYLE)
			text_edit.setStyleSheet(config.REPORT_SETTINGS_LONG_STYLE)
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
		group_layout = QVBoxLayout()
		group_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

		for index, house in enumerate(house_group):
			house_index = group_index * 10 + index
			form_layout = QFormLayout()
			name_edit = QLineEdit(text=house["name"])
			name_edit.textChanged.connect(lambda text, index=house_index: self.update_house_name(index, text))
			name_edit.setStyleSheet(config.HOUSE_SETTINGS_SHORT_STYLE)
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
		violation_config = utils.load_violation_button_config()
		for col, col_config in enumerate(violation_config):
			if col >= MAX_COLS:
				continue
			for row, button_config in enumerate(col_config):
				button_number = row * len(violation_config) + col + 1
				button = utils.create_button(on_click_handler=self.handle_punish_button_click, text=button_config['name'], style=config.ADMIN_BUTTON_STYLE)
				self.violation_buttons[button_number] = (button, button_config['type'], button_config['time'], button_config['reason'])
				self.violation_buttons_layout.addWidget(button, row, col)
		self.main_layout.insertLayout(0, self.violation_buttons_layout)

	def init_reports_ui(self):
		self.report_buttons_layout = QGridLayout()
		self.report_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
		self.report_buttons_layout.setHorizontalSpacing(10)
		self.report_buttons_layout.setVerticalSpacing(5)
		button_configs = utils.load_report_button_config()
		for col, col_config in enumerate(button_configs):
			if col >= MAX_COLS:
				continue
			for row, button_config in enumerate(col_config):
				button_number = row * len(button_configs) + col + 1
				button = utils.create_button(on_click_handler=self.handle_report_button_click, text=button_config['name'], style=config.ADMIN_BUTTON_STYLE)
				self.buttons[button_number] = (button, button_config['text'])
				self.report_buttons_layout.addWidget(button, row, col)
		self.main_layout.insertLayout(0, self.report_buttons_layout)

	def init_house_ui(self):
		self.house_layout = QGridLayout()
		self.house_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
		self.house_layout.setHorizontalSpacing(10)
		self.house_layout.setVerticalSpacing(5)
		house_button_configs = utils.load_house_button_config()

		def teleport_closure(name):
			return lambda: self.teleport_to_house(name)

		for col, col_config in enumerate(house_button_configs):
			if col >= MAX_COLS:
				continue
			for row, house_button_config in enumerate(col_config):
				button_number = row * len(house_button_configs) + col + 1
				name = house_button_config['name']

				button = utils.create_button(on_click_handler=teleport_closure(name), text=name, style=config.ADMIN_BUTTON_STYLE)
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
		title = utils.create_label(text="Статистика:", style=config.ADMIN_BUTTON_STYLE)
		title.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
		self.reports_counter.addWidget(title)
		labels = ["За день:", "За неделю:", "За месяц:"]
		for label_text in labels:
			label = utils.create_label(text=label_text, style=config.ADMIN_BUTTON_STYLE)
			label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
			self.reports_counter.addWidget(label)
			self.report_labels.append(label)
		self.additional_layout.addLayout(self.reports_counter)
		self.update_report_labels()

	def init_sync_buttons(self):
		# mute_button = utils.create_button(on_click_handler=lambda: self.handle_punish_button_click("mute"), text="mute", style=config.ADMIN_BUTTON_STYLE)
		# prison_button = utils.create_button(on_click_handler=lambda: self.handle_punish_button_click("prison"), text="prison", style=config.ADMIN_BUTTON_STYLE)
		# ban_button = utils.create_button(on_click_handler=lambda: self.handle_punish_button_click("ban"), text="ban", style=config.ADMIN_BUTTON_STYLE)
		uncuff_button = utils.create_button(on_click_handler=self.handle_uncuff_button_click, text="uncuff", style=config.ADMIN_BUTTON_STYLE)
		dimension_sync_button = utils.create_button(on_click_handler=self.handle_sync_button_click, text="dimension_sync", style=config.ADMIN_BUTTON_STYLE)
		car_sync_button = utils.create_button(on_click_handler=self.handle_car_sync_button_click, text="car_sync", style=config.ADMIN_BUTTON_STYLE)
		# uo_delete_button = utils.create_button(on_click_handler=self.handle_uo_delete_button_click, text="uo_delete", style=config.ADMIN_BUTTON_STYLE)
		reof_button = utils.create_button(on_click_handler=self.handle_reof_button_click, text="reof", style=config.ADMIN_BUTTON_STYLE)
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
		for button, button_punish_type, punish_time, punish_reason in self.violation_buttons.values():
			if button is self.sender():
				if hasattr(self, "gta_modal"):
					if not self.gta_modal.isHidden():
						return
				self.modal = GTAModal(modal_type=button_punish_type, time=punish_time, reason=punish_reason)
				return self.modal.show()

	def handle_report_button_click(self, text_to_copy=None):
		text_to_copy = text_to_copy or next(text for button, text in self.buttons.values() if button is self.sender())
		position = mouse.get_position()
		now = datetime.now()
		start_date = datetime(now.year, 4, 1, 7)
		end_date = datetime(now.year, 4, 2, 7)
		mouse.click((LEFT+245, (TOP+345 if start_date <= now < end_date else TOP+330)))
		pyperclip.copy(text_to_copy)
		keyboard.send('ctrl+v')
		keyboard.send('enter')
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
		paste_to_console(f"dimension_sync {utils.load_secret_config().get('id', '')}")
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
		daily_reports, weekly_reports, monthly_reports, all_reports = utils.get_reports_count()
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
		time.sleep(0.1)
		mouse.click(TELEPORT_TO_HOUSE)


	def update_buttons(self):
		if self.x() != LEFT+1000 or self.y() != TOP+4:
			self.setFixedSize(WINDOW_WIDTH-1000, 400)
			self.move(LEFT+1000, TOP+4)
		is_console_open = all(utils.is_within_range(utils.get_pixel_color(*coord, LEFT=LEFT, TOP=TOP), color) for coord, color in pixel_conditions["should_show_violation_buttons"].items())
		is_report_open = all(utils.is_within_range(utils.get_pixel_color(*coord, LEFT=LEFT, TOP=TOP), color) for coord, color in pixel_conditions["should_show_report_buttons"].items())
		is_teleport_open = all(utils.is_within_range(utils.get_pixel_color(*coord, LEFT=LEFT, TOP=TOP), color) for coord, color in pixel_conditions["should_show_teleport_buttons"].items())
		is_panel_open = all(utils.is_within_range(utils.get_pixel_color(*coord, LEFT=LEFT, TOP=TOP), color) for coord, color in pixel_conditions["should_show_control_buttons"].items())

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
		today_date = datetime.now().strftime(config.DATE_FORMAT)
		click_data = utils.load_click_data()
		click_data[today_date] = click_data.get(today_date, 0) + 1
		utils.save_click_data(click_data)
		self.update_report_labels()


def paste_to_console(text: str):
	mouse.click((LEFT+55, TOP+375))
	time.sleep(0.1)
	mouse.click((LEFT+500, TOP+335))
	keyboard.send('ctrl+a, backspace')
	pyperclip.copy(text)
	keyboard.send('ctrl+v')
	keyboard.send('enter')

def create_control_layout(instance):
	control_layout = QHBoxLayout()
	minimize_button = utils.create_button(on_click_handler=instance.showMinimized, icon_name='minimize.svg', style=config.CONTROL_BUTTONS_STYLE)
	close_button = utils.create_button(on_click_handler=instance.close_app if isinstance(instance, MainApp) else instance.close, icon_name='delete.svg', style=config.CONTROL_BUTTONS_STYLE)
	control_layout.addWidget(minimize_button)
	control_layout.addWidget(close_button)
	control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
	return control_layout

def autologin():
	secret_file = utils.load_secret_config()
	pyperclip.copy("/alogin13")
	keyboard.send('t')
	time.sleep(0.5)
	keyboard.send('ctrl+v')
	keyboard.send('enter')
	time.sleep(0.5)
	try:
		keyboard.send('asciitilde')
	except ValueError:
		keyboard.send('ё')
	time.sleep(0.5)
	mouse.click((LEFT+80, TOP+380))
	pyperclip.copy(secret_file["password"])
	keyboard.send('ctrl+v')
	keyboard.send('enter')
	time.sleep(0.5)
	paste_to_console("hp")
	time.sleep(1)
	paste_to_console("fly")
	try:
		keyboard.send('asciitilde')
	except ValueError:
		keyboard.send('ё')


keyboard.add_hotkey('F8', autologin)

def update_coordinates():
	global WINDOW_WIDTH
	global WINDOW_HEIGHT
	global TELEPORT_TO_HOUSE
	global MAX_COLS
	global LEFT, TOP, RIGHT, BOTTOM
	while True:
		process = utils.get_process("GTA5.exe")
		if process is not None:
			LEFT, TOP, RIGHT, BOTTOM = utils.get_window_coordinates(process[0])
			if utils.has_border(process[0]):
				LEFT += 8
				TOP += 31
				RIGHT -= 9
				BOTTOM -= 9
			WINDOW_WIDTH = RIGHT - LEFT
			WINDOW_HEIGHT = BOTTOM - TOP
			TELEPORT_TO_HOUSE = (LEFT+WINDOW_WIDTH/2 - 50, TOP+WINDOW_HEIGHT/2 + 101)
			MAX_COLS = (WINDOW_WIDTH - 1170) // 163
		time.sleep(0.5)

if __name__ == '__main__':
	mouse = utils.Mouse()
	thread = threading.Thread(target=update_coordinates)
	thread.start()
	app = QApplication(sys.argv)
	main_app = MainApp()
	main_app.show()
	sys.exit(app.exec())
