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
Tyre inner layer temperature Widget
"""

from .. import calculation as calc
from .. import heatmap as hmp
from ..api_control import api
from ..const_common import TEXT_PLACEHOLDER, TEXT_NA
from ._base import Overlay


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config, widget_name):
        # Assign base setting
        super().__init__(config, widget_name)
        layout = self.set_grid_layout(
            gap_hori=self.wcfg["horizontal_gap"],
            gap_vert=self.wcfg["vertical_gap"],
        )
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        inner_gap = self.wcfg["inner_gap"]
        self.leading_zero = min(max(self.wcfg["leading_zero"], 1), 3)
        self.sign_text = "°" if self.wcfg["show_degree_sign"] else ""
        text_width = 3 + len(self.sign_text) + (self.cfg.units["temperature_unit"] == "Fahrenheit")

        # Base style
        self.setStyleSheet(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )
        bar_style_tcmpd = self.set_qss(
            fg_color=self.wcfg["font_color_tyre_compound"],
            bg_color=self.wcfg["bkg_color_tyre_compound"]
        )
        bar_style_itemp = self.set_qss(
            fg_color=self.wcfg["font_color_inner_layer"],
            bg_color=self.wcfg["bkg_color_inner_layer"]
        )

        # Heatmap style list: 0 - fl, 1 - fr, 2 - rl, 3 - rr
        self.heatmap_styles = 4 * [
            hmp.load_heatmap_style(
                heatmap_name=self.wcfg["heatmap_name"],
                default_name=hmp.HEATMAP_DEFAULT_TYRE,
                swap_style=self.wcfg["swap_style"],
                fg_color=self.wcfg["font_color_inner_layer"],
                bg_color=self.wcfg["bkg_color_inner_layer"],
            )
        ]

        # Tyre inner temperature
        self.bars_itemp = self.set_table(
            text=TEXT_NA,
            style=bar_style_itemp,
            width=font_m.width * text_width + bar_padx,
            layout=layout,
            inner_gap=inner_gap,
        )

        # Tyre compound
        if self.wcfg["show_tyre_compound"]:
            self.bars_tcmpd = self.set_qlabel(
                text=TEXT_PLACEHOLDER,
                style=bar_style_tcmpd,
                width=font_m.width + bar_padx,
                count=2,
            )
            self.set_grid_layout_vert(
                layout=layout,
                targets=self.bars_tcmpd,
            )

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if self.state.active:

            # Tyre compound
            if self.wcfg["show_tyre_compound"]:
                class_name = api.read.vehicle.class_name()
                tcmpd_name = api.read.tyre.compound_name()
                for cmpd_idx, bar_tcmpd in enumerate(self.bars_tcmpd):
                    self.update_tcmpd(bar_tcmpd, f"{class_name} - {tcmpd_name[cmpd_idx]}", cmpd_idx * 2)

            # Inner layer temperature: 0 - fl, 3 - fr, 6 - rl, 9 - rr
            if self.wcfg["show_inner_center_outer"]:
                itemp = api.read.tyre.inner_temperature_ico()
                for tyre_idx, bar_itemp in enumerate(self.bars_itemp):
                    self.update_itemp(bar_itemp, round(itemp[tyre_idx]), tyre_idx // 3)
            else:  # 0 - fl, 1 - fr, 2 - rl, 3 - rr
                itemp = api.read.tyre.inner_temperature_avg()
                for tyre_idx, bar_itemp in enumerate(self.bars_itemp):
                    self.update_itemp(bar_itemp, round(itemp[tyre_idx]), tyre_idx)

    # GUI update methods
    def update_itemp(self, target, data, index):
        """Tyre inner temperature"""
        if target.last != data:
            target.last = data
            target.setText(self.format_temperature(data))
            target.setStyleSheet(calc.select_grade(self.heatmap_styles[index], data))

    def update_tcmpd(self, target, data, index):
        """Tyre compound"""
        if target.last != data:
            target.last = data
            target.setText(hmp.select_compound_symbol(data))
            # Update heatmap style
            if self.wcfg["enable_heatmap_auto_matching"]:
                heatmap_style = hmp.load_heatmap_style(
                    heatmap_name=hmp.select_tyre_heatmap_name(data),
                    default_name=hmp.HEATMAP_DEFAULT_TYRE,
                    swap_style=self.wcfg["swap_style"],
                    fg_color=self.wcfg["font_color_inner_layer"],
                    bg_color=self.wcfg["bkg_color_inner_layer"],
                )
                self.heatmap_styles[index] = heatmap_style
                self.heatmap_styles[index + 1] = heatmap_style

    # GUI generate methods
    def set_table(self, text, style, width, layout, inner_gap):
        """Set table"""
        if self.wcfg["show_inner_center_outer"]:
            layout_inner = tuple(self.set_grid_layout(gap=inner_gap) for _ in range(4))
            bar_set = self.set_qlabel(
                text=text,
                style=style,
                width=width,
                count=12,  # 3 x 4 tyres
                last=0,
            )
            for idx, inner in enumerate(layout_inner):
                self.set_grid_layout_table_row(inner, bar_set[idx * 3:idx * 3 + 3])
            self.set_grid_layout_quad(layout, layout_inner)
        else:
            bar_set = self.set_qlabel(
                text=text,
                style=style,
                width=width,
                count=4,
                last=0,
            )
            self.set_grid_layout_quad(layout, bar_set)
        return bar_set

    # Additional methods
    def format_temperature(self, value):
        """Format temperature"""
        if value < -100:
            return TEXT_PLACEHOLDER
        if self.cfg.units["temperature_unit"] == "Fahrenheit":
            return f"{calc.celsius2fahrenheit(value):0{self.leading_zero}.0f}{self.sign_text}"
        return f"{value:0{self.leading_zero}.0f}{self.sign_text}"
