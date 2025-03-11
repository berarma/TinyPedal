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
Vehicle brand editor
"""

import os
import logging
import json
import time
import socket
from urllib.request import urlopen

from PySide2.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QDialogButtonBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
    QHeaderView,
    QMenu,
    QAction,
)

from ..api_control import api
from ..setting import ConfigType, cfg, copy_setting
from ..module_control import wctrl
from ._common import (
    BaseEditor,
    TableBatchReplace,
    QSS_EDITOR_BUTTON,
)

HEADER_BRANDS = "Vehicle name","Brand name"

logger = logging.getLogger(__name__)


class VehicleBrandEditor(BaseEditor):
    """Vehicle brand editor"""

    def __init__(self, master):
        super().__init__(master)
        self.set_utility_title("Vehicle Brand Editor")
        self.setMinimumSize(600, 500)

        self.brands_temp = copy_setting(cfg.user.brands)

        # Set table
        self.table_brands = QTableWidget(self)
        self.table_brands.setColumnCount(len(HEADER_BRANDS))
        self.table_brands.setHorizontalHeaderLabels(HEADER_BRANDS)
        self.table_brands.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_brands.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table_brands.cellChanged.connect(self.set_modified)
        self.refresh_table()
        self.set_unmodified()

        # Set button
        layout_button = self.set_layout_button()

        # Set layout
        layout_main = QVBoxLayout()
        layout_main.addWidget(self.table_brands)
        layout_main.addLayout(layout_button)
        self.setLayout(layout_main)

    def set_layout_button(self):
        """Set button layout"""
        # Menu
        import_menu = QMenu(self)

        import_rf2 = QAction("RF2 Rest API", self)
        import_rf2.triggered.connect(self.import_from_rf2)
        import_menu.addAction(import_rf2)

        import_lmu = QAction("LMU Rest API", self)
        import_lmu.triggered.connect(self.import_from_lmu)
        import_menu.addAction(import_lmu)

        import_json = QAction("JSON file", self)
        import_json.triggered.connect(self.import_from_file)
        import_menu.addAction(import_json)

        # Button
        button_import = QPushButton("Import from")
        button_import.setStyleSheet(QSS_EDITOR_BUTTON)
        button_import.setMenu(import_menu)

        button_add = QPushButton("Add")
        button_add.clicked.connect(self.add_brand)
        button_add.setStyleSheet(QSS_EDITOR_BUTTON)

        button_sort = QPushButton("Sort")
        button_sort.clicked.connect(self.sort_brand)
        button_sort.setStyleSheet(QSS_EDITOR_BUTTON)

        button_delete = QPushButton("Delete")
        button_delete.clicked.connect(self.delete_brand)
        button_delete.setStyleSheet(QSS_EDITOR_BUTTON)

        button_replace = QPushButton("Replace")
        button_replace.clicked.connect(self.open_replace_dialog)
        button_replace.setStyleSheet(QSS_EDITOR_BUTTON)

        button_reset = QDialogButtonBox(QDialogButtonBox.Reset)
        button_reset.clicked.connect(self.reset_setting)
        button_reset.setStyleSheet(QSS_EDITOR_BUTTON)

        button_apply = QDialogButtonBox(QDialogButtonBox.Apply)
        button_apply.clicked.connect(self.applying)
        button_apply.setStyleSheet(QSS_EDITOR_BUTTON)

        button_save = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Close)
        button_save.accepted.connect(self.saving)
        button_save.rejected.connect(self.close)
        button_save.setStyleSheet(QSS_EDITOR_BUTTON)

        # Set layout
        layout_button = QHBoxLayout()
        layout_button.addWidget(button_import)
        layout_button.addWidget(button_add)
        layout_button.addWidget(button_sort)
        layout_button.addWidget(button_delete)
        layout_button.addWidget(button_replace)
        layout_button.addWidget(button_reset)
        layout_button.addStretch(1)
        layout_button.addWidget(button_apply)
        layout_button.addWidget(button_save)
        return layout_button

    def refresh_table(self):
        """Refresh brands list"""
        self.table_brands.setRowCount(0)
        row_index = 0
        for veh_name, brand_name in self.brands_temp.items():
            self.add_vehicle_entry(row_index, veh_name, brand_name)
            row_index += 1

    def import_from_rf2(self):
        """Import brand from RF2"""
        self.import_from_restapi("RF2")

    def import_from_lmu(self):
        """Import brand from LMU"""
        self.import_from_restapi("LMU")

    def import_from_restapi(self, sim_name: str):
        """Import brand from Rest API"""
        config = cfg.user.setting["module_restapi"]
        url_host = config["url_host"]

        if sim_name == "LMU":
            url_port = config["url_port_lmu"]
            resource_name = "sessions/getAllVehicles"
        elif sim_name == "RF2":
            url_port = config["url_port_rf2"]
            resource_name = "race/car"
        else:
            return

        url = f"http://{url_host}:{url_port}/rest/{resource_name}"

        try:
            with urlopen(url, timeout=3) as raw_resource:
                if raw_resource.getcode() != 200:
                    raise ValueError
                dict_vehicles = json.loads(raw_resource.read().decode("utf-8"))
                self.parse_brand_data(dict_vehicles)

        except (TypeError, AttributeError, KeyError, ValueError,
                OSError, TimeoutError, socket.timeout):
            logger.error("Failed importing vehicle data from %s Rest API", sim_name)
            msg_text = (
                f"Unable to import vehicle data from {sim_name} Rest API.<br><br>"
                "Make sure game is running and try again."
            )
            QMessageBox.warning(self, "Error", msg_text)

    def import_from_file(self):
        """Import brand from file"""
        veh_file_data = QFileDialog.getOpenFileName(self, filter="*.json")
        if not veh_file_data[0]:
            return

        try:
            # Limit import file size under 5120kb
            if os.path.getsize(veh_file_data[0]) > 5120000:
                raise TypeError
            # Load JSON
            with open(veh_file_data[0], "r", encoding="utf-8") as jsonfile:
                dict_vehicles = json.load(jsonfile)
                self.parse_brand_data(dict_vehicles)

        except (AttributeError, IndexError, KeyError, TypeError,
                FileNotFoundError, ValueError, OSError):
            logger.error("Failed importing %s", veh_file_data[0])
            msg_text = "Cannot import selected file.<br><br>Invalid vehicle data file."
            QMessageBox.warning(self, "Error", msg_text)

    def parse_brand_data(self, vehicles: dict):
        """Parse brand data"""
        if vehicles[0].get("desc"):
            # Match LMU data format
            brands_db = {
                veh["desc"]: veh["manufacturer"]
                for veh in vehicles
            }
        elif vehicles[0].get("name"):
            # Match RF2 data format
            brands_db = {
                parse_vehicle_name(veh): veh["manufacturer"]
                for veh in vehicles
            }
        else:
            raise KeyError

        self.update_brands_temp()
        brands_db.update(self.brands_temp)
        self.brands_temp = brands_db
        self.refresh_table()
        QMessageBox.information(self, "Data Imported", "Vehicle brand data imported.")

    def open_replace_dialog(self):
        """Open replace dialog"""
        selector = {HEADER_BRANDS[1]: 1}
        _dialog = TableBatchReplace(self, selector, self.table_brands)
        _dialog.open()

    def add_brand(self):
        """Add new brand"""
        row_index = self.table_brands.rowCount()
        # Add all missing vehicle name from active session
        veh_total = api.read.vehicle.total_vehicles()
        for index in range(veh_total):
            veh_name = api.read.vehicle.vehicle_name(index)
            if not self.is_value_in_table(veh_name, self.table_brands):
                self.add_vehicle_entry(row_index, veh_name, "Unknown")
                row_index += 1
        # Add new name entry
        new_brand_name = self.new_name_increment("New Vehicle Name", self.table_brands)
        self.add_vehicle_entry(row_index, new_brand_name, "Unknown")
        self.table_brands.setCurrentCell(row_index, 0)

    def add_vehicle_entry(self, row_index: int, veh_name: str, brand_name: str):
        """Add new brand entry to table"""
        self.table_brands.insertRow(row_index)
        self.table_brands.setItem(row_index, 0, QTableWidgetItem(veh_name))
        self.table_brands.setItem(row_index, 1, QTableWidgetItem(brand_name))

    def sort_brand(self):
        """Sort brands in ascending order"""
        if self.table_brands.rowCount() > 1:
            self.table_brands.sortItems(1)
            self.set_modified()

    def delete_brand(self):
        """Delete brand entry"""
        selected_rows = set(data.row() for data in self.table_brands.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Error", "No data selected.")
            return

        if not self.confirm_operation(message="<b>Delete selected rows?</b>"):
            return

        for row_index in sorted(selected_rows, reverse=True):
            self.table_brands.removeRow(row_index)
        self.set_modified()

    def reset_setting(self):
        """Reset setting"""
        msg_text = (
            "Are you sure you want to reset brand preset to default?<br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        if self.confirm_operation(message=msg_text):
            self.brands_temp = copy_setting(cfg.default.brands)
            self.set_modified()
            self.refresh_table()

    def applying(self):
        """Save & apply"""
        self.save_setting()

    def saving(self):
        """Save & close"""
        self.save_setting()
        self.accept()  # close

    def update_brands_temp(self):
        """Update temporary changes to brands temp first"""
        self.brands_temp.clear()
        for index in range(self.table_brands.rowCount()):
            key_name = self.table_brands.item(index, 0).text()
            item_name = self.table_brands.item(index, 1).text()
            self.brands_temp[key_name] = item_name

    def save_setting(self):
        """Save setting"""
        self.update_brands_temp()
        cfg.user.brands = copy_setting(self.brands_temp)
        cfg.save(0, cfg_type=ConfigType.BRANDS)
        while cfg.is_saving:  # wait saving finish
            time.sleep(0.01)
        wctrl.reload()
        self.set_unmodified()


def parse_vehicle_name(vehicle):
    """Parse vehicle name"""
    # Example path string: "D:\\RF2\\Installed\\Vehicles\\SOMECAR\\1.50\\CAR_24.VEH"
    path_split = vehicle["vehFile"].split("\\")
    if len(path_split) < 2:
        # If VEH path does not contain version number, split name by space directly
        # Example name: "#24 Some Car 1.50"
        version_length = len(vehicle["name"].split(" ")[-1]) + 1
    else:
        # Get version number from last second split of path_split
        version_length = len(path_split[-2]) + 1
    return vehicle["name"][:-version_length]
