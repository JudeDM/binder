import sys
import traceback

from PyQt6.QtCore import QMargins, QSize
from pyqttoast import ToastPreset
from utils import show_notification


def setup_excepthook():
	sys.excepthook = my_excepthook

def my_excepthook(type, value, tback):
	tb_lines = traceback.format_exception(type, value, tback)
	formatted_tb = ''.join(tb_lines)
	if str(value) == "":
		error_message = formatted_tb
	else:
		error_message = f"{str(value)}\n\n{formatted_tb}"
	show_notification(
		title="Произошла неизвестная ошибка!\nПросьба сообщить об ошибке в дискорд: dmitriy_win",
		duration=15000, preset=ToastPreset.ERROR_DARK,
		text=error_message,
		icon_separator=False,
		text_section_margins=QMargins(0, 0, 0, 0),
		# fixed_size=QSize(1000, 500),
	)
	sys.__excepthook__(type, value, tback)
