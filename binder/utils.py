import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import urllib.request
import uuid
import zlib
from concurrent.futures import ThreadPoolExecutor
from ctypes import windll
from datetime import datetime, timedelta
from pathlib import Path

# import hwid
import sslcrypto
from pydantic import BaseModel, Field
from PyQt6.QtCore import QMargins, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QMouseEvent, QPixmap
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QWidget, QScrollArea)
from pyqttoast import (Toast, ToastButtonAlignment, ToastIcon, ToastPosition,
                       ToastPreset)

__location__ = os.getcwd()

DATE_FORMAT = "%d.%m.%Y"
ADDIDIONAL_BUTTONS = {
	"prison": "punish",
	"mute": "punish",
	"ban": "punish",
	"reof": "fast",
	"dimension_sync": "fast",
	"car_sync": "car_sync",
	"uo_delete": "simple",
	"marketplace_stash": "simple",
	"tpcar": "simple",
	"dped_tp": "simple",
	"uncuff": "uncuff",
	"force_rename": "force_rename",
	"veh_repair": "simple",
}

cached_files = {}
icons_map = {
	"about": QIcon("data/icons/about.svg"),
	"arrow_down": QIcon("data/icons/arrow_down.svg"),
	"arrow_up": QIcon("data/icons/arrow_up.svg"),
	"add": QIcon("data/icons/add.svg"),
	"delete": QIcon("data/icons/delete.svg"),
	"discord": QIcon("data/icons/discord.svg"),
	"github": QIcon("data/icons/github.svg"),
	"minimize": QIcon("data/icons/minimize.svg"),
	"visible": QIcon("data/icons/visibility_on.svg"),
	"invisible": QIcon("data/icons/visibility_off.svg"),
	"settings": QIcon("data/icons/settings.svg"),
	"checkbox_checked": QIcon("data/icons/checkbox_checked.svg"),
	"checkbox_unchecked": QIcon("data/icons/checkbox_unchecked.svg"),
	"tooltip": QIcon("data/icons/tooltip.svg"),
}


TOLERANCE = 5

class TabPixelInfo:
	__slots__ = ('x', 'y', 'color', 'left_side', 'top_side')
	def __init__(self, x: int, y: int, color: tuple[int, int, int], left_side: bool, top_side: bool):
		self.x = x
		self.y = y
		self.color = color
		self.left_side = left_side
		self.top_side = top_side

PIXEL_MAP = {
	"admin_panel": [
		TabPixelInfo(940, 360, (85, 85, 85), True, True),
		TabPixelInfo(940, 385, (85, 85, 85), True, True),
	],
	"console_tab": [
		TabPixelInfo(12, 12, (255, 255, 255), True, True),
		TabPixelInfo(12, 60, (255, 255, 255), True, True),
		TabPixelInfo(20, 370, (68, 68, 68), True, True),
		TabPixelInfo(70, 370, (68, 68, 68), True, True),
	],
	"reports_tab": [
		TabPixelInfo(250, 370, (68, 68, 68), True, True),
		TabPixelInfo(305, 336, (68, 68, 68), True, True),
	],
	"teleport_tab": [
		TabPixelInfo(340, 370, (68, 68, 68), True, True),
		TabPixelInfo(420, 370, (68, 68, 68), True, True),
	],
}

def read_pixel(x: int, y: int) -> tuple[int, int, int]:
	hdc = windll.user32.GetDC(0)
	pixel = windll.gdi32.GetPixel(hdc, x, y)
	windll.user32.ReleaseDC(0, hdc)
	return (pixel & 0xFF, (pixel >> 8) & 0xFF, (pixel >> 16) & 0xFF)

def is_color_within_tolerance(color: tuple[int, int, int], target: tuple[int, int, int]) -> bool:
	return all(abs(color[i] - target[i]) <= TOLERANCE for i in range(3))

