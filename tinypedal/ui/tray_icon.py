#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2024 TinyPedal developers, see contributors.md file
#
#  This file is part of TinyPedal.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Tray icon
"""

from PySide2.QtWidgets import QSystemTrayIcon

from ..const import APP_NAME, VERSION
from .menu import OverlayMenu


class TrayIcon(QSystemTrayIcon):
    """System tray icon & menu"""

    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent

        # Config tray icon
        self.setIcon(parent.windowIcon())
        self.setToolTip(f"{APP_NAME} v{VERSION}")
        self.activated.connect(self.active_doubleclick)

        # Create tray menu
        menu = OverlayMenu("Overlay", parent, True)
        self.setContextMenu(menu)

    def active_doubleclick(self, active_reason: QSystemTrayIcon.ActivationReason):
        """Active on doubleclick"""
        if active_reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._parent.show_app()
