import os
import re
import subprocess
import sys
import time
import traceback
import webbrowser
from datetime import datetime
from enum import Enum
from functools import partial
from typing import Callable

import keyboard
import pyperclip
from PyQt6.QtCore import QObject, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QMouseEvent, QPalette
from PyQt6.QtWidgets import (QApplication, QComboBox, QDialog, QFormLayout,
                             QGridLayout, QHBoxLayout, QLayout, QLineEdit,
                             QMessageBox, QPushButton, QScrollArea, QScrollBar,
                             QSpacerItem, QVBoxLayout, QWidget)
from pyqt_advanced_slider import Slider

import config
import utils
from utils import configuration

binder = None
mouse = None

MAX_COLS = 1
MAX_BUTTONS_PER_COL = 10
WINDOW_WIDTH, WINDOW_HEIGHT = 0, 0
LEFT, TOP, RIGHT, BOTTOM = 0, 0, 0, 0

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
		self.setStyleSheet(config.NOTIFICATION_STYLE.replace("%color%", color))


class MainApp(QDialog):
	def __init__(self):
		super(MainApp, self).__init__()
		utils.check_update()
		self.dragging = False
		self.binder_running = False
		self.setWindowTitle('Настройки')
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.setStyleSheet(config.MAIN_APP_STYLE)
		self.setup_labels_and_edits()
		self.setup_buttons()
		self.init_ui()

	def mousePressEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse press event.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragPos = event.globalPosition().toPoint()
			self.dragging = True

	def mouseMoveEvent(self, event: QMouseEvent) -> None:
		"""
		Moves the window when dragging the mouse.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if not self.dragging:
			return
		
		if event.buttons() == Qt.MouseButton.LeftButton:
			drag_pos = event.globalPosition().toPoint()
			self.move(self.pos() + drag_pos - self.dragPos)
			self.dragPos = drag_pos

	def mouseReleaseEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse release event.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragging = False

	def setup_labels_and_edits(self) -> None:
		"""
		Setup labels and edits for the main app.

		Returns:
		- None
		"""
		settings_data = configuration.settings_config
		self.id_on_launch = str(settings_data.user_gid)
		self.password_edit = utils.create_line(text=configuration.password, style=config.MAIN_APP_PASSOWRD_LINE_STYLE)
		self.id_label = utils.create_label(text="ID на сервере:")
		self.id_label_description = utils.create_label(text="Для dimension_sync и car_sync", style=config.MAIN_APP_LABEL_DESCRIPTION_STYLE)
		self.password_label = utils.create_label(text="Админ-пароль:")
		self.password_label_description = utils.create_label(text="Для автовхода через F8", style=config.MAIN_APP_LABEL_DESCRIPTION_STYLE)
		self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
		self.id_edit = utils.create_line(text=self.id_on_launch, style=config.MAIN_APP_LINE_STYLE)
		self.footer_settings_label = utils.create_label(text="Изменение настроек окон:")


	def setup_buttons(self) -> None:
		"""
		Setup buttons for the main app.

		Returns:
		- None
		"""
		self.settings_button, self.about_button, self.save_button, self.show_password_button, self.buttons_settings_button, self.toggle_binder_button = (
			utils.create_button(on_click_handler=self.show_settings_page, icon_name="settings", style=config.MAIN_APP_HEADER_BUTTON_STYLE),
			utils.create_button(on_click_handler=self.show_about_page, icon_name="about", style=config.MAIN_APP_HEADER_BUTTON_STYLE),
			utils.create_button(on_click_handler=self.save_settings_data, text="Сохранить", style=config.MAIN_APP_CONTROL_BUTTON_STYLE),
			utils.create_button(on_click_handler=self.toggle_password_visibility, icon_name="visible", style=config.MAIN_APP_PASSWORD_VISIBILITY_BUTTON_STYLE),
			utils.create_button(on_click_handler=self.show_buttons_settings, text="Настройка кнопок", style=config.MAIN_APP_CONTROL_BUTTON_STYLE),
			utils.create_button(on_click_handler=self.toggle_binder, text="Запустить биндер", style=config.MAIN_APP_FOOTER_BUTTON_STYLE),
		)

	def init_ui(self):
		layout = QVBoxLayout()
		control_layout = create_header_layout(self)
		layout.addLayout(control_layout)
		main_controls_layout = QVBoxLayout()
		colomns_layout = QHBoxLayout()
		id_label_box = QVBoxLayout()
		id_label_box.addWidget(self.id_label)
		id_label_box.addWidget(self.id_label_description)
		id_label_box.setSpacing(0)
		password_label_box = QVBoxLayout()
		password_label_box.addWidget(self.password_label)
		password_label_box.addWidget(self.password_label_description)
		password_label_box.setSpacing(0)
		labels_column = QVBoxLayout()
		labels_column.addLayout(id_label_box)
		labels_column.addLayout(password_label_box)
		edits_column = QVBoxLayout()
		edits_column.addWidget(self.id_edit)
		password_edit_box = QHBoxLayout()
		password_edit_box.setSpacing(0)
		password_edit_box.addWidget(self.password_edit)
		password_edit_box.addWidget(self.show_password_button)
		edits_column.addLayout(password_edit_box)
		colomns_layout.addLayout(labels_column)
		colomns_layout.addLayout(edits_column)
		buttons_row1 = QHBoxLayout()
		buttons_row1.addWidget(self.save_button)
		buttons_row1.addWidget(self.buttons_settings_button)
		main_controls_layout.addLayout(colomns_layout)
		main_controls_layout.addLayout(buttons_row1)
		main_controls_layout.addWidget(self.toggle_binder_button)
		input_widget = QWidget()
		input_widget.setFixedWidth(400)
		input_widget.setLayout(main_controls_layout)
		layout.addWidget(input_widget)


		self.setLayout(layout)

	def toggle_password_visibility(self) -> None:
		"""
		Toggles the password visibility of the password edit line.

		Returns:
		- None
		"""
		if self.password_edit.echoMode() == QLineEdit.EchoMode.Password:
			self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
			self.show_password_button.setIcon(utils.icons_map["invisible"])
		else:
			self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
			self.show_password_button.setIcon(utils.icons_map["visible"])

	def show_buttons_settings(self) -> None:
		"""
		Shows the Report Settings window.

		Returns:
		- None
		"""
		report_settings_window = SettingsWindow(title="Настройка кнопок", active_window="report")
		report_settings_window.exec()

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
			user_id = str(configuration.settings_config.user_gid)
			if self.id_on_launch == user_id:
				return self.show_notification("Вы не поменяли ID после запуска биндера!\nНе забудьте его поменять, иначе можете помешать игрокам.")
		self.toggle_binder_button.setText("Выключить биндер")
		self.toggle_binder_button.clicked.disconnect()
		self.toggle_binder_button.clicked.connect(self.stop_binder)
		self.binder_running = True
		global binder
		binder = Binder()
		binder.start_window()

	def stop_binder(self):
		self.toggle_binder_button.setText("Запустить биндер")
		self.toggle_binder_button.clicked.disconnect()
		self.toggle_binder_button.clicked.connect(self.start_binder)
		self.binder_running = False
		if binder:
			binder.close_window()

	def show_about_page(self):
		if hasattr(self, "about_page") and not self.about_page.isHidden():
			return
		self.about_page = AboutWindow()
		self.about_page.show()

	def show_settings_page(self):
		if hasattr(self, "settings_page") and not self.settings_page.isHidden():
			return
		self.settings_page = ConfigSettingsWindow()
		self.settings_page.show()

	def save_settings_data(self):
		try:
			int(self.id_edit.text())
		except (ValueError, TypeError):
			return self.show_notification("ID должен быть целочисленным значением!", NotificationType.ERROR)
		configuration.password = self.password_edit.text()
		config_data = configuration.settings_config
		config_data.user_gid = int(self.id_edit.text())
		data = utils.SettingsStructure(**config_data.model_dump())
		self.show_notification("Данные успешно сохранены!")
		configuration.save_config("settings", data.model_dump())

	def show_notification(self, text: str, notification_type: NotificationType=NotificationType.DEFAULT):
		self.notification = Notification(text, notification_type)
		self.notification.show()


class GTAModal(QWidget):
	def __init__(self, command_name: str, time = None, reason = None):
		super().__init__()
		self.command_name = command_name
		self.modal_type = utils.ADDIDIONAL_BUTTONS[command_name]
		self.time = time
		self.reason = reason
		self.callbacks = {
			"punish": self.punish_command,
			"simple": self.simple_command,
			"uncuff": self.middle_command,
			"force_rename": self.middle_command,
			"car_sync": self.car_sync,
		}
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
		title_text = utils.create_label(text=self.command_name, style=config.GTA_MODAL_TITLE_STYLE)
		title_layout = QHBoxLayout()
		title_layout.addWidget(title_text)
		title_widget.setLayout(title_layout)
		self.main_layout.addWidget(title_widget)

	def setup_middle(self):
		middle_layout = QVBoxLayout()
		if self.modal_type == "punish":
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

		elif self.modal_type == "simple" or self.modal_type == "car_sync":
			gid_label, self.gid_edit = (
				utils.create_label(text="ID:", style=config.GTA_MODAL_TEXT_STYLE),
				utils.create_line(style=config.GTA_MODAL_LINE_STYLE),
			)
			middle_layout.addWidget(gid_label)
			middle_layout.addWidget(self.gid_edit)

		elif self.modal_type == "uncuff" or self.modal_type == "force_rename":
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


		middle_widget = QWidget()
		middle_widget.setStyleSheet(config.GTA_MODAL_MIDDLE_BACKGROUND_COLOR_STYLE)
		middle_widget.setLayout(middle_layout)
		self.main_layout.addWidget(middle_widget)

	def setup_footer(self):
		footer_widget = QWidget()
		footer_widget.setFixedHeight(66)
		footer_widget.setStyleSheet(config.GTA_MODAL_FOOTER_BACKGROUND_COLOR_STYLE)
		footer_layout = QHBoxLayout()
		send_button = utils.create_button(on_click_handler=self.callbacks[self.modal_type], text="Отправить", style=config.GTA_MODAL_SEND_BUTTON_STYLE)
		cancel_button = utils.create_button(on_click_handler=self.close, text="Отмена", style=config.GTA_MODAL_CANCEL_BUTTON_STYLE)
		send_button.setFixedSize(130, 37)
		cancel_button.setFixedSize(110, 37)
		footer_layout.addWidget(send_button)
		footer_layout.addWidget(cancel_button)
		footer_widget.setLayout(footer_layout)
		self.main_layout.addWidget(footer_widget)

	def punish_command(self) -> None:
		"""
		Punishes a user with the specified GID, time, and reason.
		
		Args:
		- self (GTAModal): The current instance of GTAModal.
		
		Returns:
		- None
		"""
		try:
			gid: int = int(self.gid_edit.text())
		except (ValueError, TypeError):
			return self.show_notification("GID должен быть целым числом!", NotificationType.ERROR)
		time: str = self.time_edit.text()
		reason: str = self.reason_edit.text()
		paste_to_console(f"{self.modal_type} {gid} {time} {reason}")
		self.close()

	def simple_command(self) -> None:
		"""
		Executes a simple command with the specified gid.

		Args:
		- self (GTAModal): The current instance of GTAModal.

		Returns:
		- None
		"""
		try:
			gid = int(self.gid_edit.text())
		except (ValueError, TypeError):
			return self.show_notification("ID должен быть целочисленным значением!", NotificationType.ERROR)
		paste_to_console(f"{self.command_name} {gid}")
		self.close()

	def middle_command(self) -> None:
		"""
		Uncuffs or force renames a player with the specified GID and reason.

		Args:
		- self (GTAModal): The current instance of GTAModal.

		Returns:
		- None
		"""
		try:
			gid = int(self.gid_edit.text())
		except (ValueError, TypeError):
			return self.show_notification("ID должен быть целочисленным значением!", NotificationType.ERROR)
		reason: str = self.reason_edit.text()
		paste_to_console(f"{self.modal_type} {gid} {reason}")
		self.close()

	def car_sync(self):
		user_gid = configuration.settings_config.user_gid
		car_gid = self.gid_edit.text()
		actions = [
			f"dimension {user_gid} 1",
			f"tpcar {car_gid}",
			f"veh_repair {car_gid}",
			f"dimension {user_gid} 0",
			f"tpcar {car_gid}"
		]
		for action in actions:
			paste_to_console(action)
			time.sleep(1)
		self.close()

	def show_notification(self, text: str, notification_type: NotificationType=NotificationType.DEFAULT):
		self.notification = Notification(text, notification_type)
		self.notification.show()


class UpdateHistoryWorker(QObject):
	history_updated = pyqtSignal(list)

	def fetch_commits(self):
		return utils.get_commits_history()

	def load_commits(self):
		commits = self.fetch_commits()
		self.history_updated.emit(commits)


class ConfigSettingsWindow(QWidget):
	def __init__(self):
		super().__init__()
		self.visible_buttons = configuration.settings_config.visible_buttons
		self.dragging = False
		self.setup_ui()

	def setup_ui(self):
		self.setWindowTitle("Настройки")
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.setStyleSheet(config.MAIN_APP_STYLE)
		self.setFixedWidth(480)
		self.main_layout = QVBoxLayout(self)
		control_layout = create_header_layout(instance=self)
		self.main_layout.addLayout(control_layout)
		self.init_variables_settings()
		self.init_additional_buttons_settings()

	def init_additional_buttons_settings(self) -> None:
		titles_layout = QHBoxLayout()
		self.preview_buttons_layout = QVBoxLayout()
		columns_layout = QHBoxLayout()
		self.available_buttons_layout = QVBoxLayout()
		self.available_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

		selected_buttons_title = utils.create_label("Выбранные кнопки:", style=config.ABOUT_WINDOW_TITLE_STYLE)
		available_buttons_title = utils.create_label("Доступные кнопки:", style=config.ABOUT_WINDOW_TITLE_STYLE)

		titles_layout.addWidget(selected_buttons_title)
		titles_layout.addWidget(available_buttons_title)
		self.main_layout.addLayout(titles_layout)
		for button_name in self.visible_buttons:
			self.add_button_row(button_name=button_name, layout=self.preview_buttons_layout, controls=self.visible_buttons_controls)
		for button_name in [button for button in utils.ADDIDIONAL_BUTTONS.keys() if button not in self.visible_buttons]:
			self.add_button_row(button_name=button_name, layout=self.available_buttons_layout, controls=self.available_buttons_controls)

		self.preview_buttons_layout.setContentsMargins(10, 0, 20, 0)
		columns_layout.addLayout(self.preview_buttons_layout)
		columns_layout.addLayout(self.available_buttons_layout)
		self.available_buttons_layout.addStretch(0)
		self.preview_buttons_layout.addStretch(0)
		self.main_layout.addLayout(columns_layout)


	def add_button_row(self, button_name: str, layout: QVBoxLayout, controls) -> None:
		button_row = self.get_button_row(text=button_name, control_layout=controls())
		layout.insertLayout(0,button_row)
		self.update_spacer_item()

	def get_button_row(self, text: str, control_layout: QHBoxLayout) -> QHBoxLayout:
		button = utils.create_button(text=text, style=config.BINDER_SETTINGS_WINDOW_BUTTON_STYLE)
		button_row = QHBoxLayout()
		button_row.addWidget(button)
		button_row.addLayout(control_layout)
		button_row.setSpacing(10)
		return button_row

	def clear_layout(self, layout: QLayout):
		while layout.count():
			item = layout.takeAt(0)
			if item.widget():
				item.widget().deleteLater()
			elif item.layout():
				self.clear_layout(item.layout())
		layout.update()
		layout.deleteLater()

	def count_non_spacer_items(self, layout: QLayout) -> int:
		return sum(1 for i in range(layout.count()) if not isinstance(layout.itemAt(i), QSpacerItem))

	def add_available_item(self):
		button = self.sender()
		row_index = self.find_layout_index_containing_widget(self.preview_buttons_layout, button)
		button_name = self.get_button_name_by_index(self.preview_buttons_layout, row_index)
		self.remove_button_row(self.preview_buttons_layout, row_index)
		self.add_button_row(button_name=button_name, layout=self.available_buttons_layout, controls=self.available_buttons_controls)
		self.update_config()

	def add_preview_item(self):
		if self.count_non_spacer_items(self.preview_buttons_layout) >= 6:
			return self.show_notification("Можно добавить до 6 кнопок!")
		button = self.sender()
		row_index = self.find_layout_index_containing_widget(self.available_buttons_layout, button)
		button_name = self.get_button_name_by_index(self.available_buttons_layout, row_index)
		self.remove_button_row(self.available_buttons_layout, row_index)
		self.add_button_row(button_name=button_name, layout=self.preview_buttons_layout, controls=self.visible_buttons_controls)
		self.update_config()

	def get_button_name_by_index(self, layout: QVBoxLayout, row_index: int) -> str:
		return layout.itemAt(row_index).itemAt(0).widget().text()

	def remove_button_row(self, layout: QVBoxLayout, row_index: int):
		if row_index != -1:
			item = layout.takeAt(row_index)
			self.clear_layout(item.layout())
			self.update_spacer_item()

	def find_layout_index_containing_widget(self, layout: QLayout, widget: QObject) -> int:
		for i in range(layout.count()):
			item = layout.itemAt(i)
			if item.widget() == widget:
				return i
			if item.layout() is not None and self.layout_contains_widget(item.layout(), widget):
				return i
		return -1

	def layout_contains_widget(self, layout: QLayout, widget: QObject) -> bool:
		for i in range(layout.count()):
			item = layout.itemAt(i)
			if item.widget() == widget or (item.layout() is not None and self.layout_contains_widget(item.layout(), widget)):
				return True
		return False

	def move_item(self, direction: str):
		sender = self.sender()
		row_index = self.find_layout_index_containing_widget(self.preview_buttons_layout, sender)

		if direction not in ['up', 'down']:
			raise ValueError("Direction must be 'up' or 'down'")

		total_rows = self.count_non_spacer_items(layout=self.preview_buttons_layout)
		if row_index < 0 or row_index >= total_rows:
			raise IndexError("Index out of range")

		if direction == 'up' and row_index == 0:
			return
		if direction == 'down' and row_index == total_rows - 1:
			return

		if direction == 'up':
			new_index = row_index - 1
			item_to_move = self.preview_buttons_layout.takeAt(row_index)
			item_to_replace = self.preview_buttons_layout.takeAt(new_index)
			self.preview_buttons_layout.insertItem(new_index, item_to_move)
			self.preview_buttons_layout.insertItem(row_index, item_to_replace)
		else:
			new_index = row_index + 1
			item_to_replace = self.preview_buttons_layout.takeAt(new_index)
			item_to_move = self.preview_buttons_layout.takeAt(row_index)
			self.preview_buttons_layout.insertItem(row_index, item_to_replace)
			self.preview_buttons_layout.insertItem(new_index, item_to_move)
		self.update_config()

	def update_config(self):
		selected_buttons = [self.get_button_name_by_index(self.preview_buttons_layout, i) for i in range(self.count_non_spacer_items(self.preview_buttons_layout))]
		config_data = configuration.settings_config
		config_data.visible_buttons = selected_buttons
		configuration.save_config(config_name="settings", data=config_data.model_dump())

	def visible_buttons_controls(self) -> QHBoxLayout:
		return self.create_control_buttons(
			move_buttons=True, delete_handler=self.add_available_item
		)

	def available_buttons_controls(self) -> QHBoxLayout:
		return self.create_control_buttons(
			move_buttons=False, add_handler=self.add_preview_item
		)

	def create_control_buttons(self, move_buttons: bool, delete_handler=None, add_handler=None) -> QHBoxLayout:
		item_control_buttons = QHBoxLayout()
		if move_buttons:
			item_move_buttons = QVBoxLayout()
			moveup_button = utils.create_button(
				on_click_handler=lambda: self.move_item("up"),
				icon_name="arrow_up",
				style=config.SETTINGS_REORDER_BUTTON_STYLE
			)
			movedown_button = utils.create_button(
				on_click_handler=lambda: self.move_item("down"),
				icon_name="arrow_down",
				style=config.SETTINGS_REORDER_BUTTON_STYLE
			)
			item_move_buttons.addWidget(moveup_button)
			item_move_buttons.addWidget(movedown_button)
			item_control_buttons.addLayout(item_move_buttons)
			delete_button = utils.create_button(
				on_click_handler=delete_handler,
				icon_name="delete",
				style=config.SETTINGS_DELETE_BUTTON_STYLE
			)
			item_control_buttons.addWidget(delete_button)
		else:
			add_button = utils.create_button(
				on_click_handler=add_handler,
				icon_name="add",
				style=config.SETTINGS_DELETE_BUTTON_STYLE
			)
			item_control_buttons.addWidget(add_button)
		item_control_buttons.setSpacing(5)
		return item_control_buttons

	def update_spacer_item(self):
		preview_count = self.count_non_spacer_items(self.preview_buttons_layout)
		available_count = self.count_non_spacer_items(self.available_buttons_layout)
		self.setFixedHeight(250+39*max(preview_count, available_count))

	def init_variables_settings(self):
		title = utils.create_label("Изменение переменных:", style=config.ABOUT_WINDOW_TITLE_STYLE)
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		variables_box = QHBoxLayout()
		labels_layout = QVBoxLayout()
		edits_layout = QVBoxLayout()
		uncuff_reason_label = utils.create_label("Причина uncuff:", style=config.ABOUT_WINDOW_TEXT_STYLE)
		self.uncuff_edit = utils.create_line(text=configuration.settings_config.default_reasons.uncuff, style=config.MAIN_APP_LINE_STYLE)
		self.uncuff_edit.textChanged.connect(self.line_edit_text_changed)
		force_rename_reason_label = utils.create_label("Причина force_rename:", style=config.ABOUT_WINDOW_TEXT_STYLE)
		force_rename_edit = utils.create_line(text=configuration.settings_config.default_reasons.force_rename, style=config.MAIN_APP_LINE_STYLE)
		force_rename_edit.textChanged.connect(self.line_edit_text_changed)

		width_slider_label = utils.create_label("Ширина кнопок:", style=config.ABOUT_WINDOW_TEXT_STYLE)
		width_slider = Slider(self)
		width_slider.setRange(80, 200)
		width_slider.setValue(configuration.settings_config.button_style.width)
		width_slider.setSuffix(' px')
		width_slider.setSingleStep(1)
		width_slider.setAccentColor(QColor(config.LINE_BACKGROUND_COLOR))
		width_slider.setBorderColor(QColor('#555555'))
		width_slider.setBackgroundColor(QColor('#555555'))
		width_slider.setTextColor(QColor(config.TEXT_COLOR))
		width_slider.setFixedHeight(27)
		width_slider.setFont(QFont('Columbia', 11, 500))
		width_slider.valueChanged.connect(self.slider_value_changed)


		labels_layout.addWidget(uncuff_reason_label)
		labels_layout.addWidget(force_rename_reason_label)
		labels_layout.addWidget(width_slider_label)
		edits_layout.addWidget(self.uncuff_edit)
		edits_layout.addWidget(force_rename_edit)
		edits_layout.addWidget(width_slider)

		variables_box.addLayout(labels_layout)
		variables_box.addLayout(edits_layout)
		self.main_layout.addWidget(title)
		self.main_layout.addLayout(variables_box)

	def line_edit_text_changed(self, value):
		config_data = configuration.settings_config
		if self.sender() == self.uncuff_edit:
			config_data.default_reasons.uncuff = value
		else:
			config_data.default_reasons.force_rename = value
		configuration.save_config(config_name="settings", data=config_data.model_dump())

	def slider_value_changed(self, value):
		settings_data = configuration.settings_config
		settings_data.button_style.width = value
		configuration.save_config(config_name="settings", data=settings_data.model_dump())

	def mousePressEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse press event.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragPos = event.globalPosition().toPoint()
			self.dragging = True

	def mouseMoveEvent(self, event: QMouseEvent) -> None:
		"""
		Moves the window when dragging the mouse.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if not self.dragging:
			return
		
		if event.buttons() == Qt.MouseButton.LeftButton:
			drag_pos = event.globalPosition().toPoint()
			self.move(self.pos() + drag_pos - self.dragPos)
			self.dragPos = drag_pos

	def mouseReleaseEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse release event.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragging = False

	def show_notification(self, text: str, notification_type: NotificationType=NotificationType.DEFAULT):
		self.notification = Notification(text, notification_type)
		self.notification.show()