def check_tab_state(tab_name: str, pixel_info: list[TabPixelInfo], right: int, bottom: int, left: int, top: int) -> tuple[str, bool]:
	for info in pixel_info:
		adjusted_x = left + info.x if info.left_side else right - info.x
		adjusted_y = top + info.y if info.top_side else bottom - info.y

		try:
			if not is_color_within_tolerance(read_pixel(adjusted_x, adjusted_y), info.color):
				return tab_name, False
		except Exception as e:
			return tab_name, False

	return tab_name, True

def get_tabs_state(right: int, bottom: int, left: int, top: int) -> dict[str, bool]:
	with ThreadPoolExecutor() as executor:
		return dict(executor.map(
			lambda item: check_tab_state(item[0], item[1], right, bottom, left, top),
			PIXEL_MAP.items()
		))


class HWIDGenerator:
	def __init__(self):
		self.attributes = {
			"drive_serial": self.get_drive_serial,
			"cpu_id": self.get_cpu_id,
			"username": self.get_username,
			"mac_address": self.get_mac_address,
			"system_id": self.get_system_id,
			"motherboard_serial": self.get_motherboard_serial,
			"system_uuid": self.get_system_uuid,
		}

	@staticmethod
	def get_drive_serial():
		return hex(uuid.getnode())

	@staticmethod
	def get_cpu_id():
		return hashlib.md5(platform.processor().encode()).hexdigest()

	@staticmethod
	def get_username():
		return os.getlogin()

	@staticmethod
	def get_mac_address():
		mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
		return ':'.join(mac[e:e+2] for e in range(0, 12, 2))

	@staticmethod
	def get_system_id():
		return platform.node()

	@staticmethod
	def get_motherboard_serial():
		return subprocess.check_output('wmic baseboard get serialnumber', shell=True).decode().split('\n')[1].strip()

	@staticmethod
	def get_system_uuid():
		return subprocess.check_output('wmic csproduct get uuid', shell=True).decode().split('\n')[1].strip()

	def generate_hwid(self):
		hwid_string = '-'.join(f"{attr()}" for attr in self.attributes.values())
		return hashlib.sha256(hwid_string.encode()).hexdigest()


hwid_generator = HWIDGenerator()


key = hashlib.sha256(hwid_generator.generate_hwid().encode()).digest()


def calculate_md5(file_path: str) -> str | None:
	"""
	Calculate the MD5 hash of the file located at the given file_path.

	Args:
	- file_path (str): The path to the file.

	Returns:
	- str | None: The MD5 hash of the file, or None if the file is not found or an error occurs.
	"""
	try:
		with open(file_path, "rb") as f:
			file_data = f.read()
			return None if file_data is None else hashlib.md5(file_data).hexdigest()
	except Exception:
		return None

def calculate_crc32(file_path: str) -> str:
	prev = 0
	try:
		with open(file_path, "rb") as f:
			for eachLine in f:
				prev = zlib.crc32(eachLine, prev)
		return f"{prev & 0xFFFFFFFF:X}"
	except Exception:
		return None


def default_visible_buttons():
	return ["dimension_sync", "car_sync", "uncuff", "reof"]

def default_default_reasons():
	return {"uncuff": "Поблизости никого нет"}

class DefaultReasons(BaseModel):
	uncuff: str = Field(default="Поблизости никого нет")
	force_rename: str = Field(default="2.7 правил проекта")


class ButtonStyle(BaseModel):
	size: list[int] = Field(default_factory=lambda: [153, 33])

	@property
	def width(self):
		return self.size[0]

	@property
	def height(self):
		return self.size[1]

	@width.setter
	def width(self, value):
		self.size[0] = value

	@height.setter
	def height(self, value):
		self.size[1] = value


class AutoSendStructure(BaseModel):
	reports: bool = Field(default=True)
	violations: bool = Field(default=True)
	teleports: bool = Field(default=True)
	commands: bool = Field(default=True)


