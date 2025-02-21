import time
import webbrowser

import binder_utils
import keyboard
import pyperclip
from coordinate_updater import CoordinateUpdater
from PyQt6.QtCore import QObject, QSize, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget
from pyqttoast import ToastPreset
from utils import (ADDITIONAL_BUTTONS, DraggableWidget, Mouse, configuration,
                   create_button, create_header_layout, create_label,
                   create_line, get_commits_history, get_reports_count,
                   get_reports_info, show_notification)

mouse = Mouse()

class UpdateHistoryWorker(QObject):
	history_updated = pyqtSignal(list)

	def __init__(self, commits_count: int = 10000):
		self.commits_count = commits_count
		super().__init__()

	def fetch_commits(self):
		return get_commits_history(commits_count=self.commits_count)

	def load_commits(self):
		commits = self.fetch_commits()
		self.history_updated.emit(commits)


class GTAModal(QWidget):
	def __init__(self, coordinate_updater: CoordinateUpdater, command_name: str, time=None, reason=None):
		super().__init__()
		self.coordinate_updater = coordinate_updater
		self.command_name = command_name
		self.modal_type = ADDITIONAL_BUTTONS[command_name]
		self.time = time
		self.reason = reason
		self.setup_coordinates()
		self.setup_callbacks()
		self.setup_ui()

	def setup_coordinates(self):
		self.coordinate_updater.coordinates_updated.connect(self.update_window_size)
		self.left = self.coordinate_updater.left
		self.top = self.coordinate_updater.top

	def setup_callbacks(self):
		self.callbacks = {
			"punish": self.punish_command,
			"simple": self.simple_command,
			"uncuff": self.middle_command,
			"mute_report": self.middle_command,
			"force_rename": self.middle_command,
			"car_sync": self.car_sync,
		}

	def update_window_size(self, left, top, *_):
		self.left = left
		self.top = top

	def setup_ui(self):
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		self.setFixedWidth(290)
		self.main_layout = QVBoxLayout()
		self.main_layout.setSpacing(0)
		self.setProperty("class", "modal")
		self.setup_title()
		self.setup_middle()
		self.setup_footer()
		self.setLayout(self.main_layout)

	def setup_title(self):
		title_label = create_label(text=self.command_name)
		title_layout = QHBoxLayout()
		title_layout.addWidget(title_label)

		title_widget = QWidget()
		title_widget.setProperty("class", "modal-title")
		title_widget.setFixedHeight(66)
		title_widget.setLayout(title_layout)
		self.main_layout.addWidget(title_widget)

	def setup_middle(self):
		middle_layout = QVBoxLayout()
		gid_label, self.gid_edit = create_label("ID:"), create_line()

		middle_layout.addWidget(gid_label)
		middle_layout.addWidget(self.gid_edit)

		if self.modal_type == "punish":
			time_label, reason_label = create_label("Время:"), create_label("Причина:")
			self.time_edit, self.reason_edit = create_line(text=self.time), create_line(text=self.reason)
			middle_layout.addWidget(time_label)
			middle_layout.addWidget(self.time_edit)
			middle_layout.addWidget(reason_label)
			middle_layout.addWidget(self.reason_edit)

		elif self.modal_type in {"uncuff", "mute_report", "force_rename"}:
			reason_label, self.reason_edit = create_label("Причина:"), create_line(text=self.reason)
			middle_layout.addWidget(reason_label)
			middle_layout.addWidget(self.reason_edit)

		middle_widget = QWidget()
		middle_widget.setProperty("class", "modal-middle")
		middle_widget.setLayout(middle_layout)
		self.main_layout.addWidget(middle_widget)

	def setup_footer(self):
		footer_layout = QHBoxLayout()
		send_button = create_button(on_click=self.callbacks[self.modal_type], text="Отправить", class_name="modal-button-send")
		cancel_button = create_button(on_click=self.close, text="Отмена", class_name="modal-button-cancel")

		send_button.setFixedSize(130, 37)
		cancel_button.setFixedSize(110, 37)

		footer_layout.addWidget(send_button)
		footer_layout.addWidget(cancel_button)

		footer_widget = QWidget()
		footer_widget.setProperty("class", "modal-footer")
		footer_widget.setFixedHeight(66)
		footer_widget.setLayout(footer_layout)
		self.main_layout.addWidget(footer_widget)

	def punish_command(self):
		self.execute_command(["gid", "time", "reason"], "violations")

	def simple_command(self):
		self.execute_command(["gid"], "commands")

	def middle_command(self):
		self.execute_command(["gid", "reason"], "commands")

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
			self.paste_to_console(text=action, paste_type="commands")
			time.sleep(1)
		self.close()

	def execute_command(self, fields, paste_type):
		try:
			gid = int(self.gid_edit.text())
			args = [gid]
			if "time" in fields:
				args.append(self.time_edit.text())
			if "reason" in fields:
				args.append(self.reason_edit.text())
			command = f"{self.command_name} {' '.join(map(str, args))}"
			self.paste_to_console(text=command, paste_type=paste_type)
			self.close()
		except (ValueError, TypeError):
			show_notification(parent=self, preset=ToastPreset.ERROR_DARK, text="ID должен быть целочисленным значением!")

	def paste_to_console(self, text, paste_type=None):
		mouse.click((self.left + 55, self.top + 375))
		time.sleep(0.2)
		mouse.click((self.left + 500, self.top + 335))
		keyboard.send("ctrl+a, backspace")
		pyperclip.copy(text)
		keyboard.send('ctrl+v')
		time.sleep(0.1)
		if paste_type and getattr(configuration.settings_config.auto_send, paste_type, False):
			keyboard.send("enter")


