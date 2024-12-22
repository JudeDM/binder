import os
import subprocess

import utils
from coordinate_updater import CoordinateUpdater
from dialogs import AboutWindow
from PyQt6.QtCore import QMargins, QSize, QThread
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QLineEdit, QToolTip,
                             QVBoxLayout)
from pyqttoast import ToastPreset
from pyqttooltip import Tooltip, TooltipPlacement
from qtpy.QtWidgets import QPushButton
from settings import ButtonsSettings, ConfigSettingsWindow
from utils import (DraggableWidget, check_update, configuration,
                   create_header_layout, show_notification)

from binder import Binder


class MainApp(DraggableWidget):
	def __init__(self, app: QApplication, coordinate_updater: CoordinateUpdater):
		super().__init__()
		check_update()
		self.app = app
		self.coordinate_updater = coordinate_updater
		self.binder_running = False
		self.setWindowTitle('Настройки')
		self.setup_worker() #/ Ждём фикса pyqttoast под multiline
		self.setup_tooltip_settings()
		self.setup_labels_and_edits()
		self.setup_buttons()
		self.setup_ui()

	def setup_worker(self):
		from dialogs import UpdateHistoryWorker

		self.worker = UpdateHistoryWorker(commits_count=100)
		self.thread = QThread()
		self.worker.moveToThread(self.thread)
		self.worker.history_updated.connect(self.show_update_info)
		self.thread.started.connect(self.worker.load_commits)
		self.thread.finished.connect(self.thread.deleteLater)
		self.thread.start()

	def show_update_info(self, commits: list[dict]):
		if not commits:
			return
		config_data = configuration.settings_config
		if config_data.show_update_info is False:
			return
		config_data.show_update_info = False
		configuration.save_config(config_name="settings", data=config_data.model_dump())
		date = commits[0]['date']
		message = commits[0]['message']
		show_notification(
			parent=self,
			title=f"Информация об обновлении {date}",
			text=message,
			show_forever=True,
			preset=ToastPreset.INFORMATION_DARK
		)

	def setup_tooltip_settings(self):
		QToolTip.setFont(self.font())
		QApplication.instance().setStyle("Fusion")

	def setup_labels_and_edits(self):
		settings_data = configuration.settings_config
		self.id_on_launch = str(settings_data.user_gid)
		# self.password_edit = utils.create_line(text=configuration.password, class_name="password-line")
		# self.password_edit.setDisabled(True)
		# self.password_edit.setPlaceholderText("Временно отключено")
		# self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
		# self.password_edit.setFixedWidth(165)

		self.id_label = utils.create_label(text="ID на сервере:")
		# self.password_label = utils.create_label(text="Админ-пароль:")

		self.id_tooltip_icon = self.create_tooltip_icon(
			icon_name="tooltip", text="Используется для синхронизации dimension_sync и car_sync"
		)
		# self.password_tooltip_icon = self.create_tooltip_icon(
		# 	icon_name="tooltip", text="Используется для автовхода через F8"
		# )

		self.id_edit = utils.create_line(text=self.id_on_launch)
		self.id_edit.setFixedWidth(200)
		self.footer_settings_label = utils.create_label(text="Изменение настроек окон:")

	def create_tooltip_icon(self, icon_name: str, text: str) -> QPushButton:
		tooltip_icon = utils.create_button(icon_name=icon_name, class_name="tooltip-icon")
		tooltip = Tooltip(tooltip_icon, text)
		tooltip.setPlacement(TooltipPlacement.RIGHT)
		tooltip.setFallbackPlacements([TooltipPlacement.TOP, TooltipPlacement.BOTTOM])
		tooltip.setTriangleEnabled(True)
		tooltip.setMaximumWidth(250)
		tooltip.setBackgroundColor(QColor('#1D1D1E'))
		tooltip.setTextColor(QColor('#FFFFFF'))
		tooltip.setBorderEnabled(True)
		tooltip.setBorderColor(QColor('#FF7A2F'))
		tooltip.setFont(QFont('Arial', 10))
		tooltip.setMargins(QMargins(10, 8, 10, 8))
		return tooltip_icon

	def setup_buttons(self):
		self.settings_button = utils.create_button(
			on_click=self.show_settings_page, icon_name="settings", class_name="invisible-button window-control-button"
		)
		self.about_button = utils.create_button(
			on_click=self.show_about_page, icon_name="about", class_name="invisible-button window-control-button"
		)
		# self.show_password_button = utils.create_button(
		# 	on_click=self.toggle_password_visibility, icon_name="visible", class_name="password-mode-button"
		# )
		# self.show_password_button = utils.create_button(
		# 	class_name="password-mode-button"
		# )
		self.save_button = utils.create_button(on_click=self.save_settings_data, text="Сохранить", class_name="main-button")
		# self.show_password_button.setIconSize(QSize(21, 21))
		self.buttons_settings_button = utils.create_button(on_click=self.show_buttons_settings_page, text="Настройка кнопок", class_name="main-button")
		self.toggle_binder_button = utils.create_button(on_click=self.toggle_binder, text="Запустить биндер", class_name="main-button")

	def setup_ui(self):
		main_layout = QVBoxLayout()
		main_layout.addLayout(create_header_layout(self))
		main_layout.setContentsMargins(15, 15, 15, 15)

		main_controls_layout = QVBoxLayout()
		main_controls_layout.addLayout(self.create_columns_layout())
		main_controls_layout.addLayout(self.create_buttons_row())
		main_controls_layout.addWidget(self.toggle_binder_button)

		main_layout.addLayout(main_controls_layout)
		self.setLayout(main_layout)

	def create_columns_layout(self):
		columns_layout = QHBoxLayout()

		labels_column = QVBoxLayout()
		labels_column.addLayout(self.create_label_box(self.id_label, self.id_tooltip_icon))
		# labels_column.addLayout(self.create_label_box(self.password_label, self.password_tooltip_icon))

		edits_column = QVBoxLayout()
		edits_column.addWidget(self.id_edit)
		# password_edit_box = QHBoxLayout()
		# password_edit_box.setSpacing(0)
		# password_edit_box.addWidget(self.password_edit)
		# password_edit_box.addWidget(self.show_password_button)
		# edits_column.addLayout(password_edit_box)

		columns_layout.addLayout(labels_column)
		columns_layout.addLayout(edits_column)
		return columns_layout

	def create_label_box(self, label, tooltip_icon):
		label_box = QHBoxLayout()
		label_box.addWidget(label)
		# label_box.addWidget(tooltip_icon)
		return label_box

	def create_buttons_row(self):
		buttons_row = QHBoxLayout()
		buttons_row.setSpacing(10)
		buttons_row.setContentsMargins(0, 15, 0, 0)
		buttons_row.addWidget(self.save_button)
		buttons_row.addWidget(self.buttons_settings_button)
		return buttons_row

	def toggle_password_visibility(self):
		if self.password_edit.echoMode() == QLineEdit.EchoMode.Password:
			self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
			self.show_password_button.setIcon(utils.icons_map["invisible"])
		else:
			self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
			self.show_password_button.setIcon(utils.icons_map["visible"])

	def close_app(self):
		subprocess.run(
			["taskkill", "/F", "/PID", str(os.getpid())],
			shell=True,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL
		)

	def toggle_binder(self):
		if self.binder_running:
			self.stop_binder()
		else:
			self.start_binder()

	def start_binder(self):
		if not getattr(self, "isWarned", False):
			self.isWarned = True
			user_id = str(configuration.settings_config.user_gid)
			if self.id_on_launch == user_id:
				show_notification(parent=self, duration=8000, preset=ToastPreset.WARNING_DARK, maximum_width=600, text="Вы не поменяли ID после запуска биндера!\nНе забудьте его поменять, иначе можете помешать игрокам.")
				return
		self.toggle_binder_button.setText("Выключить биндер")
		self.binder_running = True
		self.initiate_binder()

	def initiate_binder(self):
		global binder
		binder = Binder(coordinate_updater=self.coordinate_updater, app=self)
		binder.setWindowIcon(self.app.windowIcon())
		binder.show()

	def stop_binder(self):
		self.toggle_binder_button.setText("Запустить биндер")
		self.binder_running = False
		if binder:
			binder.destroy()

	def show_buttons_settings_page(self):
		self.show_page("buttons_settings_page", ButtonsSettings, title="Настройка кнопок")

	def show_about_page(self):
		self.show_page("about_page", AboutWindow)

	def show_settings_page(self):
		self.show_page("settings_page", ConfigSettingsWindow)

	def show_page(self, page_attr, page_class, **kwargs):
		page = getattr(self, page_attr, None)
		if page and not page.isHidden():
			page.raise_()
			page.activateWindow()
		else:
			if 'app' in page_class.__init__.__code__.co_varnames:
				kwargs.setdefault('app', self.app)
			setattr(self, page_attr, page_class(**kwargs))
			page = getattr(self, page_attr)
			page.setWindowIcon(self.app.windowIcon())
			page.show()

	def save_settings_data(self):
		try:
			int(self.id_edit.text())
		except (ValueError, TypeError):
			show_notification(preset=ToastPreset.ERROR_DARK, text="ID должен быть целочисленным значением!")
			return
		self.update_configuration()

	def update_configuration(self):
		# configuration.password = self.password_edit.text()
		config_data = configuration.settings_config
		config_data.user_gid = int(self.id_edit.text())
		data = utils.SettingsStructure(**config_data.model_dump())
		show_notification(parent=self, text="Данные успешно сохранены!")
		configuration.save_config("settings", data.model_dump())

	def closeEvent(self, event):
		event.ignore()
		self.close_app()