class SettingsStructure(BaseModel):
	user_gid: int = Field(default=1)
	button_style: ButtonStyle = Field(default_factory=ButtonStyle)
	visible_buttons: list[str] = Field(default_factory=default_visible_buttons)
	default_reasons: DefaultReasons = Field(default_factory=DefaultReasons)
	auto_send: AutoSendStructure = Field(default_factory=AutoSendStructure)
	show_update_info: bool = Field(default=True)


class FileSettingsStructure(BaseModel):
	data: SettingsStructure = Field(default_factory=SettingsStructure)
	version: int = Field(default=1)


class ConfigStructure(BaseModel):
	data: list = Field(default_factory=list)
	version: int = Field(default=1)


class ClickDataStructure(BaseModel):
	data: dict[str, int] = Field(default_factory=dict)
	version: int = Field(default=1)


class Configuration:
	data_path = Path(__location__) / "data"
	configs_path = data_path / "configs"
	config_names = ["reports", "violations", "teleports"]
	def __init__(self):
		self._cache = {}

	def validate_configs(self) -> None:
		self.create_directories()
		self.rename_old_configs()
		self.validate_config_files()
		self.validate_settings()
		self.validate_click_data()

	def create_directories(self) -> None:
		"""
		Create necessary directories.
		"""
		self.data_path.mkdir(parents=True, exist_ok=True)
		self.configs_path.mkdir(parents=True, exist_ok=True)

	def rename_old_configs(self) -> None:
		"""
		Rename old configuration files to new names.
		"""
		old_new_names = {
			"button_config.json": "reports.json",
			"violation_config.json": "violations.json",
			"secret.json": "settings.json",
			"click_data": "clicks.json"
		}

		for old_name, new_name in old_new_names.items():
			old_path = self.configs_path / old_name
			new_path = self.configs_path / new_name
			if old_path.exists():
				if new_path.exists():
					new_path.unlink()
				old_path.rename(new_path)

	def validate_config_files(self):
		for config_name in ["reports", "violations", "settings", "teleports", "click_data"]:
			config_path = self.configs_path / f"{config_name}.json"
			if not config_path.exists():
				default_data = ConfigStructure() if config_name != "settings" else FileSettingsStructure()
				self._save_config(config_path, default_data.model_dump())
			else:
				try:
					with config_path.open("r", encoding="utf-8") as file:
						json.load(file)  # Just checking if JSON is valid
				except json.JSONDecodeError:
					default_data = ConfigStructure() if config_name != "settings" else FileSettingsStructure()
					self._save_config(config_path, default_data.model_dump())

	def validate_settings(self) -> None:
		"""
		Validate settings configuration file.
		"""
		settings_config_path = self.configs_path / "settings.json"
		if settings_config_path.exists():
			try:
				with settings_config_path.open("r", encoding="utf-8") as file:
					data = json.load(file)
			except json.JSONDecodeError:
				new_data = FileSettingsStructure(
					data=SettingsStructure(),
					version=1
				)
				self._save_config(settings_config_path, new_data.model_dump())
				return

			if isinstance(data, dict):
				if data.get("version") is None:
					new_data = FileSettingsStructure(
						data=SettingsStructure(
							user_gid=data.get("user_gid", 1),
							button_style=ButtonStyle(**data.get("button_style", {})),
							visible_buttons=data.get("visible_buttons", default_visible_buttons()),
							default_reasons=data.get("default_reasons", default_default_reasons()),
							auto_send=AutoSendStructure(**data.get("auto_send", {}))
						),
						version=1
					)
					self._save_config(settings_config_path, new_data.model_dump())
			else:
				new_data = FileSettingsStructure(
					data=SettingsStructure(),
					version=1
				)
				self._save_config(settings_config_path, new_data.model_dump())
		else:
			new_data = FileSettingsStructure(
				data=SettingsStructure(),
				version=1
			)
			self._save_config(settings_config_path, new_data.model_dump())

	def validate_click_data(self) -> None:
		"""
		Validate click data configuration file.
		"""
		click_data_path = self.configs_path / "click_data.json"
		if click_data_path.exists():
			try:
				with click_data_path.open("r", encoding="utf-8") as file:
					data = json.load(file)
			except json.JSONDecodeError:
				new_data = ClickDataStructure()
				self._save_config(click_data_path, new_data.model_dump())
				return

			if isinstance(data, dict):
				if data.get("version") is None:
					new_data = ClickDataStructure(data=data)
					self._save_config(click_data_path, new_data.model_dump())
			else:
				new_data = ClickDataStructure()
				self._save_config(click_data_path, new_data.model_dump())
		else:
			new_data = ClickDataStructure()
			self._save_config(click_data_path, new_data.model_dump())

	def _save_config(self, path: Path, data: dict) -> None:
		"""
		Save the configuration data to the given path.
		"""
		with path.open("w", encoding="utf-8") as file:
			json.dump(data, file, ensure_ascii=False, indent=4)

	def _get_config_data(self, file_path: Path):
		try:
			file_crc32 = calculate_crc32(file_path=file_path)
		except FileNotFoundError:
			self.validate_configs()
			return self._get_config_data(file_path=file_path)
		if file_crc32 and file_path in self._cache and self._cache[file_path]['crc32'] == file_crc32:
			return self._cache[file_path]['data']
		else:
			self.validate_configs()
			try:
				with file_path.open("r", encoding="utf-8") as file:
					data = None
					if "styles.css" in file_path.name:
						data = file.read()
					else:
						data = json.load(file)
					self._cache[file_path] = {
						'crc32': file_crc32,
						'data': data
					}
					return data
			except Exception:
				if "styles.css" in file_path.name:
					return ""
				return {}

	def save_config(self, config_name: str, data: dict) -> None:
		file_mapping = {
			'click_data': 'click_data.json',
			'violations': 'violations.json',
			'reports': 'reports.json',
			'settings': 'settings.json',
			'teleports': 'teleports.json'
		}
		file_name = file_mapping.get(config_name)
		if file_name:
			file_path = self.configs_path / file_name
			if config_name == 'settings':
				data = FileSettingsStructure(data=SettingsStructure(**data)).model_dump()
			elif config_name == 'click_data':
				data = ClickDataStructure(data=data).model_dump()
			else:
				data = ConfigStructure(data=data).model_dump()
			self._save_config(file_path, data)
			self._cache[file_path] = {
				'crc32': calculate_crc32(file_path=file_path),
				'data': data
			}

	@property
	def resource_path(self) -> Path:
		""" Get absolute path to resource for PyInstaller """
		try:
			base_path = sys._MEIPASS
		except Exception:
			return self.data_path
		return Path(base_path) / "data"

	@property
	def click_data(self) -> dict[str, int]:
		file_path = self.configs_path / 'click_data.json'
		return self._get_config_data(file_path)["data"]

	@property
	def violations_config(self) -> list[dict[str, str]]:
		file_path = self.configs_path / 'violations.json'
		return self._get_config_data(file_path)["data"]

	@property
	def reports_config(self) -> list[dict[str, str]]:
		file_path = self.configs_path / 'reports.json'
		return self._get_config_data(file_path)["data"]

	@property
	def settings_config(self) -> SettingsStructure:
		file_path = self.configs_path / 'settings.json'
		return SettingsStructure(**self._get_config_data(file_path)["data"])

	@property
	def stylesheet(self) -> str:
		file_path = self.resource_path / 'styles.css'
		return self._get_config_data(file_path)

	@property
	def password(self) -> str:
		credentials_file = self.configs_path / "credentials"
		if not credentials_file.exists():
			return ""

		with open(credentials_file, "rb") as file:
			data = file.read()
		try:
			iv, ciphertext = data.split(b"|")
			return sslcrypto.aes.decrypt(ciphertext, iv, key).decode("utf-8")
		except (ValueError, UnicodeDecodeError):
			return ""


	@password.setter
	def password(self, password: str) -> None:
		ciphertext, iv = sslcrypto.aes.encrypt(password.encode("utf-8"), key)
		password = iv + b"|" + ciphertext
		with open(self.configs_path / "credentials", "wb") as file:
			file.write(password)


	@property
	def teleports_config(self) -> list[dict[str, str]]:
		file_path = self.configs_path / 'teleports.json'
		return self._get_config_data(file_path)["data"]

	@teleports_config.setter
	def save(self, data: dict):
		file_path = self.configs_path / 'teleports.json'
		config_data = ConfigStructure(data=data).model_dump()
		self._save_config(file_path, config_data)
		self._cache[file_path] = {
			'crc32': calculate_crc32(file_path=file_path),
			'data': config_data
		}


