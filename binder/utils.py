from ctypes import Structure, windll, pointer, c_ulong, c_bool, c_int, WINFUNCTYPE, c_uint32, create_unicode_buffer, byref, wintypes
import hashlib
import os
import json
import subprocess
import urllib.request
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton
from PyQt6.QtGui import QIcon
from typing import Callable

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
CLICK_DATA_FILE = os.path.join(__location__, "data/configs/click_data.json")
BUTTON_VIOLATION_CONFIG_FILE = os.path.join(__location__, "data/configs/violation_config.json")
BUTTON_REPORT_CONFIG_FILE = os.path.join(__location__, "data/configs/button_config.json")
BUTTON_HOUSE_CONFIG_FILE = os.path.join(__location__, "data/configs/house_info.json")
SECRET_FILE = os.path.join(__location__, "data/configs/secret.json")
DATE_FORMAT = "%d.%m.%Y"


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
	- pid (int): The process ID.

	Returns:
	- str | None: The name of the process, or None if the process does not exist or cannot be accessed.
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

def load_click_data() -> dict[str, int]:
	"""
	Load the click data from a JSON file.

	Returns:
	- dict: The click data loaded from the file, or an empty dictionary if the file does not exist.
	"""
	return json.load(open(CLICK_DATA_FILE, "r", encoding="utf-8")) if os.path.exists(CLICK_DATA_FILE) else {}

def save_click_data(click_data: dict) -> None:
	"""
	Save the click data to a JSON file.

	Args:
	- click_data (dict): The click data to save.

	Returns:
	- None
	"""
	with open(CLICK_DATA_FILE, "w", encoding="utf8") as f:
		json.dump(click_data, f, indent=4)

def load_violation_button_config() -> dict:
	"""
	Load the violation button configuration data from a JSON file.

	Returns:
	- data (dict): The violation button configuration data loaded from the file.
	"""
	return json.load(open(BUTTON_VIOLATION_CONFIG_FILE, "r", encoding="utf-8")) if os.path.exists(BUTTON_VIOLATION_CONFIG_FILE) else {}

def save_violation_button_config(data: dict) -> None:
	"""
	Save the violation button configuration data to a JSON file.

	Args:
	- data (dict): The violation button configuration data to save.

	Returns:
	- None
	"""
	with open(BUTTON_VIOLATION_CONFIG_FILE, 'w', encoding="utf-8") as json_file:
		json.dump(data, json_file, indent=4, ensure_ascii=False)

def load_report_button_config() -> dict:
	"""
	Load the report button configuration data from a JSON file.

	Returns:
	- data (dict): The report button configuration data loaded from the file.
	"""
	return json.load(open(BUTTON_REPORT_CONFIG_FILE, "r", encoding="utf-8")) if os.path.exists(BUTTON_REPORT_CONFIG_FILE) else {}

def save_report_button_config(data: dict) -> None:
	"""
	Save the report button configuration data to a JSON file.

	Args:
	- data (dict): The report button configuration data to save.

	Returns:
	- None
	"""
	with open(BUTTON_REPORT_CONFIG_FILE, 'w', encoding="utf-8") as json_file:
		json.dump(data, json_file, indent=4, ensure_ascii=False)

def load_secret_config() -> dict:
	"""
	Load the secret configuration data from a JSON file.

	Returns:
	- data (dict): The secret configuration data loaded from the file.
	"""
	return json.load(open(SECRET_FILE, "r", encoding="utf-8")) if os.path.exists(SECRET_FILE) else {}

def save_secret_data(data: dict) -> None:
	"""
	Save the secret data to a JSON file.

	Args:
	- data (dict): The secret data to save.

	Returns:
	- None
	"""
	with open(SECRET_FILE, 'w', encoding="utf8") as json_file:
		json.dump(data, json_file, indent=4, ensure_ascii=False)

def load_house_button_config() -> dict:
	"""
	Load the house button configuration data from a JSON file.

	Returns:
	- data (dict): The house button configuration data loaded from the file.
	"""
	return json.load(open(BUTTON_HOUSE_CONFIG_FILE, "r", encoding="utf-8")) if os.path.exists(BUTTON_HOUSE_CONFIG_FILE) else {}

def save_house_button_config(data: dict) -> None:
	"""
	Save the house button configuration data to a JSON file.

	Args:
	- data (dict): The house button configuration data to save.

	Returns:
	- None
	"""
	with open(BUTTON_HOUSE_CONFIG_FILE, 'w', encoding="utf-8") as json_file:
		json.dump(data, json_file, indent=4, ensure_ascii=False)

def get_reports_info() -> dict[str, dict[str, int]]:
	"""
	Get the number of reports for the current day, week, month and all time.

	Returns:
	- reports_dict (dict[str, dict[str, int]]): A dictionary containing the number of reports for the current day, week, month and all time.
	"""
	reports_dict: dict[str, dict[str, int]] = {}
	today_date = datetime.now().strftime(DATE_FORMAT)
	week_ago_date = (datetime.now() - timedelta(days=datetime.now().weekday() + 1)).strftime(DATE_FORMAT)
	month_ago_date = (datetime.now() - timedelta(days=30)).strftime(DATE_FORMAT)
	report_data = load_click_data()
	week_ago_date_dt = datetime.strptime(week_ago_date, DATE_FORMAT)
	today_date_dt = datetime.strptime(today_date, DATE_FORMAT)
	month_ago_date_dt = datetime.strptime(month_ago_date, DATE_FORMAT)
	reports_dict["daily_reports"] = {today_date: report_data.get(today_date, 0)}
	reports_dict["weekly_reports"] = {week_ago_date: report_data.get(week_ago_date, 0)}
	reports_dict["monthly_reports"] = {month_ago_date: report_data.get(month_ago_date, 0)}
	first_day = next(iter(report_data), today_date)
	reports_dict["all_reports"] = {first_day: report_data.get(first_day, 0)}
	for date in report_data:
		date_dt = datetime.strptime(date, DATE_FORMAT)
		if week_ago_date_dt <= date_dt <= today_date_dt:
			reports_dict.setdefault("weekly_reports", {})[date] = report_data[date]
		if month_ago_date_dt <= date_dt <= today_date_dt:
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

def create_line(text: str | None = None, style: str | None = None) -> QLineEdit:
	"""
	Create a QLineEdit widget with optional text and style.

	Args:
	- text: The text to initialize the QLineEdit with.
	- style: The style sheet to apply to the QLineEdit.

	Returns:
	- QLineEdit: The created QLineEdit widget.
	"""
	line = QLineEdit()
	if text is not None:
		line.setText(str(text))
	if style is not None:
		line.setStyleSheet(style)
	return line

def create_label(text: str | None = None, style: str | None = None) -> QLabel:
	"""
	Create a QLabel widget with optional text and style.

	Args:
	- text: The text to initialize the QLabel with.
	- style: The style sheet to apply to the QLabel.

	Returns:
	- QLabel: The created QLabel widget.
	"""
	label = QLabel()
	if text is not None:
		label.setText(str(text))
	if style is not None:
		label.setStyleSheet(style)
	return label

def create_button(on_click_handler: Callable | None = None, text: str | None = None, icon_name: str | None = None, style: str | None = None) -> QPushButton:
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
        button.setIcon(QIcon(f"data/icons/{icon_name}"))
    if style:
        button.setStyleSheet(style)
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
	"""
	Structure representing a point with X and Y coordinates.

	Attributes:
	- x (c_ulong): X-coordinate.
	- y (c_ulong): Y-coordinate.
	"""
	_fields_ = [("x", c_ulong), ("y", c_ulong)]