class AboutWindow(QWidget):
	def __init__(self):
		super().__init__()
		self.setup_ui()
		self.dragging = False

	@classmethod
	def clear_layout(cls, layout):
		while layout.count():
			item = layout.takeAt(0)
			if widget := item.widget():
				widget.setParent(None)
			else:
				cls.clear_layout(item.layout())

	def setup_ui(self):
		self.setWindowTitle("Дополнительная информация")
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.setFixedSize(600, 800)
		self.setStyleSheet(config.BACKGROUND_COLOR_STYLE)
		self.main_layout = QVBoxLayout(self)
		control_layout = create_header_layout(instance=self)
		self.main_layout.addLayout(control_layout)
		self.init_reports_info_area()
		self.init_update_history_area()
		self.init_about_area()
		self.init_footer()

		self.worker = UpdateHistoryWorker()
		self.thread = QThread()
		self.worker.moveToThread(self.thread)
		self.worker.history_updated.connect(self.update_history_area)
		self.thread.started.connect(self.worker.load_commits)
		self.thread.finished.connect(self.thread.deleteLater)
		self.thread.start()

	def init_reports_info_area(self):
		reports_info_area = QVBoxLayout()
		reports_area = QVBoxLayout()
		reports_area_info = QHBoxLayout()
		title = utils.create_label(text="Статистика по репортам:", style=config.ABOUT_WINDOW_TITLE_STYLE)
		title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		reports_data = utils.get_reports_info()
		daily_reports, weekly_reports, monthly_reports, all_reports = utils.get_reports_count(reports_data=reports_data)
		daily_text = f"За сегодня: {daily_reports}\n({next(iter(reports_data["daily_reports"]))})"
		weekly_text = f"За неделю: {weekly_reports}\n(с {next(iter(reports_data["weekly_reports"]))})"
		monthly_text = f"За месяц: {monthly_reports}\n(с {next(iter(reports_data["monthly_reports"]))})"
		all_text = f"За всё время: {all_reports}\n(с {next(iter(reports_data["all_reports"]))})"
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
		reports_info_area.addWidget(title)
		reports_info_area.addLayout(reports_area)
		self.main_layout.addLayout(reports_info_area)

	def init_update_history_area(self):
		update_history_area_layout = QVBoxLayout()
		update_history_title = utils.create_label(text="История обновлений:", style=config.ABOUT_WINDOW_TITLE_STYLE)
		update_history_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		self.update_history_text_layout = QVBoxLayout()
		loading_text = utils.create_label(text="Загрузка...", style=config.ABOUT_WINDOW_SCROLL_AREA_TITLE_STYLE)
		loading_text.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
		loading_text.setWordWrap(True)
		self.update_history_text_layout.addWidget(loading_text)
		update_history_area_layout.addWidget(update_history_title)
		scroll_area = QScrollArea()
		scroll_area.setWidgetResizable(True)
		scroll_content = QWidget()
		scroll_content.setLayout(self.update_history_text_layout)
		scroll_area.setWidget(scroll_content)
		scroll_area.setStyleSheet(config.ABOUT_WINDOW_SCROLL_AREA_STYLE)
		update_history_area_layout.addWidget(scroll_area)
		self.main_layout.addLayout(update_history_area_layout)

	def update_history_area(self, commits: list[dict]):
		self.clear_layout(layout=self.update_history_text_layout)
		for commit in commits:
			time_label = utils.create_label(text=commit['date'], style=config.ABOUT_WINDOW_SCROLL_AREA_TITLE_STYLE)
			time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
			commit_label = utils.create_label(text=commit['message'], style=config.ABOUT_WINDOW_SCROLL_AREA_TEXT_STYLE)
			commit_label.setWordWrap(True)
			self.update_history_text_layout.addWidget(time_label)
			self.update_history_text_layout.addWidget(commit_label)

	def init_about_area(self):
		about_area = QVBoxLayout()
		title = utils.create_label(text="Немного о приложении:", style=config.ABOUT_WINDOW_TITLE_STYLE)
		title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		text = "Биндер для GTA 5 RP, обеспечивающий удобство в модерировании.\nО проблемах/предложениях сообщать через контактные данные ниже."
		text = utils.create_label(text=text, style=config.ABOUT_WINDOW_TEXT_STYLE)
		text.setWordWrap(True)
		about_area.addWidget(title)
		about_area.addWidget(text)
		self.main_layout.addLayout(about_area)

	def show_reports_info_page(self, period_type: str) -> None:
		"""
		Show the information page for the specified period type.

		Args:
		- period_type (str): The type of period for which to show the information.

		Returns:
		- None
		"""
		if hasattr(self, "reports_info_page") and not self.reports_info_page.isHidden():
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
		github_button = utils.create_button(on_click_handler=self.open_github, icon_name='github', style=config.ABOUT_WINDOW_ICONS_BUTTON_STYLE)
		discord_button = utils.create_button(on_click_handler=self.open_discord, icon_name='discord', style=config.ABOUT_WINDOW_ICONS_BUTTON_STYLE)
		footer_icons_layout.addWidget(github_button)
		footer_icons_layout.addWidget(discord_button)
		footer_layout.addLayout(footer_icons_layout)
		self.main_layout.addLayout(footer_layout)

	def open_github(self) -> None:
		"""
		Opens the GitHub repository page in the default web browser.

		Returns:
		- None
		"""
		webbrowser.open(url="https://github.com/JudeDM/binder/tree/main")

	def open_discord(self) -> None:
		"""
		Opens the Discord profile page in the default web browser.

		Returns:
		- None
		"""
		webbrowser.open(url="discord://-/users/208575718093750276")

	def mousePressEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse press event.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragPos = event.globalPosition().toPoint()
			self.dragging = True

	def mouseMoveEvent(self, event: QMouseEvent) -> None:
		"""
		Moves the window when dragging the mouse.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if not self.dragging:
			return
		
		if event.buttons() == Qt.MouseButton.LeftButton:
			drag_pos = event.globalPosition().toPoint()
			self.move(self.pos() + drag_pos - self.dragPos)
			self.dragPos = drag_pos

	def mouseReleaseEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse release event.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragging = False

	def closeEvent(self, event):
		self.thread.quit()
		self.thread.wait()
		event.accept()


class ReporsInfoWindow(QWidget):
	def __init__(self, period_type: int):
		super().__init__()
		self.dragging = False
		self.period_type = period_type
		self.setup_ui()

	def setup_ui(self):
		self.setWindowTitle("Статистика по репортам")
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.setMinimumSize(400, 200)
		self.setStyleSheet(config.BACKGROUND_COLOR_STYLE)
		self.main_layout = QVBoxLayout(self)
		control_layout = create_header_layout(self)
		self.main_layout.addLayout(control_layout)
		self.init_report_area()

	def init_report_area(self):
		reports_data = utils.get_reports_info()[self.period_type]
		text_area = QVBoxLayout()
		STATS_title = utils.create_label(text="Статистика по репортам:", style=config.ABOUT_WINDOW_TITLE_STYLE)
		STATS_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		text = "\n".join(f"{key} - {value}" for key, value in reports_data.items())
		text_label = utils.create_label(text=text, style=config.ABOUT_WINDOW_TEXT_STYLE)
		text_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		text_area.addWidget(STATS_title)
		text_area.addWidget(text_label)
		self.main_layout.addLayout(text_area)

	def mousePressEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse press event.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragPos = event.globalPosition().toPoint()
			self.dragging = True

	def mouseMoveEvent(self, event: QMouseEvent) -> None:
		"""
		Moves the window when dragging the mouse.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if not self.dragging:
			return
		
		if event.buttons() == Qt.MouseButton.LeftButton:
			drag_pos = event.globalPosition().toPoint()
			self.move(self.pos() + drag_pos - self.dragPos)
			self.dragPos = drag_pos

	def mouseReleaseEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse release event.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragging = False