configuration = Configuration()


def get_reports_info() -> dict[str, dict[str, int]]:
	"""
	Get the number of reports for the current day, week, month and all time.

	Returns:
	- reports_dict (dict[str, dict[str, int]]): A dictionary containing the number of reports for the current day, week, month and all time.
	"""
	report_data = configuration.click_data
	today_date_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
	today_date = today_date_dt.strftime(DATE_FORMAT)
	days_since_sunday = today_date_dt.weekday() + 1
	last_sunday_dt = today_date_dt - timedelta(days=days_since_sunday)
	if today_date_dt.weekday() == 6:
		last_sunday_dt = today_date_dt
	last_sunday = last_sunday_dt.strftime(DATE_FORMAT)
	first_month_date = today_date_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime(DATE_FORMAT)
	first_month_date_dt = datetime.strptime(first_month_date, DATE_FORMAT)
	reports_dict: dict[str, dict[str, int]] = {
		"daily_reports": {today_date: report_data.get(today_date, 0)}
	}
	reports_dict["weekly_reports"] = {last_sunday: report_data.get(last_sunday, 0)}
	reports_dict["monthly_reports"] = {first_month_date: report_data.get(first_month_date, 0)}
	first_day = next(iter(report_data), today_date)
	reports_dict["all_reports"] = {first_day: report_data.get(first_day, 0)}
	for date in report_data:
		date_dt = datetime.strptime(date, DATE_FORMAT)
		if last_sunday_dt <= date_dt <= today_date_dt:
			reports_dict.setdefault("weekly_reports", {})[date] = report_data[date]
		if first_month_date_dt <= date_dt <= today_date_dt:
			reports_dict.setdefault("monthly_reports", {})[date] = report_data[date]
		reports_dict.setdefault("all_reports", {})[date] = report_data[date]
	return reports_dict

