from hashlib import sha384
import time
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING

import binder_utils
from coordinate_updater import CoordinateUpdater
from dialogs import GTAModal
from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (QGridLayout, QHBoxLayout, QLayout, QPushButton,
                             QScrollArea, QVBoxLayout, QWidget)
from utils import (ADDIDIONAL_BUTTONS, DATE_FORMAT, configuration,
                   create_button, create_label, get_reports_count,
                   get_tabs_state, HorizontalScrollArea)

if TYPE_CHECKING:
	from app import MainApp

report_labels = ["день:", "неделю:", "месяц:"]


class WorkerSignals(QObject):
	clear_layout = pyqtSignal(QGridLayout)
	init_violations_ui = pyqtSignal()
	init_reports_ui = pyqtSignal()
	init_teleport_ui = pyqtSignal()
	init_additional_ui = pyqtSignal()

class Worker(QObject):
	tab_name_map = {
		"console_tab": {"layout": "violations_layout", "func": "init_violations_ui", "is_ui": "is_violation_ui"},
		"reports_tab": {"layout": "reports_layout", "func": "init_reports_ui", "is_ui": "is_report_ui"},
		"teleport_tab": {"layout": "teleports_layout", "func": "init_teleport_ui", "is_ui": "is_teleport_ui"},
		"admin_panel": {"layout": "additional_layout", "func": "init_additional_ui", "is_ui": "is_additional_ui"}
	}

	def __init__(self, binder_instance: 'Binder'):
		super().__init__()
		self.binder_instance = binder_instance
		self.signals = WorkerSignals()
		self._running = True

		self.is_violation_ui = False
		self.is_report_ui = False
		self.is_teleport_ui = False
		self.is_additional_ui = False

	def process(self):
		while self._running:
			if binder_utils.get_process("GTA5.exe") is None:
				time.sleep(5)
				continue
			tabs_state = get_tabs_state(
				self.binder_instance.right,
				self.binder_instance.bottom,
				self.binder_instance.left,
				self.binder_instance.top
			)
			for tab, is_open in tabs_state.items():
				tab_info = self.tab_name_map.get(tab)
				is_ui_attr = getattr(self, tab_info["is_ui"])
				try:
					if is_open and not is_ui_attr:
						setattr(self, tab_info["is_ui"], True)
						getattr(self.signals, tab_info["func"]).emit()
					elif not is_open and is_ui_attr:
						setattr(self, tab_info["is_ui"], False)
						self.signals.clear_layout.emit(getattr(self.binder_instance, tab_info["layout"]))
				except TypeError:
					pass
			time.sleep(0.1)

	def stop(self):
		self._running = False


