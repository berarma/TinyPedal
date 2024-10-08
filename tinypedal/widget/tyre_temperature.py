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
Tyre temperature Widget
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QGridLayout

from .. import calculation as calc
from .. import heatmap as hmp
from ..api_control import api
from ._base import Overlay

WIDGET_NAME = "tyre_temperature"


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Overlay.__init__(self, config, WIDGET_NAME)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        text_def = "n/a"
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        bar_gap = self.wcfg["bar_gap"]
        inner_gap = self.wcfg["inner_gap"]
        self.leading_zero = min(max(self.wcfg["leading_zero"], 1), 3)
        self.sign_text = "°" if self.wcfg["show_degree_sign"] else ""
        self.tyre_compound_string = self.cfg.units["tyre_compound_symbol"].ljust(20, "?")

        text_width = 3 + len(self.sign_text) + (self.cfg.units["temperature_unit"] == "Fahrenheit")
        bar_width_ttemp = font_m.width * text_width + bar_padx
        bar_width_tcmpd = font_m.width + bar_padx

        # Base style
        self.heatmap = hmp.load_heatmap(self.wcfg["heatmap_name"], "tyre_default")
        self.setStyleSheet(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )
        bar_style_tcmpd = self.set_qss(
            fg_color=self.wcfg["font_color_tyre_compound"],
            bg_color=self.wcfg["bkg_color_tyre_compound"]
        )
        bar_style_stemp = self.set_qss(
            fg_color=self.wcfg["font_color_surface"],
            bg_color=self.wcfg["bkg_color_surface"]
        )
        bar_style_itemp = self.set_qss(
            fg_color=self.wcfg["font_color_innerlayer"],
            bg_color=self.wcfg["bkg_color_innerlayer"]
        )

        # Create layout
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)  # remove border
        layout.setSpacing(bar_gap)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setLayout(layout)

        # Tyre temperature
        layout_stemp = QGridLayout()
        layout_stemp.setSpacing(inner_gap)
        self.bar_stemp = self.set_table(
            text=text_def,
            style=bar_style_stemp,
            width=bar_width_ttemp,
            layout=layout_stemp,
        )
        self.set_primary_orient(
            target=layout_stemp,
            column=self.wcfg["column_index_surface"],
        )

        if self.wcfg["show_tyre_compound"]:
            self.bar_tcmpd = self.set_qlabel(
                text="-",
                style=bar_style_tcmpd,
                width=bar_width_tcmpd,
                count=2,
            )
            self.set_layout_vert(layout_stemp, self.bar_tcmpd)

        # Tyre inner temperature
        if self.wcfg["show_innerlayer"]:
            layout_itemp = QGridLayout()
            layout_itemp.setSpacing(inner_gap)
            self.bar_itemp = self.set_table(
                text=text_def,
                style=bar_style_itemp,
                width=bar_width_ttemp,
                layout=layout_itemp,
            )
            self.set_primary_orient(
                target=layout_itemp,
                column=self.wcfg["column_index_innerlayer"],
            )

            if self.wcfg["show_tyre_compound"]:
                bar_blank = self.set_qlabel(
                    text="",
                    style=bar_style_tcmpd,
                    width=bar_width_tcmpd,
                    count=2,
                )
                self.set_layout_vert(layout_itemp, bar_blank)

        # Last data
        self.last_tcmpd = [None] * 2
        self.last_stemp = self.create_last_data()
        self.last_itemp = self.create_last_data()

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if self.state.active:

            # Tyre compound
            if self.wcfg["show_tyre_compound"]:
                tcmpd = api.read.tyre.compound()
                for cmpd_idx in range(2):
                    self.update_tcmpd(
                        self.bar_tcmpd[cmpd_idx],
                        tcmpd[cmpd_idx],
                        self.last_tcmpd[cmpd_idx]
                    )
                    self.last_tcmpd[cmpd_idx] = tcmpd[cmpd_idx]

            if self.wcfg["show_inner_center_outer"]:
                # Surface temperature
                stemp = api.read.tyre.surface_temperature_ico()
                for tyre_idx in range(4):  # 0 - fl, 1 - fr, 2 - rl, 3 - rr
                    for patch_idx in range(3):  # 0 1 2 / 7 8 9
                        self.update_stemp(
                            self.bar_stemp[tyre_idx][patch_idx],
                            stemp[tyre_idx][patch_idx],
                            self.last_stemp[tyre_idx][patch_idx]
                        )
                        self.last_stemp[tyre_idx][patch_idx] = stemp[tyre_idx][patch_idx]

                # Inner layer temperature
                if self.wcfg["show_innerlayer"]:
                    itemp = api.read.tyre.inner_temperature_ico()
                    for tyre_idx in range(4):
                        for patch_idx in range(3):
                            self.update_itemp(
                                self.bar_itemp[tyre_idx][patch_idx],
                                itemp[tyre_idx][patch_idx],
                                self.last_itemp[tyre_idx][patch_idx]
                            )
                            self.last_itemp[tyre_idx][patch_idx] = itemp[tyre_idx][patch_idx]
            else:
                # Surface temperature
                stemp = api.read.tyre.surface_temperature_avg()
                for tyre_idx in range(4):  # 0 - fl, 1 - fr, 2 - rl, 3 - rr
                    self.update_stemp(
                        self.bar_stemp[tyre_idx],
                        stemp[tyre_idx],
                        self.last_stemp[tyre_idx]
                    )
                    self.last_stemp[tyre_idx] = stemp[tyre_idx]

                # Inner layer temperature
                if self.wcfg["show_innerlayer"]:
                    itemp = api.read.tyre.inner_temperature_avg()
                    for tyre_idx in range(4):
                        self.update_itemp(
                            self.bar_itemp[tyre_idx],
                            itemp[tyre_idx],
                            self.last_itemp[tyre_idx]
                        )
                        self.last_itemp[tyre_idx] = itemp[tyre_idx]

    # GUI update methods
    def update_stemp(self, target_bar, curr, last):
        """Tyre surface temperature"""
        if round(curr) != round(last):
            color_temp = hmp.select_color(self.heatmap, curr)
            if self.wcfg["swap_style"]:
                color = f"color: {self.wcfg['font_color_surface']};background: {color_temp};"
            else:
                color = f"color: {color_temp};background: {self.wcfg['bkg_color_surface']};"

            target_bar.setText(self.format_temperature(curr))
            target_bar.setStyleSheet(color)

    def update_itemp(self, target_bar, curr, last):
        """Tyre inner temperature"""
        if round(curr) != round(last):
            color_temp = hmp.select_color(self.heatmap, curr)
            if self.wcfg["swap_style"]:
                color = f"color: {self.wcfg['font_color_innerlayer']};background: {color_temp};"
            else:
                color = f"color: {color_temp};background: {self.wcfg['bkg_color_innerlayer']};"

            target_bar.setText(self.format_temperature(curr))
            target_bar.setStyleSheet(color)

    def update_tcmpd(self, target_bar, curr, last):
        """Tyre compound"""
        if curr != last:
            target_bar.setText(self.tyre_compound_string[curr])

    # GUI generate methods
    def set_table(self, text, style, width, layout):
        """Set table"""
        if self.wcfg["show_inner_center_outer"]:
            bar_set = tuple(self.set_qlabel(
                text=text,
                style=style,
                width=width,
                count=3,
            ) for _ in range(4))  # 3 x 4 array
            self.set_layout_tri_quad(layout, bar_set)
        else:
            bar_set = self.set_qlabel(
                text=text,
                style=style,
                width=width,
                count=4,
            )
            self.set_layout_quad(layout, bar_set)
        return bar_set

    @staticmethod
    def set_layout_quad(layout, bar_set, row_start=1, column_left=0, column_right=9):
        """Set layout - quad

        Default row index start from 1; reserve row index 0 for caption.
        """
        for idx in range(4):
            layout.addWidget(bar_set[idx], row_start + (idx > 1),
                column_left + (idx % 2) * column_right)

    @staticmethod
    def set_layout_tri_quad(layout, bar_set, row_start=1, column_left=0, column_right=7):
        """Set layout - tri-quad - (0,1,2) * 4

        Default row index start from 1; reserve row index 0 for caption.
        Default column left index start from 0, and right start from 7; reserve 3 columns in middle.
        Example: (0,1,2) to (7,8,9)
        """
        for outer_index in range(4):
            row_index = row_start + int(outer_index > 1)
            for index in range(3):
                if outer_index % 2:  # even(right) columns
                    layout.addWidget(bar_set[outer_index][index],
                        row_index, index + column_left + column_right)
                else:  # odd(left) columns
                    layout.addWidget(bar_set[outer_index][index],
                        row_index, index + column_left)

    @staticmethod
    def set_layout_vert(layout, bar_set, row_count=2):
        """Set layout - vertical

        Start from row index 1; reserve row index 0 for caption.
        """
        for index in range(row_count):
            layout.addWidget(bar_set[index], index + 1, 4)

    # Additional methods
    def format_temperature(self, value):
        """Format temperature"""
        if self.cfg.units["temperature_unit"] == "Fahrenheit":
            return f"{calc.celsius2fahrenheit(value):0{self.leading_zero}.0f}{self.sign_text}"
        return f"{value:0{self.leading_zero}.0f}{self.sign_text}"

    def create_last_data(self):
        """Create last data list"""
        if self.wcfg["show_inner_center_outer"]:
            return [[-273.15] * 3 for _ in range(4)]
        return [-273.15] * 4
