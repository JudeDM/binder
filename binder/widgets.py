from PyQt6.QtCore import (QMimeData, QPointF, QPropertyAnimation, Qt,
                          pyqtProperty)
from PyQt6.QtGui import (QColor, QCursor, QDrag, QDragEnterEvent, QDropEvent,
                         QMouseEvent, QPainter, QPen, QPixmap)
from PyQt6.QtWidgets import QPushButton


class MovableButton(QPushButton):
	def __init__(self, text, on_click_handler, row: int, column: int, data=None, parent=None):
		super().__init__(text)
		self.parent = parent
		self.setAcceptDrops(True)
		self.row, self.column = row, column
		self.on_click_handler = on_click_handler
		self.data = data or {}
		self.start_pos = QPointF()
		self.is_dragged = False
		self.clicked.connect(on_click_handler)
		self.setProperty("class", "draggable-button")
		self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
		self.dot_color = QColor("#B0B0B0")
		self._dot_opacity = 0.0
		self.dot_animation = QPropertyAnimation(self, b"dotOpacity")
		self.dot_animation.setDuration(150)

	@pyqtProperty(float)
	def dotOpacity(self):
		return self._dot_opacity

	@dotOpacity.setter
	def dotOpacity(self, value):
		self._dot_opacity = value
		self.update()

	def enterEvent(self, event):
		self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
		self.dot_animation.stop()
		self.dot_animation.setStartValue(self._dot_opacity)
		self.dot_animation.setEndValue(1.0)
		self.dot_animation.start()
		super().enterEvent(event)

	def leaveEvent(self, event):
		self.unsetCursor()
		self.dot_animation.stop()
		self.dot_animation.setStartValue(self._dot_opacity)
		self.dot_animation.setEndValue(0.0)
		self.dot_animation.start()
		super().leaveEvent(event)

	def mousePressEvent(self, event: QMouseEvent) -> None:
		if event.button() == Qt.MouseButton.LeftButton:
			self.start_pos = event.pos()
			self.is_dragged = False
			self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
			super().mousePressEvent(event)

	def mouseReleaseEvent(self, event: QMouseEvent) -> None:
		self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
		if not self.is_dragged:
			super().mouseReleaseEvent(event)
		else:
			self.dot_animation.stop()
			self._dot_opacity = 0.0
			self.update()

	def mouseMoveEvent(self, event: QMouseEvent) -> None:
		if event.buttons() & Qt.MouseButton.LeftButton and (event.pos() - self.start_pos).manhattanLength() > 5:
			self.is_dragged = True
			self.dot_animation.stop()
			self._dot_opacity = 1.0
			self.update()
			drag = QDrag(self)
			mime_data = QMimeData()
			mime_data.setText(self.text())
			drag.setMimeData(mime_data)
			pixmap = self._create_drag_pixmap()
			drag.setPixmap(pixmap)
			drag.setHotSpot(event.pos())
			drag.exec()

	def _create_drag_pixmap(self) -> QPixmap:
		pixmap = self.grab()
		painter = QPainter(pixmap)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		pen = QPen(QColor("#FF7A2F"))
		pen.setWidth(4)
		painter.setPen(pen)
		painter.drawRect(pixmap.rect())
		painter.end()
		return pixmap

	def paintEvent(self, event):
		super().paintEvent(event)

		icon_name = self.objectName()
		if icon_name in ['prison', 'ban', 'mute']:
			icon_path = f"data/icons/{icon_name}.svg"
			icon = QPixmap(icon_path)
			if not icon.isNull():
				icon = icon.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio)
				icon_rect = icon.rect()
				icon_rect.moveTo(self.width() - icon_rect.width() - 10, (self.height() - icon_rect.height()) // 2)
				painter = QPainter(self)
				painter.drawPixmap(icon_rect, icon)
				painter.end()

		if self._dot_opacity > 0:
			painter = QPainter(self)
			painter.setRenderHint(QPainter.RenderHint.Antialiasing)
			painter.setPen(Qt.NoPen)
			dot_color = QColor(self.dot_color)
			dot_color.setAlphaF(self._dot_opacity)
			painter.setBrush(dot_color)
			dot_radius = 2
			dot_spacing = 6
			left_margin = 6
			column_spacing = 4
			top_margin = (self.height() - 3 * dot_radius * 2 - 2 * dot_spacing) / 2
			for i in range(3):
				x1 = left_margin
				x2 = left_margin + column_spacing + dot_radius * 2
				y = top_margin + i * (2 * dot_radius + dot_spacing)
				painter.drawEllipse(int(x1), int(y), dot_radius * 2, dot_radius * 2)
				painter.drawEllipse(int(x2), int(y), dot_radius * 2, dot_radius * 2)
			painter.end()


	def dragEnterEvent(self, event: QDragEnterEvent) -> None:
		if event.mimeData().hasText():
			self.setStyleSheet("border: 2px solid #FF7A2F;")
			event.acceptProposedAction()

	def dragLeaveEvent(self, event: QDragEnterEvent) -> None:
		self.setStyleSheet("")

	def dropEvent(self, event: QDropEvent) -> None:
		source_button = event.source()
		if isinstance(source_button, MovableButton):
			self._swap_button_data(source_button)
			event.acceptProposedAction()
		self.setStyleSheet("")

	def _swap_button_data(self, source_button: 'MovableButton') -> None:
		from settings import ButtonsSettings

		source_text, source_handler = source_button.text(), source_button.on_click_handler
		source_button.setText(self.text())
		self.setText(source_text)
		self.on_click_handler = source_handler
		self.data, source_button.data = source_button.data, self.data

		source_object_name = source_button.objectName()
		source_button.setObjectName(self.objectName())
		self.setObjectName(source_object_name)

		if isinstance(self.parent, ButtonsSettings):
			buttons_dict = self.parent.teleports_config if self.parent.active_window == "teleport" else self.parent.reports_config if self.parent.active_window == "report" else self.parent.violations_config
			source_button_index = next((i for i, btn in enumerate(buttons_dict) if btn["name"] == source_button.text()), None)
			target_button_index = next((i for i, btn in enumerate(buttons_dict) if btn["name"] == self.text()), None)

			if source_button_index is not None and target_button_index is not None:
				buttons_dict[source_button_index], buttons_dict[target_button_index] = buttons_dict[target_button_index], buttons_dict[source_button_index]

				source_button_data = buttons_dict[source_button_index]
				target_button_data = buttons_dict[target_button_index]
				source_button_data["row"], target_button_data["row"] = target_button_data["row"], source_button_data["row"]
				source_button_data["column"], target_button_data["column"] = target_button_data["column"], source_button_data["column"]
