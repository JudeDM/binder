import time
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Union

import binder_utils
import keyboard
import pyperclip
from coordinate_updater import CoordinateUpdater
from dialogs import GTAModal
from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (QGridLayout, QHBoxLayout, QLayout, QPushButton,
							 QScrollArea, QVBoxLayout, QWidget)
from utils import (ADDITIONAL_BUTTONS, DATE_FORMAT, HorizontalScrollArea,
				   Mouse, configuration, create_button, create_label,
				   get_reports_count, get_tabs_state)

if TYPE_CHECKING:
	from app import MainApp

from dataclasses import dataclass


@dataclass
class TabInfo:
	layout: str
	init_signal: str
	is_ui: str


class WorkerSignals(QObject):
	clear_layout = pyqtSignal(object)
	init_violations_ui = pyqtSignal()
	init_reports_ui = pyqtSignal()
	init_teleport_ui = pyqtSignal()
	init_additional_ui = pyqtSignal()


class Worker(QObject):
	tab_name_map: dict[str, TabInfo] = {
		"console_tab": TabInfo(
			layout="violations_layout",
			init_signal="init_violations_ui",
			is_ui="is_violation_ui",
		),
		"reports_tab": TabInfo(
			layout="reports_layout",
			init_signal="init_reports_ui",
			is_ui="is_report_ui",
		),
		"teleport_tab": TabInfo(
			layout="teleports_layout",
			init_signal="init_teleport_ui",
			is_ui="is_teleport_ui",
		),
		"admin_panel": TabInfo(
			layout="additional_layout",
			init_signal="init_additional_ui",
			is_ui="is_additional_ui",
		),
	}

	def __init__(self, binder_instance: 'Binder'):
		super().__init__()
		self.binder_instance = binder_instance
		self.signals = WorkerSignals()
		self._running = True

		self.ui_states: dict[str, bool] = {
			tab_info.is_ui: False for tab_info in self.tab_name_map.values()
		}

	def process(self):
		while self._running:
			if binder_utils.get_process("GTA5.exe") is None:
				time.sleep(5)
				continue

			tabs_state = get_tabs_state(
				self.binder_instance.right,
				self.binder_instance.bottom,
				self.binder_instance.left,
				self.binder_instance.top,
			)

			for tab, is_open in tabs_state.items():
				tab_info = self.tab_name_map.get(tab)
				if not tab_info:
					continue

				current_state = self.ui_states.get(tab_info.is_ui, False)
				if is_open and not current_state:
					init_signal = getattr(self.signals, tab_info.init_signal, None)
					if init_signal:
						init_signal.emit()
					self.ui_states[tab_info.is_ui] = True
				elif not is_open and current_state:
					layout = getattr(self.binder_instance, tab_info.layout, None)
					if layout:
						self.signals.clear_layout.emit(layout)
					self.ui_states[tab_info.is_ui] = False

			time.sleep(0.2)

	def stop(self):
		self._running = False