class AboutWindow(DraggableWidget):
	def __init__(self):
		super().__init__()
		self.setup_ui()
		self.setup_worker()

	def update_window_size(self, left, top, right, bottom, width, height, max_cols):
		self.left, self.top = left, top

	@classmethod
	def clear_layout(cls, layout):
		while layout.count():
			item = layout.takeAt(0)
			if widget := item.widget():
				widget.setParent(None)
			elif layout_item := item.layout():
				cls.clear_layout(layout_item)

	def setup_ui(self):
		self.setWindowTitle("Информация")
		self.setFixedSize(600, 800)
		self.main_layout = QVBoxLayout(self)
		self.main_layout.addLayout(create_header_layout(instance=self))
		self.init_reports_info_area()
		self.init_update_history_area()
		self.init_about_area()
		self.init_footer()

	def setup_worker(self):
		self.worker = UpdateHistoryWorker()
		self.thread = QThread()
		self.worker.moveToThread(self.thread)
		self.worker.history_updated.connect(self.update_history_area)
		self.thread.started.connect(self.worker.load_commits)
		self.thread.finished.connect(self.thread.deleteLater)
		self.thread.start()

	def init_reports_info_area(self):
		reports_info_area = QVBoxLayout()
		title = create_label(text="Статистика по репортам:", class_name="title-label", alignment=Qt.AlignmentFlag.AlignHCenter)
		reports_data = get_reports_info()
		daily, weekly, monthly, all_reports = get_reports_count(reports_data=reports_data)

		daily_label = create_label(text=f"За сегодня: {daily}\n({next(iter(reports_data['daily_reports']))})", alignment=Qt.AlignmentFlag.AlignHCenter)
		weekly_label = create_label(text=f"За неделю: {weekly}\n(с {next(iter(reports_data['weekly_reports']))})", alignment=Qt.AlignmentFlag.AlignHCenter)
		monthly_label = create_label(text=f"За месяц: {monthly}\n(с {next(iter(reports_data['monthly_reports']))})", alignment=Qt.AlignmentFlag.AlignHCenter)
		all_label = create_label(text=f"За всё время: {all_reports}\n(с {next(iter(reports_data['all_reports']))})", alignment=Qt.AlignmentFlag.AlignHCenter)

		reports_buttons_area = QHBoxLayout()
		reports_buttons_area.setContentsMargins(30, 0, 30, 0)
		reports_buttons_area.setSpacing(50)
		reports_buttons_area.addWidget(create_button(on_click=lambda: self.show_reports_info_page("weekly_reports"), text="Подробнее за неделю", class_name="buttons-control-section-all"))
		reports_buttons_area.addWidget(create_button(on_click=lambda: self.show_reports_info_page("monthly_reports"), text="Подробнее за месяц", class_name="buttons-control-section-all"))

		reports_area = QVBoxLayout()
		reports_area_info = QHBoxLayout()
		reports_area_info.addWidget(daily_label)
		reports_area_info.addWidget(weekly_label)
		reports_area_info.addWidget(monthly_label)
		reports_area_info.addWidget(all_label)
		reports_area.addLayout(reports_area_info)
		reports_area.addLayout(reports_buttons_area)

		reports_info_area.addWidget(title)
		reports_info_area.addLayout(reports_area)
		self.main_layout.addLayout(reports_info_area)

	def init_update_history_area(self):
		update_history_area_layout = QVBoxLayout()
		update_history_title = create_label(text="История обновлений:", class_name="title-label", alignment=Qt.AlignmentFlag.AlignHCenter)
		self.update_history_text_layout = QVBoxLayout()
		self.loading_text = create_label(text="Загрузка...", alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, word_wrap=True)
		self.update_history_text_layout.addWidget(self.loading_text)

		update_history_area_layout.addWidget(update_history_title)
		scroll_area = QScrollArea()
		scroll_area.setWidgetResizable(True)
		scroll_content = QWidget()
		scroll_content.setLayout(self.update_history_text_layout)
		scroll_area.setWidget(scroll_content)
		update_history_area_layout.addWidget(scroll_area)
		self.main_layout.addLayout(update_history_area_layout)

	def update_history_area(self, commits: list[dict]):
		if not commits:
			return self.loading_text.setText("Ошибка получения истории обновлений")
		self.clear_layout(self.update_history_text_layout)
		for commit in commits:
			time_label = create_label(text=commit['date'], class_name="subtitle-label", alignment=Qt.AlignmentFlag.AlignHCenter)
			commit_label = create_label(text=commit['message'], word_wrap=True)
			self.update_history_text_layout.addWidget(time_label)
			self.update_history_text_layout.addWidget(commit_label)

	def init_about_area(self):
		about_area = QVBoxLayout()
		title = create_label(text="Информация о приложении:", class_name="title-label", alignment=Qt.AlignmentFlag.AlignHCenter)
		info_text = create_label(text="Биндер для GTA 5 RP, обеспечивающий удобство в модерировании.\nО проблемах/предложениях сообщать через контактные данные ниже.", alignment=Qt.AlignmentFlag.AlignHCenter, word_wrap=True)
		about_area.addWidget(title)
		about_area.addWidget(info_text)
		self.main_layout.addLayout(about_area)

	def show_reports_info_page(self, period_type: str):
		if hasattr(self, "reports_info_page") and self.reports_info_page.period_type != period_type:
			self.reports_info_page.close()
		self.reports_info_page = ReporsInfoWindow(period_type=period_type)
		self.reports_info_page.show()

	def init_footer(self):
		footer_layout = QVBoxLayout()
		developer_label = create_label(text="Начало разработки: 25 декабря 2023 года\nРазработчик: Dmitriy Win", alignment=Qt.AlignmentFlag.AlignHCenter)
		footer_layout.addWidget(developer_label)

		footer_icons_layout = QHBoxLayout()
		github_button = create_button(on_click=self.open_github, icon_name='github', class_name="invisible-button")
		discord_button = create_button(on_click=self.open_discord, icon_name='discord', class_name="invisible-button")
		github_button.setIconSize(QSize(25, 25))
		discord_button.setIconSize(QSize(25, 25))
		footer_icons_layout.addWidget(github_button)
		footer_icons_layout.addWidget(discord_button)
		footer_layout.addLayout(footer_icons_layout)
		self.main_layout.addLayout(footer_layout)

	def open_github(self):
		webbrowser.open("https://github.com/JudeDM/binder/tree/main")

	def open_discord(self):
		webbrowser.open("discord://-/users/208575718093750276")

	def closeEvent(self, event):
		self.thread.quit()
		self.thread.wait()
		event.accept()

class ReporsInfoWindow(DraggableWidget):
	def __init__(self, period_type: str):
		self.period_type = period_type
		super().__init__()
		self.setup_ui()

	def setup_ui(self):
		self.setWindowTitle("Статистика по репортам")
		self.setMinimumSize(400, 200)
		self.main_layout = QVBoxLayout(self)
		self.main_layout.addLayout(create_header_layout(self))
		self.init_report_area()

	def init_report_area(self):
		reports_data = get_reports_info().get(self.period_type, {})
		text_area = QVBoxLayout()
		stats_title = create_label(text="Статистика по репортам:", class_name="title-label", alignment=Qt.AlignmentFlag.AlignHCenter)
		report_text = "\n".join(f"{key} - {value}" for key, value in sorted(reports_data.items(), reverse=True))
		text_label = create_label(text=report_text, alignment=Qt.AlignmentFlag.AlignHCenter, word_wrap=True)
		text_area.addWidget(stats_title)
		text_area.addWidget(text_label)
		self.main_layout.addLayout(text_area)
