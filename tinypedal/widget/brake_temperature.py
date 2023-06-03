#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2023  Xiang
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
Brake temperature Widget
"""

from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QFont, QFontMetrics
from PySide2.QtWidgets import (
    QGridLayout,
    QLabel,
)

from .. import calculation as calc
from .. import validator as val
from .. import readapi as read_data
from ..base import Widget

WIDGET_NAME = "brake_temperature"


class Draw(Widget):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Widget.__init__(self, config, WIDGET_NAME)

        # Config font
        self.font = QFont()
        self.font.setFamily(self.wcfg['font_name'])
        self.font.setPixelSize(self.wcfg['font_size'])
        font_w = QFontMetrics(self.font).averageCharWidth()

        # Config variable
        text_def = "n/a"
        bar_padx = round(self.wcfg["font_size"] * self.wcfg["bar_padding"])
        bar_gap = self.wcfg["bar_gap"]
        inner_gap = self.wcfg["inner_gap"]
        self.leading_zero = min(max(self.wcfg["leading_zero"], 1), 3)
        self.sign_text = "°" if self.wcfg["show_degree_sign"] else ""

        if self.cfg.units["temperature_unit"] == "Fahrenheit":
            text_width = 4 + len(self.sign_text)
        else:
            text_width = 3 + len(self.sign_text)

        self.bar_width = font_w * text_width

        # Base style
        self.heatmap = list(self.load_heatmap().items())

        self.setStyleSheet(
            f"font-family: {self.wcfg['font_name']};"
            f"font-size: {self.wcfg['font_size']}px;"
            f"font-weight: {self.wcfg['font_weight']};"
            f"padding: 0 {bar_padx}px;"
        )

        # Create layout
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)  # remove border
        layout_btemp = QGridLayout()
        layout_btavg = QGridLayout()
        layout_btemp.setSpacing(inner_gap)
        layout_btavg.setSpacing(inner_gap)
        layout.setSpacing(bar_gap)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        column_btemp = self.wcfg["column_index_temperature"]
        column_btavg = self.wcfg["column_index_average"]

        # Brake temperature
        bar_style_btemp = (
            f"color: {self.wcfg['font_color_temperature']};"
            f"background: {self.wcfg['bkg_color_temperature']};"
            f"min-width: {self.bar_width}px;"
        )
        self.bar_btemp_fl = QLabel(text_def)
        self.bar_btemp_fl.setAlignment(Qt.AlignCenter)
        self.bar_btemp_fl.setStyleSheet(bar_style_btemp)
        self.bar_btemp_fr = QLabel(text_def)
        self.bar_btemp_fr.setAlignment(Qt.AlignCenter)
        self.bar_btemp_fr.setStyleSheet(bar_style_btemp)
        self.bar_btemp_rl = QLabel(text_def)
        self.bar_btemp_rl.setAlignment(Qt.AlignCenter)
        self.bar_btemp_rl.setStyleSheet(bar_style_btemp)
        self.bar_btemp_rr = QLabel(text_def)
        self.bar_btemp_rr.setAlignment(Qt.AlignCenter)
        self.bar_btemp_rr.setStyleSheet(bar_style_btemp)

        layout_btemp.addWidget(self.bar_btemp_fl, 0, 0)
        layout_btemp.addWidget(self.bar_btemp_fr, 0, 1)
        layout_btemp.addWidget(self.bar_btemp_rl, 1, 0)
        layout_btemp.addWidget(self.bar_btemp_rr, 1, 1)

        # Average brake temperature
        if self.wcfg["show_average"]:
            bar_style_btavg = (
                f"color: {self.wcfg['font_color_average']};"
                f"background: {self.wcfg['bkg_color_average']};"
                f"min-width: {self.bar_width}px;"
            )
            self.bar_btavg_fl = QLabel(text_def)
            self.bar_btavg_fl.setAlignment(Qt.AlignCenter)
            self.bar_btavg_fl.setStyleSheet(bar_style_btavg)
            self.bar_btavg_fr = QLabel(text_def)
            self.bar_btavg_fr.setAlignment(Qt.AlignCenter)
            self.bar_btavg_fr.setStyleSheet(bar_style_btavg)
            self.bar_btavg_rl = QLabel(text_def)
            self.bar_btavg_rl.setAlignment(Qt.AlignCenter)
            self.bar_btavg_rl.setStyleSheet(bar_style_btavg)
            self.bar_btavg_rr = QLabel(text_def)
            self.bar_btavg_rr.setAlignment(Qt.AlignCenter)
            self.bar_btavg_rr.setStyleSheet(bar_style_btavg)

            layout_btavg.addWidget(self.bar_btavg_fl, 0, 0)
            layout_btavg.addWidget(self.bar_btavg_fr, 0, 1)
            layout_btavg.addWidget(self.bar_btavg_rl, 1, 0)
            layout_btavg.addWidget(self.bar_btavg_rr, 1, 1)

        # Set layout
        if self.wcfg["layout"] == 0:
            # Vertical layout
            layout.addLayout(layout_btemp, column_btemp, 0)
            if self.wcfg["show_average"]:
                layout.addLayout(layout_btavg, column_btavg, 0)
        else:
            # Horizontal layout
            layout.addLayout(layout_btemp, 0, column_btemp)
            if self.wcfg["show_average"]:
                layout.addLayout(layout_btavg, 0, column_btavg)
        self.setLayout(layout)

        # Last data
        self.checked = False
        self.last_lap_stime = 0
        self.last_lap_etime = 0
        self.btavg_samples = 1  # number of temperature samples
        self.highlight_timer_start = 0  # sector timer start

        self.last_btemp = [-273.15] * 4
        self.last_btavg = [0] * 4

        # Set widget state & start update
        self.set_widget_state()
        self.update_timer.start()

    @Slot()
    def update_data(self):
        """Update when vehicle on track"""
        if self.wcfg["enable"] and read_data.state():

            # Reset switch
            if not self.checked:
                self.checked = True

            # Read brake temperature data
            btemp = read_data.brake_temp()

            # Brake temperature
            self.update_btemp("btemp_fl", btemp[0], self.last_btemp[0])
            self.update_btemp("btemp_fr", btemp[1], self.last_btemp[1])
            self.update_btemp("btemp_rl", btemp[2], self.last_btemp[2])
            self.update_btemp("btemp_rr", btemp[3], self.last_btemp[3])
            self.last_btemp = btemp

            # Brake average temperature
            if self.wcfg["show_average"]:
                lap_stime, lap_etime = read_data.lap_timestamp()

                if lap_stime != self.last_lap_stime:  # time stamp difference
                    self.last_lap_stime = lap_stime  # reset time stamp counter
                    self.btavg_samples = 1
                    self.highlight_timer_start = lap_etime  # start timer

                    # Highlight reading
                    self.update_btavg("btavg_fl", self.last_btavg[0], 0, 1)
                    self.update_btavg("btavg_fr", self.last_btavg[1], 0, 1)
                    self.update_btavg("btavg_rl", self.last_btavg[2], 0, 1)
                    self.update_btavg("btavg_rr", self.last_btavg[3], 0, 1)

                # Update if time diff
                if lap_etime > self.last_lap_etime:
                    self.last_lap_etime = lap_etime
                    self.btavg_samples += 1
                    btavg = tuple(map(calc.average_value,
                                      self.last_btavg,
                                      btemp,
                                      [self.btavg_samples]*4
                                      ))
                else:
                    btavg = self.last_btavg

                # Update highlight timer
                if self.highlight_timer_start:
                    highlight_timer = lap_etime - self.highlight_timer_start
                    if highlight_timer >= self.wcfg["highlight_duration"]:
                        self.highlight_timer_start = 0  # stop timer
                else:
                    # Update average reading
                    self.update_btavg("btavg_fl", btavg[0], self.last_btavg[0])
                    self.update_btavg("btavg_fr", btavg[1], self.last_btavg[1])
                    self.update_btavg("btavg_rl", btavg[2], self.last_btavg[2])
                    self.update_btavg("btavg_rr", btavg[3], self.last_btavg[3])
                    self.last_btavg = btavg
        else:
            if self.checked:
                self.checked = False
                self.last_lap_stime = 0
                self.last_lap_etime = 0
                self.btavg_samples = 1
                self.highlight_timer_start = 0
                self.last_btavg = [0] * 4

    # GUI update methods
    def update_btemp(self, suffix, curr, last):
        """Brake temperature"""
        if round(curr) != round(last):
            if self.wcfg["swap_style"]:
                color = (f"color: {self.color_heatmap(curr)};"
                         f"background: {self.wcfg['bkg_color_temperature']};")
            else:
                color = (f"color: {self.wcfg['font_color_temperature']};"
                         f"background: {self.color_heatmap(curr)};")

            sign = "°" if self.wcfg["show_degree_sign"] else ""

            getattr(self, f"bar_{suffix}").setText(
                f"{self.temp_units(curr):0{self.leading_zero}.0f}{sign}")

            getattr(self, f"bar_{suffix}").setStyleSheet(
                f"{color}min-width: {self.bar_width}px;")

    def update_btavg(self, suffix, curr, last, highlighted=0):
        """Brake average temperature"""
        if round(curr) != round(last):
            if highlighted:
                color = (f"color: {self.wcfg['font_color_highlighted']};"
                         f"background: {self.wcfg['bkg_color_highlighted']};")
            else:
                color = (f"color: {self.wcfg['font_color_average']};"
                         f"background: {self.wcfg['bkg_color_average']};")

            getattr(self, f"bar_{suffix}").setText(
                f"{self.temp_units(curr):02.0f}{self.sign_text}")

            getattr(self, f"bar_{suffix}").setStyleSheet(color)

    # Additional methods
    def temp_units(self, value):
        """Temperature units"""
        if self.cfg.units["temperature_unit"] == "Fahrenheit":
            return calc.celsius2fahrenheit(value)
        return value

    def load_heatmap(self):
        """Load heatmap dict"""
        if self.wcfg["heatmap_name"] in self.cfg.heatmap_user:
            heatmap = self.cfg.heatmap_user[self.wcfg["heatmap_name"]]
            if val.verify_heatmap(heatmap):
                return heatmap
        return self.cfg.heatmap_default["brake_default"]

    def color_heatmap(self, temp):
        """Heatmap color"""
        return calc.color_heatmap(self.heatmap, temp)