class Binder(QWidget):
	def __init__(self, coordinate_updater: CoordinateUpdater, app: 'MainApp'):
		super().__init__()
		self.app = app
		self.coordinate_updater = coordinate_updater

		self.worker = Worker(self)
		self.thread = QThread()

		self.worker.moveToThread(self.thread)
		self._setup_signals()

		self.thread.started.connect(self.worker.process)
		self.thread.finished.connect(self.worker.stop)
		self.thread.finished.connect(self.thread.deleteLater)

		self.mouse = Mouse()

		self.left = self.coordinate_updater.left
		self.top = self.coordinate_updater.top
		self.right = self.coordinate_updater.right
		self.bottom = self.coordinate_updater.bottom
		self.window_width = self.coordinate_updater.window_width
		self.window_height = self.coordinate_updater.window_height

		self.set_fixed_size_and_position()

		self.setWindowTitle("Панель")
		self.setWindowFlags(
			Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
		)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

		self.button_style = None

		self.violation_buttons: dict[QPushButton, dict] = {}
		self.report_buttons: dict[QPushButton, dict] = {}
		self.teleport_buttons: dict[QPushButton, dict] = {}
		self.report_labels: list = []

		self.init_ui()
		self.thread.start()

		self.coordinate_updater.coordinates_updated.connect(self.update_window_size)

	def _setup_signals(self):
		self.worker.signals.clear_layout.connect(self.clear_layout)
		self.worker.signals.init_violations_ui.connect(self.init_violations_ui)
		self.worker.signals.init_reports_ui.connect(self.init_reports_ui)
		self.worker.signals.init_teleport_ui.connect(self.init_teleport_ui)
		self.worker.signals.init_additional_ui.connect(self.init_additional_ui)

	def set_fixed_size_and_position(self):
		self.setFixedSize(max(0, self.window_width - 999), 430)
		self.move(self.left + 989, self.top - 13)

	def update_window_size(
		self,
		left: int,
		top: int,
		right: int,
		bottom: int,
		width: int,
		height: int,
	):
		new_width = width - 999
		if self.width() != new_width:
			self.setFixedSize(new_width, 430)

		new_x = left + 989
		new_y = top - 13
		if self.x() != new_x or self.y() != new_y:
			self.move(new_x, new_y)

		self.left = left
		self.top = top
		self.right = right
		self.bottom = bottom
		self.window_width = width
		self.window_height = height

	def init_ui(self):
		self.main_layout = QHBoxLayout()
		self.main_layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.main_layout)

	def init_ui_section(
		self,
		scroll_area: QScrollArea,
		config: list,
		handler,
		buttons_dict: dict[QPushButton, dict],
	):
		scroll_area.setFixedHeight(400)

		layout = QGridLayout()
		layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
		layout.setHorizontalSpacing(10)
		layout.setVerticalSpacing(5)

		for index, button_config in enumerate(config):
			row = index % 10
			col = index // 10
			button = create_button(
				on_click=partial(handler, button_config.get("type")),
				text=button_config["name"],
				class_name="admin-button",
			)
			buttons_dict[button] = button_config
			layout.addWidget(button, row, col)
		container_widget = QWidget()
		container_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		container_widget.setLayout(layout)

		scroll_area.setWidget(container_widget)
		scroll_area.setWidgetResizable(True)

	def init_violations_ui(self):
		self.violations_layout = HorizontalScrollArea()
		self.violation_buttons.clear()
		self.init_ui_section(
			scroll_area=self.violations_layout,
			config=configuration.violations_config,
			handler=self.handle_additional_button_click,
			buttons_dict=self.violation_buttons,
		)
		self.main_layout.insertWidget(0, self.violations_layout)

	def init_reports_ui(self):
		self.reports_layout = HorizontalScrollArea()
		self.report_buttons.clear()
		self.init_ui_section(
			scroll_area=self.reports_layout,
			config=configuration.reports_config,
			handler=self.handle_report_button_click,
			buttons_dict=self.report_buttons,
		)
		self.main_layout.insertWidget(0, self.reports_layout)

	def init_teleport_ui(self):
		self.teleports_layout = HorizontalScrollArea()
		self.teleport_buttons.clear()
		self.init_ui_section(
			scroll_area=self.teleports_layout,
			config=configuration.teleports_config,
			handler=self.handle_teleport_button_click,
			buttons_dict=self.teleport_buttons,
		)
		self.main_layout.insertWidget(0, self.teleports_layout)

	def init_additional_ui(self):
		self.additional_layout = QVBoxLayout()
		self.additional_layout.setAlignment(
			Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
		)
		self.additional_layout.setContentsMargins(0, 56, 0, 0)

		self.init_sync_buttons()
		self.init_reports_counter()

		self.main_layout.addLayout(self.additional_layout)

	def init_reports_counter(self):
		self.reports_counter = QVBoxLayout()
		self.reports_counter.setSpacing(5)

		title = create_label(text="Репортов (д | н | м):", class_name="admin-label")
		title.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
		self.report_counts = create_label(text="0 | 0 | 0", class_name="admin-label")
		self.report_counts.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
		self.reports_counter.addWidget(title)
		self.reports_counter.addWidget(self.report_counts)
		self.additional_layout.addLayout(self.reports_counter)
		self.update_report_labels()

	def init_sync_buttons(self):
		buttons_columns = QHBoxLayout()
		buttons_box = None
		buttons_columns.setAlignment(Qt.AlignmentFlag.AlignRight)
		buttons_columns.setSpacing(5)

		buttons_per_row = 8

		visible_buttons = configuration.settings_config.visible_buttons

		for index, button_name in enumerate(visible_buttons):
			if index % buttons_per_row == 0:
				buttons_box = QVBoxLayout()
				buttons_box.setSpacing(5)
				buttons_box.setAlignment(Qt.AlignmentFlag.AlignTop)
				buttons_columns.addLayout(buttons_box)

			button = create_button(
				on_click=partial(self.handle_additional_button_click, None),
				text=button_name,
				class_name="admin-button",
			)
			buttons_box.addWidget(button)

		self.additional_layout.addLayout(buttons_columns)





	def handle_report_button_click(self, button_type: str | None = None):
		text_to_copy = (
			button_type
			or self.report_buttons.get(self.sender(), {}).get("text")
			or ""
		)
		position = self.mouse.get_position()
		now = datetime.now()
		start_date = datetime(now.year, 4, 1, 7)
		end_date = datetime(now.year, 4, 2, 7)
		y_position = self.top + 345 if start_date <= now < end_date else self.top + 330
		self.mouse.click((self.left + 245, y_position))
		pyperclip.copy(text_to_copy)
		pyperclip.copy(text_to_copy)  # На всякий случай
		keyboard.send("ctrl+v")

		if configuration.settings_config.auto_send.reports:
			keyboard.send("enter")

		self.mouse.move(position)
		self.update_click_data()

	def handle_teleport_button_click(self, button_type: str | None = None):
		text_to_copy = (
			button_type
			or self.teleport_buttons.get(self.sender(), {}).get("coords")
			or ""
		)
		position = self.mouse.get_position()
		self.paste_to_console(text=f"tpc {text_to_copy}")

		if configuration.settings_config.auto_send.teleports:
			keyboard.send("enter")
			self.mouse.click((self.left + 370, self.top + 365))
			self.mouse.move(position)

	def handle_additional_button_click(self, button_type: str | None = None) -> None:
		button = self.sender()
		if not isinstance(button, QPushButton):
			return

		button_name = button.text()
		parsed_button_type = (
			ADDITIONAL_BUTTONS.get(button_type) if button_type else ADDITIONAL_BUTTONS.get(button_name)
		)

		if button_type is None and button_name not in configuration.settings_config.visible_buttons:
			return

		gta_modal_active = hasattr(self, "gta_modal") and self.gta_modal and not self.gta_modal.isHidden()
		if gta_modal_active:
			return

		match parsed_button_type:
			case "fast":
				self.process_fast_button_click(button_name=button_name)
				return
			case "punish":
				violation_data = self.violation_buttons.get(button, {})
				self.gta_modal = GTAModal(
					coordinate_updater=self.coordinate_updater,
					command_name=button_type or button_name,
					time=violation_data.get("time"),
					reason=violation_data.get("reason"),
				)
			case "uncuff":
				self.gta_modal = GTAModal(
					coordinate_updater=self.coordinate_updater,
					command_name=button_name,
					reason=configuration.settings_config.default_reasons.uncuff,
				)
			case "mute_report":
				self.gta_modal = GTAModal(
					coordinate_updater=self.coordinate_updater,
					command_name=button_name,
					reason=configuration.settings_config.default_reasons.mute_report,
				)
			case "force_rename":
				self.gta_modal = GTAModal(
					coordinate_updater=self.coordinate_updater,
					command_name=button_name,
					reason=configuration.settings_config.default_reasons.force_rename,
				)
			case _:
				self.gta_modal = GTAModal(
					coordinate_updater=self.coordinate_updater,
					command_name=button_name,
				)

		self.gta_modal.show()

	def process_fast_button_click(self, button_name: str):
		position = self.mouse.get_position()
		command = button_name if button_name == "reof" else f"{button_name} {configuration.settings_config.user_gid}"
		self.paste_to_console(text=command)

		if configuration.settings_config.auto_send.commands:
			keyboard.send("enter")
			self.mouse.click((self.left + 290, self.top + 365))
			self.mouse.move(position)

	@classmethod
	def clear_layout(cls, layout_or_widget: Union[QLayout, HorizontalScrollArea]):
		if isinstance(layout_or_widget, HorizontalScrollArea):
			widget = layout_or_widget.widget()
			if widget:
				layout = widget.layout()
				if layout:
					cls.clear_layout(layout)
			layout_or_widget.setParent(None)
			layout_or_widget.deleteLater()
		elif isinstance(layout_or_widget, QLayout):
			while layout_or_widget.count():
				item = layout_or_widget.takeAt(0)
				widget = item.widget()
				if widget:
					widget.setParent(None)
					widget.deleteLater()
				else:
					sub_layout = item.layout()
					if sub_layout:
						cls.clear_layout(sub_layout)

	def update_report_labels(self):
		daily, weekly, monthly, _ = get_reports_count()
		self.report_counts.setText(f"{daily} | {weekly} | {monthly}")

	def update_click_data(self):
		today_date = datetime.now().strftime(DATE_FORMAT)
		click_data = configuration.click_data
		click_data[today_date] = click_data.get(today_date, 0) + 1
		configuration.save_config(config_name="click_data", data=click_data)
		self.update_report_labels()

	def closeEvent(self, event):
		self.worker.signals.clear_layout.disconnect()
		self.worker.signals.init_violations_ui.disconnect()
		self.worker.signals.init_reports_ui.disconnect()
		self.worker.signals.init_teleport_ui.disconnect()
		self.worker.signals.init_additional_ui.disconnect()
		self.worker.stop()
		self.thread.quit()
		self.thread.wait()
		self.app.stop_binder()
		super().closeEvent(event)

	def paste_to_console(self, text: str):
		self.mouse.click((self.left + 55, self.top + 375))
		time.sleep(0.1)
		self.mouse.click((self.left + 500, self.top + 335))
		keyboard.send("ctrl+a, backspace")
		pyperclip.copy(text)
		keyboard.send("ctrl+v")
		time.sleep(0.1)
