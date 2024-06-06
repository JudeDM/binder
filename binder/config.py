DATE_FORMAT = "%d.%m.%Y"
UNCUFF_DEFAULT_REASON = "Поблизости никого нет"

TEXT_COLOR = "#e0e0e0"
BORDER_COLOR = "#3D5A80"
BACKGROUND_COLOR = "#0f1c2e"
LINE_BACKGROUND_COLOR = "#4d648d"
BACKGROUND_COLOR_STYLE = f"background-color: {BACKGROUND_COLOR}"
CONTROL_BUTTONS_STYLE = f"width: 40px; background-color: {BACKGROUND_COLOR}; border: none;"
WINDOW_HEADER_STYLE = f"font-weight: 600; font-size: 16px; color: {TEXT_COLOR}"


# NOTIFICATION STYLE
NOTIFICATION_STYLE = f"""
    QMessageBox {{
        background-color: {BACKGROUND_COLOR};
        border: 2px solid %color%;
    }}
    QPushButton {{
        background-color: %color%;
        color: white;
        border: 1px solid %color%;
        padding: 5px;
        width: 100%;
    }}
    QLabel {{
        color: %color%;
        font-size: 14px;
        font-weight: bold;
    }}
"""

# SETTINGS WINDOW STYLE
SETTINGS_WINDOW_STYLE = F"""
	QScrollBar:horizontal
	{{
		height: 15px;
		margin: 3px 15px 3px 15px;
		border: 1px transparent #2A2929;
		border-radius: 4px;
		background-color: {BORDER_COLOR};
	}}

	QScrollBar::handle:horizontal
	{{
		background-color: {BORDER_COLOR};
		min-width: 5px;
		border-radius: 4px;
	}}

	QScrollBar::add-line:horizontal
	{{
		margin: 0px 3px 0px 3px;
		border-image: url(:/qss_icons/rc/right_arrow_disabled.png);
		width: 10px;
		height: 10px;
		subcontrol-position: right;
		subcontrol-origin: margin;
	}}

	QScrollBar::sub-line:horizontal
	{{
		margin: 0px 3px 0px 3px;
		border-image: url(:/qss_icons/rc/left_arrow_disabled.png);
		height: 10px;
		width: 10px;
		subcontrol-position: left;
		subcontrol-origin: margin;
	}}

	QScrollBar::add-line:horizontal:hover,QScrollBar::add-line:horizontal:on
	{{
		border-image: url(:/qss_icons/rc/right_arrow.png);
		height: 10px;
		width: 10px;
		subcontrol-position: right;
		subcontrol-origin: margin;
	}}


	QScrollBar::sub-line:horizontal:hover, QScrollBar::sub-line:horizontal:on
	{{
		border-image: url(:/qss_icons/rc/left_arrow.png);
		height: 10px;
		width: 10px;
		subcontrol-position: left;
		subcontrol-origin: margin;
	}}

	QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal
	{{
		background: none;
	}}

	QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal
	{{
		background: none;
	}}

	QPushButton
	{{
		font-weight: bold;
		font-size: 16px;
		color: {TEXT_COLOR};
		background-color: {BORDER_COLOR};
		border: 4px solid {BORDER_COLOR};
	}}
"""

ADMIN_BUTTON_STYLE = """
	QPushButton {
		border-radius: 0px;
		background-color: #555555;
		color: #ffffff;
		font-weight: 450;
		font-family: "Columbia";
		font-size: 13px;
		width: 153px;
		height: 33px;
	}

	QPushButton:hover {
		background-color: #666666;
	}

	QLabel {
		color: #ffffff;
		font-family: "Arial";
		font-size: 20px;
	}"""

ADMIN_STATS_STYLE = """
    color: #ffffff;
    font-family: "Arial";
    font-size: 17px;
    font-weight: 600;
"""


#MAIN APP STYLE
MAIN_APP_CONTROL_BUTTON_STYLE = f"""
    font-weight: 600;
    font-size: 16px;
    color: {TEXT_COLOR};
    background-color: {BORDER_COLOR};
    border: 2px solid {BORDER_COLOR};
"""
MAIN_APP_FOOTER_BUTTON_STYLE = f"""
    margin-top: 5px;
    font-weight: 600;
    font-size: 16px;
    color: {TEXT_COLOR};
    background-color: {BORDER_COLOR};
    border: 5px solid {BORDER_COLOR};
"""
MAIN_APP_HEADER_BUTTON_STYLE = f"""
    width: 40px;
    background-color: {BACKGROUND_COLOR};
    border: none;
"""
MAIN_APP_LABEL_TEXT_STYLE = f"""
    font-weight: 600;
    font-size: 17px;
    color: {TEXT_COLOR};
"""
MAIN_APP_LINE_STYLE = f"""
    font-size: 15px;
    font-weight: 600;
    color: {TEXT_COLOR};
    background-color: {LINE_BACKGROUND_COLOR};
    border: 2px solid {BORDER_COLOR};
"""


