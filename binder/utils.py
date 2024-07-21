import contextlib
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
from ctypes import (WINFUNCTYPE, Structure, byref, c_bool, c_int, c_uint32,
                    c_ulong, create_unicode_buffer, pointer, windll, wintypes)
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable, NamedTuple

# import hwid
import sslcrypto
from pydantic import BaseModel, Field
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QMouseEvent
from PyQt6.QtWidgets import (QApplication, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QWidget)

__location__ = os.getcwd()
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
}


class HWIDGenerator:
    def __init__(self):
        self.drive_serial = self.safe_execute(self.get_drive_serial)
        self.cpu_id = self.safe_execute(self.get_cpu_id)
        self.username = self.safe_execute(self.get_username)
        self.mac_address = self.safe_execute(self.get_mac_address)
        self.system_id = self.safe_execute(self.get_system_id)
        self.motherboard_serial = self.safe_execute(self.get_motherboard_serial)
        self.system_uuid = self.safe_execute(self.get_system_uuid)

    @staticmethod
    def safe_execute(method):
        try:
            return method()
        except Exception as e:
            return str(e)

    @staticmethod
    def get_drive_serial() -> str:
        return hex(uuid.getnode())

    @staticmethod
    def get_cpu_id() -> str:
        return hashlib.md5(platform.processor().encode()).hexdigest()

    @staticmethod
    def get_username() -> str:
        return os.getlogin()

    @staticmethod
    def get_mac_address() -> str:
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ':'.join([mac[e:e+2] for e in range(0, 12, 2)])

    @staticmethod
    def get_system_id() -> str:
        return platform.node()

    @staticmethod
    def get_motherboard_serial() -> str:
        return subprocess.check_output('wmic baseboard get serialnumber', shell=True).decode().split('\n')[1].strip()

    @staticmethod
    def get_system_uuid() -> str:
        return subprocess.check_output('wmic csproduct get uuid', shell=True).decode().split('\n')[1].strip()

    def generate_hwid(self) -> str:
        hwid_string = (
            f"{self.drive_serial}-{self.cpu_id}-{self.username}-"
            f"{self.mac_address}-{self.system_id}-"
            f"{self.motherboard_serial}-{self.system_uuid}"
        )
        return hashlib.sha256(hwid_string.encode()).hexdigest()


hwid_generator = HWIDGenerator()

class TabPixelInfo(NamedTuple):
	"""
	An object representing the pixel information of a tab.

	Attributes:
	- x (int): The x-coordinate of the pixel.
	- y (int): The y-coordinate of the pixel.
	- color (tuple): The RGB values of the pixel.
	- left_side (bool): Whether the pixel is on the left side of the tab.
	- top_side (bool): Whether the pixel is on the top side of the tab.
	"""
	x: int
	y: int
	color: tuple
	left_side: bool
	top_side: bool


pixel_map: dict[str, list[TabPixelInfo]] = {
	"game_window": [
		TabPixelInfo(x=20, y=370, color=(68, 68, 68), left_side=False, top_side=False),
		TabPixelInfo(x=70, y=370, color=(68, 68, 68), left_side=False, top_side=False)
	],
	"admin_panel": [
		TabPixelInfo(x=940, y=360, color=(85, 85, 85), left_side=True, top_side=True),
		TabPixelInfo(x=940, y=385, color=(85, 85, 85), left_side=True, top_side=True)
	],
	"console_tab": [
		TabPixelInfo(x=12, y=12, color=(255, 255, 255), left_side=True, top_side=True),
		TabPixelInfo(x=12, y=60, color=(255, 255, 255), left_side=True, top_side=True),
		TabPixelInfo(x=20, y=370, color=(68, 68, 68), left_side=True, top_side=True),
		TabPixelInfo(x=70, y=370, color=(68, 68, 68), left_side=True, top_side=True)
	],
	"reports_tab": [
		TabPixelInfo(x=250, y=370, color=(68, 68, 68), left_side=True, top_side=True),
		TabPixelInfo(x=305, y=338, color=(68, 68, 68), left_side=True, top_side=True)
	],
	"teleport_tab": [
		TabPixelInfo(x=340, y=370, color=(68, 68, 68), left_side=True, top_side=True),
		TabPixelInfo(x=420, y=370, color=(68, 68, 68), left_side=True, top_side=True)
	]
}


