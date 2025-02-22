import sys
import traceback

from PyQt6.QtCore import QMargins, QSize
from pyqttoast import ToastPreset
from utils import show_notification
from urllib.error import URLError
import errno

def setup_excepthook():
	sys.excepthook = my_excepthook

def my_excepthook(type, value, tback):
	tb_lines = traceback.format_exception(type, value, tback)
	formatted_tb = ''.join(tb_lines)

	if isinstance(value, OSError) and value.errno == errno.ENOSPC:
		error_message = "На устройстве не осталось свободного места!"
	elif isinstance(value, URLError):
		error_message = f"Ошибка сети: {value.reason}"""
	elif isinstance(value, RuntimeError) and "wrapped C/C++ object of type" in str(value):
		return
	else:
		custom_message = str(value) if str(value) else formatted_tb
		error_message = f"{custom_message}\n\n{formatted_tb}"

	show_notification(
		title="Произошла ошибка! Обратитесь в дискорд: dmitriy_win",
		duration=0,
		preset=ToastPreset.ERROR_DARK,
		text=error_message,
		icon_separator=False,
		text_section_margins=QMargins(0, 0, 0, 0),
	)

	sys.__excepthook__(type, value, tback)

sys.excepthook = my_excepthook