class Binder(QWidget):
	def __init__(self, coordinate_updater: CoordinateUpdater, app: 'MainApp'):
		super().__init__()
		self.app = app
		self.worker = Worker(self)
		self.thread = QThread()

		self.worker.moveToThread(self.thread)

		self.worker.signals.clear_layout.connect(self.clear_layout)
		self.worker.signals.init_violations_ui.connect(self.init_violations_ui)
		self.worker.signals.init_reports_ui.connect(self.init_reports_ui)
		self.worker.signals.init_teleport_ui.connect(self.init_teleport_ui)
		self.worker.signals.init_additional_ui.connect(self.init_additional_ui)

		self.thread.started.connect(self.worker.process)
		self.thread.finished.connect(self.worker.stop)
		self.thread.finished.connect(self.thread.deleteLater)

		self.thread.start()
		self.coordinate_updater = coordinate_updater

		self.coordinate_updater.coordinates_updated.connect(self.update_window_size)
		self.left = self.coordinate_updater.left
		self.top = self.coordinate_updater.top
		self.right = self.coordinate_updater.right
		self.bottom = self.coordinate_updater.bottom
		self.window_width = self.coordinate_updater.window_width
		self.window_height = self.coordinate_updater.window_height
		self.setFixedSize(max(0, self.window_width-999), 420)

		self.move(self.left+1000, self.top-9)
		self.setWindowTitle("Панель")
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
		self.settings_config = configuration.settings_config
		self.button_style = None
		self.violation_buttons: dict[QPushButton, dict] = {}
		self.report_buttons: dict[QPushButton, dict] = {}
		self.teleport_buttons: dict[QPushButton, dict] = {}
		self.report_labels = []
		self.init_ui()


	def update_window_size(self, left, top, right, bottom, width, height):
		if self.width() != width - 1000:
			self.setFixedSize(width - 999, 420)
		if self.x() != left+1000 or self.y() != top+4:
			self.move(left+1000, top-9)
		self.left = left
		self.top = top
		self.right = right
		self.bottom = bottom
		self.window_width = width
		self.window_height = height

	def init_ui_section(self, scroll_area: QScrollArea, config: dict, handler, attribute_name: str):
		scroll_area.setMaximumHeight(500)

		layout = QGridLayout()
		layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
		layout.setHorizontalSpacing(10)
		layout.setVerticalSpacing(5)

		for index, button_config in enumerate(config):
			row = index % 10
			col = index // 10
			button = create_button(
				on_click=partial(handler, button_config['type']) if attribute_name == 'violation_buttons' else handler,
				text=button_config['name'],
				class_name="admin-button"
			)
			buttons = getattr(self, attribute_name)
			buttons[button] = button_config
			setattr(self, attribute_name, buttons)
			layout.addWidget(button, row, col)

		container_widget = QWidget()
		container_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		container_widget.setLayout(layout)

		scroll_area.setWidget(container_widget)
		scroll_area.setWidgetResizable(True)

	def init_violations_ui(self):
		self.violations_layout = HorizontalScrollArea()
		self.violation_buttons.clear()
		self.init_ui_section(scroll_area=self.violations_layout, config=configuration.violations_config, handler=self.handle_additional_button_click, attribute_name='violation_buttons')
		self.main_layout.insertWidget(0, self.violations_layout)

	def init_reports_ui(self):
		self.reports_layout = HorizontalScrollArea()
		self.report_buttons.clear()
		self.init_ui_section(scroll_area=self.reports_layout, config=configuration.reports_config, handler=self.handle_report_button_click, attribute_name='report_buttons')
		self.main_layout.insertWidget(0, self.reports_layout)

	def init_teleport_ui(self):
		self.teleports_layout = HorizontalScrollArea()
		self.teleport_buttons.clear()
		self.init_ui_section(scroll_area=self.teleports_layout, config=configuration.teleports_config, handler=self.handle_teleport_button_click, attribute_name='teleport_buttons')
		self.main_layout.insertWidget(0, self.teleports_layout)

	def init_additional_ui(self):
		self.additional_layout = QVBoxLayout()
		self.additional_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
		self.additional_layout.setContentsMargins(0, 42, 0 ,0)
		self.init_sync_buttons()
		self.init_reports_counter()
		self.main_layout.addLayout(self.additional_layout)

	def init_reports_counter(self):
		self.reports_counter = QVBoxLayout()
		self.reports_counter.setSpacing(5)
		title = create_label(text="Репортов за:", class_name="admin-label")
		title.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
		self.reports_counter.addWidget(title)
		for label_text in report_labels:
			label = create_label(text=label_text, class_name="admin-label")
			label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
			self.reports_counter.addWidget(label)
			self.report_labels.append(label)
		self.additional_layout.addLayout(self.reports_counter)
		self.update_report_labels()

	def init_sync_buttons(self):
		buttons_box = QVBoxLayout()
		buttons_box.setAlignment(Qt.AlignmentFlag.AlignRight)
		settings_config = configuration.settings_config
		for button_name in settings_config.visible_buttons:
			button = create_button(
				on_click=partial(self.handle_additional_button_click, None),
				text=button_name,
				class_name="admin-button"
				)
			buttons_box.addWidget(button)
		self.additional_layout.addLayout(buttons_box)

	def handle_report_button_click(self, text_to_copy=None):
		text_to_copy = text_to_copy or self.report_buttons.get(self.sender(), {}).get('text')
		position = binder_utils.mouse_position()
		now = datetime.now()
		start_date = datetime(now.year, 4, 1, 7)
		end_date = datetime(now.year, 4, 2, 7)
		binder_utils.mouse_click((self.left+245, (self.top+345 if start_date <= now < end_date else self.top+330)))
		binder_utils.keyboard_send(text_to_copy)
		if configuration.settings_config.auto_send.reports is True:
			binder_utils.keyboard_press("enter")
		binder_utils.mouse_move(position)
		self.update_click_data()

	def handle_teleport_button_click(self, text_to_copy=None):
		text_to_copy = text_to_copy or self.teleport_buttons.get(self.sender(), {}).get('coords')
		position = binder_utils.mouse_position()
		self.paste_to_console(text=f"tpc {text_to_copy}", paste_type="teleports")
		if configuration.settings_config.auto_send.teleports is True:
			binder_utils.keyboard_press("enter")
			binder_utils.mouse_click((self.left+370, self.top+365))
			binder_utils.mouse_move(position)

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
		parsed_button_type = ADDIDIONAL_BUTTONS[button_type] if button_type is not None else ADDIDIONAL_BUTTONS[button_name]
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
					coordinate_updater=self.coordinate_updater,
					command_name=button_type or button_name,
					time=violation_data.get('time', None),
					reason=violation_data.get('reason', None)
				)
			case "uncuff":
				self.gta_modal = GTAModal(coordinate_updater=self.coordinate_updater, command_name=button_name, reason=settings_config.default_reasons.uncuff)
			case "force_rename":
				self.gta_modal = GTAModal(coordinate_updater=self.coordinate_updater, command_name=button_name, reason=settings_config.default_reasons.force_rename)
			case _:
				self.gta_modal = GTAModal(coordinate_updater=self.coordinate_updater, command_name=button_name)
		self.gta_modal.show()

	def process_fast_button_click(self, button_name: str):
		position = binder_utils.mouse_position()
		settings_config = configuration.settings_config
		self.paste_to_console(text=button_name if button_name == "reof" else f"{button_name} {settings_config.user_gid}", paste_type="commands")
		if settings_config.auto_send.commands is True:
			binder_utils.keyboard_press("enter")
			binder_utils.mouse_click((self.left+370, self.top+365))
			binder_utils.mouse_move(position)

	@classmethod
	def clear_layout(cls, layout_or_widget: QLayout | QScrollArea):
		if isinstance(layout_or_widget, QScrollArea):
			widget = layout_or_widget.widget()
			if widget is not None:
				layout = widget.layout()
				if layout is not None:
					cls.clear_layout(layout)
			layout_or_widget.setParent(None)
			layout_or_widget.deleteLater()
		elif isinstance(layout_or_widget, QLayout):
			while layout_or_widget.count():
				item = layout_or_widget.takeAt(0)
				if widget := item.widget():
					widget.setParent(None)
					widget.deleteLater()
				elif sub_layout := item.layout():
					cls.clear_layout(sub_layout)

	def update_report_labels(self):
		daily_reports, weekly_reports, monthly_reports, all_reports = get_reports_count()
		for label, count in zip(self.report_labels[-3:], [daily_reports, weekly_reports, monthly_reports]):
			label.setText(f"{label.text()[:label.text().index(':')]}: {count}")

	def update_click_data(self):
		today_date = datetime.now().strftime(DATE_FORMAT)
		click_data = configuration.click_data
		click_data[today_date] = click_data.get(today_date, 0) + 1
		configuration.save_config(config_name="click_data", data=click_data)
		self.update_report_labels()

	def closeEvent(self, event):
		self.worker.stop()
		self.thread.quit()
		self.thread.wait()
		self.app.stop_binder()

	def paste_to_console(self, text: str, paste_type: str | None = None):
		binder_utils.mouse_click((self.left+55, self.top+375))
		time.sleep(0.1)
		binder_utils.mouse_click((self.left+500, self.top+335))
		binder_utils.keyboard_press("ctrl+a backspace")
		binder_utils.keyboard_send(text)
		time.sleep(0.1)