key = hashlib.sha256(hwid_generator.generate_hwid().encode()).digest()

def get_process(process_name: str) -> tuple[int, int] | None:
	"""
	Get the window handle and process ID of the first window with the given process name.

	Args:
	- process_name (str): The name of the process.

	Returns:
	- tuple[int, int] | None: A tuple containing the window handle (int) and process ID (int) of the first matching window,
		or None if no matching window is found.
	"""
	return next(((hwnd, pid) for hwnd, pid in get_process_handles() if process_name == get_process_name(pid)), None)

def get_process_handles() -> list[tuple[int, int]]:
	"""
	Get handles of all windows and their corresponding process IDs.

	Returns:
	- list[tuple[int, int]]: A list of tuples, where each tuple contains a window handle
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
	- hwnd (int): The window handle.

	Returns:
	- tuple[int, int, int, int] | None: The left, top, right, and bottom coordinates of the window,
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


def get_process_name(pid: int) -> str | None:
	"""
	Get the name of the process with the given process ID.

	Args:
	- pid (int): The process ID.

	Returns:
	- str | None: The name of the process, or None if the process does not exist or cannot be accessed.
	"""
	kernel32 = windll.kernel32

	with contextlib.suppress(Exception):
		hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
		if not hProcess:
			return None

		buffer = create_unicode_buffer(260)
		buffer_size = c_uint32(260)
		success = kernel32.QueryFullProcessImageNameW(hProcess, 0, byref(buffer), byref(buffer_size))
		kernel32.CloseHandle(hProcess)

		if success:
			return os.path.basename(buffer.value) if buffer.value else None
	return None

def has_border(hwnd: wintypes.HWND) -> bool:
	"""
	Check if a window has a border or caption.

	Args:
	- hwnd (ctypes.wintypes.HWND): The window handle.

	Returns:
	- bool: True if the window has a border or caption, False otherwise.
	"""
	style = GetWindowLong(hwnd, c_int(GWL_STYLE))
	has_border = bool(style & WS_BORDER)
	has_caption = bool(style & WS_CAPTION)
	return has_border or has_caption

def get_pixel_color(x: int, y: int, LEFT: int | None = None, TOP:  int | None = None) -> tuple[int, int, int]:
	"""
	Get the color of a pixel at the specified coordinates.

	Args:
	- x (int): The x-coordinate of the pixel.
	- y (int): The y-coordinate of the pixel.
	- LEFT (int | None): The left offset.
	- TOP (int | None): The top offset.

	Returns:
	- tuple[int, int, int]: The RGB values of the pixel.
	"""
	hdc = user32.GetDC(0)
	pixel = windll.gdi32.GetPixel(hdc, x + (LEFT or 0), y + (TOP or 0))
	user32.ReleaseDC(0, hdc)
	red = pixel & 0xFF
	green = (pixel >> 8) & 0xFF
	blue = (pixel >> 16) & 0xFF
	return red, green, blue

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

	def validate_config_files(self) -> None:
		"""
		Validate individual configuration files.
		"""
		for file_name in self.config_names:
			config_path = self.configs_path / f"{file_name}.json"
			if config_path.exists():
				with config_path.open("r", encoding="utf-8") as file:
					try:
						data = json.load(file)
					except json.JSONDecodeError:
						new_data = ConfigStructure()
						self._save_config(config_path, new_data.model_dump())
						continue
				if isinstance(data, list) and data and isinstance(data[0], list) and isinstance(data[0][0], dict):
					all_buttons = [button for group in data for button in group]
					new_data = ConfigStructure(data=all_buttons)
					self._save_config(config_path, new_data.model_dump())
				elif not isinstance(data, dict):
					new_data = ConfigStructure()
					self._save_config(config_path, new_data.model_dump())
			else:
				new_data = ConfigStructure()
				self._save_config(config_path, new_data.model_dump())

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
	def violations_config(self) -> dict:
		file_path = self.configs_path / 'violations.json'
		return self._get_config_data(file_path)["data"]

	@property
	def reports_config(self) -> dict:
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
	def teleports_config(self) -> dict:
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
	return '\n'.join(f"- {line}" for line in new_text.splitlines())

def convert_datetime_format(time: str) -> str:
	datetime_matches = re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', time)
	for match in datetime_matches:
		dt = datetime.strptime(match, '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=3)
		formatted_dt = dt.strftime('%d.%m.%Y, %H:%M:%S')
		text = time.replace(match, formatted_dt)
	return text

def get_commits_history() -> list[dict]:
	try:
		response = urllib.request.urlopen(url="https://api.github.com/repos/judedm/Binder/commits?per_page=10000", timeout=5)
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
	"""
	Create a QLineEdit widget with optional text and style.

	Args:
	- text: The text to initialize the QLineEdit with.
	- class_name: The class name to apply to the QLineEdit.

	Returns:
	- QLineEdit: The created QLineEdit widget.
	"""
	line = QLineEdit()
	if text is not None:
		line.setText(str(text))
	if class_name is not None:
		line.setProperty("class", class_name)
	line.setCursorPosition(0)
	return line

def create_label(text: str | None = None, class_name: str | None = None) -> QLabel:
	"""
	Create a QLabel widget with optional text and style.

	Args:
	- text: The text to initialize the QLabel with.
	- style: The class name to apply to the QLabel.

	Returns:
	- QLabel: The created QLabel widget.
	"""
	label = QLabel()
	label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
	if text is not None:
		label.setText(str(text))
	if class_name is not None:
		label.setProperty("class", class_name)
	return label

def create_button(on_click_handler: Callable | None = None, text: str | None = None, icon_name: str | None = None, class_name: str | None = None) -> QPushButton:
	"""
	Create a QPushButton widget with optional text, click handler, icon and style.

	Args:
	- on_click_handler (Callable | None): The function to call when the button is clicked.
	- text (str | None): The text to initialize the QPushButton with.
	- icon_name (str | None): The name of the icon to set for the button.
	- style (str | None): The style sheet to apply to the QPushButton.

	Returns:
	- QPushButton: The created QPushButton widget.
	"""
	button: QPushButton = QPushButton()
	if text:
		button.setText(text)
	if on_click_handler:
		button.clicked.connect(on_click_handler)
	if icon_name:
		button.setIcon(icons_map[icon_name])
		button.setIconSize(QSize(16, 16))
	if class_name:
		button.setProperty("class", class_name)
	return button

def is_within_range(color1: tuple[int, int, int], color2: tuple[int, int, int], tolerance: int = 5) -> bool:
	"""
	Check if two colors are within a given tolerance range.

	Args:
	- color1 (tuple[int, int, int]): The first color as a tuple of three integers.
	- color2 (tuple[int, int, int]): The second color as a tuple of three integers.
	- tolerance (int): The maximum difference between color components. Default is 5.

	Returns:
	- bool: True if the colors are within the tolerance range, False otherwise.
	"""
	return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))

replacements = {
	"%background-color%": "#0f1c2e",
	"%font-color%": "#e0e0e0",
	"%button-color%": "#4d648d",
	"%line-background-color%": "#3D5A80"
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
	except urllib.error.UrlError:
		return
	data = json.loads(response.read().decode())
	mismatched_files = [fp for fp, exp_hash in data["hashes"].items() if calculate_md5(fp) != exp_hash]
	if mismatched_files:
		updater_path = os.path.join(os.getcwd(), "..", "updater.exe")
		if not os.path.exists(updater_path):
			url = "https://github.com/JudeDM/binder/raw/main/updater.exe"
			urllib.request.urlretrieve(url, updater_path)
		subprocess.run(["taskkill", "/F", "/PID", str(os.getpid()), "&", "start", "cmd", "/c", updater_path], cwd=os.path.dirname(updater_path), shell=True)

def is_tab_open(tab_name: str, RIGHT: int, BOTTOM: int, LEFT: int, TOP: int) -> bool:
	"""
	Check if a tab is open by comparing the color of pixels at specific coordinates.

	Args:
	- tab_name (str): The name of the tab.

	Returns:
	- bool: True if all pixels match the specified color, False otherwise.
	"""
	return all(
		is_within_range(
			get_pixel_color(
				x=line.x if line.left_side else RIGHT - line.x,
				y=line.y if line.top_side else BOTTOM - line.y,
				LEFT=LEFT, TOP=TOP
			), line.color
		) for line in pixel_map[tab_name]
	)

class NotificationType(Enum):
	CRITICAL = "critical"
	WARNING = "warning"
	DEFAULT = "default"

	def get_color(self) -> str:
		colors = {
			self.__class__.CRITICAL: "red",
			self.__class__.WARNING: "orange",
			self.__class__.DEFAULT: "#00aaff",
		}
		return colors.get(self, "white")

	def get_icon(self) -> QMessageBox:
		icons = {
			self.__class__.CRITICAL: QMessageBox.Icon.Critical,
			self.__class__.WARNING: QMessageBox.Icon.Warning,
			self.__class__.DEFAULT: QMessageBox.Icon.Information,
		}
		return icons.get(self, QMessageBox.Icon.Information)

def copy_to_clipboard(text):
    clipboard = QApplication.clipboard()
    clipboard.setText(text)

class Notification(QMessageBox):
	def __init__(self, text: str, notification_type: NotificationType = NotificationType.DEFAULT):
		super().__init__()
		self.setIcon(notification_type.get_icon())
		self.setWindowTitle("Уведомление")
		self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
		self.setText(text)
		if notification_type == NotificationType.CRITICAL:
			copy_button = QPushButton("Скопировать ошибку")
			copy_button.setFixedWidth(160)
			self.addButton(copy_button, QMessageBox.ButtonRole.NoRole)
			self.setStandardButtons(QMessageBox.StandardButton.Ok)
			def on_copy_button_clicked():
				copy_to_clipboard(text.split("<br><pre>")[1].split("</pre><br><b>")[0])
			copy_button.clicked.connect(on_copy_button_clicked)
		color = notification_type.get_color()
		style = parse_stylesheet().replace("%color%", color)
		self.setStyleSheet(style)


class DragableWidget(QWidget):
	def __init__(self):
		super().__init__(None)
		self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
		self.initial_pos = None

	def mousePressEvent(self, event: QMouseEvent):
		if event.button() == Qt.MouseButton.LeftButton:
			self.initial_pos = event.position().toPoint()
		super().mousePressEvent(event)
		event.accept()

	def mouseMoveEvent(self, event: QMouseEvent):
		if self.initial_pos is not None:
			delta = event.position().toPoint() - self.initial_pos
			self.window().move(
				self.window().x() + delta.x(),
				self.window().y() + delta.y(),
			)
		super().mouseMoveEvent(event)
		event.accept()

	def mouseReleaseEvent(self, event: QMouseEvent):
		self.initial_pos = None
		super().mouseReleaseEvent(event)
		event.accept()

	def show_notification(self, text: str, notification_type: NotificationType=NotificationType.DEFAULT):
		self.notification = Notification(text, notification_type)
		self.notification.show()


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
		buttons = self.MOUSEEVENTF_RIGHTDOWN if button_name.find("right") >= 0 else 0
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
	"""
	Structure representing a point with X and Y coordinates.

	Attributes:
	- x (c_ulong): X-coordinate.
	- y (c_ulong): Y-coordinate.
	"""
	_fields_ = [("x", c_ulong), ("y", c_ulong)]
