import time
from hmac import new

import binder_utils
from PyQt6.QtCore import QThread, pyqtSignal


class CoordinateUpdater(QThread):
	coordinates_updated = pyqtSignal(int, int, int, int, int, int)

	def __init__(self):
		super().__init__()
		self._running = True
		self.left = 0
		self.top = 0
		self.right = 0
		self.bottom = 0
		self.window_width = 0
		self.window_height = 0

	def update_coordinates(self, process):
		left, top, right, bottom = binder_utils.get_window_coordinates(process[0])
		if binder_utils.has_border(process[0]):
			left += 8
			top += 31
			right -= 9
			bottom -= 9
		self.window_width = right - left
		self.window_height = bottom - top
		return left, top, right, bottom

	def run(self):
		while self._running:
			try:
				process = binder_utils.get_process("GTA5.exe")
				if process is not None:
					new_left, new_top, new_right, new_bottom = self.update_coordinates(process)
					if (
						(new_left, new_top, new_right, new_bottom) != (self.left, self.top, self.right, self.bottom)
						or self.window_width != self.right - self.left
						or self.window_height != self.bottom - self.top
					):
						self.left, self.top, self.right, self.bottom = new_left, new_top, new_right, new_bottom
						self.coordinates_updated.emit(self.left, self.top, self.right, self.bottom, self.window_width, self.window_height)

				time.sleep(1.5)
			except Exception as e:
				print(e)

	def stop(self):
		self._running = False
		self.wait()

	# def autologin(self):
	# 	from utils import configuration

	# 	binder_utils.keyboard_press("t")
	# 	time.sleep(0.5)
	# 	binder_utils.keyboard_press('ctrl+a backspace')
	# 	binder_utils.keyboard_send('/alogin13')
	# 	time.sleep(0.5)
	# 	binder_utils.keyboard_press("enter")
	# 	time.sleep(0.5)
	# 	binder_utils.keyboard_press("`")
	# 	time.sleep(0.5)
	# 	binder_utils.mouse_click((self.left+80, self.top+380))
	# 	binder_utils.keyboard_send(configuration.password)
	# 	time.sleep(0.5)
	# 	binder_utils.keyboard_send('hp')
	# 	time.sleep(1)
	# 	binder_utils.keyboard_send('fly')
	# 	binder_utils.keyboard_press("`")
