from PyQt6.QtCore import QEasingCurve, QObject, QPropertyAnimation, Qt
from PyQt6.QtGui import QColor, QFont, QIntValidator
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox,
                             QGraphicsOpacityEffect, QGridLayout, QHBoxLayout,
                             QLayout, QPlainTextEdit, QPushButton, QScrollArea,
                             QScrollBar, QSizePolicy, QSpacerItem,
                             QTableWidget, QVBoxLayout, QWidget)
from pyqt_advanced_slider import Slider
from pyqttoast import ToastPreset
from utils import (ADDITIONAL_BUTTONS, DraggableWidget, HorizontalScrollArea,
                   configuration, create_button, create_header_layout,
                   create_label, create_line, parse_stylesheet, replacements,
                   show_notification)
from widgets import MovableButton

autosend_categories = [
	("Репорты", "reports"),
	("Наказания", "violations"),
	("Телепорты", "teleports"),
	("Команды", "commands")
]


class ConfigSettingsWindow(DraggableWidget):
	def __init__(self):
		super().__init__()
		self.visible_buttons = configuration.settings_config.visible_buttons
		self.setup_ui()

	def setup_ui(self):
		self.setWindowTitle("Настройки")
		self.setFixedWidth(500)
		self.main_layout = QVBoxLayout(self)
		control_layout = create_header_layout(instance=self)
		self.main_layout.addLayout(control_layout)
		self.init_variables_settings()
		self.init_autosend_settings()
		self.init_additional_buttons_settings()

	def init_additional_buttons_settings(self) -> None:
		titles_layout = QHBoxLayout()
		self.preview_buttons_layout = QVBoxLayout()
		columns_layout = QHBoxLayout()
		self.available_buttons_layout = QVBoxLayout()
		self.available_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

		title = create_label("Изменение кнопок боковой панели", class_name="title-label")
		selected_buttons_title = create_label("Выбранные кнопки", class_name="subtitle-label")
		available_buttons_title = create_label("Доступные кнопки", class_name="subtitle-label")
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		selected_buttons_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		available_buttons_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

		titles_layout.addWidget(selected_buttons_title)
		titles_layout.addWidget(available_buttons_title)
		self.main_layout.addWidget(title)
		self.main_layout.addLayout(titles_layout)
		for button_name in reversed(self.visible_buttons):
			self.add_button_row(button_name=button_name, layout=self.preview_buttons_layout, controls=self.visible_buttons_controls)
		for button_name in [button for button in ADDITIONAL_BUTTONS.keys() if button not in self.visible_buttons]:
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
		button = create_button(text=text, class_name="admin-button")
		button_row = QHBoxLayout()
		button_row.addWidget(button)
		button_row.addLayout(control_layout)
		button_row.setSpacing(10)
		button_row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
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
			moveup_button = create_button(
				on_click=lambda: self.move_item("up"),
				icon_name="arrow_up",
				class_name="invisible-button item-move-button"
			)
			movedown_button = create_button(
				on_click=lambda: self.move_item("down"),
				icon_name="arrow_down",
				class_name="invisible-button item-move-button"
			)
			item_move_buttons.addWidget(moveup_button)
			item_move_buttons.addWidget(movedown_button)
			item_move_buttons.setSpacing(0)
			item_control_buttons.setContentsMargins(0, 0, 0, 0)
			item_control_buttons.addLayout(item_move_buttons)
			delete_button = create_button(
				on_click=delete_handler,
				icon_name="delete",
				class_name="invisible-button item-delete-button"
			)
			item_control_buttons.addWidget(delete_button)
		else:
			add_button = create_button(
				on_click=add_handler,
				icon_name="add",
				class_name="invisible-button"
			)
			item_control_buttons.addWidget(add_button)
		item_control_buttons.setSpacing(5)
		return item_control_buttons


	def update_spacer_item(self):
		preview_count = self.count_non_spacer_items(self.preview_buttons_layout)
		available_count = self.count_non_spacer_items(self.available_buttons_layout)
		self.setFixedHeight(498+40*max(preview_count, available_count))

	def init_variables_settings(self):
		title = create_label(text="Изменение переменных", class_name="title-label")
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		variables_box = QHBoxLayout()
		labels_layout = QVBoxLayout()
		edits_layout = QVBoxLayout()
		uncuff_reason_label = create_label("Причина uncuff:")
		self.uncuff_edit = create_line(text=configuration.settings_config.default_reasons.uncuff)
		self.uncuff_edit.textChanged.connect(self.line_edit_text_changed)
		mute_report_reason_label = create_label("Причина mute_report:")
		self.mute_report_edit = create_line(text=configuration.settings_config.default_reasons.mute_report)
		self.mute_report_edit.textChanged.connect(self.line_edit_text_changed)
		force_rename_reason_label = create_label("Причина force_rename:")
		self.force_rename_edit = create_line(text=configuration.settings_config.default_reasons.force_rename)
		self.force_rename_edit.textChanged.connect(self.line_edit_text_changed)

		labels_layout.addWidget(uncuff_reason_label)
		labels_layout.addWidget(force_rename_reason_label)
		labels_layout.addWidget(mute_report_reason_label)
		edits_layout.addWidget(self.uncuff_edit)
		edits_layout.addWidget(self.force_rename_edit)
		edits_layout.addWidget(self.mute_report_edit)

		variables_box.addLayout(labels_layout)
		variables_box.addLayout(edits_layout)
		self.main_layout.addWidget(title)
		self.main_layout.addLayout(variables_box)


	def init_autosend_settings(self):
		title = create_label(text="Изменение автоматической отправки", class_name="title-label")
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		description = create_label(text="В случае, если чекбокс не активирован, то при нажатии на кнопку в интерфейсе биндера сообщение или команда будут вставлены в поле для ввода, но не отправлены.")
		description.setWordWrap(True)
		autosend_settings = configuration.settings_config.auto_send

		table_widget = QTableWidget()
		table_widget.setShowGrid(False)
		table_widget.setRowCount(2)
		table_widget.setColumnCount(len(autosend_categories))

		for col, (label_text, setting_name) in enumerate(autosend_categories):
			label_widget = QWidget()
			label_layout = QHBoxLayout(label_widget)
			label = create_label(label_text)
			label.setAlignment(Qt.AlignmentFlag.AlignCenter)
			label_layout.addWidget(label)
			label_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
			label_layout.setContentsMargins(0, 0, 0, 0)
			label_widget.setLayout(label_layout)

			checkbox_widget = QWidget()
			checkbox_layout = QHBoxLayout(checkbox_widget)
			checkbox = QCheckBox()
			checkbox.setChecked(getattr(autosend_settings, setting_name))
			checkbox.stateChanged.connect(self.checkbox_state_changed)
			setattr(self, f"{setting_name}_checkbox", checkbox)
			checkbox_layout.addWidget(checkbox)
			checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
			checkbox_layout.setContentsMargins(0, 0, 0, 0)
			checkbox_widget.setLayout(checkbox_layout)

			table_widget.setCellWidget(0, col, label_widget)
			table_widget.setCellWidget(1, col, checkbox_widget)

		table_widget.horizontalHeader().setVisible(False)
		table_widget.verticalHeader().setVisible(False)
		table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
		table_widget.setSelectionMode(QAbstractItemView.NoSelection)
		table_widget.setFixedHeight(60)
		table_widget.setFixedWidth(len(autosend_categories) * 120)
		for col in range(len(autosend_categories)):
			table_widget.setColumnWidth(col, 120)


		self.main_layout.addWidget(title)
		self.main_layout.addWidget(description)
		self.main_layout.addWidget(table_widget)

	def checkbox_state_changed(self, state: int):
		bool_state = state == 2
		config_data = configuration.settings_config
		if self.sender() == self.reports_checkbox:
			config_data.auto_send.reports = bool_state
		elif self.sender() == self.violations_checkbox:
			config_data.auto_send.violations = bool_state
		elif self.sender() == self.teleports_checkbox:
			config_data.auto_send.teleports = bool_state
		elif self.sender() == self.commands_checkbox:
			config_data.auto_send.commands = bool_state
		configuration.save_config(config_name="settings", data=config_data.model_dump())

	def line_edit_text_changed(self, value):
		config_data = configuration.settings_config
		if self.sender() == self.uncuff_edit:
			config_data.default_reasons.uncuff = value
		elif self.sender() == self.mute_report_edit:
			config_data.default_reasons.mute_report = value
		elif self.sender() == self.force_rename_edit:
			config_data.default_reasons.force_rename = value
		configuration.save_config(config_name="settings", data=config_data.model_dump())

