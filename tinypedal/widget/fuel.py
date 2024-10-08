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
Fuel Widget
"""

from PySide2.QtCore import Qt, QRectF
from PySide2.QtGui import QPainter, QPixmap
from PySide2.QtWidgets import QGridLayout

from .. import calculation as calc
from ..module_info import minfo
from ._base import Overlay

WIDGET_NAME = "fuel"


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Overlay.__init__(self, config, WIDGET_NAME)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        text_def = "-.--"
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        bar_gap = self.wcfg["bar_gap"]
        self.bar_width = max(self.wcfg["bar_width"], 3)
        style_width = font_m.width * self.bar_width + bar_padx

        self.decimals = tuple(
            map(self.decimal_range, (
            self.wcfg["decimal_places_end"],  # 0
            self.wcfg["decimal_places_remain"],  # 1
            self.wcfg["decimal_places_refuel"],  # 2
            self.wcfg["decimal_places_used"],  # 3
            self.wcfg["decimal_places_delta"],  # 4
            self.wcfg["decimal_places_early"],  # 5
            self.wcfg["decimal_places_laps"],  # 6
            self.wcfg["decimal_places_minutes"],  # 7
            self.wcfg["decimal_places_save"],  # 8
            self.wcfg["decimal_places_pits"],  # 9
        )))

        # Base style
        self.setStyleSheet(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Create layout
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)  # remove border
        layout.setSpacing(bar_gap)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setLayout(layout)

        layout_upper = QGridLayout()
        layout_lower = QGridLayout()
        layout_upper.setSpacing(0)
        layout_lower.setSpacing(0)
        layout.addLayout(layout_upper, self.wcfg["column_index_upper"], 0)
        layout.addLayout(layout_lower, self.wcfg["column_index_lower"], 0)

        # Caption
        if self.wcfg["show_caption"]:
            bar_style_desc = self.set_qss(
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
                font_size=int(self.wcfg['font_size'] * 0.8)
            )
            caption_upper = (
                self.wcfg["caption_text_end"],
                self.wcfg["caption_text_remain"],
                self.wcfg["caption_text_refuel"],
                self.wcfg["caption_text_used"],
                self.wcfg["caption_text_delta"],
            )
            caption_lower = (
                self.wcfg["caption_text_early"],
                self.wcfg["caption_text_laps"],
                self.wcfg["caption_text_minutes"],
                self.wcfg["caption_text_save"],
                self.wcfg["caption_text_pits"],
            )

            row_idx_upper = 2 * self.wcfg["swap_upper_caption"]
            for index, text_caption in enumerate(caption_upper):
                cap_temp = self.set_qlabel(
                    text=text_caption,
                    style=bar_style_desc,
                )
                layout_upper.addWidget(cap_temp, row_idx_upper, index)

            row_idx_lower = 2 - 2 * self.wcfg["swap_lower_caption"]
            for index, text_caption in enumerate(caption_lower):
                cap_temp = self.set_qlabel(
                    text=text_caption,
                    style=bar_style_desc,
                )
                layout_lower.addWidget(cap_temp, row_idx_lower, index)

        # Estimated end fuel
        bar_style_fuel_end = self.set_qss(
            fg_color=self.wcfg["font_color_end"],
            bg_color=self.wcfg["bkg_color_end"]
        )
        self.bar_fuel_end = self.set_qlabel(
            text=text_def,
            style=bar_style_fuel_end,
            fixed_width=style_width,
        )

        # Remaining fuel
        self.bar_style_fuel_curr = (
            self.set_qss(
                fg_color=self.wcfg["font_color_remain"],
                bg_color=self.wcfg["bkg_color_remain"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_remain"],
                bg_color=self.wcfg["warning_color_low_fuel"])
        )
        self.bar_fuel_curr = self.set_qlabel(
            text=text_def,
            style=self.bar_style_fuel_curr[0],
            fixed_width=style_width,
        )

        # Total needed fuel
        self.bar_style_fuel_need = (
            self.set_qss(
                fg_color=self.wcfg["font_color_refuel"],
                bg_color=self.wcfg["bkg_color_refuel"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_refuel"],
                bg_color=self.wcfg["warning_color_low_fuel"])
        )
        self.bar_fuel_need = self.set_qlabel(
            text=text_def,
            style=self.bar_style_fuel_need[0],
            fixed_width=style_width,
        )

        # Estimated fuel consumption
        bar_style_fuel_used = self.set_qss(
            fg_color=self.wcfg["font_color_used"],
            bg_color=self.wcfg["bkg_color_used"]
        )
        self.bar_fuel_used = self.set_qlabel(
            text=text_def,
            style=bar_style_fuel_used,
            fixed_width=style_width,
        )

        # Delta fuel consumption
        bar_style_fuel_delta = self.set_qss(
            fg_color=self.wcfg["font_color_delta"],
            bg_color=self.wcfg["bkg_color_delta"]
        )
        self.bar_fuel_delta = self.set_qlabel(
            text=text_def,
            style=bar_style_fuel_delta,
            fixed_width=style_width,
        )

        # Estimate pit stop counts when pitting at end of current lap
        bar_style_fuel_early = self.set_qss(
            fg_color=self.wcfg["font_color_early"],
            bg_color=self.wcfg["bkg_color_early"]
        )
        self.bar_fuel_early = self.set_qlabel(
            text=text_def,
            style=bar_style_fuel_early,
            fixed_width=style_width,
        )

        # Estimated laps current fuel can last
        bar_style_fuel_laps = self.set_qss(
            fg_color=self.wcfg["font_color_laps"],
            bg_color=self.wcfg["bkg_color_laps"]
        )
        self.bar_fuel_laps = self.set_qlabel(
            text=text_def,
            style=bar_style_fuel_laps,
            fixed_width=style_width,
        )

        # Estimated minutes current fuel can last
        bar_style_fuel_mins = self.set_qss(
            fg_color=self.wcfg["font_color_minutes"],
            bg_color=self.wcfg["bkg_color_minutes"]
        )
        self.bar_fuel_mins = self.set_qlabel(
            text=text_def,
            style=bar_style_fuel_mins,
            fixed_width=style_width,
        )

        # Estimated one less pit fuel consumption
        bar_style_fuel_save = self.set_qss(
            fg_color=self.wcfg["font_color_save"],
            bg_color=self.wcfg["bkg_color_save"]
        )
        self.bar_fuel_save = self.set_qlabel(
            text=text_def,
            style=bar_style_fuel_save,
            fixed_width=style_width,
        )

        # Estimate pit stop counts when pitting at end of current stint
        bar_style_fuel_pits = self.set_qss(
            fg_color=self.wcfg["font_color_pits"],
            bg_color=self.wcfg["bkg_color_pits"]
        )
        self.bar_fuel_pits = self.set_qlabel(
            text=text_def,
            style=bar_style_fuel_pits,
            fixed_width=style_width,
        )

        # Fuel level bar
        if self.wcfg["show_fuel_level_bar"]:
            self.fuel_level_width = (font_m.width * self.bar_width + bar_padx) * 5
            fuel_level_height = max(self.wcfg["fuel_level_bar_height"], 1)
            self.rect_fuel_left = QRectF(0, 0, 0, fuel_level_height)
            self.rect_fuel_start = QRectF(
                0, 0,
                max(self.wcfg["starting_fuel_level_mark_width"], 1),
                fuel_level_height
            )
            self.rect_fuel_refuel = QRectF(
                0, 0,
                max(self.wcfg["refueling_level_mark_width"], 1),
                fuel_level_height
            )
            self.fuel_level = self.set_qlabel(
                fixed_width=self.fuel_level_width,
                fixed_height=fuel_level_height,
            )
            self.pixmap_fuel_level = QPixmap(self.fuel_level_width, fuel_level_height)
            self.draw_fuel_level(0, 0, 0)
            layout.addWidget(self.fuel_level, self.wcfg["column_index_middle"], 0)

        # Set layout
        layout_upper.addWidget(self.bar_fuel_end, 1, 0)
        layout_upper.addWidget(self.bar_fuel_curr, 1, 1)
        layout_upper.addWidget(self.bar_fuel_need, 1, 2)
        layout_upper.addWidget(self.bar_fuel_used, 1, 3)
        layout_upper.addWidget(self.bar_fuel_delta, 1, 4)
        layout_lower.addWidget(self.bar_fuel_early, 1, 0)
        layout_lower.addWidget(self.bar_fuel_laps, 1, 1)
        layout_lower.addWidget(self.bar_fuel_mins, 1, 2)
        layout_lower.addWidget(self.bar_fuel_save, 1, 3)
        layout_lower.addWidget(self.bar_fuel_pits, 1, 4)

        # Last data
        self.last_amount_end = None
        self.last_amount_curr = None
        self.last_amount_need = None
        self.last_used_last = None
        self.last_delta_fuel = None
        self.last_est_pits_early = None
        self.last_est_runlaps = None
        self.last_est_runmins = None
        self.last_fuel_save = None
        self.last_est_pits_end = None
        self.last_level_state = None

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if self.state.active:

            # Estimated end fuel
            amount_end = f"{self.fuel_units(minfo.fuel.amountEndStint):.{self.decimals[0]}f}"
            self.update_fuel(
                self.bar_fuel_end, amount_end, self.last_amount_end)
            self.last_amount_end = amount_end

            # Remaining fuel
            amount_curr = f"{self.fuel_units(minfo.fuel.amountCurrent):.{self.decimals[1]}f}"
            self.update_fuel(
                self.bar_fuel_curr, amount_curr, self.last_amount_curr,
                self.bar_style_fuel_curr[
                    minfo.fuel.estimatedLaps <= self.wcfg["low_fuel_lap_threshold"]])
            self.last_amount_curr = amount_curr

            # Total needed fuel
            amount_need = f"{calc.sym_range(self.fuel_units(minfo.fuel.amountNeeded), 9999):+.{self.decimals[2]}f}"
            self.update_fuel(
                self.bar_fuel_need, amount_need, self.last_amount_need,
                self.bar_style_fuel_need[
                minfo.fuel.estimatedLaps <= self.wcfg["low_fuel_lap_threshold"]])
            self.last_amount_need = amount_need

            # Estimated fuel consumption
            used_last = f"{self.fuel_units(minfo.fuel.estimatedConsumption):.{self.decimals[3]}f}"
            self.update_fuel(
                self.bar_fuel_used, used_last, self.last_used_last)
            self.last_used_last = used_last

            # Delta fuel consumption
            delta_fuel = f"{self.fuel_units(minfo.fuel.deltaConsumption):+.{self.decimals[4]}f}"
            self.update_fuel(
                self.bar_fuel_delta, delta_fuel, self.last_delta_fuel)
            self.last_delta_fuel = delta_fuel

            # Estimate pit stop counts when pitting at end of current lap
            est_pits_early = f"{min(max(minfo.fuel.estimatedNumPitStopsEarly, 0), 99.99):.{self.decimals[5]}f}"
            self.update_fuel(
                self.bar_fuel_early, est_pits_early, self.last_est_pits_early)
            self.last_est_pits_early = est_pits_early

            # Estimated laps current fuel can last
            est_runlaps = f"{min(minfo.fuel.estimatedLaps, 9999):.{self.decimals[6]}f}"
            self.update_fuel(
                self.bar_fuel_laps, est_runlaps, self.last_est_runlaps)
            self.last_est_runlaps = est_runlaps

            # Estimated minutes current fuel can last
            est_runmins = f"{min(minfo.fuel.estimatedMinutes, 9999):.{self.decimals[7]}f}"
            self.update_fuel(
                self.bar_fuel_mins, est_runmins, self.last_est_runmins)
            self.last_est_runmins = est_runmins

            # Estimated one less pit fuel consumption
            fuel_save = f"{min(max(self.fuel_units(minfo.fuel.oneLessPitConsumption), 0), 99.99):.{self.decimals[8]}f}"
            self.update_fuel(
                self.bar_fuel_save, fuel_save, self.last_fuel_save)
            self.last_fuel_save = fuel_save

            # Estimate pit stop counts when pitting at end of current stint
            est_pits_end = f"{min(max(minfo.fuel.estimatedNumPitStopsEnd, 0), 99.99):.{self.decimals[9]}f}"
            self.update_fuel(
                self.bar_fuel_pits, est_pits_end, self.last_est_pits_end)
            self.last_est_pits_end = est_pits_end

            # Fuel level bar
            if self.wcfg["show_fuel_level_bar"]:
                level_capacity = minfo.fuel.capacity
                level_curr = minfo.fuel.amountCurrent
                level_start = minfo.fuel.amountStart
                level_refill = level_curr + minfo.fuel.amountNeeded

                level_state = round(level_start * level_refill, 3)
                if level_capacity and level_state != self.last_level_state:
                    self.draw_fuel_level(
                        level_curr / level_capacity,
                        level_start / level_capacity,
                        level_refill / level_capacity,
                    )
                    self.last_level_state = level_state

    # GUI update methods
    def update_fuel(self, target_bar, curr, last, color=None):
        """Update fuel data"""
        if curr != last:
            if color:  # low fuel warning
                target_bar.setStyleSheet(color)
            target_bar.setText(curr[:self.bar_width].strip("."))

    def draw_fuel_level(self, fuel_curr, fuel_start, fuel_refill):
        """Fuel level"""
        self.pixmap_fuel_level.fill(self.wcfg["bkg_color_fuel_level"])
        painter = QPainter(self.pixmap_fuel_level)
        painter.setPen(Qt.NoPen)

        # Update fuel level highlight
        self.rect_fuel_left.setWidth(fuel_curr * self.fuel_level_width)
        painter.fillRect(self.rect_fuel_left, self.wcfg["highlight_color_fuel_level"])

        # Update starting fuel level mark
        if self.wcfg["show_starting_fuel_level_mark"]:
            self.rect_fuel_start.moveLeft(fuel_start * self.fuel_level_width)
            painter.fillRect(self.rect_fuel_start, self.wcfg["starting_fuel_level_mark_color"])

        if self.wcfg["show_refueling_level_mark"]:
            self.rect_fuel_refuel.moveLeft(fuel_refill * self.fuel_level_width)
            painter.fillRect(self.rect_fuel_refuel, self.wcfg["refueling_level_mark_color"])

        self.fuel_level.setPixmap(self.pixmap_fuel_level)

    # Additional methods
    def fuel_units(self, fuel):
        """2 different fuel unit conversion, default is Liter"""
        if self.cfg.units["fuel_unit"] == "Gallon":
            return calc.liter2gallon(fuel)
        return fuel

    @staticmethod
    def decimal_range(value):
        """Decimal place range"""
        return min(max(int(value), 0), 3)