def get_reports_count(reports_data: dict[str, dict[str, int]] | None = None) -> tuple[int, int, int, int]:
	"""
	Get the number of reports for the current day, week, month and all time.

	Args:
	- reports_data (dict[str, dict[str, int]] | None): The reports data to use.

	Returns:
	- daily_reports (int): The number of reports for the current day.
	- weekly_reports (int): The number of reports for the current week.
	- monthly_reports (int): The number of reports for the current month.
	- all_reports (int): The number of reports for all time.
	"""
	if reports_data is None:
		reports_data = get_reports_info()
	daily_reports = sum(reports_data["daily_reports"].values())
	weekly_reports = sum(reports_data["weekly_reports"].values())
	monthly_reports = sum(reports_data["monthly_reports"].values())
	all_reports = sum(reports_data["all_reports"].values())
	return daily_reports, weekly_reports, monthly_reports, all_reports

def clean_text(text: str) -> str:
	new_text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
	new_text = re.sub(r'^\-\s*', '', new_text, flags=re.MULTILINE)
	new_text = re.sub(r'^\s+', '', new_text, flags=re.MULTILINE)
	new_text = re.sub(r'[;.]$', '', new_text, flags=re.MULTILINE)
	return '\n'.join(f"• {line}" for line in new_text.splitlines())