class ButtonsSettings(DraggableWidget):
	def __init__(self, title: str, app: QApplication):
		super().__init__()
		self.animations = []
		self.app = app
		self.active_window = None
		self.is_click_process = False
		self.active_button: MovableButton | None = None
		self.reports_config = configuration.reports_config.copy()
		self.teleports_config = configuration.teleports_config.copy()
		self.violations_config = configuration.violations_config.copy()
		self.setWindowTitle(title)
		self.setFixedSize(1200, 550)

		self.violations_grid_widget = QWidget()
		self.violations_grid_widget.setLayout(QGridLayout())
		self.reports_grid_widget = QWidget()
		self.reports_grid_widget.setLayout(QGridLayout())
		self.teleports_grid_widget = QWidget()
		self.teleports_grid_widget.setLayout(QGridLayout())

		self.init_ui()
		self.show_report_settings()
		self.setAcceptDrops(True)

	def fade_in_widget(self, widget, duration=300):
		effect = QGraphicsOpacityEffect()
		widget.setGraphicsEffect(effect)
		animation = QPropertyAnimation(effect, b"opacity")
		animation.setDuration(duration)
		animation.setStartValue(0)
		animation.setEndValue(1)
		animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
		animation.start()
		self.animations.append(animation)

	def fade_out_widget(self, widget, on_finished, duration=300):
		effect = QGraphicsOpacityEffect()
		widget.setGraphicsEffect(effect)
		animation = QPropertyAnimation(effect, b"opacity")
		animation.setDuration(duration)
		animation.setStartValue(1)
		animation.setEndValue(0)
		animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
		animation.finished.connect(on_finished)
		animation.start()
		self.animations.append(animation)

	def init_ui(self):
		self.main_layout = QVBoxLayout(self)
		self.init_header()
		self.middle_layout = QHBoxLayout()
		self.middle_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
		self.middle_layout.setContentsMargins(0, 0, 0, 0)
		self.middle_layout.setSpacing(0)
		self.init_control_section()
		self.update_control_section_box()
		self.init_middle()
		self.main_layout.addLayout(self.middle_layout)
		self.main_layout.setContentsMargins(0, 0, 0, 0)
		self.main_layout.setSpacing(0)
		self.init_footer()

	def init_header(self):
		header_layout = QHBoxLayout()
		header_buttons_layout = QHBoxLayout()
		header_violation_section = create_button(on_click=self.show_violation_settings, text="Наказания", class_name="invisible-button buttons-settings-header-buttons buttons-control-section-all")
		header_report_section = create_button(on_click=self.show_report_settings, text="Репорты", class_name="invisible-button buttons-settings-header-buttons buttons-control-section-top buttons-control-section-bottom buttons-control-section-right")
		header_teleport_section = create_button(on_click=self.show_teleport_settings, text="Телепорты", class_name="invisible-button buttons-settings-header-buttons buttons-control-section-top buttons-control-section-bottom buttons-control-section-right")
		header_buttons_layout.addWidget(header_violation_section)
		header_buttons_layout.addWidget(header_report_section)
		header_buttons_layout.addWidget(header_teleport_section)
		header_buttons_layout.setSpacing(0)
		header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
		control_layout = QHBoxLayout()
		control_layout_widget = QWidget()
		control_layout_widget.setFixedSize(86, 40)
		control_layout_widget.setLayout(control_layout)
		control_layout_widget.setProperty("class", "buttons-control-section-right buttons-control-section-bottom buttons-control-section-top")
		minimize_button = create_button(on_click=self.showMinimized, icon_name='minimize', class_name='invisible-button window-control-button')
		close_button = create_button(on_click=self.close, icon_name='delete', class_name='invisible-button window-control-button')
		control_layout.addWidget(minimize_button)
		control_layout.addWidget(close_button)
		control_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
		control_layout.setContentsMargins(5, 5, 15, 5)
		header_layout.addLayout(header_buttons_layout)
		header_layout.addWidget(control_layout_widget)
		self.main_layout.addLayout(header_layout)

	def update_control_section_box(self, button: QPushButton | None = None):
		if hasattr(self, "button_edit_panel_edits_layout"):
			self.button_edit_panel_edits_layout.setParent(None)
			self.clear_layout(self.button_edit_panel_edits_layout)

		button_name_label = create_label(text="Название кнопки:")
		button_name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

		self.button_edit_panel_edits_layout = QVBoxLayout()
		self.button_edit_panel_edits_layout.setContentsMargins(0, 0, 0, 0)
		self.button_edit_panel_edits_layout.setSpacing(10)
		self.button_edit_panel_edits_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
		self.button_edit_panel_name_edit = create_line(class_name="buttons-control-section-edit")
		self.button_edit_panel_name_edit.textChanged.connect(self.handle_line_edit)
		self.button_edit_panel_name_edit.setObjectName("edit_name")
		self.button_edit_panel_name_edit.setFixedSize(280, 33)
		if button is not None:
			self.button_edit_panel_name_edit.setText(button.text())
		self.button_edit_panel_name_edit.setAlignment(Qt.AlignmentFlag.AlignTop)
		self.button_edit_panel_edits_layout.addWidget(button_name_label)
		self.button_edit_panel_edits_layout.addWidget(self.button_edit_panel_name_edit)

		if self.active_window == "report":
			button_description_label = create_label(text="Описание кнопки:")
			button_description_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
			self.button_edit_panel_description_edit = QPlainTextEdit()
			self.button_edit_panel_description_edit.textChanged.connect(self.handle_line_edit)
			self.button_edit_panel_description_edit.setObjectName("edit_text")
			self.button_edit_panel_description_edit.setFixedSize(280, 150)
			self.button_edit_panel_description_edit.setProperty("class", "buttons-control-section-edit")
			self.button_edit_panel_description_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
			self.button_edit_panel_edits_layout.addWidget(button_description_label)
			self.button_edit_panel_edits_layout.addWidget(self.button_edit_panel_description_edit)
		elif self.active_window == "teleport":
			button_teleport_label = create_label(text="Координаты:")
			button_teleport_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
			self.button_edit_panel_coordinates_edit = create_line(class_name="buttons-control-section-edit")
			self.button_edit_panel_coordinates_edit.textChanged.connect(self.handle_line_edit)
			self.button_edit_panel_coordinates_edit.setObjectName("edit_coords")
			self.button_edit_panel_coordinates_edit.setFixedSize(280, 33)
			self.button_edit_panel_coordinates_edit.setAlignment(Qt.AlignmentFlag.AlignTop)
			self.button_edit_panel_edits_layout.addWidget(button_teleport_label)
			self.button_edit_panel_edits_layout.addWidget(self.button_edit_panel_coordinates_edit)
		else:
			self.setup_violation_settings()

		self.button_edit_panel_layout_dynamic.addLayout(self.button_edit_panel_edits_layout)

	def setup_violation_settings(self):
		button_time_label = create_label(text="Время:")
		button_time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
		self.button_edit_panel_violation_time_edit = create_line(class_name="buttons-control-section-edit")
		self.button_edit_panel_violation_time_edit.textChanged.connect(self.handle_line_edit)
		int_validator = QIntValidator(self)
		self.button_edit_panel_violation_time_edit.setValidator(int_validator)
		self.button_edit_panel_violation_time_edit.setObjectName("edit_time")
		self.button_edit_panel_violation_time_edit.setFixedSize(280, 33)
		self.button_edit_panel_violation_time_edit.setAlignment(Qt.AlignmentFlag.AlignTop)
		button_type_label = create_label(text="Тип:")
		button_type_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

		violation_buttons_layout = QHBoxLayout()
		violation_buttons_layout.setContentsMargins(0, 0, 0, 0)
		self.button_edit_panel_prison_button = create_button(text="prison", class_name="invisible-button selected-button")
		self.button_edit_panel_mute_button = create_button(text="mute", class_name="invisible-button")
		self.button_edit_panel_ban_button = create_button(text="ban", class_name="invisible-button")
		self.button_edit_panel_prison_button.clicked.connect(self.handle_violation_type_button_click)
		self.button_edit_panel_mute_button.clicked.connect(self.handle_violation_type_button_click)
		self.button_edit_panel_ban_button.clicked.connect(self.handle_violation_type_button_click)
		self.button_edit_panel_prison_button.setObjectName("prison")
		self.button_edit_panel_mute_button.setObjectName("mute")
		self.button_edit_panel_ban_button.setObjectName("ban")

		violation_buttons_layout.addWidget(self.button_edit_panel_prison_button)
		violation_buttons_layout.addWidget(self.button_edit_panel_mute_button)
		violation_buttons_layout.addWidget(self.button_edit_panel_ban_button)
		violation_buttons_layout.setSpacing(30)
		violation_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

		button_description_label = create_label(text="Причина наказания:")
		button_description_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
		self.button_edit_panel_violation_reason_edit = QPlainTextEdit()
		self.button_edit_panel_violation_reason_edit.textChanged.connect(self.handle_line_edit)
		self.button_edit_panel_violation_reason_edit.setObjectName("edit_reason")
		self.button_edit_panel_violation_reason_edit.setFixedSize(280, 50)
		self.button_edit_panel_violation_reason_edit.setProperty("class", "buttons-control-section-edit")
		self.button_edit_panel_violation_reason_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

		self.button_edit_panel_edits_layout.addWidget(button_time_label)
		self.button_edit_panel_edits_layout.addWidget(self.button_edit_panel_violation_time_edit)
		self.button_edit_panel_edits_layout.addWidget(button_type_label)
		self.button_edit_panel_edits_layout.addLayout(violation_buttons_layout)
		self.button_edit_panel_edits_layout.addWidget(button_description_label)
		self.button_edit_panel_edits_layout.addWidget(self.button_edit_panel_violation_reason_edit)

	def init_control_section(self):
		self.control_panel_layout = QVBoxLayout()
		self.control_panel_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
		control_widget = QWidget()
		control_widget.setFixedSize(372, 510)
		control_widget.setLayout(self.control_panel_layout)
		control_widget.setProperty("class", "buttons-control-section-right buttons-control-section-left buttons-control-section-bottom")

		self.button_edit_panel_layout = QVBoxLayout()
		self.button_edit_panel_layout.setContentsMargins(0, 0, 0, 0)
		self.button_edit_panel_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

		button_edit_panel_widget = QWidget()
		button_edit_panel_widget.setProperty("class", "buttons-control-section-widget buttons-control-section-all")
		button_edit_panel_widget.setLayout(self.button_edit_panel_layout)
		button_edit_panel_widget.setFixedSize(330, 420)
		self.control_panel_layout.addWidget(button_edit_panel_widget)

		button_edit_panel_title_layout = QHBoxLayout()
		button_edit_panel_title_layout.setContentsMargins(0, 0, 0, 0)
		button_edit_panel_title_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
		button_edit_panel_title = create_label(text="Настройка кнопки", class_name="buttons-control-section-bottom")
		button_edit_panel_title.setFixedSize(330, 50)
		button_edit_panel_title.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
		button_edit_panel_title_layout.addWidget(button_edit_panel_title)
		self.button_edit_panel_layout.addLayout(button_edit_panel_title_layout)

		delete_button = create_button(on_click=self.delete_button, text="Удалить кнопку", class_name="buttons-control-section-delete")
		delete_button.setContentsMargins(0, 20, 0, 0)
		delete_layout = QHBoxLayout()
		delete_layout.addWidget(delete_button)
		delete_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
		self.button_edit_panel_layout_dynamic = QVBoxLayout()
		self.button_edit_panel_layout.addLayout(self.button_edit_panel_layout_dynamic)
		self.button_edit_panel_layout.addLayout(delete_layout)

		buttons_size_control_layout = QVBoxLayout()
		buttons_size_control_layout.setContentsMargins(0, 0, 0, 0)
		buttons_size_control_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
		buttons_size_control_widget = QWidget()
		buttons_size_control_widget.setLayout(buttons_size_control_layout)

		width_slider_label = create_label("Ширина кнопок:")
		width_slider_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
		width_slider = Slider(self)
		width_slider.setRange(80, 180)
		width_slider.setValue(configuration.settings_config.button_style.width)
		width_slider.setSuffix(' px')
		width_slider.setSingleStep(1)
		background_color = QColor("#FF7A2F")
		slider_color = QColor("#252424")
		text_color = QColor(replacements.get("%font-color%"))
		width_slider.setAccentColor(background_color)
		width_slider.setBorderColor(slider_color)
		width_slider.setBackgroundColor(slider_color)
		width_slider.setBorderRadius(10)
		width_slider.setTextColor(text_color)
		width_slider.setFixedSize(280, 18)
		width_slider.setFont(QFont('Columbia', 12, 500))
		width_slider.sliderReleased.connect(self.slider_value_changed)

		buttons_size_control_layout.addWidget(width_slider_label)
		buttons_size_control_layout.addWidget(width_slider)
		self.control_panel_layout.addWidget(buttons_size_control_widget)

		self.middle_layout.addWidget(control_widget)

	def slider_value_changed(self, value):
		settings_data = configuration.settings_config
		settings_data.button_style.width = value
		configuration.save_config(config_name="settings", data=settings_data.model_dump())
		style = parse_stylesheet()
		self.app.setStyleSheet(style)
		self.animate_button_width_change(value)

	def animate_button_width_change(self, new_width):
		for button in self.findChildren(MovableButton):
			width_animation = QPropertyAnimation(button, b"maximumWidth")
			width_animation.setDuration(300)
			width_animation.setStartValue(button.width())
			width_animation.setEndValue(new_width)
			width_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
			width_animation.start()
			self.animations.append(width_animation)

	def init_middle(self):
		middle_layout = QHBoxLayout()
		middle_layout.setContentsMargins(0, 0, 0, 0)
		middle_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
		middle_layout.setSpacing(0)

		middle_widget = QWidget()
		middle_widget.setFixedSize(828, 470)
		middle_widget.setProperty("class", "buttons-control-section-right")
		middle_widget.setLayout(middle_layout)
		middle_widget.setContentsMargins(0, 0, 0, 15)

		self.middle_layout.addWidget(middle_widget)

		scroll_area = HorizontalScrollArea(middle_widget)
		scroll_area.setWidgetResizable(True)
		scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

		scroll_widget = QWidget()
		scroll_widget.setProperty("class", "scroll_widget")
		self.main_scroll_layout = QHBoxLayout(scroll_widget)
		self.main_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

		scroll_widget.setLayout(self.main_scroll_layout)
		scroll_area.setWidget(scroll_widget)
		scroll_area.setMaximumWidth(810)

		middle_layout.addWidget(scroll_area)

	def init_footer(self):
		footer_layout = QHBoxLayout()
		footer_buttons_layout = QHBoxLayout()
		add_button = create_button(on_click=self.add_button, text="Добавить кнопку", class_name="invisible-button buttons-settings-footer-buttons buttons-control-section-right buttons-control-section-bottom buttons-control-section-top")
		save_button = create_button(on_click=self.save_config, text="Сохранить", class_name="invisible-button buttons-settings-footer-buttons buttons-control-section-right buttons-control-section-bottom buttons-control-section-top")
		footer_buttons_layout.addWidget(add_button)
		footer_buttons_layout.addWidget(save_button)
		footer_buttons_layout.setSpacing(0)
		footer_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
		footer_layout.addLayout(footer_buttons_layout)
		self.main_layout.addLayout(footer_layout)

	def show_report_settings(self):
		if self.active_window == "report":
			return
		self.active_window = "report"
		self.fade_in_widget(self.reports_grid_widget, duration=300)
		self.update_control_section_box()
		self.update_buttons()

	def show_violation_settings(self):
		if self.active_window == "violation":
			return
		self.active_window = "violation"
		self.fade_in_widget(self.violations_grid_widget, duration=300)
		self.update_control_section_box()
		self.update_buttons()

	def show_teleport_settings(self):
		if self.active_window == "teleport":
			return
		self.active_window = "teleport"
		self.fade_in_widget(self.teleports_grid_widget, duration=300)
		self.update_control_section_box()
		self.update_buttons()

	def update_buttons(self):
		while self.main_scroll_layout.count():
			old_widget = self.main_scroll_layout.takeAt(0).widget()
			if old_widget:
				old_widget.setVisible(False)

		if self.active_window == "report":
			self.main_scroll_layout.addWidget(self.reports_grid_widget)
			self.reports_grid_widget.setVisible(True)
			self.populate_buttons(self.reports_grid_widget.layout(), self.reports_config)
		elif self.active_window == "violation":
			self.main_scroll_layout.addWidget(self.violations_grid_widget)
			self.violations_grid_widget.setVisible(True)
			self.populate_buttons(self.violations_grid_widget.layout(), self.violations_config)
		elif self.active_window == "teleport":
			self.main_scroll_layout.addWidget(self.teleports_grid_widget)
			self.teleports_grid_widget.setVisible(True)
			self.populate_buttons(self.teleports_grid_widget.layout(), self.teleports_config)

	def populate_buttons(self, layout: QGridLayout, buttons_dict: list):
		while layout.count():
			item = layout.takeAt(0)
			if item.widget():
				item.widget().deleteLater()
		is_violation = self.active_window == "violation"
		for button_index, button_data in enumerate(buttons_dict):
			column = button_index // 10
			row = button_index % 10
			button_data["column"] = column
			button_data["row"] = row
			button = MovableButton(
				text=button_data["name"],
				row=row,
				column=column,
				on_click_handler=self.handle_button_click,
				data=button_data,
				parent=self
			)
			if is_violation:
				button.setObjectName(button_data["type"])
			layout.addWidget(button, row, column)

	def handle_violation_type_button_click(self):

		if self.active_button is None:
			return

		button_dict = self.active_button.data
		violation_type = self.sender().objectName()
		if violation_type == button_dict.get("type"):
			return
		button_dict["type"] = violation_type

		for btn in (self.button_edit_panel_prison_button,
					self.button_edit_panel_ban_button,
					self.button_edit_panel_mute_button):
			btn.setProperty("class", "invisible-button")

		selected_button: QPushButton = {
			"prison": self.button_edit_panel_prison_button,
			"ban": self.button_edit_panel_ban_button,
			"mute": self.button_edit_panel_mute_button
		}.get(violation_type)

		if selected_button:
			selected_button.setProperty("class", "invisible-button selected-button")

		style = parse_stylesheet()
		self.app.setStyleSheet(style)

		grid_layout = self.main_scroll_layout.itemAt(0).widget().layout()
		item_at_grid = grid_layout.itemAtPosition(self.active_button.row, self.active_button.column)
		if item_at_grid is None:
			return
		button_at_grid = item_at_grid.widget()
		button_at_grid.data = button_dict
		self.active_button.data = button_dict
		self.active_button.setObjectName(violation_type)

	def handle_line_edit(self):
		if self.active_button is None or self.is_click_process:
			return

		button_dict = self.active_button.data

		new_value = (self.sender().toPlainText() if isinstance(self.sender(), QPlainTextEdit)
					else self.sender().text())

		button_key = self.sender().objectName().split("_")[1]
		if button_key == "time":
			new_value = str(new_value)

		button_dict[button_key] = new_value

		grid_layout = self.main_scroll_layout.itemAt(0).widget().layout()
		item_at_grid = grid_layout.itemAtPosition(self.active_button.row, self.active_button.column)
		if item_at_grid is None:
			return
		button_at_grid = item_at_grid.widget()
		button_at_grid.setText(button_dict["name"])
		button_at_grid.data = button_dict
		self.active_button.data = button_dict

	def handle_button_click(self, button: QPushButton | None = None):
		button: MovableButton = button or self.sender()
		self.active_button = button
		self.is_click_process = True

		self.button_edit_panel_name_edit.setText(button.data["name"])

		if self.active_window == "report":
			self.button_edit_panel_description_edit.setPlainText(button.data["text"])
		elif self.active_window == "violation":
			self.button_edit_panel_violation_time_edit.setText(str(button.data["time"]) if not isinstance(button.data["time"], str) else button.data["time"])
			self.button_edit_panel_violation_reason_edit.setPlainText(button.data["reason"])

			violation_type = button.data["type"]
			button_classes = {
				"prison": self.button_edit_panel_prison_button,
				"ban": self.button_edit_panel_ban_button,
				"mute": self.button_edit_panel_mute_button
			}

			for btn in button_classes.values():
				btn.setProperty("class", "invisible-button")

			if violation_type in button_classes:
				button_classes[violation_type].setProperty("class", "invisible-button selected-button")

			style = parse_stylesheet()
			self.app.setStyleSheet(style)
		elif self.active_window == "teleport":
			self.button_edit_panel_coordinates_edit.setText(button.data["coords"])

		self.is_click_process = False

	def add_button(self):
		new_button_data = {
			"violation": {"name": "Новая кнопка", "type": "prison", "reason": "Причина", "time": "10"},
			"report": {"name": "Новая кнопка", "text": "Текст кнопки"},
			"teleport": {"name": "Новая кнопка", "coords": "000.00, 000.00, 000.00"}
		}.get(self.active_window)
		buttons_dict = {
			"violation": self.violations_config,
			"report": self.reports_config,
			"teleport": self.teleports_config
		}.get(self.active_window)

		if new_button_data and buttons_dict is not None:
			button_count = len(buttons_dict)
			column = (button_count - 1) // 10
			row = (button_count - 1) % 10
			new_button_data["column"] = column
			new_button_data["row"] = row
			buttons_dict.append(new_button_data)

			new_button = MovableButton(
				text=new_button_data["name"],
				row=row,
				column=column,
				on_click_handler=self.handle_button_click,
				data=new_button_data,
				parent=self
			)
			current_grid_layout = self.get_current_grid_layout()
			current_grid_layout.addWidget(new_button, row, column)
			self.update_buttons()
			self.handle_button_click(button=new_button)

	def delete_button(self):
		if self.active_button is None:
			return
		self.perform_button_deletion()

	def perform_button_deletion(self):
		buttons_dicts = {
			"violation": self.violations_config,
			"report": self.reports_config,
			"teleport": self.teleports_config
		}
		buttons_dict = buttons_dicts.get(self.active_window)
		if buttons_dict is None:
			return

		current_grid_layout = self.get_current_grid_layout()
		item = current_grid_layout.itemAtPosition(self.active_button.row, self.active_button.column)
		if item is None:
			return

		widget = item.widget()
		deleted_button_index = current_grid_layout.indexOf(widget) if widget else -1
		if deleted_button_index == -1:
			return

		buttons_dict.pop(deleted_button_index)

		for i in reversed(range(current_grid_layout.count())):
			widget = current_grid_layout.itemAt(i).widget()
			if widget:
				current_grid_layout.removeWidget(widget)
				widget.deleteLater()

		for button_index, button_data in enumerate(buttons_dict):
			column = button_index // 10
			row = button_index % 10
			button = MovableButton(
				text=button_data["name"],
				row=row,
				column=column,
				on_click_handler=self.handle_button_click,
				data=button_data,
				parent=self
			)
			current_grid_layout.addWidget(button, row, column)

		self.update_buttons()
		active_item = current_grid_layout.itemAt(deleted_button_index) or current_grid_layout.itemAt(deleted_button_index - 1)
		if active_item:
			active_button = active_item.widget()
			self.handle_button_click(button=active_button)

	def get_current_grid_layout(self) -> QGridLayout:
		return {
			"report": self.reports_grid_widget.layout(),
			"violation": self.violations_grid_widget.layout(),
			"teleport": self.teleports_grid_widget.layout()
		}.get(self.active_window)


	def save_config(self):
		show_notification(parent=self, text="Конфиг успешно сохранён.")
		if self.active_window == "teleport":
			configuration.save_config("teleports", self.teleports_config)
		elif self.active_window == "report":
			configuration.save_config("reports", self.reports_config)
		elif self.active_window == "violation":
			configuration.save_config("violations", self.violations_config)

	@classmethod
	def clear_layout(cls, layout):
		while layout.count():
			item = layout.takeAt(0)
			if widget := item.widget():
				widget.setParent(None)
			else:
				cls.clear_layout(item.layout())