class SettingsWindow(QDialog):
	def __init__(self, title: str, active_window: str = "report"):
		super().__init__()
		self.dragging = False
		self.setStyleSheet(config.SETTINGS_WINDOW_STYLE)
		palette = self.palette()
		palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Window, QColor(config.BACKGROUND_COLOR))
		self.setPalette(palette)
		self.active_window = active_window
		self.windows: dict[str, ViolationSettingsWindow | ReportSettingsWindow | TeleportSettingsWindow] = {
			"violation": ViolationSettingsWindow(settings_instance=self),
			"report": ReportSettingsWindow(settings_instance=self),
			"teleport": TeleportSettingsWindow(settings_instance=self)}
		self.config = []
		self.setWindowTitle(title)
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.setMinimumSize(1200, 550)
		self.main_layout = QVBoxLayout(self)
		control_layout = create_header_layout(self)
		self.header_window_buttons = QHBoxLayout()
		violation_window, reports_window, teleports_window = (
			utils.create_button(on_click_handler=self.show_violation_settings, text="Наказания", style=config.SETTINGS_HEADER_TABS_BUTTONS_STYLE),
			utils.create_button(on_click_handler=self.show_buttons_settings, text="Репорты", style=config.SETTINGS_HEADER_TABS_BUTTONS_STYLE),
			utils.create_button(on_click_handler=self.show_teleport_settings, text="Телепорты", style=config.SETTINGS_HEADER_TABS_BUTTONS_STYLE),
		)
		self.header_window_buttons.addWidget(violation_window)
		self.header_window_buttons.addWidget(reports_window)
		self.header_window_buttons.addWidget(teleports_window)
		self.main_layout.addLayout(control_layout)
		self.main_layout.addLayout(self.header_window_buttons)
		control_panel_layout = QHBoxLayout()
		add_column_button = utils.create_button(on_click_handler=self.add_item, text="Добавить кнопку", style=config.SETTINGS_FOOTER_BUTTONS_STYLE)
		save_button = utils.create_button(on_click_handler=self.save_config, text="Сохранить", style=config.SETTINGS_FOOTER_BUTTONS_STYLE)
		control_panel_layout.addWidget(add_column_button)
		control_panel_layout.addWidget(save_button)
		self.updateConfig()
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
		self.windows[self.active_window].update_layout()

	def updateConfig(self) -> None:
		if self.active_window == "teleport":
			self.config = configuration.teleports_config
		elif self.active_window == "report":
			self.config = configuration.reports_config
		elif self.active_window == "violation":
			self.config = configuration.violations_config

	def mousePressEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse press event.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragPos = event.globalPosition().toPoint()
			self.dragging = True

	def mouseMoveEvent(self, event: QMouseEvent) -> None:
		"""
		Moves the window when dragging the mouse.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if not self.dragging:
			return
		
		if event.buttons() == Qt.MouseButton.LeftButton:
			drag_pos = event.globalPosition().toPoint()
			self.move(self.pos() + drag_pos - self.dragPos)
			self.dragPos = drag_pos

	def mouseReleaseEvent(self, event: QMouseEvent) -> None:
		"""
		Handles the mouse release event.

		Args:
		- event (QMouseEvent): The mouse event.

		Returns:
		- None
		"""
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragging = False

	def add_item(self):
		if len(self.config) > MAX_COLS*10-1:
			return

		new_item = {"name": ""}
		if self.active_window == "report":
			new_item["text"] = ""
		elif self.active_window == "teleport":
			new_item["coords"] = ""
		elif self.active_window == "violation":
			new_item |= {"time": "", "reason": "", "type": "prison"}

		self.config.append(new_item)
		self.windows[self.active_window].update_layout()


	def remove_item(self, item_index):
		del self.config[item_index]
		self.windows[self.active_window].update_layout()

# TODO: реализовать, как в настроках приложения
	def move_item(self, index, action):
		lst = self.config
		if action == 'down' and index < len(lst) - 1:
			lst[index], lst[index + 1] = lst[index + 1], lst[index]
		elif action == 'up' and index > 0:
			lst[index], lst[index - 1] = lst[index - 1], lst[index]
		self.windows[self.active_window].update_layout()


	def show_violation_settings(self) -> None:
		"""
		Shows the Violation Settings window.

		Returns:
		- None
		"""
		self._change_window("violation")

	def show_buttons_settings(self) -> None:
		"""
		Shows the Report Settings window.

		Returns:
		- None
		"""
		self._change_window("report")

	def show_teleport_settings(self) -> None:
		"""
		Shows the Teleport Settings window.

		Returns:
		- None
		"""
		self._change_window("teleport")
	def _change_window(self, arg0):
		self.clear_layout(self.main_scroll_layout)
		self.active_window = arg0
		self.updateConfig()
		self.windows[self.active_window].update_layout()

	@classmethod
	def clear_layout(cls, layout):
		while layout.count():
			item = layout.takeAt(0)
			if widget := item.widget():
				widget.setParent(None)
			else:
				cls.clear_layout(item.layout())

	def item_control_buttons(self, item_index):
		item_control_buttons = QHBoxLayout()
		item_move_buttons = QVBoxLayout()
		delete_button, moveup_button, movedown_button = (
			utils.create_button(on_click_handler=lambda: self.remove_item(item_index), icon_name="delete", style=config.SETTINGS_DELETE_BUTTON_STYLE),
			utils.create_button(on_click_handler=lambda: self.move_item(item_index, "up"), icon_name="arrow_up", style=config.SETTINGS_REORDER_BUTTON_STYLE),
			utils.create_button(on_click_handler=lambda: self.move_item(item_index, "down"), icon_name="arrow_down", style=config.SETTINGS_REORDER_BUTTON_STYLE),
		)
		item_move_buttons.addWidget(moveup_button)
		item_move_buttons.addWidget(movedown_button)
		item_control_buttons.addLayout(item_move_buttons)
		item_control_buttons.addWidget(delete_button)
		item_control_buttons.setSpacing(5)
		return item_control_buttons

	def save_config(self):
		self.show_notification("Конфиг успешно сохранён.")
		if self.active_window == "teleport":
			configuration.save_config("teleports", self.config)
		elif self.active_window == "report":
			configuration.save_config("reports", self.config)
		elif self.active_window == "violation":
			configuration.save_config("violations", self.config)


	def show_notification(self, text: str, notification_type: NotificationType=NotificationType.DEFAULT):
		self.notification = Notification(text, notification_type)
		self.notification.show()


class ViolationSettingsWindow():
	def __init__(self, settings_instance: SettingsWindow):
		self.settings_instance = settings_instance

	@property
	def config(self) -> dict:
		return self.settings_instance.config
	
	@property
	def horizontal_scrollbar(self) -> QScrollBar:
		return self.settings_instance.horizontal_scrollbar
	
	@property
	def main_scroll_layout(self) -> QVBoxLayout:
		return self.settings_instance.main_scroll_layout

	def update_layout(self):
		current_scroll_position = self.horizontal_scrollbar.value()
		self.settings_instance.clear_layout(self.main_scroll_layout)
		self.violation_manager_layout = QHBoxLayout()
		for group_index, violation_group in enumerate(self.config[i:i+10] for i in range(0, len(self.config), 10)):
			self.create_violation_group_layout(violation_group, group_index)
		self.main_scroll_layout.addLayout(self.violation_manager_layout)
		self.horizontal_scrollbar.setValue(current_scroll_position)

	def create_violation_group_layout(self, violation_group, group_index):
		group_layout = QVBoxLayout()
		group_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
		type_title = utils.create_label(text="Тип:", style=config.VIOLATION_SETTINGS_SHORT_LABEL_STYLE)
		name_title = utils.create_label(text="Название кнопки:", style=config.SETTINGS_GAME_BOTTON_LABEL_STYLE)
		time_title = utils.create_label(text="Время:", style=config.VIOLATION_SETTINGS_SHORT_LABEL_STYLE)
		reason_title = utils.create_label(text="Причина:", style=config.VIOLATION_SETTINGS_LONG_LABEL_STYLE)
		titles_layout = QHBoxLayout()
		titles_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
		titles_layout.addWidget(type_title)
		titles_layout.addWidget(name_title)
		titles_layout.addWidget(time_title)
		titles_layout.addWidget(reason_title)
		group_layout.addLayout(titles_layout)
		for index, violation in enumerate(violation_group):
			violation_index = group_index * 10 + index
			row = QHBoxLayout()
			form_layout = QFormLayout()
			type_edit = QComboBox()
			type_edit.addItems(['prison', 'mute', 'ban'])
			type_edit.setStyleSheet(config.VIOLATION_SETTINGS_SHORT_STYLE)
			type_edit.setCurrentText(violation["type"] if "type" in violation else None)
			type_edit.activated.connect(lambda index, type_edit=type_edit, violation_index=violation_index: self.update_violation_field(violation_index, "type", type_edit.currentText()))
			name_edit = utils.create_line(text=violation["name"], style=config.SETTINGS_GAME_BOTTON_LINE_STYLE)
			name_edit.textChanged.connect(lambda text, index=violation_index: self.update_violation_field(index, "name", text))
			time_edit = utils.create_line(text=violation["time"], style=config.VIOLATION_SETTINGS_SHORT_STYLE)
			time_edit.textChanged.connect(lambda text, index=violation_index: self.update_violation_field(index, "time", text))
			reason_edit = utils.create_line(text=violation["reason"], style=config.VIOLATION_SETTINGS_LONG_STYLE)
			reason_edit.textChanged.connect(lambda text, index=violation_index: self.update_violation_field(index, "reason", text))
			row.addWidget(type_edit)
			row.addWidget(name_edit)
			row.addWidget(time_edit)
			row.addWidget(reason_edit)
			row.addLayout(self.settings_instance.item_control_buttons(violation_index))
			form_layout.addRow(row)
			group_layout.addLayout(form_layout)
		self.violation_manager_layout.addLayout(group_layout)

	def update_violation_field(self, item_index, field, new_name):
		self.config[item_index][field] = new_name


class ReportSettingsWindow():
	def __init__(self, settings_instance: SettingsWindow):
		self.settings_instance = settings_instance

	@property
	def config(self) -> dict:
		return self.settings_instance.config

	@property
	def horizontal_scrollbar(self) -> QScrollBar:
		return self.settings_instance.horizontal_scrollbar
	
	@property
	def main_scroll_layout(self) -> QVBoxLayout:
		return self.settings_instance.main_scroll_layout


	def update_layout(self):
		current_scroll_position = self.horizontal_scrollbar.value()
		self.settings_instance.clear_layout(self.main_scroll_layout)
		self.report_manager_layout = QHBoxLayout()
		for group_index, report_group in enumerate(self.config[i:i+10] for i in range(0, len(self.config), 10)):
			self.create_report_group_layout(report_group, group_index)
		self.main_scroll_layout.addLayout(self.report_manager_layout)
		self.horizontal_scrollbar.setValue(current_scroll_position)

	def create_report_group_layout(self, report_group, group_index):
		group_layout = QVBoxLayout()
		group_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
		name_title = utils.create_label(text="Название кнопки:", style=config.SETTINGS_GAME_BOTTON_LABEL_STYLE)
		text_title = utils.create_label(text="Текст ответа:", style=config.REPORT_SETTINGS_LONG_LABEL_STYLE)
		titles_layout = QHBoxLayout()
		titles_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
		titles_layout.addWidget(name_title)
		titles_layout.addWidget(text_title)
		group_layout.addLayout(titles_layout)
		for index, report in enumerate(report_group):
			report_index = group_index * 10 + index
			row = QHBoxLayout()
			form_layout = QFormLayout()

			name_edit = utils.create_line(text=report["name"], style=config.SETTINGS_GAME_BOTTON_LINE_STYLE)
			text_edit = utils.create_line(text=report["text"], style=config.REPORT_SETTINGS_LONG_STYLE)
			name_edit.textChanged.connect(lambda text, index=report_index: self.update_report_field(index, "name", text))
			text_edit.textChanged.connect(lambda text, index=report_index: self.update_report_field(index, "text", text))
			row.addWidget(name_edit)
			row.addWidget(text_edit)
			row.addLayout(self.settings_instance.item_control_buttons(report_index))
			form_layout.addRow(row)
			group_layout.addLayout(form_layout)
		self.report_manager_layout.addLayout(group_layout)

	def update_report_field(self, item_index: int, field: str, new_name: str) -> None:
		"""
		Update the specified field of the report at the given index.

		Args:
		- item_index (int): The index of the report to update.
		- field (str): The field of the report to update.
		- new_name (str): The new value for the specified field.

		Returns:
		- None
		"""
		self.config[item_index][field] = new_name


class TeleportSettingsWindow():
	def __init__(self, settings_instance: SettingsWindow):
		self.settings_instance = settings_instance

	@property
	def config(self) -> dict:
		return self.settings_instance.config

	@property
	def horizontal_scrollbar(self) -> QScrollBar:
		return self.settings_instance.horizontal_scrollbar
	
	@property
	def main_scroll_layout(self) -> QVBoxLayout:
		return self.settings_instance.main_scroll_layout


	def update_layout(self):
		current_scroll_position = self.horizontal_scrollbar.value()
		self.settings_instance.clear_layout(self.main_scroll_layout)
		self.teleport_manager_layout = QHBoxLayout()
		for group_index, teleport_group in enumerate(self.config[i:i+10] for i in range(0, len(self.config), 10)):
			self.create_teleport_group_layout(teleport_group, group_index)
		self.main_scroll_layout.addLayout(self.teleport_manager_layout)
		self.horizontal_scrollbar.setValue(current_scroll_position)

	def create_teleport_group_layout(self, teleport_group, group_index):
		group_layout = QVBoxLayout()
		group_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
		name_title = utils.create_label(text="Название кнопки:", style=config.SETTINGS_GAME_BOTTON_LABEL_STYLE)
		text_title = utils.create_label(text="Координаты:", style=config.TELEPORT_SETTINGS_LABEL_STYLE)
		titles_layout = QHBoxLayout()
		titles_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
		titles_layout.addWidget(name_title)
		titles_layout.addWidget(text_title)
		group_layout.addLayout(titles_layout)
		for index, report in enumerate(teleport_group):
			button_index = group_index * 10 + index
			row = QHBoxLayout()
			form_layout = QFormLayout()
			name_edit = utils.create_line(text=report["name"], style=config.SETTINGS_GAME_BOTTON_LINE_STYLE)
			coords_edit = utils.create_line(text=report["coords"], style=config.TELEPORT_SETTINGS_COORDINATES_LINE_STYLE)
			name_edit.textChanged.connect(lambda text, index=button_index: self.update_teleport_field(index, "name", text))
			coords_edit.textChanged.connect(lambda text, index=button_index: self.update_teleport_field(index, "coords", text))
			row.addWidget(name_edit)
			row.addWidget(coords_edit)
			row.addLayout(self.settings_instance.item_control_buttons(button_index))
			form_layout.addRow(row)
			group_layout.addLayout(form_layout)
		self.teleport_manager_layout.addLayout(group_layout)

	def update_teleport_field(self, item_index: int, field: str, new_name: str) -> None:
		"""
		Update the specified field of the teleport at the given index.

		Args:
		- item_index (int): The index of the report to update.
		- field (str): The field of the report to update.
		- new_name (str): The new value for the specified field.

		Returns:
		- None
		"""
		self.config[item_index][field] = new_name

class Binder(QWidget):
	def __init__(self):
		super().__init__()
		self.setFixedSize(WINDOW_WIDTH-1000, 400)
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
		self.violation_buttons: dict[QPushButton, dict] = {}
		self.report_buttons: dict[QPushButton, dict] = {}
		self.teleport_buttons: dict[QPushButton, dict] = {}
		self.report_labels = []
		self.is_violation_ui, self.is_report_ui, self.is_teleport_ui, self.is_additional_ui = False, False, False, False
		self.init_ui()
		timer = QTimer(self, timeout=self.update_buttons)
		timer.start(100)

	@property
	def admin_button_style(self) -> str:
		settings_config = configuration.settings_config
		button_style = settings_config.button_style
		style = config.ADMIN_BUTTON_STYLE
		match = re.search(r"%([\s\S]+?)%", style, flags=re.IGNORECASE)
		while match is not None:
			value = getattr(button_style, match.group(1))
			style = style[:match.start()] + str(value) + style[match.end():]
			match = re.search(r"%([\s\S]+?)%", style, flags=re.IGNORECASE)
		return style

	def init_ui_section(self, layout: QGridLayout, config: dict, handler, attribute_name: str):
		layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
		layout.setHorizontalSpacing(10)
		layout.setVerticalSpacing(5)
		
		for index, button_config in enumerate(config):
			row = index % MAX_BUTTONS_PER_COL
			col = index // MAX_BUTTONS_PER_COL
			if col >= MAX_COLS:
				continue
			button = utils.create_button(
				on_click_handler=partial(handler, button_config['type']) if attribute_name == 'violation_buttons' else handler,
				text=button_config['name'],
				style=self.admin_button_style
			)
			buttons = getattr(self, attribute_name)
			buttons[button] = button_config
			setattr(self, attribute_name, buttons)
			layout.addWidget(button, row, col)
		
		self.main_layout.insertLayout(0, layout)

	def init_violations_ui(self):
		self.violations_layout = QGridLayout()
		self.violation_buttons.clear()
		self.init_ui_section(layout=self.violations_layout, config=configuration.violations_config, handler=self.handle_additional_button_click, attribute_name='violation_buttons')

	def init_reports_ui(self):
		self.reports_layout = QGridLayout()
		self.report_buttons.clear()
		self.init_ui_section(layout=self.reports_layout, config=configuration.reports_config, handler=self.handle_report_button_click, attribute_name='report_buttons')

	def init_teleport_ui(self):
		self.teleports_layout = QGridLayout()
		self.teleport_buttons.clear()
		self.init_ui_section(layout=self.teleports_layout, config=configuration.teleports_config, handler=self.handle_teleport_button_click, attribute_name='teleport_buttons')

	def init_additional_ui(self):
		self.additional_layout = QVBoxLayout()
		self.additional_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
		self.additional_layout.setContentsMargins(0, 31, 0 ,0)
		self.init_sync_buttons()
		self.init_reports_counter()
		self.main_layout.addLayout(self.additional_layout)

	def init_reports_counter(self):
		self.reports_counter = QVBoxLayout()
		self.reports_counter.setSpacing(5)
		title = utils.create_label(text="Репортов за:", style=self.admin_button_style)
		title.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
		self.reports_counter.addWidget(title)
		labels = ["день:", "неделю:", "месяц:"]
		for label_text in labels:
			label = utils.create_label(text=label_text, style=self.admin_button_style)
			label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
			self.reports_counter.addWidget(label)
			self.report_labels.append(label)
		self.additional_layout.addLayout(self.reports_counter)
		self.update_report_labels()

	def init_sync_buttons(self):
		buttons_box = QVBoxLayout()
		settings_config = configuration.settings_config
		for button_name in settings_config.visible_buttons:
			button = utils.create_button(on_click_handler=partial(self.handle_additional_button_click, None), text=button_name, style=self.admin_button_style)
			buttons_box.addWidget(button)
		self.additional_layout.addLayout(buttons_box)

	def handle_report_button_click(self, text_to_copy=None):
		text_to_copy = text_to_copy or self.report_buttons.get(self.sender(), {}).get('text')
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

	def handle_teleport_button_click(self, text_to_copy=None):
		text_to_copy = text_to_copy or self.teleport_buttons.get(self.sender(), {}).get('coords')
		position = mouse.get_position()
		paste_to_console(f"tpc {text_to_copy}")
		mouse.click((LEFT+370, TOP+365))
		mouse.move(position)

	def init_ui(self):
		self.main_layout = QHBoxLayout()
		self.setLayout(self.main_layout)

	def handle_additional_button_click(self, button_type: str | None = None) -> None:
		"""
		Handles the click event of the uncuff button.

		Returns:
		- None
		"""
		button_name = self.sender().text()
		parsed_button_type = utils.ADDIDIONAL_BUTTONS[button_type] if button_type is not None else utils.ADDIDIONAL_BUTTONS[button_name]
		settings_config = configuration.settings_config
		if button_type is None and button_name not in configuration.settings_config.visible_buttons:
			return
		if hasattr(self, "gta_modal") and self.gta_modal is not None and not self.gta_modal.isHidden():
			return
		match parsed_button_type:
			case "fast":
				return self.process_fast_button_click(button_name=button_name)
			case "punish":
				violation_data = self.violation_buttons.get(self.sender(), {})
				self.gta_modal = GTAModal(
					command_name=button_type or button_name,
					time=violation_data.get('time', None),
					reason=violation_data.get('reason', None)
				)
			case "uncuff":
				self.gta_modal = GTAModal(command_name=button_name, reason=settings_config.default_reasons.uncuff)
			case "force_rename":
				self.gta_modal = GTAModal(command_name=button_name, reason=settings_config.default_reasons.force_rename)
			case _:
				self.gta_modal = GTAModal(command_name=button_name)
		self.gta_modal.show()

	def process_fast_button_click(self, button_name: str):
		position = mouse.get_position()
		settings_config = configuration.settings_config
		paste_to_console(button_name if button_name == "reof" else f"{button_name} {settings_config.user_gid}")
		mouse.click((LEFT+185, TOP+365))
		mouse.move(position)

	@classmethod
	def clear_layout(cls, layout):
		if layout is not None:
			while layout.count():
				item = layout.takeAt(0)
				if widget := item.widget():
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


	def update_buttons(self):
		if self.x() != LEFT+1000 or self.y() != TOP+4:
			self.setFixedSize(WINDOW_WIDTH-1000, 400)
			self.move(LEFT+1000, TOP+4)

		self.is_violation_ui = self.toggle_ui("console_tab", self.is_violation_ui, self.init_violations_ui, getattr(self, "violations_layout", None))
		self.is_report_ui = self.toggle_ui("reports_tab", self.is_report_ui, self.init_reports_ui, getattr(self, "reports_layout", None))
		self.is_teleport_ui = self.toggle_ui("teleport_tab", self.is_teleport_ui, self.init_teleport_ui, getattr(self, "teleports_layout", None))
		self.is_additional_ui = self.toggle_ui("admin_panel", self.is_additional_ui, self.init_additional_ui, getattr(self, "additional_layout", None))

	def start_window(self):
		self.show()

	def close_window(self):
		self.destroy()

	def update_click_data(self):
		today_date = datetime.now().strftime(utils.DATE_FORMAT)
		click_data = configuration.click_data
		click_data[today_date] = click_data.get(today_date, 0) + 1
		configuration.save_config(config_name="click_data", data=click_data)
		self.update_report_labels()


	def toggle_ui(self,  tab_name: str, is_ui: bool, init_ui_func: Callable[[], None], layout: QGridLayout) -> bool:
		"""
		Toggles the UI for the given tab.

		Args:
		- tab_name (str): The name of the tab to toggle.
		- is_ui (bool): Whether the UI is currently open or not.
		- init_ui_func (Callable[[], None]): The function to initialize the UI.
		- layout (QGridLayout): The layout to clear if the UI is closed.

		Returns:
		- bool: Whether the UI is currently open or not.
		"""
		is_open = utils.is_tab_open(tab_name, RIGHT, BOTTOM, LEFT, TOP)
		if is_open and not is_ui:
			is_ui = True
			init_ui_func()
		elif not is_open and is_ui:
			is_ui = False
			self.clear_layout(layout)
		return is_ui


def paste_to_console(text: str):
	mouse.click((LEFT+55, TOP+375))
	time.sleep(0.1)
	mouse.click((LEFT+500, TOP+335))
	keyboard.send('ctrl+a, backspace')
	pyperclip.copy(text)
	keyboard.send('ctrl+v')
	keyboard.send('enter')

def create_header_layout(instance: MainApp | Binder, title: str | None = None) -> QHBoxLayout:
	"""
	Creates a horizontal layout for the application controls.

	Args:
	- instance (MainApp | Binder): The instance of the main application or binder.

	Returns:
	- QHBoxLayout: The layout containing the minimize and close buttons.
	"""
	header_layout = QHBoxLayout()
	header_title = utils.create_label(text=title, style=config.WINDOW_HEADER_STYLE)
	control_layout = QHBoxLayout()
	minimize_button = utils.create_button(on_click_handler=instance.showMinimized, icon_name='minimize', style=config.CONTROL_BUTTONS_STYLE)
	close_button = utils.create_button(on_click_handler=instance.close_app if isinstance(instance, MainApp) else instance.close, icon_name='delete', style=config.CONTROL_BUTTONS_STYLE)
	if isinstance(instance, MainApp):
		control_layout.addWidget(instance.about_button)
		control_layout.addWidget(instance.settings_button)
	control_layout.addWidget(minimize_button)
	control_layout.addWidget(close_button)
	control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
	header_layout.addWidget(header_title)
	header_layout.addLayout(control_layout)
	return header_layout

def autologin():
	pyperclip.copy("/alogin13")
	keyboard.send('t')
	time.sleep(0.5)
	keyboard.send('ctrl+a')
	keyboard.send('ctrl+v')
	time.sleep(0.5)
	keyboard.send('enter')
	time.sleep(0.5)
	try:
		keyboard.send('asciitilde')
	except ValueError:
		keyboard.send('ё')
	time.sleep(0.5)
	mouse.click((LEFT+80, TOP+380))
	pyperclip.copy(configuration.password)
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

class CoordinateUpdater(QThread):
	coordinates_updated = pyqtSignal()

	def __init__(self):
		super().__init__()
		self._running = True

	def run(self):
		global WINDOW_WIDTH, WINDOW_HEIGHT, MAX_COLS, LEFT, TOP, RIGHT, BOTTOM
		while self._running:
			process = utils.get_process("GTA5.exe")
			if process is not None:
				button_width = configuration.settings_config.button_style.width
				LEFT, TOP, RIGHT, BOTTOM = utils.get_window_coordinates(process[0])
				if utils.has_border(process[0]):
					LEFT += 8
					TOP += 31
					RIGHT -= 9
					BOTTOM -= 9
				WINDOW_WIDTH = RIGHT - LEFT
				WINDOW_HEIGHT = BOTTOM - TOP
				MAX_COLS = (WINDOW_WIDTH - 1010 - max(150, button_width)) // (button_width + 10)
				self.coordinates_updated.emit()
			time.sleep(1)

	def stop(self):
		self._running = False
		self.wait()


def my_excepthook(type, value, tback):
	QMessageBox.critical(
			main_app, "Ошибка", f"{str(value)}\n{traceback.format_tb(tback)}\n\nПросьба сообщить об ошибке в дискдорд: JudeDM",
			QMessageBox.StandardButton.Close
		)
	sys.__excepthook__(type, value, tback)
 
sys.excepthook = my_excepthook

if __name__ == '__main__':
	mouse = utils.Mouse()
	coordinate_updater = CoordinateUpdater()
	coordinate_updater.start()
	app = QApplication(sys.argv)
	app.aboutToQuit.connect(coordinate_updater.stop)
	main_app = MainApp()
	main_app.show()
	sys.exit(app.exec())