def convert_datetime_format(time: str) -> str:
	datetime_matches = re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', time)
	for match in datetime_matches:
		dt = datetime.strptime(match, '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=3)
		formatted_dt = dt.strftime('%d.%m.%Y, %H:%M:%S')
		text = time.replace(match, formatted_dt)
	return text

def get_commits_history(commits_count: int) -> list[dict]:
	try:
		response = urllib.request.urlopen(url=f"https://api.github.com/repos/judedm/Binder/commits?per_page={commits_count}", timeout=5)
		commits = json.loads(response.read().decode())
		data = []
		for commit in commits:
			message = commit["commit"]["message"]
			if "\n\n" in message:
				data.append(
					{
						"date": convert_datetime_format(commit["commit"]["committer"]["date"]),
						"message": clean_text(message.split("\n\n")[1])
					}
				)
		return data
	except urllib.error.URLError:
		return []

def create_line(text: str | None = None, class_name: str | None = None) -> QLineEdit:
	line = QLineEdit()
	if text is not None:
		line.setText(str(text))
	if class_name is not None:
		line.setProperty("class", class_name)
	line.setCursorPosition(0)
	return line

def create_label(text: str | None = None, class_name: str | None = None, alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft, word_wrap: bool = False) -> QLabel:
	label = QLabel()
	label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
	if text is not None:
		label.setText(str(text))
	if class_name is not None:
		label.setProperty("class", class_name)
	label.setAlignment(alignment)
	if word_wrap:
		label.setWordWrap(True)
	return label

def create_button(on_click=None, text=None, icon_name=None, class_name=None):
	button = QPushButton(text or "")
	if on_click:
		button.clicked.connect(on_click)
	if icon_name:
		button.setIcon(icons_map[icon_name])
	if class_name:
		button.setProperty("class", class_name)
	return button


replacements = {
	"%background-color%": "#1D1D1E",
	"%font-color%": "#FFFFFF",
	"%button-color%": "#252424",
	"%line-background-color%": "#252424"
}

def parse_stylesheet() -> str:
	style = configuration.stylesheet
	for key, value in replacements.items():
		style = style.replace(key, value)
	style = style.replace("%admin-button-width%", str(configuration.settings_config.button_style.width))
	return style

def check_update():
	urllib.request.urlcleanup()
	try:
		response = urllib.request.urlopen(url="https://raw.githubusercontent.com/JudeDM/binder/main/info.json", timeout=5)
	except urllib.error.URLError:
		return
	data = json.loads(response.read().decode())
	mismatched_files = [fp for fp, exp_hash in data["hashes"].items() if calculate_md5(fp) != exp_hash]
	if mismatched_files:
		config_data = configuration.settings_config
		config_data.show_update_info = True
		configuration.save_config(config_name="settings", data=config_data.model_dump())
		updater_path = os.path.join(os.getcwd(), "..", "updater.exe")
		if not os.path.exists(updater_path):
			url = "https://github.com/JudeDM/binder/raw/main/updater.exe"
			urllib.request.urlretrieve(url, updater_path)
		subprocess.run(["taskkill", "/F", "/PID", str(os.getpid()), "&", "start", "cmd", "/c", updater_path], cwd=os.path.dirname(updater_path), shell=True)



class DraggableWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
		self.initial_pos = None
		self.main_container = QWidget(self)
		self.main_container.setStyleSheet("border: 1px solid #FF7A2F")
		self.main_container.move(0, 0)

	def resizeEvent(self, event):
		self.main_container.resize(self.size())
		super().resizeEvent(event)

	def mousePressEvent(self, event: QMouseEvent):
		if event.button() == Qt.MouseButton.LeftButton:
			self.initial_pos = event.position().toPoint()
		super().mousePressEvent(event)
		event.accept()

	def mouseMoveEvent(self, event: QMouseEvent):
		if self.initial_pos is not None:
			delta = event.position().toPoint() - self.initial_pos
			self.move(self.x() + delta.x(), self.y() + delta.y())
		super().mouseMoveEvent(event)
		event.accept()

	def mouseReleaseEvent(self, event: QMouseEvent):
		self.initial_pos = None
		super().mouseReleaseEvent(event)
		event.accept()


def show_notification(
		parent: QWidget | None = None,
		title: str | None = None,
		text: str | None = None,
		duration: int | None = 4000,
		preset: ToastPreset = ToastPreset.SUCCESS_DARK,
		position: ToastPosition | None = ToastPosition.BOTTOM_MIDDLE,
		always_on_main_screen: bool | None = None,
		relative_to_widget: QWidget | None = None,
		maximum_on_screen: int | None = None,
		vertical_spacing: int | None = None,
		offset_x: int | None = None,
		offset_y: int | None = None,
		show_forever: bool | None = None,
		show_duration_bar: bool | None = None,
		icon: ToastIcon | None = None,
		icon_custom_path: str | None = None,
		icon_size: QSize | None = None,
		icon_color: QColor | None = None,
		icon_separator: bool | None = None,
		icon_separator_color: QColor | None = None,
		icon_separator_width: int | None = None,
		close_button_alignment: ToastButtonAlignment | None = None,
		close_button_icon: ToastIcon | None = None,
		close_button_icon_color: QColor | None = None,
		close_button_icon_size: QSize | None = None,
		close_button_size: QSize | None = None,
		title_font: QFont | None = None,
		text_font: QFont | None = None,
		background_color: QColor | None = None,
		title_color: QColor | None = None,
		text_color: QColor | None = None,
		duration_bar_color: QColor | None = None,
		fade_in_duration: int | None = None,
		fade_out_duration: int | None = None,
		border_radius: int | None = None,
		maximum_width: int | None = None,
		maximum_height: int | None = None,
		minimum_width: int | None = None,
		minimum_height: int | None = None,
		fixed_size: QSize | None = None,
		stay_on_top: bool | None = None,
		reset_duration_on_hover: bool | None = None,
		text_section_spacing: int | None = None,
		margins: QMargins | None = None,
		icon_margins: QMargins | None = None,
		icon_section_margins: QMargins | None = None,
		text_section_margins: QMargins | None = None,
		close_button_margins: QMargins | None = None,
		**kwargs
):
	toast = Toast(parent)

	# Basic toast setup
	if title is not None:
		toast.setTitle(title)
	if text is not None:
		toast.setText(text)
	if duration is not None:
		toast.setDuration(duration)
	if show_forever:
		toast.setDuration(0)

	if preset:
		toast.applyPreset(preset)

	if position:
		Toast.setPosition(position)
	if always_on_main_screen is not None:
		Toast.setAlwaysOnMainScreen(always_on_main_screen)
	if relative_to_widget:
		Toast.setPositionRelativeToWidget(relative_to_widget)
	if maximum_on_screen is not None:
		Toast.setMaximumOnScreen(maximum_on_screen)
	if vertical_spacing is not None:
		Toast.setSpacing(vertical_spacing)
	if offset_x is not None and offset_y is not None:
		Toast.setOffset(offset_x, offset_y)

	if icon_custom_path:
		toast.setIcon(QPixmap(icon_custom_path))
	elif icon:
		toast.setIcon(icon)
	if icon_size is not None:
		toast.setIconSize(icon_size)
	if icon_color is not None:
		toast.setIconColor(icon_color)
	if icon_separator is not None:
		toast.setShowIconSeparator(icon_separator)
	if icon_separator_color is not None:
		toast.setIconSeparatorColor(icon_separator_color)
	if icon_separator_width is not None:
		toast.setIconSeparatorWidth(icon_separator_width)

	if close_button_alignment is not None:
		toast.setCloseButtonAlignment(close_button_alignment)
	if close_button_icon is not None:
		toast.setCloseButtonIcon(close_button_icon)
	if close_button_icon_color is not None:
		toast.setCloseButtonIconColor(close_button_icon_color)
	if close_button_icon_size is not None:
		toast.setCloseButtonIconSize(close_button_icon_size)
	if close_button_size is not None:
		toast.setCloseButtonSize(close_button_size)

	if title_font is not None:
		toast.setTitleFont(title_font)
	if text_font is not None:
		toast.setTextFont(text_font)
	if background_color is not None:
		toast.setBackgroundColor(background_color)
	if title_color is not None:
		toast.setTitleColor(title_color)
	if text_color is not None:
		toast.setTextColor(text_color)
	if duration_bar_color is not None:
		toast.setDurationBarColor(duration_bar_color)

	if show_duration_bar is not None:
		toast.setShowDurationBar(show_duration_bar)
	if fade_in_duration is not None:
		toast.setFadeInDuration(fade_in_duration)
	if fade_out_duration is not None:
		toast.setFadeOutDuration(fade_out_duration)
	if border_radius is not None:
		toast.setBorderRadius(border_radius)
	if stay_on_top is not None:
		toast.setStayOnTop(stay_on_top)
	if reset_duration_on_hover is not None:
		toast.setResetDurationOnHover(reset_duration_on_hover)

	if maximum_width is not None:
		toast.setMaximumWidth(maximum_width)
	if maximum_height is not None:
		toast.setMaximumHeight(maximum_height)
	if minimum_width is not None:
		toast.setMinimumWidth(minimum_width)
	if minimum_height is not None:
		toast.setMinimumHeight(minimum_height)
	if fixed_size is not None:
		toast.setFixedSize(fixed_size)

	if text_section_spacing is not None:
		toast.setTextSectionSpacing(text_section_spacing)
	if margins is not None:
		toast.setMargins(margins)
	if icon_margins is not None:
		toast.setIconMargins(icon_margins)
	if icon_section_margins is not None:
		toast.setIconSectionMargins(icon_section_margins)
	if text_section_margins is not None:
		toast.setTextSectionMargins(text_section_margins)
	if close_button_margins is not None:
		toast.setCloseButtonMargins(close_button_margins)

	toast.show()


def create_header_layout(instance) -> QHBoxLayout:
	"""
	Creates a horizontal layout for the application controls.

	Args:
	- instance (MainApp | Binder): The instance of the main application or binder.

	Returns:
	- QHBoxLayout: The layout containing the minimize and close buttons.
	"""
	header_layout = QHBoxLayout()
	# if title := instance.windowTitle():
	# 	header_title = utils.create_label(text=title)
	# 	header_layout.addWidget(header_title)
	from app import MainApp
	control_layout = QHBoxLayout()
	minimize_button = create_button(on_click=instance.showMinimized, icon_name='minimize', class_name='invisible-button window-control-button')
	close_button = create_button(on_click=instance.close_app if isinstance(instance, MainApp) else instance.close, icon_name='delete', class_name='invisible-button window-control-button')
	if isinstance(instance, MainApp):
		control_layout.addWidget(instance.about_button)
		control_layout.addWidget(instance.settings_button)
	control_layout.addWidget(minimize_button)
	control_layout.addWidget(close_button)
	control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
	header_layout.addLayout(control_layout)
	return header_layout

class HorizontalScrollArea(QScrollArea):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

		self.setMouseTracking(True)

	def wheelEvent(self, event):
		if event.angleDelta().y() != 0:
			scroll_amount = event.angleDelta().y() // 2
			self.horizontalScrollBar().setValue(
				self.horizontalScrollBar().value() - scroll_amount
			)
			event.accept()
		else:
			super().wheelEvent(event)

	def enterEvent(self, event):
		self.setFocus()
		super().enterEvent(event)