# GTA MODAL STYLE
GTA_MODAL_TITLE_STYLE = """
    font-family: 'Verdana';
    font-weight: 500;
    font-size: 26px;
    color: #fdfdfd
"""
GTA_MODAL_TEXT_STYLE = f"""
    margin-top: 10px;
    font-family: 'Verdana';
    font-weight: 500;
    font-size: 14px;
    color: {TEXT_COLOR};
"""
GTA_MODAL_LINE_STYLE = """
    padding-left: 10px;
    height: 39px;
    font-family: 'Verdana';
    font-size: 16px;
    color: #6a6f75;
    background-color: #15181b;
    border: 2px solid #84491e;
"""
GTA_MODAL_SEND_BUTTON_STYLE = f"""
    font-family: 'Verdana';
    font-weight: 600;
    font-size: 15px;
    color: {TEXT_COLOR};
    background-color: #f0233c;
"""
GTA_MODAL_CANCEL_BUTTON_STYLE = f"""
    font-family: 'Verdana';
    font-weight: 600;
    font-size: 15px;
    color: {TEXT_COLOR};
    background-color: #2f3843
"""
GTA_MODAL_TITLE_BACKGROUND_COLOR_STYLE = "background-color: #1d1f23"
GTA_MODAL_MIDDLE_BACKGROUND_COLOR_STYLE = "background-color: #1b1e22"
GTA_MODAL_FOOTER_BACKGROUND_COLOR_STYLE = "background-color: #1e2327"


# SETTINGS STYLE
SETTINGS_BUTTON_STYLE = """
    min-height: 30px;
    min-width: 30px;
    border: none;
"""


# REPORT SETTINGS STYLE
REPORT_SETTINGS_SHORT_STYLE = f"""
    min-width: 140px;
    max-width: 140px;
    font-size: 14px;
    font-weight: 500;
    color: {TEXT_COLOR};
    background-color: {LINE_BACKGROUND_COLOR};
    border: 2px solid {BORDER_COLOR};
"""
REPORT_SETTINGS_LONG_STYLE = f"""
    min-width: 300px;
    max-width: 300px;
    font-size: 14px;
    font-weight: 500;
    color: {TEXT_COLOR};
    background-color: {LINE_BACKGROUND_COLOR};
    border: 2px solid {BORDER_COLOR};
"""
REPORT_SETTINGS_SHORT_LABEL_STYLE = f"""
    min-width: 145px;
    max-width: 145px;
    font-weight: 600;
    font-size: 15px;
    color: {TEXT_COLOR};
"""
REPORT_SETTINGS_LONG_LABEL_STYLE = f"""
    min-width: 305px;
    max-width: 305px;
    font-weight: 600;
    font-size: 15px;
    color: {TEXT_COLOR};
"""


#VIOLATION SETTINGS STYLE
VIOLATION_SETTINGS_SHORT_STYLE = f"""
    min-width: 100px;
    max-width: 100px;
    font-size: 14px;
    font-weight: 500;
    color: {TEXT_COLOR};
    background-color: {LINE_BACKGROUND_COLOR};
    border: 2px solid {BORDER_COLOR};
"""
VIOLATION_SETTINGS_LONG_STYLE = f"""
    min-width: 300px;
    max-width: 300px;
    font-size: 14px;
    font-weight: 500;
    color: {TEXT_COLOR};
    background-color: {LINE_BACKGROUND_COLOR};
    border: 2px solid {BORDER_COLOR};
"""
VIOLATION_SETTINGS_SHORT_LABEL_STYLE = f"""
    min-width: 105px;
    max-width: 105px;
    font-weight: 600;
    font-size: 15px;
    color: {TEXT_COLOR};
"""
VIOLATION_SETTINGS_LONG_LABEL_STYLE = f"""
    min-width: 300px;
    max-width: 300px;
    font-weight: 600;
    font-size: 15px;
    color: {TEXT_COLOR};
"""

# TELEPORT SETTINGS STYLE
TELEPORT_SETTINGS_SHORT_STYLE = f"""
    min-width: 180px;
    max-width: 180px;
    font-size: 15px;
    font-weight: 500;
    color: {TEXT_COLOR};
    background-color: {LINE_BACKGROUND_COLOR};
    border: 2px solid {BORDER_COLOR};
"""
TELEPORT_SETTINGS_LABEL_STYLE = f"""
    min-width: 180px;
    max-width: 180px;
    font-weight: 600;
    font-size: 15px;
    color: {TEXT_COLOR};
"""

# ABOUT WINDOW STYLE
ABOUT_WINDOW_TITLE_STYLE = f"""
    font-weight: 700;
    font-size: 18px;
    color: {TEXT_COLOR};
    margin-top: 20px;
"""
ABOUT_WINDOW_TEXT_STYLE = f"""
    font-weight: 600;
    font-size: 15px;
    color: {TEXT_COLOR};
"""
ABOUT_WINDOW_ICONS_BUTTON_STYLE = f"""
    height: 40px;
    background-color:{BACKGROUND_COLOR};
    border: none;
"""
ABOUT_WINDOW_BUTTON_STYLE = f"""
    margin-top: 5px;
    font-weight: 600;
    font-size: 14px;
    color: {TEXT_COLOR};
    background-color: {BORDER_COLOR};
    border: 5px solid {BORDER_COLOR};
"""