import sys

import psutil
from app import MainApp
from coordinate_updater import CoordinateUpdater
from exceptions import setup_excepthook
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from utils import configuration, parse_stylesheet

if __name__ == '__main__':
    process = psutil.Process()
    process.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)

    setup_excepthook()
    global app
    coordinate_updater = CoordinateUpdater()
    coordinate_updater.start()
    app = QApplication(sys.argv)
    style = parse_stylesheet()
    app.setStyleSheet(style)
    app_icon = QIcon(str(configuration.resource_path / 'logo.ico'))
    app.setWindowIcon(app_icon)
    app.aboutToQuit.connect(coordinate_updater.stop)
    main_app = MainApp(app=app, coordinate_updater=coordinate_updater)
    main_app.show()
    # keyboard.add_hotkey('F8', coordinate_updater.autologin)
    sys.exit(app.exec())
