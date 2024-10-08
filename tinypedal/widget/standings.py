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
Standings Widget
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QGridLayout

from .. import calculation as calc
from .. import formatter as fmt
from ..api_control import api
from ..module_info import minfo
from ._base import Overlay

WIDGET_NAME = "standings"


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Overlay.__init__(self, config, WIDGET_NAME)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        bar_gap = self.wcfg["bar_gap"]
        self.drv_width = max(int(self.wcfg["driver_name_width"]), 1)
        self.veh_width = max(int(self.wcfg["vehicle_name_width"]), 1)
        self.brd_width = max(int(self.wcfg["brand_logo_width"]), 1)
        self.brd_height = max(self.wcfg["font_size"], 1)
        self.cls_width = max(int(self.wcfg["class_width"]), 1)
        self.gap_width = max(int(self.wcfg["time_gap_width"]), 1)
        self.int_width = max(int(self.wcfg["time_interval_width"]), 1)
        self.gap_decimals = max(int(self.wcfg["time_gap_decimal_places"]), 0)
        self.int_decimals = max(int(self.wcfg["time_interval_decimal_places"]), 0)
        self.tyre_compound_string = self.cfg.units["tyre_compound_symbol"].ljust(20, "?")
        self.show_class_interval = (self.wcfg["enable_multi_class_split_mode"]
            and self.wcfg["show_time_interval_from_same_class"])

        # Base style
        self.setStyleSheet(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )
        self.bar_split_style = f"margin-top: {self.wcfg['split_gap']}px;max-height: 0;"

        # Max display players
        if self.wcfg["enable_multi_class_split_mode"]:
            self.veh_range = min(max(int(self.wcfg["max_vehicles_split_mode"]), 5), 126)
        else:
            self.veh_range = min(max(int(self.wcfg["max_vehicles_combined_mode"]), 5), 126)

        # Empty data set (last value sets toggle state, 0 - show, 1 - draw gap, 2 - hide)
        self.empty_vehicles_data = (
            (0,2),  # in_pit
            ("",0,2),  # position
            ("",0,2),  # driver name
            ("",0,2),  # vehicle name
            ("",0,2),  # pos_class
            ("",2),  # veh_class
            ("",0,2),  # tire_idx
            ("",0,2),  # laptime
            ("",0,2),  # best laptime
            ("",0,2),  # time_gap
            (-1,0,0,2),  # pit_count
            ("",0,2),  # time_int
        )
        self.pixmap_brandlogo = {"blank": QPixmap()}
        self.data_bar = {}
        self.curr_data = [None] * self.veh_range
        self.last_data = [tuple(None for _ in self.empty_vehicles_data)] * self.veh_range

        # Create layout
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)  # remove border
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(bar_gap)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setLayout(layout)

        # Driver position
        if self.wcfg["show_position"]:
            self.bar_style_pos = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_position"],
                    bg_color=self.wcfg["bkg_color_position"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_position"],
                    bg_color=self.wcfg["bkg_color_player_position"])
            )
            self.set_table(
                name="pos",
                style=self.bar_style_pos[0],
                width=2 * font_m.width + bar_padx,
                column=self.wcfg["column_index_position"],
            )
        # Driver name
        if self.wcfg["show_driver_name"]:
            self.bar_style_drv = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_driver_name"],
                    bg_color=self.wcfg["bkg_color_driver_name"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_driver_name"],
                    bg_color=self.wcfg["bkg_color_player_driver_name"])
            )
            self.set_table(
                name="drv",
                style=self.bar_style_drv[0],
                width=self.drv_width * font_m.width + bar_padx,
                column=self.wcfg["column_index_driver"],
            )
        # Vehicle name
        if self.wcfg["show_vehicle_name"]:
            self.bar_style_veh = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_vehicle_name"],
                    bg_color=self.wcfg["bkg_color_vehicle_name"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_vehicle_name"],
                    bg_color=self.wcfg["bkg_color_player_vehicle_name"])
            )
            self.set_table(
                name="veh",
                style=self.bar_style_veh[0],
                width=self.veh_width * font_m.width + bar_padx,
                column=self.wcfg["column_index_vehicle"],
            )
        # Brand logo
        if self.wcfg["show_brand_logo"]:
            self.bar_style_brd = (
                self.set_qss(
                    bg_color=self.wcfg["bkg_color_brand_logo"]),
                self.set_qss(
                    bg_color=self.wcfg["bkg_color_player_brand_logo"])
            )
            self.set_table(
                name="brd",
                style=self.bar_style_brd[0],
                width=self.brd_width,
                column=self.wcfg["column_index_brand_logo"],
            )
        # Time gap
        if self.wcfg["show_time_gap"]:
            self.bar_style_gap = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_time_gap"],
                    bg_color=self.wcfg["bkg_color_time_gap"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_time_gap"],
                    bg_color=self.wcfg["bkg_color_player_time_gap"])
            )
            self.set_table(
                name="gap",
                style=self.bar_style_gap[0],
                width=self.gap_width * font_m.width + bar_padx,
                column=self.wcfg["column_index_timegap"],
            )
        # Time interval
        if self.wcfg["show_time_interval"]:
            self.bar_style_int = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_time_interval"],
                    bg_color=self.wcfg["bkg_color_time_interval"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_time_interval"],
                    bg_color=self.wcfg["bkg_color_player_time_interval"])
            )
            self.set_table(
                name="int",
                style=self.bar_style_int[0],
                width=self.int_width * font_m.width + bar_padx,
                column=self.wcfg["column_index_timeinterval"],
            )
        # Vehicle laptime
        if self.wcfg["show_laptime"]:
            self.bar_style_lpt = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_laptime"],
                    bg_color=self.wcfg["bkg_color_laptime"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_laptime"],
                    bg_color=self.wcfg["bkg_color_player_laptime"])
            )
            self.set_table(
                name="lpt",
                style=self.bar_style_lpt[0],
                width=8 * font_m.width + bar_padx,
                column=self.wcfg["column_index_laptime"],
            )
        # Vehicle best laptime
        if self.wcfg["show_best_laptime"]:
            self.bar_style_blp = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_best_laptime"],
                    bg_color=self.wcfg["bkg_color_best_laptime"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_best_laptime"],
                    bg_color=self.wcfg["bkg_color_player_best_laptime"])
            )
            self.set_table(
                name="blp",
                style=self.bar_style_blp[0],
                width=8 * font_m.width + bar_padx,
                column=self.wcfg["column_index_best_laptime"],
            )
        # Position in class
        if self.wcfg["show_position_in_class"]:
            self.bar_style_pic = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_position_in_class"],
                    bg_color=self.wcfg["bkg_color_position_in_class"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_position_in_class"],
                    bg_color=self.wcfg["bkg_color_player_position_in_class"])
            )
            self.set_table(
                name="pic",
                style=self.bar_style_pic[0],
                width=2 * font_m.width + bar_padx,
                column=self.wcfg["column_index_position_in_class"],
            )
        # Vehicle class
        if self.wcfg["show_class"]:
            bar_style_cls = self.set_qss(
                fg_color=self.wcfg["font_color_class"],
                bg_color=self.wcfg["bkg_color_class"]
            )
            self.set_table(
                name="cls",
                style=bar_style_cls,
                width=self.cls_width * font_m.width + bar_padx,
                column=self.wcfg["column_index_class"],
            )
        # Vehicle in pit
        if self.wcfg["show_pit_status"]:
            self.pit_status_text = (
                self.wcfg["pit_status_text"],
                self.wcfg["garage_status_text"]
            )
            self.bar_style_pit = (
                self.set_qss(
                    fg_color="#00000000",
                    bg_color="#00000000"),
                self.set_qss(
                    fg_color=self.wcfg["font_color_pit"],
                    bg_color=self.wcfg["bkg_color_pit"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_garage"],
                    bg_color=self.wcfg["bkg_color_garage"])
            )
            self.set_table(
                name="pit",
                style=self.bar_style_pit[1],
                width=max(map(len, self.pit_status_text)) * font_m.width + bar_padx,
                column=self.wcfg["column_index_pitstatus"],
            )
        # Tyre compound index
        if self.wcfg["show_tyre_compound"]:
            self.bar_style_tcp = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_tyre_compound"],
                    bg_color=self.wcfg["bkg_color_tyre_compound"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_tyre_compound"],
                    bg_color=self.wcfg["bkg_color_player_tyre_compound"])
            )
            self.set_table(
                name="tcp",
                style=self.bar_style_tcp[0],
                width=2 * font_m.width + bar_padx,
                column=self.wcfg["column_index_tyre_compound"],
            )
        # Pitstop count
        if self.wcfg["show_pitstop_count"]:
            self.bar_style_psc = (
                self.set_qss(
                    fg_color=self.wcfg["font_color_pitstop_count"],
                    bg_color=self.wcfg["bkg_color_pitstop_count"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_player_pitstop_count"],
                    bg_color=self.wcfg["bkg_color_player_pitstop_count"]),
                self.set_qss(
                    fg_color=self.wcfg["font_color_pit_request"],
                    bg_color=self.wcfg["bkg_color_pit_request"])
            )
            self.set_table(
                name="psc",
                style=self.bar_style_psc[0],
                width=2 * font_m.width + bar_padx,
                column=self.wcfg["column_index_pitstop_count"],
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if self.state.active:

            standings_list = minfo.relative.standings
            total_idx = len(standings_list) - 1  # skip final -1 index
            total_veh_idx = api.read.vehicle.total_vehicles()
            in_race = api.read.session.in_race()

            # Standings update
            for idx in range(self.veh_range):

                # Get vehicle data
                if idx < total_idx and -1 <= standings_list[idx] < total_veh_idx:
                    self.curr_data[idx] = self.get_data(
                        standings_list[idx], minfo.vehicles.dataSet, in_race,
                        standings_list[idx] == -1)  # set state
                elif self.last_data[idx] == self.empty_vehicles_data:
                    continue  # skip if already empty
                else:
                    self.curr_data[idx] = self.empty_vehicles_data
                # Driver position
                if self.wcfg["show_position"]:
                    self.update_pos(self.data_bar[f"{idx}_pos"],
                                    self.curr_data[idx][1],
                                    self.last_data[idx][1],
                                    )
                # Driver name
                if self.wcfg["show_driver_name"]:
                    self.update_drv(self.data_bar[f"{idx}_drv"],
                                    self.curr_data[idx][2],
                                    self.last_data[idx][2],
                                    )
                # Vehicle name
                if self.wcfg["show_vehicle_name"]:
                    self.update_veh(self.data_bar[f"{idx}_veh"],
                                    self.curr_data[idx][3],
                                    self.last_data[idx][3],
                                    )
                # Brand logo
                if self.wcfg["show_brand_logo"]:
                    self.update_brd(self.data_bar[f"{idx}_brd"],
                                    self.curr_data[idx][3],
                                    self.last_data[idx][3],
                                    )
                # Time gap
                if self.wcfg["show_time_gap"]:
                    self.update_gap(self.data_bar[f"{idx}_gap"],
                                    self.curr_data[idx][9],
                                    self.last_data[idx][9],
                                    )
                # Time interval
                if self.wcfg["show_time_interval"]:
                    self.update_int(self.data_bar[f"{idx}_int"],
                                    self.curr_data[idx][11],
                                    self.last_data[idx][11],
                                    )
                # Vehicle laptime
                if self.wcfg["show_laptime"]:
                    self.update_lpt(self.data_bar[f"{idx}_lpt"],
                                    self.curr_data[idx][7],
                                    self.last_data[idx][7],
                                    )
                # Vehicle best laptime
                if self.wcfg["show_best_laptime"]:
                    self.update_blp(self.data_bar[f"{idx}_blp"],
                                    self.curr_data[idx][8],
                                    self.last_data[idx][8],
                                    )
                # Position in class
                if self.wcfg["show_position_in_class"]:
                    self.update_pic(self.data_bar[f"{idx}_pic"],
                                    self.curr_data[idx][4],
                                    self.last_data[idx][4],
                                    )
                # Vehicle class
                if self.wcfg["show_class"]:
                    self.update_cls(self.data_bar[f"{idx}_cls"],
                                    self.curr_data[idx][5],
                                    self.last_data[idx][5]
                                    )
                # Vehicle in pit
                if self.wcfg["show_pit_status"]:
                    self.update_pit(self.data_bar[f"{idx}_pit"],
                                    self.curr_data[idx][0],
                                    self.last_data[idx][0]
                                    )
                # Tyre compound index
                if self.wcfg["show_tyre_compound"]:
                    self.update_tcp(self.data_bar[f"{idx}_tcp"],
                                    self.curr_data[idx][6],
                                    self.last_data[idx][6],
                                    )
                # Pitstop count
                if self.wcfg["show_pitstop_count"]:
                    self.update_psc(self.data_bar[f"{idx}_psc"],
                                    self.curr_data[idx][10],
                                    self.last_data[idx][10],
                                    )
                # Store last data reading
                self.last_data[idx] = self.curr_data[idx]

    # GUI update methods
    def update_pos(self, target_bar, curr, last):
        """Driver position"""
        if curr != last:
            if curr[0] != "":
                text = f"{curr[0]:02d}"
            else:
                text = ""

            target_bar.setText(text)
            target_bar.setStyleSheet(self.bar_style_pos[curr[1]])
            self.toggle_visibility(curr[2], target_bar)

    def update_drv(self, target_bar, curr, last):
        """Driver name"""
        if curr != last:
            if self.wcfg["driver_name_shorten"]:
                text = fmt.shorten_driver_name(curr[0])
            else:
                text = curr[0]

            if self.wcfg["driver_name_uppercase"]:
                text = text.upper()

            if self.wcfg["driver_name_align_center"]:
                text = text[:self.drv_width]
            else:
                text = text[:self.drv_width].ljust(self.drv_width)

            target_bar.setText(text)
            target_bar.setStyleSheet(self.bar_style_drv[curr[1]])
            self.toggle_visibility(curr[2], target_bar)

    def update_veh(self, target_bar, curr, last):
        """Vehicle name"""
        if curr != last:
            if self.wcfg["show_vehicle_brand_as_name"]:
                vname = self.cfg.user.brands.get(curr[0], curr[0])
            else:
                vname = curr[0]

            if self.wcfg["vehicle_name_uppercase"]:
                text = vname.upper()
            else:
                text = vname

            if self.wcfg["vehicle_name_align_center"]:
                text = text[:self.veh_width]
            else:
                text = text[:self.veh_width].ljust(self.veh_width)

            target_bar.setText(text)
            target_bar.setStyleSheet(self.bar_style_veh[curr[1]])
            self.toggle_visibility(curr[2], target_bar)

    def update_brd(self, target_bar, curr, last):
        """Brand logo"""
        if curr != last:
            if curr[0]:
                brand_name = self.cfg.user.brands.get(curr[0], curr[0])
            else:
                brand_name = "blank"
            # Draw brand logo
            target_bar.setPixmap(self.load_brand_logo(brand_name))
            # Draw background
            target_bar.setStyleSheet(self.bar_style_brd[curr[1]])
            self.toggle_visibility(curr[2], target_bar)

    def update_gap(self, target_bar, curr, last):
        """Time gap"""
        if curr != last:
            target_bar.setText(curr[0][:self.gap_width].strip("."))
            target_bar.setStyleSheet(self.bar_style_gap[curr[1]])
            self.toggle_visibility(curr[2], target_bar)

    def update_int(self, target_bar, curr, last):
        """Time interval"""
        if curr != last:
            if curr[0] != "":
                text = self.int_to_next(*curr[0])[:self.int_width].strip(".")
            else:
                text = ""

            target_bar.setText(text)
            target_bar.setStyleSheet(self.bar_style_int[curr[1]])
            self.toggle_visibility(curr[2], target_bar)

    def update_lpt(self, target_bar, curr, last):
        """Vehicle laptime"""
        if curr != last:
            if curr[0] != "":
                text = self.set_laptime(*curr[0])
            else:
                text = ""

            target_bar.setText(text)
            target_bar.setStyleSheet(self.bar_style_lpt[curr[1]])
            self.toggle_visibility(curr[2], target_bar)

    def update_blp(self, target_bar, curr, last):
        """Vehicle best laptime"""
        if curr != last:
            if curr[0] != "":
                text = self.set_best_laptime(curr[0])
            else:
                text = ""

            target_bar.setText(text)
            target_bar.setStyleSheet(self.bar_style_blp[curr[1]])
            self.toggle_visibility(curr[2], target_bar)

    def update_pic(self, target_bar, curr, last):
        """Position in class"""
        if curr != last:
            if curr[0] != "":
                text = f"{curr[0]:02d}"
            else:
                text = ""

            target_bar.setText(text)
            target_bar.setStyleSheet(self.bar_style_pic[curr[1]])
            self.toggle_visibility(curr[2], target_bar)

    def update_cls(self, target_bar, curr, last):
        """Vehicle class"""
        if curr != last:
            text, bg_color = self.set_class_style(curr[0])
            target_bar.setText(text[:self.cls_width])
            target_bar.setStyleSheet(
                f"color: {self.wcfg['font_color_class']};background: {bg_color};")
            self.toggle_visibility(curr[1], target_bar)

    def update_pit(self, target_bar, curr, last):
        """Vehicle in pit"""
        if curr != last:
            if curr[0]:
                text = self.pit_status_text[curr[0] - 1]
            else:
                text = ""

            target_bar.setText(text)
            target_bar.setStyleSheet(self.bar_style_pit[curr[0]])
            self.toggle_visibility(curr[1], target_bar)

    def update_tcp(self, target_bar, curr, last):
        """Tyre compound index"""
        if curr != last:
            text = self.set_tyre_cmp(curr[0])
            target_bar.setText(text)
            target_bar.setStyleSheet(self.bar_style_tcp[curr[1]])
            self.toggle_visibility(curr[2], target_bar)

    def update_psc(self, target_bar, curr, last):
        """Pitstop count"""
        if curr != last:
            if self.wcfg["show_pit_request"] and curr[1] == 1:
                color = self.bar_style_psc[2]
            elif curr[2]:  # highlighted player
                color = self.bar_style_psc[1]
            else:
                color = self.bar_style_psc[0]

            text = self.set_pitcount(curr[0])
            target_bar.setText(text)
            target_bar.setStyleSheet(color)
            self.toggle_visibility(curr[3], target_bar)

    # GUI generate methods
    def set_table(self, name: str, style: str, width: int, column: int):
        """Set table"""
        for idx in range(self.veh_range):
            bar_name = f"{idx}_{name}"
            self.data_bar[bar_name] = self.set_qlabel(
                text="",
                style=style,
                width=width,
            )
            self.layout().addWidget(self.data_bar[bar_name], idx, column)
            if idx > 0:  # show only first row initially
                self.data_bar[bar_name].hide()

    # Additional methods
    def toggle_visibility(self, state, row_bar):
        """Hide row bar if empty data"""
        if state == 0:
            if row_bar.isHidden():
                row_bar.show()
        elif state == 1:
            if self.wcfg["split_gap"] > 0:  # draw gap
                row_bar.setStyleSheet(self.bar_split_style)
                if row_bar.isHidden():
                    row_bar.show()
            else:  # hide gap
                if not row_bar.isHidden():
                    row_bar.hide()
        else:
            if not row_bar.isHidden():
                row_bar.hide()

    def load_brand_logo(self, brand_name):
        """Load brand logo"""
        # Load cached logo
        if brand_name in self.pixmap_brandlogo:
            return self.pixmap_brandlogo[brand_name]
        # Add available logo to cached
        if brand_name in self.cfg.user.brands_logo:
            logo_temp = QPixmap(f"{self.cfg.path.brand_logo}{brand_name}.png")
            if calc.image_size_adaption(
                logo_temp.width(), logo_temp.height(), self.brd_width, self.brd_height):
                logo_image = logo_temp.scaledToWidth(  # adapt to width
                    self.brd_width, mode=Qt.SmoothTransformation)
            else:
                logo_image = logo_temp.scaledToHeight(  # adapt to height
                    self.brd_height, mode=Qt.SmoothTransformation)
            self.pixmap_brandlogo[brand_name] = logo_image
            return self.pixmap_brandlogo[brand_name]
        # Load blank logo if unavailable
        return self.pixmap_brandlogo["blank"]

    def set_tyre_cmp(self, tc_indices):
        """Substitute tyre compound index with custom chars"""
        if tc_indices:
            return "".join((self.tyre_compound_string[idx] for idx in tc_indices))
        return ""

    @staticmethod
    def set_pitcount(pits):
        """Set pitstop count test"""
        if pits == 0:
            return "-"
        if pits > 0:
            return f"{pits}"
        return ""

    def set_class_style(self, vehclass_name):
        """Compare vehicle class name with user defined dictionary"""
        if vehclass_name in self.cfg.user.classes:
            return tuple(*self.cfg.user.classes[vehclass_name].items())  # sub_name, sub_color
        if vehclass_name and self.wcfg["show_random_color_for_unknown_class"]:
            return vehclass_name, fmt.random_color_class(vehclass_name)
        return vehclass_name, self.wcfg["bkg_color_class"]

    @staticmethod
    def set_laptime(inpit, laptime_last, pit_time):
        """Set lap time"""
        if inpit:
            return f"PIT{pit_time: >5.1f}"[:8] if pit_time > 0 else "-:--.---"
        if laptime_last <= 0:
            return f"OUT{pit_time: >5.1f}"[:8] if pit_time > 0 else "-:--.---"
        return calc.sec2laptime_full(laptime_last)[:8].rjust(8)

    @staticmethod
    def set_best_laptime(laptime_best):
        """Set best lap time"""
        if laptime_best <= 0:
            return "-:--.---"
        return calc.sec2laptime_full(laptime_best)[:8].rjust(8)

    def gap_to_session_bestlap(self, bestlap, sbestlap, cbestlap):
        """Gap to session best laptime"""
        if self.wcfg["show_time_gap_from_class_best"]:
            time = bestlap - cbestlap  # class best
        else:
            time = bestlap - sbestlap  # session best
        if time == 0 and bestlap > 0:
            return self.wcfg["time_gap_leader_text"]
        if time < 0 or bestlap < 1:  # no time set
            return "0.0"
        return f"{time:.{self.gap_decimals}f}"

    def gap_to_leader_race(self, gap_behind, position):
        """Gap to race leader"""
        if position == 1:
            return self.wcfg["time_gap_leader_text"]
        if isinstance(gap_behind, int):
            return f"{gap_behind:.0f}L"
        return f"{gap_behind:.{self.gap_decimals}f}"

    def int_to_next(self, position, gap_behind):
        """Interval to next"""
        if position == 1:
            return self.wcfg["time_interval_leader_text"]
        if isinstance(gap_behind, int):
            return f"{gap_behind:.0f}L"
        return f"{gap_behind:.{self.int_decimals}f}"

    def get_data(self, index, veh_info, in_race, state):
        """Standings data"""
        # Highlighted player
        hi_player = self.wcfg["show_player_highlighted"] and veh_info[index].isPlayer

        # 0 Vehicle in pit (in_pit: bool, state)
        in_pit = (veh_info[index].inPit, state)

        # 1 Driver position (position: int, hi_player, state)
        position = (veh_info[index].positionOverall, hi_player, state)

        # 2 Driver name (drv_name: str, hi_player, state)
        drv_name = (veh_info[index].driverName, hi_player, state)

        # 3 Vehicle name (veh_name: str, hi_player, state)
        veh_name = (veh_info[index].vehicleName, hi_player, state)

        # 4 Position in class (pos_class: int, hi_player, state)
        pos_class = (veh_info[index].positionInClass, hi_player, state)

        # 5 Vehicle class (veh_class: str, state)
        veh_class = (veh_info[index].vehicleClass, state)

        # 6 Tyre compound index (tire_idx: tuple, hi_player, state)
        tire_idx = (veh_info[index].tireCompound, hi_player, state)

        # 7 Lap time (laptime: tuple, hi_player, state)
        if self.wcfg["show_best_laptime"] or in_race:
            laptime = ((
                    veh_info[index].inPit,
                    veh_info[index].lastLapTime,
                    veh_info[index].pitTimer[2]
                ),
                hi_player, state)
        else:
            laptime = ((
                    0,
                    veh_info[index].bestLapTime,
                    0
                ),
                hi_player, state)

        # 8 Best lap time (best_laptime: float, hi_player, state)
        best_laptime = (veh_info[index].bestLapTime, hi_player, state)

        # 9 Time gap (time_gap: str, hi_player, state)
        if in_race:
            time_gap = (
                self.gap_to_leader_race(
                    veh_info[index].gapBehindLeader,
                    veh_info[index].positionOverall
                ),
                hi_player, state)
        else:
            time_gap = (
                self.gap_to_session_bestlap(
                    veh_info[index].bestLapTime,
                    veh_info[index].sessionBestLapTime,
                    veh_info[index].classBestLapTime,
                ),
                hi_player, state)

        # 10 Pitstop count (pit_count: int, pit_state: int, hi_player, state)
        pit_count = (
            veh_info[index].numPitStops,
            veh_info[index].pitState,
            hi_player, state)

        # 11 Time interval (time_int: tuple, hi_player, state)
        if self.show_class_interval:
            time_int = ((
                    veh_info[index].positionInClass,
                    veh_info[index].gapBehindNextInClass,
                ),
                hi_player, state)
        else:
            time_int = ((
                    veh_info[index].positionOverall,
                    veh_info[index].gapBehindNext,
                ),
                hi_player, state)

        return (in_pit, position, drv_name, veh_name, pos_class, veh_class,
                tire_idx, laptime, best_laptime, time_gap, pit_count, time_int)
